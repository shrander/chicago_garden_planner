from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import anthropic
from .models import Garden, Plant, PlantInstance, PlantingNote, GardenShare
from .forms import GardenForm, PlantForm, PlantingNoteForm
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone


@login_required
def garden_list(request):
    """Display all public gardens and user's own gardens"""

    # Get filter parameters
    search_query = request.GET.get('search', '')
    size_filter = request.GET.get('size', '')

    # Base queryset - public gardens OR user's own gardens
    if request.user.is_authenticated:
        gardens = Garden.objects.filter(  # type: ignore[attr-defined]
            Q(is_public=True) | Q(owner=request.user)
        ).select_related('owner').order_by('-updated_at')  # type: ignore[attr-defined]
    else:
        gardens = Garden.objects.filter(is_public=True).select_related('owner').order_by('-updated_at')  # type: ignore[attr-defined]

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

    # Get garden (must be public OR owned by current user OR shared with user)
    garden = get_object_or_404(Garden, pk=pk)

    # Check permissions (public OR owner OR shared with user)
    is_owner = garden.owner == request.user
    is_shared = False
    can_edit = False

    if request.user.is_authenticated:
        # Check if garden is shared with this user
        share = GardenShare.objects.filter(
            garden=garden,
            shared_with_user=request.user,
            accepted_at__isnull=False
        ).first()

        if share:
            is_shared = True
            can_edit = share.permission == 'edit'

    # Allow access if: public OR owner OR shared
    if not garden.is_public and not is_owner and not is_shared:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden('You do not have permission to view this garden.')

    # Owner has full edit rights
    if is_owner:
        can_edit = True

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

    # Calculate fill rate and statistics
    total_spaces = garden.width * garden.height
    plant_count = garden.get_plant_count()
    fill_rate = (plant_count / total_spaces * 100) if total_spaces > 0 else 0

    # Calculate detailed statistics
    plant_counts_detail = {}
    plant_type_stats_detail = {}
    path_cells_count = 0
    empty_cells_count = 0

    # Get all plants for type lookup
    all_plants_for_stats = Plant.objects.filter(
        Q(is_default=True) | Q(created_by=request.user)
    ).exclude(plant_type='utility')
    plant_type_lookup = {p.name.lower(): p.plant_type for p in all_plants_for_stats}

    for row in grid_data:
        for cell in row:
            if cell and cell.lower() not in ['empty space', '•', '']:
                if cell.lower() == 'path' or cell == '=':
                    path_cells_count += 1
                else:
                    # Count each plant
                    plant_lower = cell.lower()
                    plant_counts_detail[plant_lower] = plant_counts_detail.get(plant_lower, 0) + 1

                    # Count by type
                    plant_type = plant_type_lookup.get(plant_lower, 'unknown')
                    plant_type_stats_detail[plant_type] = plant_type_stats_detail.get(plant_type, 0) + 1
            else:
                empty_cells_count += 1

    diversity = len(plant_counts_detail)

    # Create a mapping of plant names to yield information
    plant_yields = {}
    for plant in all_plants_for_stats:
        plant_yields[plant.name.lower()] = plant

    # Create a mapping of plant names to their symbols, colors, and timing data for the grid display
    plant_map = {}
    for plant in Plant.objects.all():
        plant_map[plant.name.lower()] = {
            'symbol': plant.symbol,
            'color': plant.color,
            'name': plant.name,
            'direct_sow': plant.direct_sow,
            'days_to_germination': plant.days_to_germination,
            'days_before_transplant_ready': plant.days_before_transplant_ready,
            'transplant_to_harvest_days': plant.transplant_to_harvest_days,
            'days_to_harvest': plant.days_to_harvest,
            'sq_ft_spacing': plant.sq_ft_spacing,
            'row_spacing_inches': plant.row_spacing_inches,
            'row_spacing_between_rows': plant.row_spacing_between_rows,
            'spacing_inches': plant.spacing_inches,
            'yield_per_plant': plant.yield_per_plant,
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
            'days_to_harvest': plant.days_to_harvest,
            'planting_seasons': plant.planting_seasons,
            'life_cycle': plant.life_cycle,
            'companions': companions,
            'pest_deterrent': plant.pest_deterrent_for if plant.pest_deterrent_for else None
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
    plant_instances = garden.plant_instances.select_related('plant').all() # pyright: ignore[reportAttributeAccessIssue]

    # Create mapping of grid position to instance data
    instance_map = {}
    for instance in plant_instances:
        expected_transplant_date = instance.calculate_expected_transplant_date()
        instance_map[f"{instance.row},{instance.col}"] = {
            'id': instance.id,
            'seed_starting_method': instance.seed_starting_method,
            'planned_seed_start_date': instance.planned_seed_start_date.isoformat() if instance.planned_seed_start_date else None,
            'planned_planting_date': instance.planned_planting_date.isoformat() if instance.planned_planting_date else None,
            'seed_started_date': instance.seed_started_date.isoformat() if instance.seed_started_date else None,
            'planted_date': instance.planted_date.isoformat() if instance.planted_date else None,
            'expected_transplant_date': expected_transplant_date.isoformat() if expected_transplant_date else None,
            'expected_harvest_date': instance.expected_harvest_date.isoformat() if instance.expected_harvest_date else None,
            'actual_harvest_date': instance.actual_harvest_date.isoformat() if instance.actual_harvest_date else None,
            'harvest_status': instance.harvest_status(),
            'days_until_harvest': instance.days_until_harvest(),
            'plant_name': instance.plant.name,
            'plant_id': instance.plant.id,
            'plant_direct_sow': instance.plant.direct_sow,
        }

    instance_map_json = json.dumps(instance_map)

    # Get zone-specific information for export functionality
    from gardens.utils import get_user_frost_dates, get_growing_season_info

    user_zone = request.user.profile.gardening_zone if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.gardening_zone else '5b'
    frost_dates = get_user_frost_dates(request.user) if request.user.is_authenticated else None
    climate_info = get_growing_season_info(user_zone)

    context = {
        'garden': garden,
        'grid_data': grid_data,
        'notes': notes,
        'plants_in_garden': plants_in_garden,
        'all_plants': all_plants,
        'utility_plants': utility_plants,
        'can_edit': can_edit,
        'is_owner': is_owner,
        'is_shared': is_shared,
        'fill_rate': fill_rate,
        'plant_map_json': plant_map_json,
        'plant_map': plant_map,  # Python dict for template lookup
        'plant_database_json': plant_database_json,
        'has_api_key': has_api_key,
        'instance_map_json': instance_map_json,
        'plant_instances': plant_instances,
        # Statistics
        'diversity': diversity,
        'plant_counts_detail': plant_counts_detail,
        'plant_type_stats_detail': plant_type_stats_detail,
        'path_cells_count': path_cells_count,
        'empty_cells_count': empty_cells_count,
        'total_spaces': total_spaces,
        'plant_count': plant_count,
        'plant_yields': plant_yields,
        # Zone-specific data for export
        'user_zone': user_zone,
        'frost_dates': frost_dates,
        'climate_info': climate_info,
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
            Q(latin_name__icontains=search_query)
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

    # Process pest susceptibility list
    pest_susceptibility_list = []
    if plant.pest_susceptibility:
        pest_susceptibility_list = [pest.strip() for pest in plant.pest_susceptibility.split(',') if pest.strip()]

    # Get zone-specific data for user's zone
    from gardens.utils import get_default_zone
    user_zone = None
    zone_data = None

    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        user_zone = request.user.profile.gardening_zone
    else:
        user_zone = get_default_zone()

    if user_zone:
        zone_data = plant.zone_data.filter(zone=user_zone).first() # pyright: ignore[reportAttributeAccessIssue]

    context = {
        'plant': plant,
        'can_edit': can_edit,
        'companions': companions,
        'companion_to': companion_to,
        'pest_list': pest_list,
        'pest_susceptibility_list': pest_susceptibility_list,
        'user_zone': user_zone,
        'zone_data': zone_data,
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
        garden = get_object_or_404(Garden, pk=pk)

        # Check permissions: must be owner OR have edit share permission
        is_owner = garden.owner == request.user
        can_edit = is_owner

        if not is_owner:
            # Check if user has edit permission via share
            share = GardenShare.objects.filter(
                garden=garden,
                shared_with_user=request.user,
                permission='edit',
                accepted_at__isnull=False
            ).first()

            if share:
                can_edit = True

        if not can_edit:
            return JsonResponse({
                'success': False,
                'error': 'You do not have permission to edit this garden'
            }, status=403)

        # Parse JSON data from request body
        data = json.loads(request.body)
        grid = data.get('grid', [])
        planted_dates = data.get('planted_dates', {})

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
        existing_instances = {(inst.row, inst.col): inst for inst in garden.plant_instances.all()} # pyright: ignore[reportAttributeAccessIssue]

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
                    # Check if planted_date was provided for this position
                    position_key = f"{row_idx},{col_idx}"
                    provided_date = planted_dates.get(position_key)

                    # Check if instance already exists at this position
                    if (row_idx, col_idx) in existing_instances:
                        # Update existing instance if plant changed
                        instance = existing_instances[(row_idx, col_idx)]
                        if instance.plant != plant:
                            # Plant changed - preserve dates if user moved the plant, clear if different plant
                            instance.plant = plant
                            instance.save()

                        # Update planned_planting_date if provided (AI suggestions are planned dates)
                        if provided_date:
                            from datetime import datetime
                            instance.planned_planting_date = datetime.fromisoformat(provided_date).date()
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
                            # Update position, preserve dates (unless new date provided)
                            moved_instance.row = row_idx
                            moved_instance.col = col_idx
                            if provided_date:
                                from datetime import datetime
                                moved_instance.planned_planting_date = datetime.fromisoformat(provided_date).date()
                            moved_instance.save()
                            current_positions.add((moved_instance.row, moved_instance.col))
                        else:
                            # New plant placement - create instance with optional planned date
                            new_instance = PlantInstance(
                                garden=garden,
                                plant=plant,
                                row=row_idx,
                                col=col_idx
                            )
                            if provided_date:
                                from datetime import datetime
                                new_instance.planned_planting_date = datetime.fromisoformat(provided_date).date()
                            new_instance.save()

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
def garden_update_info(request, pk):
    """AJAX endpoint to update garden description and garden_type"""
    try:
        garden = get_object_or_404(Garden, pk=pk, owner=request.user)

        # Parse JSON data from request body
        data = json.loads(request.body)

        # Update description if provided
        if 'description' in data:
            description = data.get('description', '').strip()
            garden.description = description

        # Update garden_type if provided
        if 'garden_type' in data:
            garden_type = data.get('garden_type', '').strip()
            # Validate garden_type
            valid_types = [choice[0] for choice in Garden.GARDEN_TYPES]
            if garden_type not in valid_types:
                return JsonResponse({
                    'success': False,
                    'error': f'Invalid garden type. Must be one of: {", ".join(valid_types)}'
                }, status=400)
            garden.garden_type = garden_type

        # Save changes
        garden.save()

        return JsonResponse({
            'success': True,
            'message': 'Garden information updated successfully',
            'description': garden.description,
            'garden_type': garden.garden_type,
            'garden_type_display': garden.get_garden_type_display() # pyright: ignore[reportAttributeAccessIssue]
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

        # Get plants already in garden with their positions and dates
        plants_in_garden = set()
        garden_grid_visual = []
        planted_instances_info = []
        plant_counts = {}
        plant_type_stats = {}
        total_planted_cells = 0
        path_cells = 0

        # Get PlantInstance data for date tracking
        from .models import PlantInstance
        instances = PlantInstance.objects.filter(garden=garden).select_related('plant')
        instance_map = {(inst.row, inst.col): inst for inst in instances}

        # Get all plants for lookup
        all_plants_lookup = Plant.objects.filter(
            Q(is_default=True) | Q(created_by=request.user)
        ).exclude(plant_type='utility')
        plant_lookup = {p.name.lower(): p for p in all_plants_lookup}

        for row_idx, row in enumerate(grid_data):
            visual_row = []
            for col_idx, cell in enumerate(row):
                if cell and cell.lower() not in ['path', 'empty space', '=', '•', '']:
                    plants_in_garden.add(cell.lower())
                    total_planted_cells += 1

                    # Count occurrences of each plant
                    plant_lower = cell.lower()
                    plant_counts[plant_lower] = plant_counts.get(plant_lower, 0) + 1

                    # Count by plant type
                    plant_obj = plant_lookup.get(plant_lower)
                    if plant_obj:
                        plant_type = plant_obj.plant_type
                        plant_type_stats[plant_type] = plant_type_stats.get(plant_type, 0) + 1

                    # Pad to exactly 3 characters for uniform spacing
                    visual_row.append(cell[:3].upper().ljust(3, ' '))

                    # Check for planted instance data
                    instance = instance_map.get((row_idx, col_idx))
                    if instance:
                        # Use actual planted date if available, otherwise use planned
                        effective_planted_date = instance.planted_date or instance.planned_planting_date
                        if effective_planted_date:
                            planted_instances_info.append({
                                'plant': cell,
                                'row': row_idx,
                                'col': col_idx,
                                'planted_date': effective_planted_date.isoformat(),
                                'is_planned': instance.planted_date is None,  # Flag to indicate if date is planned
                                'expected_harvest': instance.expected_harvest_date.isoformat() if instance.expected_harvest_date else None,
                                'status': instance.harvest_status(),
                                'days_until_harvest': instance.days_until_harvest()
                            })
                elif cell and cell.lower() in ['path']:
                    path_cells += 1
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
                'days_to_harvest': plant.days_to_harvest,
                'planting_seasons': plant.planting_seasons,
                'life_cycle': plant.life_cycle,
                'companions': companions,
                'pest_deterrent': plant.pest_deterrent_for if plant.pest_deterrent_for else None,
                'pest_susceptibility': plant.pest_susceptibility if plant.pest_susceptibility else None
            }
            plant_database.append(plant_info)

        # Calculate garden statistics
        total_cells = garden.width * garden.height
        fill_rate = round((total_planted_cells / total_cells) * 100, 1) if total_cells > 0 else 0
        diversity = len(plants_in_garden)

        # Format statistics section
        stats_info = "\n\nGARDEN STATISTICS:\n"
        stats_info += f"- Total planted cells: {total_planted_cells}/{total_cells} ({fill_rate}% full)\n"
        stats_info += f"- Plant diversity: {diversity} unique species\n"
        stats_info += f"- Empty spaces: {len(empty_cells)}\n"
        stats_info += f"- Paths: {path_cells}\n"

        if plant_type_stats:
            type_list = ', '.join([f"{count} {ptype}" for ptype, count in plant_type_stats.items()])
            stats_info += f"- By type: {type_list}\n"

        if plant_counts:
            sorted_counts = sorted(plant_counts.items(), key=lambda x: x[1], reverse=True)
            count_list = ', '.join([f"{count}x {plant}" for plant, count in sorted_counts])
            stats_info += f"- Plant counts: {count_list}\n"

        # Format planted instances info
        planted_info = ""
        if planted_instances_info:
            planted_info = "\n\nPLANTED CROPS WITH DATES:\n"
            for inst in planted_instances_info:
                date_type = "planned" if inst.get('is_planned') else "planted"
                planted_info += f"- {inst['plant']} at ({inst['row']},{inst['col']}): {date_type} {inst['planted_date']}"
                if inst['expected_harvest']:
                    planted_info += f", expected harvest {inst['expected_harvest']}"
                    if inst['days_until_harvest'] is not None:
                        planted_info += f" ({inst['days_until_harvest']} days)"
                planted_info += f" [{inst['status']}]\n"

        # Get zone-specific climate information
        from gardens.utils import get_user_frost_dates, get_growing_season_info, get_default_zone

        user_zone = request.user.profile.gardening_zone if hasattr(request.user, 'profile') and request.user.profile.gardening_zone else get_default_zone()
        frost_dates = get_user_frost_dates(request.user)
        climate_info = get_growing_season_info(user_zone)

        # Format climate information for prompt
        climate_context = f"""
CLIMATE ZONE: {user_zone}
- Last Frost Date: {frost_dates['last_frost'].strftime('%B %d')}
- First Frost Date: {frost_dates['first_frost'].strftime('%B %d')}
- Growing Season: {climate_info['growing_season_days'] if climate_info else 153} days"""

        if climate_info and climate_info.get('special_considerations'):
            climate_context += f"\n- Special Considerations: {climate_info['special_considerations']}"

        # Build prompt for Claude
        prompt = f"""You are a garden planning assistant for USDA zone {user_zone}. Your goal is to create a COMPREHENSIVE garden layout by filling ALL empty spaces with companion plants.
{climate_context}

GARDEN INFORMATION:
- Size: {garden.width} columns × {garden.height} rows ({garden.width * garden.height} total cells)
- Empty cells to fill: {len(empty_cells)} cells
- Current plants: {len(plants_in_garden)} unique species{stats_info}

CURRENT GARDEN LAYOUT:
{chr(10).join(garden_grid_visual)}

(Legend: ___ = empty space, === = path, ABC = plant abbreviation)

EXISTING PLANTS AND THEIR COMPANIONS:
{chr(10).join([f"- {p}" for p in plants_in_garden]) if plants_in_garden else "None (empty garden)"}{planted_info}

AVAILABLE PLANTS DATABASE:
{json.dumps(plant_database, indent=2)}

YOUR TASK:
Create a comprehensive garden layout by filling ALL {len(empty_cells)} empty spaces with appropriate companion plants. Consider:

1. **Companion Planting**: Place companions near existing plants (check the 'companions' field)
2. **Pest Management**: Use pest deterrent plants strategically (check 'pest_deterrent' field)
3. **Plant Spacing**: Respect spacing requirements (check 'spacing' field)
4. **Variety**: Include vegetables, herbs, and flowers for a balanced ecosystem
5. **Climate Zone**: All plants are pre-selected for zone {user_zone} - consider the growing season and frost dates above
6. **Succession Planting**: Consider planting dates and harvest times (days_to_harvest field) - suggest plants to replace crops nearing harvest{'(see PLANTED CROPS section above)' if planted_instances_info else ''}
7. **Maximize Yield**: Fill all spaces efficiently - don't waste any cells!

RESPONSE FORMAT:
Return a JSON object with ALL {len(empty_cells)} empty cells filled:

{{
    "reasoning": "Brief explanation of your comprehensive planting strategy (3-4 sentences explaining companion groupings, pest management approach, and layout logic)",
    "suggestions": [
        {{"plant_name": "Tomato", "row": 0, "col": 1, "reason": "Central placement for companion grouping", "planted_date": "2025-04-15"}},
        {{"plant_name": "Basil", "row": 0, "col": 2, "reason": "Companions with tomato, pest deterrent", "planted_date": "2025-04-15"}},
        ... (continue for ALL {len(empty_cells)} empty cells)
    ]
}}

IMPORTANT:
- Provide exactly {len(empty_cells)} suggestions to fill every empty space
- Only use plant names from the available plants database
- Ensure row/col coordinates match empty cell positions: {empty_cells[:20]}{'...' if len(empty_cells) > 20 else ''}
- Create logical companion groupings across the garden
- Include "planted_date" field (YYYY-MM-DD format) for each suggestion if planting date is relevant
- The system supports both PLANNED and ACTUAL dates - your suggested planted_date will be stored as a planned date
- The system will auto-calculate expected_harvest_date based on the plant's days_to_harvest
- planted_date is OPTIONAL - omit it if you're just suggesting plant placement without dates
- If suggesting succession planting, include planted_date to indicate when to plant
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
        response_text = message.content[0].text # pyright: ignore[reportAttributeAccessIssue]

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
        seed_starting_method = data.get('seed_starting_method')
        planned_seed_start_date_str = data.get('planned_seed_start_date')
        planned_planting_date_str = data.get('planned_planting_date')
        seed_started_date_str = data.get('seed_started_date')
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

        from datetime import datetime

        # Set seed starting method
        if seed_starting_method:
            instance.seed_starting_method = seed_starting_method
        else:
            instance.seed_starting_method = None

        # Parse and set planned seed start date
        if planned_seed_start_date_str:
            instance.planned_seed_start_date = datetime.fromisoformat(planned_seed_start_date_str).date()
        else:
            instance.planned_seed_start_date = None

        # Parse and set planned planting date
        if planned_planting_date_str:
            instance.planned_planting_date = datetime.fromisoformat(planned_planting_date_str).date()
        else:
            instance.planned_planting_date = None

        # Parse and set actual seed started date
        if seed_started_date_str:
            instance.seed_started_date = datetime.fromisoformat(seed_started_date_str).date()
        else:
            instance.seed_started_date = None

        # Parse and set actual planted date
        if planted_date_str:
            instance.planted_date = datetime.fromisoformat(planted_date_str).date()
        else:
            instance.planted_date = None

        # Clear expected harvest if no planted date (actual or planned)
        if not instance.planted_date and not instance.planned_planting_date:
            instance.expected_harvest_date = None

        instance.save()

        # Calculate expected transplant date for display (not stored)
        expected_transplant_date = instance.calculate_expected_transplant_date()

        # Return updated instance data
        return JsonResponse({
            'success': True,
            'instance': {
                'id': instance.id, # pyright: ignore[reportAttributeAccessIssue]
                'seed_starting_method': instance.seed_starting_method,
                'planned_seed_start_date': instance.planned_seed_start_date.isoformat() if instance.planned_seed_start_date else None, # pyright: ignore[reportOptionalMemberAccess]
                'planned_planting_date': instance.planned_planting_date.isoformat() if instance.planned_planting_date else None, # pyright: ignore[reportOptionalMemberAccess]
                'seed_started_date': instance.seed_started_date.isoformat() if instance.seed_started_date else None, # pyright: ignore[reportOptionalMemberAccess]
                'planted_date': instance.planted_date.isoformat() if instance.planted_date else None, # pyright: ignore[reportOptionalMemberAccess]
                'expected_transplant_date': expected_transplant_date.isoformat() if expected_transplant_date else None,
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

        # Calculate expected transplant date for display
        expected_transplant_date = instance.calculate_expected_transplant_date()

        # Return updated instance data
        return JsonResponse({
            'success': True,
            'instance': {
                'id': instance.id, # pyright: ignore[reportAttributeAccessIssue]
                'seed_started_date': instance.seed_started_date.isoformat() if instance.seed_started_date else None,
                'planted_date': instance.planted_date.isoformat() if instance.planted_date else None,
                'expected_transplant_date': expected_transplant_date.isoformat() if expected_transplant_date else None,
                'expected_harvest_date': instance.expected_harvest_date.isoformat() if instance.expected_harvest_date else None,
                'actual_harvest_date': instance.actual_harvest_date.isoformat() if instance.actual_harvest_date else None, # pyright: ignore[reportOptionalMemberAccess]
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
def garden_share(request, pk):
    """Share a garden with another user by email"""
    # get_object_or_404 will raise Http404 if garden not found or not owned by user
    # Let this exception propagate (don't catch it in try/except)
    garden = get_object_or_404(Garden, pk=pk, owner=request.user)

    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        permission = data.get('permission', 'view')

        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required'}, status=400)

        # Check if already shared with this email
        if GardenShare.objects.filter(garden=garden, shared_with_email=email).exists():
            return JsonResponse({'success': False, 'error': 'Garden already shared with this email'}, status=400)

        # Check if user exists
        User = get_user_model()
        try:
            shared_user = User.objects.get(email__iexact=email)
            # User exists - create share and mark as accepted
            share = GardenShare.objects.create(
                garden=garden,
                shared_with_email=email,
                shared_with_user=shared_user,
                permission=permission,
                shared_by=request.user,
                accepted_at=timezone.now()
            )
            message = f'Garden shared with {email}. They already have an account!'
        except User.DoesNotExist:
            # User doesn't exist - create pending share and send invitation
            share = GardenShare.objects.create(
                garden=garden,
                shared_with_email=email,
                permission=permission,
                shared_by=request.user
            )

            # Send invitation email
            share_url = request.build_absolute_uri(f'/accounts/register/?email={email}&garden_share={share.id}') # pyright: ignore[reportAttributeAccessIssue]
            send_mail(
                subject=f'{request.user.username} shared a garden with you on Chicago Garden Planner',
                message=f"""Hello!

{request.user.username} has invited you to {permission} their garden "{garden.name}" on Chicago Garden Planner.

To accept this invitation, please create an account using this email address:
{share_url}

If you already have an account, please log in at:
{request.build_absolute_uri('/accounts/login/')}

Happy gardening!
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            message = f'Invitation sent to {email}. They will need to register or log in to access the garden.'

        return JsonResponse({
            'success': True,
            'message': message,
            'share': {
                'id': share.id, # pyright: ignore[reportAttributeAccessIssue]
                'email': share.shared_with_email,
                'permission': share.permission,
                'accepted': share.accepted_at is not None
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def garden_shares_list(request, pk):
    """Get list of shares for a garden"""
    garden = get_object_or_404(Garden, pk=pk, owner=request.user)

    shares = GardenShare.objects.filter(garden=garden).select_related('shared_with_user')
    shares_data = [{
        'id': share.id, # pyright: ignore[reportAttributeAccessIssue]
        'email': share.shared_with_email,
        'permission': share.permission,
        'accepted': share.accepted_at is not None,
        'shared_by': share.shared_by.username,
        'created_at': share.created_at.isoformat()
    } for share in shares]

    return JsonResponse({'success': True, 'shares': shares_data})


@login_required
@require_POST
def garden_share_revoke(request, pk, share_id):
    """Revoke a garden share"""
    garden = get_object_or_404(Garden, pk=pk, owner=request.user)
    share = get_object_or_404(GardenShare, pk=share_id, garden=garden)

    share.delete()

    return JsonResponse({'success': True, 'message': 'Share revoked successfully'})
