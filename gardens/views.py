from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Garden, Plant, PlantingNote


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
    notes = garden.notes.select_related('plant').order_by('-note_date')[:5]

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

    # Calculate fill rate
    total_spaces = garden.width * garden.height
    plant_count = garden.get_plant_count()
    fill_rate = (plant_count / total_spaces * 100) if total_spaces > 0 else 0

    context = {
        'garden': garden,
        'grid_data': grid_data,
        'notes': notes,
        'plants_in_garden': plants_in_garden,
        'can_edit': request.user.is_authenticated and garden.owner == request.user,
        'fill_rate': fill_rate,
    }

    return render(request, 'gardens/garden_detail.html', context)


@login_required
def garden_create(request):
    """Create a new garden"""
    return render(request, 'gardens/garden_form.html', {'action': 'Create'})


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

    if season:
        plants = plants.filter(planting_season=season)

    context = {
        'plants': plants.distinct(),
        'search_query': search_query,
        'plant_type_filter': plant_type,
        'season_filter': season,
        'plant_types': Plant.PLANT_TYPES,
        'seasons': Plant.SEASONS,
    }

    return render(request, 'gardens/plant_library.html', context)


@login_required
def plant_create(request):
    """Create a new plant"""
    return render(request, 'gardens/plant_form.html', {'action': 'Create'})


@login_required
def plant_edit(request, pk):
    """Edit a plant"""
    plant = get_object_or_404(Plant, pk=pk)

    # Only allow editing if user owns it or it's not a default plant
    if plant.is_default and not request.user.is_staff:
        messages.error(request, 'You cannot edit default plants.')
        return redirect('gardens:plant_library')

    if plant.created_by and plant.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You can only edit your own plants.')
        return redirect('gardens:plant_library')

    return render(request, 'gardens/plant_form.html', {'plant': plant, 'action': 'Edit'})


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