from django.contrib import admin
from django.utils.html import format_html
from .models import Plant, Garden, PlantingNote


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    """Admin interface for Plant model with companion planting support"""

    list_display = ['symbol_preview', 'name', 'latin_name', 'plant_type', 'planting_seasons_display',
                    'days_to_harvest', 'spacing_inches', 'is_default', 'companion_count']
    list_filter = ['plant_type', 'is_default', 'created_at']
    search_fields = ['name', 'latin_name', 'chicago_notes', 'pest_deterrent_for']
    filter_horizontal = ['companion_plants']
    readonly_fields = ['created_at', 'color_preview']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'latin_name', 'plant_type')
        }),
        ('Visual Display', {
            'fields': ('symbol', 'color', 'color_preview')
        }),
        ('Growing Information', {
            'fields': ('life_cycle', 'planting_seasons', 'days_to_harvest', 'spacing_inches')
        }),
        ('Chicago-Specific Notes', {
            'fields': ('chicago_notes',),
            'classes': ('wide',)
        }),
        ('Companion Planting', {
            'fields': ('companion_plants', 'pest_deterrent_for'),
            'description': 'Select plants that grow well together. Companion relationships help with pest control and growth.'
        }),
        ('Ownership', {
            'fields': ('is_default', 'created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def symbol_preview(self, obj):
        """Display colored symbol preview"""
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            obj.color,
            obj.symbol
        )
    symbol_preview.short_description = 'Symbol'

    def color_preview(self, obj):
        """Display color swatch"""
        return format_html(
            '<div style="background-color: {}; width: 100px; height: 30px; '
            'border: 1px solid #ccc; border-radius: 3px;"></div>'
            '<span style="margin-left: 10px;">{}</span>',
            obj.color,
            obj.color
        )
    color_preview.short_description = 'Color Preview'

    def planting_seasons_display(self, obj):
        """Display planting seasons as comma-separated list"""
        if obj.planting_seasons:
            return ', '.join([season.capitalize() for season in obj.planting_seasons])
        return '—'
    planting_seasons_display.short_description = 'Planting Seasons'

    def companion_count(self, obj):
        """Count of companion plants"""
        count = obj.companion_plants.count()
        if count > 0:
            return format_html('<span style="color: green;">✓ {}</span>', count)
        return '—'
    companion_count.short_description = 'Companions'

    def get_queryset(self, request):
        """Optimize queries with prefetch_related"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('companion_plants')


@admin.register(Garden)
class GardenAdmin(admin.ModelAdmin):
    """Admin interface for Garden model with layout visualization"""

    list_display = ['name', 'owner', 'size', 'dimensions', 'plant_count',
                    'is_public', 'created_at', 'updated_at']
    list_filter = ['size', 'is_public', 'created_at', 'updated_at']
    search_fields = ['name', 'description', 'owner__username']
    readonly_fields = ['created_at', 'updated_at', 'plant_count_display', 'grid_preview']
    autocomplete_fields = ['owner']

    fieldsets = (
        ('Garden Details', {
            'fields': ('name', 'description', 'owner', 'is_public')
        }),
        ('Dimensions', {
            'fields': ('size', 'width', 'height')
        }),
        ('Statistics', {
            'fields': ('plant_count_display',),
            'classes': ('collapse',)
        }),
        ('Layout Data', {
            'fields': ('layout_data', 'grid_preview'),
            'classes': ('collapse',),
            'description': 'JSON data storing the garden grid layout'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def dimensions(self, obj):
        """Display garden dimensions"""
        return f"{obj.width}' × {obj.height}'"
    dimensions.short_description = 'Dimensions'

    def plant_count(self, obj):
        """Display plant count with icon"""
        count = obj.get_plant_count()
        if count > 0:
            return format_html('<span style="color: green;">🌱 {}</span>', count)
        return '—'
    plant_count.short_description = 'Plants'

    def plant_count_display(self, obj):
        """Detailed plant count for detail view"""
        count = obj.get_plant_count()
        grid_size = obj.width * obj.height
        percentage = (count / grid_size * 100) if grid_size > 0 else 0
        return format_html(
            '<strong>{}</strong> plants out of {} spaces ({:.1f}% filled)',
            count, grid_size, percentage
        )
    plant_count_display.short_description = 'Plant Count'

    def grid_preview(self, obj):
        """Show a simple text preview of the garden grid"""
        if not obj.layout_data or 'grid' not in obj.layout_data:
            return 'No layout data'

        grid = obj.layout_data.get('grid', [])
        if not grid:
            return 'Empty grid'

        # Create a simple text representation
        preview = '<div style="font-family: monospace; font-size: 11px; line-height: 1.2;">'
        for row in grid[:10]:  # Limit to first 10 rows
            row_text = ' '.join([cell[:4].ljust(4) if cell else '    ' for cell in row[:10]])
            preview += f'{row_text}<br>'

        if len(grid) > 10:
            preview += '...<br>'
        preview += '</div>'

        return format_html(preview)
    grid_preview.short_description = 'Grid Preview'


@admin.register(PlantingNote)
class PlantingNoteAdmin(admin.ModelAdmin):
    """Admin interface for PlantingNote model"""

    list_display = ['get_title', 'garden', 'plant', 'grid_position', 'note_date', 'created_at']
    list_filter = ['note_date', 'created_at', 'updated_at']
    search_fields = ['title', 'note_text', 'garden__name', 'plant__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['garden', 'plant']
    date_hierarchy = 'note_date'

    fieldsets = (
        ('Note Information', {
            'fields': ('garden', 'plant', 'title', 'note_text')
        }),
        ('Location', {
            'fields': ('grid_position',),
            'description': 'Optional position in garden grid (e.g., "A3" or "2,5")'
        }),
        ('Timestamps', {
            'fields': ('note_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_title(self, obj):
        """Display title or truncated note"""
        if obj.title:
            return obj.title
        return obj.note_text[:50] + '...' if len(obj.note_text) > 50 else obj.note_text
    get_title.short_description = 'Title/Note'


# Customize admin site headers
admin.site.site_header = 'Chicago Garden Planner Admin'
admin.site.site_title = 'Garden Admin'
admin.site.index_title = 'Garden Management Dashboard'