from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from .constants import HARDINESS_ZONES

User = get_user_model()

class Plant(models.Model):
    """Plant library with zone-specific growing information"""

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

    LIFE_CYCLES = [
        ('annual', 'Annual'),
        ('biennial', 'Biennial'),
        ('perennial', 'Perennial'),
    ]

    name = models.CharField(max_length=100)
    latin_name = models.CharField(max_length=150)
    symbol = models.CharField(max_length=2, help_text='1-2 character symbol for grid')
    color = models.CharField(max_length=7, default='#90EE90', help_text='Hex color code')
    plant_type = models.CharField(max_length=20, choices=PLANT_TYPES)
    life_cycle = models.CharField(
        max_length=10,
        choices=LIFE_CYCLES,
        blank=True,
        help_text='Annual, Biennial, or Perennial'
    )

    # General growing information
    planting_seasons = models.JSONField(
        default=list,
        help_text='List of seasons when this plant can be planted (e.g., ["spring", "fall"])'
    )
    days_to_harvest = models.IntegerField(null=True, blank=True, help_text='Days from transplant to harvest')
    spacing_inches = models.FloatField(help_text='Spacing between plants in inches')

    # Seed starting and transplant timing
    weeks_before_last_frost_start = models.IntegerField(
        null=True,
        blank=True,
        help_text='Weeks before last frost to start seeds indoors (e.g., 6-8 for tomatoes)'
    )
    weeks_after_last_frost_transplant = models.IntegerField(
        null=True,
        blank=True,
        help_text='Weeks after last frost to transplant outdoors (0 = at last frost, negative = before)'
    )
    direct_sow = models.BooleanField(
        default=False,
        help_text='Can this plant be directly sown outdoors?'
    )
    days_to_germination = models.IntegerField(
        null=True,
        blank=True,
        help_text='Days for seeds to germinate'
    )
    days_before_transplant_ready = models.IntegerField(
        null=True,
        blank=True,
        help_text='Days from germination until seedling is ready to transplant (hardening off period)'
    )
    transplant_to_harvest_days = models.IntegerField(
        null=True,
        blank=True,
        help_text='Days from transplanting to harvest (if different from days_to_harvest)'
    )

    # Yield estimation
    yield_per_plant = models.CharField(
        max_length=100,
        blank=True,
        help_text='Expected yield per plant (e.g., "2-3 lbs", "10-15 fruits", "continuous harvest")'
    )

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


class PlantInstance(models.Model):
    """Tracks individual plant placements in garden with planting/harvesting dates"""

    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, related_name='plant_instances')
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='instances')

    # Grid position
    row = models.IntegerField(help_text='Row position in garden grid (0-indexed)')
    col = models.IntegerField(help_text='Column position in garden grid (0-indexed)')

    # Date tracking
    SEED_STARTING_METHODS = [
        ('pot', 'Started in Pot'),
        ('direct', 'Direct Sown in Garden'),
    ]

    seed_starting_method = models.CharField(
        max_length=10,
        choices=SEED_STARTING_METHODS,
        null=True,
        blank=True,
        help_text='How seeds were/will be started'
    )

    # Planned dates (for planning ahead)
    planned_seed_start_date = models.DateField(
        null=True,
        blank=True,
        help_text='Planned date to start seeds (in pot or direct sow)'
    )
    planned_planting_date = models.DateField(
        null=True,
        blank=True,
        help_text='Planned date to transplant seedlings or direct sow in garden'
    )

    # Actual dates (what really happened)
    seed_started_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual date when seeds were started (in pot or direct sown)'
    )
    planted_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual date when plant was placed in garden plot (transplant or direct sow)'
    )
    expected_harvest_date = models.DateField(
        null=True,
        blank=True,
        help_text='Expected harvest date (auto-calculated from planted_date + days_to_harvest)'
    )
    actual_harvest_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual date when harvested'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['garden', 'row', 'col']
        unique_together = ['garden', 'row', 'col']
        indexes = [
            models.Index(fields=['garden', 'row', 'col']),
            models.Index(fields=['planted_date']),
            models.Index(fields=['expected_harvest_date']),
        ]

    def __str__(self):
        return f"{self.plant.name} at ({self.row}, {self.col}) in {self.garden.name}"

    def calculate_expected_harvest_date(self):
        """
        Calculate expected harvest date based on planted_date.
        Uses transplant_to_harvest_days if available, otherwise days_to_harvest.
        """
        from datetime import timedelta

        if not self.planted_date:
            return

        # Determine days to harvest based on whether plant was direct sown or transplanted
        days = self.plant.transplant_to_harvest_days or self.plant.days_to_harvest
        if days:
            self.expected_harvest_date = self.planted_date + timedelta(days=days)

    def calculate_expected_transplant_date(self):
        """
        Calculate expected transplant date based on seed_started_date.
        Returns None if plant is direct sown or no seed_started_date.
        This is NOT stored in the database, just calculated for display.
        """
        from datetime import timedelta

        # Direct sown plants don't get transplanted
        if self.plant.direct_sow or not self.seed_started_date:
            return None

        total_days = 0
        if self.plant.days_to_germination:
            total_days += self.plant.days_to_germination
        if self.plant.days_before_transplant_ready:
            total_days += self.plant.days_before_transplant_ready

        if total_days > 0:
            return self.seed_started_date + timedelta(days=total_days)
        return None

    def save(self, *args, **kwargs):
        """
        Auto-calculate expected harvest date.
        For direct sown, sync actual dates.
        """
        # For direct sown: actual planted date should match actual seed started date
        if self.seed_starting_method == 'direct' and self.seed_started_date and not self.planted_date:
            self.planted_date = self.seed_started_date

        # Auto-calculate expected harvest date if we have a planted_date
        if self.planted_date and not self.expected_harvest_date:
            if self.plant.transplant_to_harvest_days or self.plant.days_to_harvest:
                self.calculate_expected_harvest_date()

        super().save(*args, **kwargs)

    def days_until_harvest(self):
        """Return number of days until expected harvest (negative if overdue)"""
        if not self.expected_harvest_date:
            return None
        from datetime import date
        delta = (self.expected_harvest_date - date.today()).days
        return delta

    def harvest_status(self):
        """Return harvest status: 'harvested', 'ready', 'soon', 'growing', 'overdue'"""
        if self.actual_harvest_date:
            return 'harvested'
        if not self.expected_harvest_date:
            return 'no_date'

        days = self.days_until_harvest()
        if days is None:
            return 'no_date'
        elif days < 0:
            return 'overdue'
        elif days == 0:
            return 'ready'
        elif days <= 7:
            return 'soon'
        else:
            return 'growing'


class GardenShare(models.Model):
    """Track garden sharing permissions"""

    PERMISSION_CHOICES = [
        ('view', 'Can View'),
        ('edit', 'Can Edit'),
    ]

    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, related_name='shares')
    shared_with_email = models.EmailField(help_text='Email of person to share with')
    shared_with_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='shared_gardens',
        help_text='User object once they register/login'
    )
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default='view')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares_created')
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['garden', 'shared_with_email']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.garden.name} shared with {self.shared_with_email}"


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


class UserPlantNote(models.Model):
    """User-specific growing experiences and notes for plants"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plant_notes')
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='user_notes')

    # Note content
    title = models.CharField(max_length=200, blank=True, help_text='Optional title for your note')
    note_text = models.TextField(help_text='Your experience growing this plant, tips, observations, etc.')

    # Optional metadata
    growing_season = models.IntegerField(
        null=True,
        blank=True,
        help_text='Year you grew this plant (e.g., 2024)'
    )
    success_rating = models.IntegerField(
        null=True,
        blank=True,
        choices=[
            (1, '1 - Poor'),
            (2, '2 - Fair'),
            (3, '3 - Good'),
            (4, '4 - Very Good'),
            (5, '5 - Excellent'),
        ],
        help_text='How well did this plant grow for you?'
    )
    would_grow_again = models.BooleanField(
        null=True,
        blank=True,
        help_text='Would you grow this plant again?'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'plant', 'growing_season']
        indexes = [
            models.Index(fields=['user', 'plant']),
            models.Index(fields=['plant']),
        ]

    def __str__(self):
        season = f" ({self.growing_season})" if self.growing_season else ""
        return f"{self.user.username} - {self.plant.name}{season}"


class ClimateZone(models.Model):
    """Climate and growing information for USDA hardiness zones"""

    zone = models.CharField(
        max_length=3,
        choices=HARDINESS_ZONES,
        unique=True,
        help_text='USDA Hardiness Zone'
    )

    # Geographic information
    region_examples = models.CharField(
        max_length=200,
        blank=True,
        help_text='Example cities/regions (e.g., "Chicago, Minneapolis, Portland OR")'
    )

    # Frost dates (MM-DD format)
    typical_last_frost = models.CharField(
        max_length=5,
        help_text='Typical last spring frost date (MM-DD format)'
    )
    typical_first_frost = models.CharField(
        max_length=5,
        help_text='Typical first fall frost date (MM-DD format)'
    )

    # Temperature data
    avg_annual_min_temp_f = models.IntegerField(
        help_text='Average annual minimum temperature (Fahrenheit)'
    )
    avg_summer_high_f = models.IntegerField(
        null=True,
        blank=True,
        help_text='Average summer high temperature'
    )

    # Growing season
    growing_season_days = models.IntegerField(
        help_text='Average frost-free days'
    )

    # Soil and climate characteristics
    common_soil_types = models.CharField(
        max_length=100,
        blank=True,
        help_text='Common soil types (e.g., "Clay, Loam")'
    )
    humidity_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
        ],
        default='moderate'
    )

    # Additional notes
    special_considerations = models.TextField(
        blank=True,
        help_text='Special climate considerations for this zone'
    )

    class Meta:
        ordering = ['zone']
        verbose_name = 'Climate Zone'
        verbose_name_plural = 'Climate Zones'

    def __str__(self):
        return f"Zone {self.zone} - {self.region_examples}"

    def get_growing_season_weeks(self):
        """Calculate growing season in weeks"""
        return self.growing_season_days // 7


class PlantZoneData(models.Model):
    """Zone-specific growing information for plants"""

    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='zone_data')
    zone = models.CharField(max_length=3, choices=HARDINESS_ZONES)

    # Zone-specific information
    zone_specific_notes = models.TextField(
        blank=True,
        help_text='Growing notes specific to this hardiness zone'
    )
    success_rating = models.IntegerField(
        choices=[
            (1, '⭐☆☆☆☆ Not Recommended'),
            (2, '⭐⭐☆☆☆ Challenging'),
            (3, '⭐⭐⭐☆☆ Moderate'),
            (4, '⭐⭐⭐⭐☆ Good'),
            (5, '⭐⭐⭐⭐⭐ Excellent')
        ],
        default=3,
        help_text='How well this plant grows in this zone'
    )

    # Climate considerations
    soil_amendments = models.TextField(
        blank=True,
        help_text='Recommended soil amendments for this zone'
    )
    special_considerations = models.TextField(
        blank=True,
        help_text='Special care needed in this zone (e.g., winter protection)'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['plant', 'zone']
        ordering = ['zone', 'plant__name']
        verbose_name = 'Plant Zone Data'
        verbose_name_plural = 'Plant Zone Data'
        indexes = [
            models.Index(fields=['zone']),
            models.Index(fields=['plant', 'zone']),
        ]

    def __str__(self):
        return f"{self.plant.name} in Zone {self.zone}"


class DataMigration(models.Model):
    """Track data population command execution and versions"""
    command_name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Name of the management command (e.g., populate_climate_zones)'
    )
    version = models.CharField(
        max_length=20,
        help_text='Version of the data (e.g., 1.0.0)'
    )
    last_run = models.DateTimeField(
        auto_now=True,
        help_text='Last time this command was executed'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='First time this command was run'
    )

    class Meta:
        db_table = 'data_migrations'
        verbose_name = 'Data Migration'
        verbose_name_plural = 'Data Migrations'
        ordering = ['-last_run']

    def __str__(self):
        return f"{self.command_name} (v{self.version})"
