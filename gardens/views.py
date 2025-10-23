from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import anthropic
from .models import Garden, Plant, PlantInstance, PlantingNote
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

    # Build plant database for export feature
    plant_database = []
    export_plants = Plant.objects.filter(
        Q(is_default=True) | Q(created_by=request.user)
    ).exclude(plant_type='utility').prefetch_related('companion_plants')

    for plant in export_plants:
        companions = [c.name for c in plant.companion_plants.all()]
        plant_info = {
            'name': plant.name,
            'type': plant.plant_type,
            'spacing': plant.spacing_inches,
            'companions': companions,
            'pest_deterrent': plant.pest_deterrent_for if plant.pest_deterrent_for else None,
            'chicago_notes': plant.chicago_notes[:100] if plant.chicago_notes else None
        }
        plant_database.append(plant_info)

    plant_database_json = json.dumps(plant_database)

    # Check if user has API key configured
    has_api_key = False
    if request.user.is_authenticated:
        try:
            has_api_key = bool(request.user.profile.anthropic_api_key)
        except Exception:
            has_api_key = False

    # Get PlantInstance data for date tracking
    plant_instances = garden.plant_instances.select_related('plant').all()

    # Create mapping of grid position to instance data
    instance_map = {}
    for instance in plant_instances:
        instance_map[f"{instance.row},{instance.col}"] = {
            'id': instance.id,
            'planted_date': instance.planted_date.isoformat() if instance.planted_date else None,
            'expected_harvest_date': instance.expected_harvest_date.isoformat() if instance.expected_harvest_date else None,
            'actual_harvest_date': instance.actual_harvest_date.isoformat() if instance.actual_harvest_date else None,
            'harvest_status': instance.harvest_status(),
            'days_until_harvest': instance.days_until_harvest(),
            'plant_name': instance.plant.name,
            'plant_id': instance.plant.id,
        }

    instance_map_json = json.dumps(instance_map)

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
        'plant_database_json': plant_database_json,
        'has_api_key': has_api_key,
        'instance_map_json': instance_map_json,
        'plant_instances': plant_instances,
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
@require_POST
def garden_clear(request, pk):
    """Clear all plants from a garden layout"""
    try:
        garden = get_object_or_404(Garden, pk=pk, owner=request.user)

        # Create empty grid based on garden dimensions
        empty_grid = [[''] * garden.width for _ in range(garden.height)]

        # Update garden layout with empty grid
        garden.layout_data = {'grid': empty_grid}
        garden.save()

        return JsonResponse({
            'success': True,
            'message': 'Garden layout has been cleared successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


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
    """AJAX endpoint to save garden layout changes and sync PlantInstance records"""
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

        # Sync PlantInstance records with the new grid
        # Get existing instances for this garden
        existing_instances = {(inst.row, inst.col): inst for inst in garden.plant_instances.all()}

        # Track which positions still have plants
        current_positions = set()

        # Process each cell in the grid
        for row_idx, row in enumerate(grid):
            for col_idx, cell_value in enumerate(row):
                # Skip empty cells, paths, and utility plants
                if not cell_value or cell_value.lower() in ['path', 'empty space', '=', '•', '']:
                    continue

                current_positions.add((row_idx, col_idx))

                # Try to find the Plant object for this cell
                plant = Plant.objects.filter(
                    Q(name__iexact=cell_value) | Q(symbol__iexact=cell_value)
                ).first()

                if plant:
                    # Check if instance already exists at this position
                    if (row_idx, col_idx) in existing_instances:
                        # Update existing instance if plant changed
                        instance = existing_instances[(row_idx, col_idx)]
                        if instance.plant != plant:
                            # Plant changed - preserve dates if user moved the plant, clear if different plant
                            instance.plant = plant
                            instance.save()
                    else:
                        # Check if this plant was moved from another position (preserve dates)
                        moved_instance = None
                        for pos, inst in existing_instances.items():
                            if inst.plant == plant and pos not in current_positions:
                                # This plant was likely moved
                                moved_instance = inst
                                break

                        if moved_instance:
                            # Update position, preserve dates
                            moved_instance.row = row_idx
                            moved_instance.col = col_idx
                            moved_instance.save()
                            current_positions.add((moved_instance.row, moved_instance.col))
                        else:
                            # New plant placement - create instance without dates
                            PlantInstance.objects.create(
                                garden=garden,
                                plant=plant,
                                row=row_idx,
                                col=col_idx
                            )

        # Remove instances that no longer have plants
        for pos, instance in existing_instances.items():
            if pos not in current_positions:
                instance.delete()

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

        # Get plants already in garden with their positions
        plants_in_garden = set()
        garden_grid_visual = []
        for row_idx, row in enumerate(grid_data):
            visual_row = []
            for col_idx, cell in enumerate(row):
                if cell and cell.lower() not in ['path', 'empty space', '=', '•', '']:
                    plants_in_garden.add(cell.lower())
                    # Pad to exactly 3 characters for uniform spacing
                    visual_row.append(cell[:3].upper().ljust(3, ' '))
                elif cell and cell.lower() in ['path']:
                    visual_row.append('===')
                else:
                    visual_row.append('___')
            garden_grid_visual.append(' | '.join(visual_row))

        # Build comprehensive plant database for Claude
        plant_database = []
        all_plants = Plant.objects.filter(
            Q(is_default=True) | Q(created_by=request.user)
        ).exclude(plant_type='utility').prefetch_related('companion_plants')

        for plant in all_plants:
            companions = [c.name for c in plant.companion_plants.all()]
            plant_info = {
                'name': plant.name,
                'type': plant.plant_type,
                'spacing': plant.spacing_inches,
                'companions': companions,
                'pest_deterrent': plant.pest_deterrent_for if plant.pest_deterrent_for else None,
                'chicago_notes': plant.chicago_notes[:100] if plant.chicago_notes else None
            }
            plant_database.append(plant_info)

        # Build prompt for Claude
        prompt = f"""You are a Chicago garden planning assistant (USDA zones 5b/6a). Your goal is to create a COMPREHENSIVE garden layout by filling ALL empty spaces with companion plants.

GARDEN INFORMATION:
- Size: {garden.width} columns × {garden.height} rows ({garden.width * garden.height} total cells)
- Empty cells to fill: {len(empty_cells)} cells
- Existing plants: {len(plants_in_garden)} plants

CURRENT GARDEN LAYOUT:
{chr(10).join(garden_grid_visual)}

(Legend: ___ = empty space, === = path, ABC = plant abbreviation)

EXISTING PLANTS AND THEIR COMPANIONS:
{chr(10).join([f"- {p}" for p in plants_in_garden]) if plants_in_garden else "None (empty garden)"}

AVAILABLE PLANTS DATABASE:
{json.dumps(plant_database, indent=2)}

YOUR TASK:
Create a comprehensive garden layout by filling ALL {len(empty_cells)} empty spaces with appropriate companion plants. Consider:

1. **Companion Planting**: Place companions near existing plants (check the 'companions' field)
2. **Pest Management**: Use pest deterrent plants strategically (check 'pest_deterrent' field)
3. **Plant Spacing**: Respect spacing requirements (check 'spacing' field)
4. **Variety**: Include vegetables, herbs, and flowers for a balanced ecosystem
5. **Chicago Climate**: All plants are pre-selected for zones 5b/6a
6. **Maximize Yield**: Fill all spaces efficiently - don't waste any cells!

RESPONSE FORMAT:
Return a JSON object with ALL {len(empty_cells)} empty cells filled:

{{
    "reasoning": "Brief explanation of your comprehensive planting strategy (3-4 sentences explaining companion groupings, pest management approach, and layout logic)",
    "suggestions": [
        {{"plant_name": "Tomato", "row": 0, "col": 1, "reason": "Central placement for companion grouping"}},
        {{"plant_name": "Basil", "row": 0, "col": 2, "reason": "Companions with tomato, pest deterrent"}},
        ... (continue for ALL {len(empty_cells)} empty cells)
    ]
}}

IMPORTANT:
- Provide exactly {len(empty_cells)} suggestions to fill every empty space
- Only use plant names from the available plants database
- Ensure row/col coordinates match empty cell positions: {empty_cells[:20]}{'...' if len(empty_cells) > 20 else ''}
- Create logical companion groupings across the garden
- Be comprehensive - fill the entire garden!"""

        # Call Claude API using user's API key
        client = anthropic.Anthropic(api_key=user_api_key)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,  # Increased for comprehensive layouts
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


@login_required
@require_POST
def set_planting_date(request, pk):
    """API endpoint to set planting date for a plant instance"""
    try:
        garden = get_object_or_404(Garden, pk=pk, owner=request.user)
        data = json.loads(request.body)

        row = data.get('row')
        col = data.get('col')
        planted_date_str = data.get('planted_date')

        if row is None or col is None:
            return JsonResponse({
                'success': False,
                'error': 'Row and column are required'
            }, status=400)

        # Get the plant instance at this position
        try:
            instance = PlantInstance.objects.get(garden=garden, row=row, col=col)
        except PlantInstance.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No plant found at this position'
            }, status=404)

        # Parse and set the planted date
        if planted_date_str:
            from datetime import datetime
            instance.planted_date = datetime.fromisoformat(planted_date_str).date()

            # Auto-calculate expected harvest date
            if instance.plant.days_to_harvest:
                instance.calculate_expected_harvest_date()
        else:
            # Clear dates if empty string provided
            instance.planted_date = None
            instance.expected_harvest_date = None

        instance.save()

        # Return updated instance data
        return JsonResponse({
            'success': True,
            'instance': {
                'id': instance.id,
                'planted_date': instance.planted_date.isoformat() if instance.planted_date else None,
                'expected_harvest_date': instance.expected_harvest_date.isoformat() if instance.expected_harvest_date else None,
                'actual_harvest_date': instance.actual_harvest_date.isoformat() if instance.actual_harvest_date else None,
                'harvest_status': instance.harvest_status(),
                'days_until_harvest': instance.days_until_harvest(),
            }
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
def mark_harvested(request, pk):
    """API endpoint to mark a plant as harvested"""
    try:
        garden = get_object_or_404(Garden, pk=pk, owner=request.user)
        data = json.loads(request.body)

        row = data.get('row')
        col = data.get('col')
        actual_harvest_date_str = data.get('actual_harvest_date')

        if row is None or col is None:
            return JsonResponse({
                'success': False,
                'error': 'Row and column are required'
            }, status=400)

        # Get the plant instance at this position
        try:
            instance = PlantInstance.objects.get(garden=garden, row=row, col=col)
        except PlantInstance.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'No plant found at this position'
            }, status=404)

        # Set actual harvest date
        if actual_harvest_date_str:
            from datetime import datetime
            instance.actual_harvest_date = datetime.fromisoformat(actual_harvest_date_str).date()
        else:
            # If no date provided, use today
            from datetime import date
            instance.actual_harvest_date = date.today()

        instance.save()

        # Return updated instance data
        return JsonResponse({
            'success': True,
            'instance': {
                'id': instance.id,
                'planted_date': instance.planted_date.isoformat() if instance.planted_date else None,
                'expected_harvest_date': instance.expected_harvest_date.isoformat() if instance.expected_harvest_date else None,
                'actual_harvest_date': instance.actual_harvest_date.isoformat() if instance.actual_harvest_date else None,
                'harvest_status': instance.harvest_status(),
                'days_until_harvest': instance.days_until_harvest(),
            }
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