from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class Plant(models.Model):
    """Plant library with Chicago-specific growing info"""

    PLANT_TYPES = [
        ('utility', 'Utility'),
        ('vegetable', 'Vegetable'),
        ('herb', 'Herb'),
        ('flower', 'Flower'),
        ('fruit', 'Fruit'),
        ('companion', 'Companion Plant'),
        ('cover_crop', 'Cover Crop'),
    ]

    SEASONS = [
        ('spring', 'Spring'),
        ('summer', 'Summer'),
        ('fall', 'Fall'),
        ('winter', 'Winter'),
        ('year_round', 'Year Round'),
    ]

    name = models.CharField(max_length=100)
    latin_name = models.CharField(max_length=150)
    symbol = models.CharField(max_length=2, help_text='1-2 character symbol for grid')
    color = models.CharField(max_length=7, default='#90EE90', help_text='Hex color code')
    plant_type = models.CharField(max_length=20, choices=PLANT_TYPES)

    # Chicago specific growing info
    planting_seasons = models.JSONField(
        default=list,
        help_text='List of seasons when this plant can be planted (e.g., ["spring", "fall"])'
    )
    days_to_harvest = models.IntegerField(null=True, blank=True)
    spacing_inches = models.FloatField(help_text='Spacing between plants in inches')
    chicago_notes = models.TextField(blank=True, help_text='Chicago Zone 5b/6a specific notes')

    # Companion planting
    companion_plants = models.ManyToManyField('self', blank=True, symmetrical=False)
    pest_deterrent_for = models.TextField(blank=True, help_text='Comma-separated list of pests deterred')

    # User management 
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    is_default = models.BooleanField(default=False, help_text='Default system plant')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['name', 'created_by'] # Users can't have duplicate plant names

    def __str__(self):
        return f"{self.name} ({self.latin_name})"
    
    def get_absolute_url(self):
        return reverse('plant_detail', kwargs={'pk': self.pk})
    
class Garden(models.Model):
    """User's garden layout"""

    GARDEN_SIZES = [
        ('4x4', '4\' x 4\' (16 sq ft)'),
        ('4x8', '4\' x 8\' (32 sq ft)'),
        ('8x8', '8\' x 8\' (64 sq ft)'),
        ('10x10', '10\' x 10\' (100 sq ft)'),
        ('custom', 'Custom Size'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gardens')

    # Garden specifications 
    size = models.CharField(max_length=20, choices=GARDEN_SIZES, default='10x10')
    width = models.IntegerField(default=10, help_text='Width in feet')
    height = models.IntegerField(default=10, help_text='Height in feet')

    # Layout data (json field storing 20 array)
    layout_data = models.JSONField(default=dict, help_text='Grid layout as JSON')

    # Metadata
    is_public = models.BooleanField(default=False, help_text='Allow others to view this garden')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return f"{self.name} ({self.owner.username})"
    
    def get_absolute_url(self):
        return reverse('garden_detail', kwargs={'pk': self.pk})
    
    def get_grid_size(self):
        """Return tuple of (rows, cols) for the garden grid"""
        if self.size == 'custom':
            return (self.height, self.width)
        else:
            h, w = self.size.split('x')
            return (int(h), int(w))

    def get_plant_count(self):
        """Count total plants in the garden layout (excluding paths and empty spaces)"""
        if not self.layout_data or 'grid' not in self.layout_data:
            return 0

        count = 0
        grid = self.layout_data.get('grid', [])
        for row in grid:
            for cell in row:
                # Don't count paths, empty spaces, or empty cells
                if cell and cell.lower() not in ['path', 'empty space', '=', '•', '']:
                    count += 1
        return count


class PlantingNote(models.Model):
    """Journal entries for specific plants in gardens"""

    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, related_name='notes')
    plant = models.ForeignKey(Plant, on_delete=models.SET_NULL, null=True, blank=True)

    # Note content
    title = models.CharField(max_length=200, blank=True)
    note_text = models.TextField(help_text='Your observations, tasks, or reminders')

    # Optional metadata
    grid_position = models.CharField(
        max_length=10,
        blank=True,
        help_text='Position in grid (e.g., "A3" or "2,5")'
    )
    note_date = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-note_date', '-created_at']

    def __str__(self):
        plant_name = self.plant.name if self.plant else 'General'
        return f"{self.garden.name} - {plant_name}: {self.title or self.note_text[:50]}"
