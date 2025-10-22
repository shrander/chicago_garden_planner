from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import anthropic
from .models import Garden, Plant, PlantingNote
from .forms import GardenForm, PlantForm, PlantingNoteForm


@login_required
def garden_list(request):
    """Display all public gardens and user's own gardens"""

    # Get filter parameters
    search_query = request.GET.get('search', '')
    size_filter = request.GET.get('size', '')

    # Base queryset - public gardens OR user's own gardens
    if request.user.is_authenticated:
        gardens = Garden.objects.filter(
            Q(is_public=True) | Q(owner=request.user)
        ).select_related('owner').order_by('-updated_at')
    else:
        gardens = Garden.objects.filter(is_public=True).select_related('owner').order_by('-updated_at')

    # Apply search filter
    if search_query:
        gardens = gardens.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(owner__username__icontains=search_query)
        )

    # Apply size filter
    if size_filter:
        gardens = gardens.filter(size=size_filter)

    # Get unique sizes for filter dropdown
    available_sizes = Garden.GARDEN_SIZES

    context = {
        'gardens': gardens,
        'search_query': search_query,
        'size_filter': size_filter,
        'available_sizes': available_sizes,
    }

    return render(request, 'gardens/garden_list.html', context)


@login_required
def garden_detail(request, pk):
    """Display garden detail with grid layout"""

    # Get garden (must be public OR owned by current user)
    garden = get_object_or_404(Garden, pk=pk)

    # Check permissions
    if not garden.is_public and garden.owner != request.user:
        messages.error(request, 'You do not have permission to view this garden.')
        return redirect('gardens:garden_list')

    # Get grid data
    grid_data = garden.layout_data.get('grid', []) if garden.layout_data else []

    # Get planting notes for this garden
    notes = garden.notes.select_related('plant').order_by('-note_date')[:5]  # type: ignore[attr-defined]

    # Get unique plants in this garden
    unique_plants = set()
    for row in grid_data:
        for cell in row:
            if cell and cell.lower() not in ['path', 'empty space', '=', '•', '']:
                unique_plants.add(cell.lower())

    # Try to match plant names to actual Plant objects
    plants_in_garden = []
    for plant_name in unique_plants:
        try:
            plant = Plant.objects.filter(
                Q(name__iexact=plant_name) | Q(symbol__iexact=plant_name)
            ).first()
            if plant:
                plants_in_garden.append(plant)
        except Plant.DoesNotExist:
            pass

    # Get all available plants for the plant library (if user can edit)
    all_plants = []
    utility_plants = []
    if request.user.is_authenticated and garden.owner == request.user:
        # Get utility plants (Empty Space, Path) - these go at the top
        utility_plants = Plant.objects.filter(
            plant_type='utility',
            is_default=True
        ).order_by('name')

        # Get all other plants (non-utility) sorted alphabetically
        all_plants = Plant.objects.filter(
            Q(is_default=True) | Q(created_by=request.user)
        ).exclude(plant_type='utility').order_by('name')  # Sort alphabetically by common name

    # Calculate fill rate
    total_spaces = garden.width * garden.height
    plant_count = garden.get_plant_count()
    fill_rate = (plant_count / total_spaces * 100) if total_spaces > 0 else 0

    # Create a mapping of plant names to their symbols and colors for the grid display
    plant_map = {}
    for plant in Plant.objects.all():
        plant_map[plant.name.lower()] = {
            'symbol': plant.symbol,
            'color': plant.color,
            'name': plant.name
        }

    # Convert plant_map to JSON string for JavaScript
    import json
    plant_map_json = json.dumps(plant_map)

    context = {
        'garden': garden,
        'grid_data': grid_data,
        'notes': notes,
        'plants_in_garden': plants_in_garden,
        'all_plants': all_plants,
        'utility_plants': utility_plants,
        'can_edit': request.user.is_authenticated and garden.owner == request.user,
        'fill_rate': fill_rate,
        'plant_map_json': plant_map_json,
        'plant_map': plant_map,  # Python dict for template lookup
    }

    return render(request, 'gardens/garden_detail.html', context)


@login_required
def garden_create(request):
    """Create a new garden"""
    if request.method == 'POST':
        form = GardenForm(request.POST)
        if form.is_valid():
            garden = form.save(commit=False)
            garden.owner = request.user
            garden.save()
            messages.success(request, f'Garden "{garden.name}" has been created successfully!')
            return redirect('gardens:garden_detail', pk=garden.pk)
        else:
            # If form is invalid, show errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
            return redirect('gardens:garden_list')
    else:
        # GET request - redirect to garden list (modal is shown there)
        return redirect('gardens:garden_list')


@login_required
def garden_edit(request, pk):
    """Edit an existing garden"""
    garden = get_object_or_404(Garden, pk=pk, owner=request.user)
    return render(request, 'gardens/garden_form.html', {'garden': garden, 'action': 'Edit'})


@login_required
def garden_delete(request, pk):
    """Delete a garden"""
    garden = get_object_or_404(Garden, pk=pk, owner=request.user)

    if request.method == 'POST':
        garden_name = garden.name
        garden.delete()
        messages.success(request, f'Garden "{garden_name}" has been deleted.')
        return redirect('gardens:garden_list')

    return render(request, 'gardens/garden_confirm_delete.html', {'garden': garden})


@login_required
def garden_duplicate(request, pk):
    """Duplicate a garden"""
    from django.http import JsonResponse

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        original_garden = get_object_or_404(Garden, pk=pk, owner=request.user)

        # Create a copy of the garden
        new_garden = Garden.objects.create(
            name=f"{original_garden.name} (Copy)",
            description=original_garden.description,
            owner=request.user,
            size=original_garden.size,
            width=original_garden.width,
            height=original_garden.height,
            layout_data=original_garden.layout_data,  # JSONField is copied by value
            is_public=False  # New copy is private by default
        )

        return JsonResponse({
            'success': True,
            'garden_id': new_garden.pk,
            'garden_name': new_garden.name
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def plant_library(request):
    """Display plant library"""

    search_query = request.GET.get('search', '')
    plant_type = request.GET.get('type', '')
    season = request.GET.get('season', '')

    # Get plants
    plants = Plant.objects.filter(is_default=True).order_by('name')

    # Add user's custom plants if authenticated
    if request.user.is_authenticated:
        user_plants = Plant.objects.filter(created_by=request.user).order_by('name')
        plants = plants | user_plants

    # Apply filters
    if search_query:
        plants = plants.filter(
            Q(name__icontains=search_query) |
            Q(latin_name__icontains=search_query) |
            Q(chicago_notes__icontains=search_query)
        )

    if plant_type:
        plants = plants.filter(plant_type=plant_type)

    # Get all plants and convert to list for filtering
    plants_list = list(plants.distinct())

    # Filter by season in Python (SQLite doesn't support JSONField contains)
    if season:
        plants_list = [p for p in plants_list if p.planting_seasons and season in p.planting_seasons]

    context = {
        'plants': plants_list,
        'search_query': search_query,
        'plant_type_filter': plant_type,
        'season_filter': season,
        'plant_types': Plant.PLANT_TYPES,
        'seasons': Plant.SEASONS,
    }

    return render(request, 'gardens/plant_library.html', context)


@login_required
def plant_detail(request, pk):
    """Display plant detail page"""
    plant = get_object_or_404(Plant, pk=pk)

    # Check if user can edit this plant
    can_edit = request.user.is_superuser or (plant.created_by == request.user if plant.created_by else False)

    # Get companion plants
    companions = plant.companion_plants.all()

    # Get plants that list this as a companion
    companion_to = Plant.objects.filter(companion_plants=plant)

    # Process pest deterrent list
    pest_list = []
    if plant.pest_deterrent_for:
        pest_list = [pest.strip() for pest in plant.pest_deterrent_for.split(',') if pest.strip()]

    context = {
        'plant': plant,
        'can_edit': can_edit,
        'companions': companions,
        'companion_to': companion_to,
        'pest_list': pest_list,
    }

    return render(request, 'gardens/plant_detail.html', context)


@login_required
def plant_create(request):
    """Create a new plant"""
    if request.method == 'POST':
        form = PlantForm(request.POST)
        if form.is_valid():
            plant = form.save(commit=False)
            plant.created_by = request.user
            plant.is_default = request.user.is_superuser  # Only superusers can create default plants
            plant.save()
            form.save_m2m()  # Save many-to-many relationships
            messages.success(request, f'Plant "{plant.name}" has been created successfully!')
            return redirect('gardens:plant_detail', pk=plant.pk)
    else:
        form = PlantForm()

    return render(request, 'gardens/plant_form.html', {'form': form, 'action': 'Create'})


@login_required
def plant_edit(request, pk):
    """Edit a plant"""
    plant = get_object_or_404(Plant, pk=pk)

    # Only allow editing if user owns it or is superuser
    if plant.is_default and not request.user.is_superuser:
        messages.error(request, 'You cannot edit default plants. Only superusers can edit system plants.')
        return redirect('gardens:plant_library')

    if plant.created_by and plant.created_by != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own plants.')
        return redirect('gardens:plant_library')

    if request.method == 'POST':
        form = PlantForm(request.POST, instance=plant)
        if form.is_valid():
            updated_plant = form.save(commit=False)
            # Superusers can toggle is_default, others cannot
            if not request.user.is_superuser:
                updated_plant.is_default = plant.is_default
            updated_plant.save()
            form.save_m2m()
            messages.success(request, f'Plant "{updated_plant.name}" has been updated successfully!')
            return redirect('gardens:plant_detail', pk=updated_plant.pk)
    else:
        form = PlantForm(instance=plant)

    return render(request, 'gardens/plant_form.html', {'form': form, 'plant': plant, 'action': 'Edit'})


@login_required
def plant_delete(request, pk):
    """Delete a plant"""
    plant = get_object_or_404(Plant, pk=pk)

    # Only allow deleting if user owns it
    if plant.is_default:
        messages.error(request, 'You cannot delete default plants.')
        return redirect('gardens:plant_library')

    if plant.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You can only delete your own plants.')
        return redirect('gardens:plant_library')

    if request.method == 'POST':
        plant_name = plant.name
        plant.delete()
        messages.success(request, f'Plant "{plant_name}" has been deleted.')
        return redirect('gardens:plant_library')

    return render(request, 'gardens/plant_confirm_delete.html', {'plant': plant})


@login_required
@require_POST
def garden_save_layout(request, pk):
    """AJAX endpoint to save garden layout changes"""
    try:
        garden = get_object_or_404(Garden, pk=pk, owner=request.user)

        # Parse JSON data from request body
        data = json.loads(request.body)
        grid = data.get('grid', [])

        # Validate grid dimensions
        if len(grid) != garden.height:
            return JsonResponse({
                'success': False,
                'error': f'Grid height mismatch. Expected {garden.height}, got {len(grid)}'
            }, status=400)

        for row in grid:
            if len(row) != garden.width:
                return JsonResponse({
                    'success': False,
                    'error': f'Grid width mismatch. Expected {garden.width}, got {len(row)}'
                }, status=400)

        # Update garden layout
        garden.layout_data = {'grid': grid}
        garden.save()

        return JsonResponse({
            'success': True,
            'message': 'Garden layout saved successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def garden_update_name(request, pk):
    """AJAX endpoint to update garden name"""
    try:
        garden = get_object_or_404(Garden, pk=pk, owner=request.user)

        # Parse JSON data from request body
        data = json.loads(request.body)
        new_name = data.get('name', '').strip()

        # Validate name
        if not new_name:
            return JsonResponse({
                'success': False,
                'error': 'Garden name cannot be empty'
            }, status=400)

        if len(new_name) > 100:
            return JsonResponse({
                'success': False,
                'error': 'Garden name must be 100 characters or less'
            }, status=400)

        # Update garden name
        garden.name = new_name
        garden.save()

        return JsonResponse({
            'success': True,
            'message': 'Garden name updated successfully',
            'name': garden.name
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_POST
def garden_ai_assistant(request, pk):
    """AI assistant endpoint to get garden layout suggestions from Claude"""
    try:
        garden = get_object_or_404(Garden, pk=pk, owner=request.user)

        # Check if user has configured their API key
        user_api_key = request.user.profile.anthropic_api_key
        if not user_api_key:
            return JsonResponse({
                'success': False,
                'error': 'API key not configured',
                'error_type': 'no_api_key',
                'message': 'Please add your Anthropic API key in your profile settings to use AI Garden Assistant features.'
            }, status=400)

        # Get grid data
        grid_data = garden.layout_data.get('grid', []) if garden.layout_data else []

        # Find empty spaces
        empty_cells = []
        for row_idx, row in enumerate(grid_data):
            for col_idx, cell in enumerate(row):
                if not cell or cell.lower() in ['empty space', '=', '•', '']:
                    empty_cells.append({'row': row_idx, 'col': col_idx})

        # Get plants already in garden
        plants_in_garden = set()
        for row in grid_data:
            for cell in row:
                if cell and cell.lower() not in ['path', 'empty space', '=', '•', '']:
                    plants_in_garden.add(cell.lower())

        # Get available plants with details
        available_plants = Plant.objects.filter(
            Q(is_default=True) | Q(created_by=request.user)
        ).exclude(plant_type='utility').values(
            'name', 'latin_name', 'plant_type', 'planting_seasons',
            'spacing_inches', 'chicago_notes', 'pest_deterrent_for'
        )

        # Get companion relationships
        companion_data = []
        for plant_name in plants_in_garden:
            plant = Plant.objects.filter(Q(name__iexact=plant_name) | Q(symbol__iexact=plant_name)).first()
            if plant:
                companions = list(plant.companion_plants.values_list('name', flat=True))
                if companions:
                    companion_data.append({
                        'plant': plant.name,
                        'companions': companions
                    })

        # Build prompt for Claude
        prompt = f"""You are a Chicago garden planning assistant (USDA zones 5b/6a).

I have a garden that is {garden.width}x{garden.height} grid cells.
Current state:
- Empty cells available: {len(empty_cells)} cells at positions: {empty_cells[:10]}{'...' if len(empty_cells) > 10 else ''}
- Plants already in garden: {', '.join(plants_in_garden) if plants_in_garden else 'None'}
- Companion relationships: {companion_data}

Available plants to suggest:
{list(available_plants)[:20]}

Please suggest plants to fill some of the empty spaces, considering:
1. Companion planting relationships with existing plants
2. Chicago climate suitability (zones 5b/6a)
3. Spacing requirements
4. Pest management
5. Seasonal planting appropriateness

Respond with a JSON object in this exact format:
{{
    "reasoning": "Brief explanation of your strategy (2-3 sentences)",
    "suggestions": [
        {{"plant_name": "Tomato", "row": 0, "col": 1, "reason": "Companions with existing basil, heat-tolerant"}},
        {{"plant_name": "Marigold", "row": 1, "col": 2, "reason": "Pest deterrent for nearby vegetables"}}
    ]
}}

Only suggest 3-5 plants maximum. Only use plant names from the available plants list."""

        # Call Claude API using user's API key
        client = anthropic.Anthropic(api_key=user_api_key)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse Claude's response
        response_text = message.content[0].text

        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group())
        else:
            suggestions = json.loads(response_text)

        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })

    except anthropic.AuthenticationError as e:
        return JsonResponse({
            'success': False,
            'error': 'Invalid API key',
            'error_type': 'invalid_api_key',
            'message': 'Your Anthropic API key is invalid or has expired. Please update it in your profile settings.'
        }, status=401)
    except anthropic.PermissionDeniedError as e:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied',
            'error_type': 'permission_denied',
            'message': 'Your API key does not have permission to access this resource.'
        }, status=403)
    except anthropic.RateLimitError as e:
        return JsonResponse({
            'success': False,
            'error': 'Rate limit exceeded',
            'error_type': 'rate_limit',
            'message': 'You have exceeded the rate limit for your API key. Please try again later.'
        }, status=429)
    except json.JSONDecodeError as e:
        return JsonResponse({
            'success': False,
            'error': f'Failed to parse AI response: {str(e)}'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)