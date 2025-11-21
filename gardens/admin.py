from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django import forms
import csv
import json
from .models import Plant, Garden, PlantInstance, PlantingNote, GardenShare, UserPlantNote, DataMigration


class CSVImportForm(forms.Form):
    """Form for uploading CSV file to import plants"""
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with plant data. See plant_import_template.csv for format.'
    )
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        label='Overwrite existing plants',
        help_text='If checked, plants with matching names will be updated. Otherwise, duplicates will be skipped.'
    )


@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    """Admin interface for Plant model with companion planting support"""

    list_display = ['symbol_preview', 'name', 'latin_name', 'plant_type', 'planting_seasons_display',
                    'days_to_harvest', 'spacing_inches', 'is_default', 'companion_count']
    list_filter = ['plant_type', 'is_default', 'created_at']
    search_fields = ['name', 'latin_name', 'pest_deterrent_for']
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
            'fields': ('life_cycle', 'planting_seasons', 'days_to_harvest', 'spacing_inches', 'yield_per_plant')
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

    def get_urls(self):
        """Add custom URL for CSV import"""
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='gardens_plant_import_csv'),
        ]
        return custom_urls + urls

    def import_csv(self, request):
        """Handle CSV import for bulk plant creation"""
        if request.method == 'POST':
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                overwrite = form.cleaned_data['overwrite_existing']

                # Decode the file
                try:
                    decoded_file = csv_file.read().decode('utf-8').splitlines()
                    reader = csv.DictReader(decoded_file)

                    created_count = 0
                    updated_count = 0
                    skipped_count = 0
                    errors = []

                    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                        try:
                            # Parse required fields
                            name = row.get('name', '').strip()
                            if not name:
                                errors.append(f"Row {row_num}: Missing 'name' field")
                                continue

                            # Parse planting_seasons JSON
                            planting_seasons_str = row.get('planting_seasons', '[]').strip()
                            try:
                                planting_seasons = json.loads(planting_seasons_str) if planting_seasons_str else []
                            except json.JSONDecodeError:
                                planting_seasons = []

                            # Parse boolean fields
                            direct_sow = row.get('direct_sow', '').strip().upper() in ['TRUE', '1', 'YES']

                            # Prepare plant data
                            plant_data = {
                                'latin_name': row.get('latin_name', '').strip(),
                                'symbol': row.get('symbol', '')[:2].strip(),  # Max 2 chars
                                'color': row.get('color', '#90EE90').strip(),
                                'plant_type': row.get('plant_type', '').strip(),
                                'life_cycle': row.get('life_cycle', '').strip() or None,
                                'planting_seasons': planting_seasons,
                                'spacing_inches': float(row.get('spacing_inches', 0)) if row.get('spacing_inches') else None,
                                'direct_sow': direct_sow,
                                'is_default': True,  # CSV imports are default plants
                                'created_by': None,  # System plants have no creator
                            }

                            # Parse optional integer fields
                            for field in ['days_to_harvest', 'weeks_before_last_frost_start',
                                        'weeks_after_last_frost_transplant', 'days_to_germination',
                                        'days_before_transplant_ready', 'transplant_to_harvest_days']:
                                value = row.get(field, '').strip()
                                plant_data[field] = int(value) if value else None

                            # Parse optional text fields
                            for field in ['yield_per_plant', 'pest_deterrent_for']:
                                plant_data[field] = row.get(field, '').strip()

                            # Check if plant exists
                            existing_plant = Plant.objects.filter(name=name, is_default=True).first()

                            if existing_plant:
                                if overwrite:
                                    # Update existing plant
                                    for key, value in plant_data.items():
                                        setattr(existing_plant, key, value)
                                    existing_plant.save()
                                    updated_count += 1
                                else:
                                    skipped_count += 1
                            else:
                                # Create new plant
                                Plant.objects.create(name=name, **plant_data)
                                created_count += 1

                        except Exception as e:
                            errors.append(f"Row {row_num} ({name}): {str(e)}")

                    # Show results
                    if created_count > 0:
                        messages.success(request, f'Successfully created {created_count} plant(s)')
                    if updated_count > 0:
                        messages.success(request, f'Successfully updated {updated_count} plant(s)')
                    if skipped_count > 0:
                        messages.warning(request, f'Skipped {skipped_count} duplicate plant(s)')
                    if errors:
                        for error in errors[:10]:  # Show first 10 errors
                            messages.error(request, error)
                        if len(errors) > 10:
                            messages.error(request, f'... and {len(errors) - 10} more errors')

                    return redirect('..')

                except Exception as e:
                    messages.error(request, f'Error processing CSV file: {str(e)}')
        else:
            form = CSVImportForm()

        context = {
            'form': form,
            'title': 'Import Plants from CSV',
            'site_header': 'Chicago Garden Planner Admin',
            'has_permission': True,
        }
        return render(request, 'admin/gardens/plant/import_csv.html', context)

    def changelist_view(self, request, extra_context=None):
        """Add import button to the change list view"""
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        return super().changelist_view(request, extra_context)


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


@admin.register(PlantInstance)
class PlantInstanceAdmin(admin.ModelAdmin):
    """Admin interface for PlantInstance model"""

    list_display = ['get_location', 'plant', 'garden', 'planted_date',
                    'expected_harvest_date', 'harvest_status_display', 'days_remaining']
    list_filter = ['planted_date', 'expected_harvest_date', 'actual_harvest_date', 'garden']
    search_fields = ['plant__name', 'garden__name']
    readonly_fields = ['created_at', 'updated_at', 'harvest_status_display', 'days_remaining']
    autocomplete_fields = ['garden', 'plant']
    date_hierarchy = 'planted_date'

    fieldsets = (
        ('Location', {
            'fields': ('garden', 'plant', 'row', 'col')
        }),
        ('Date Tracking', {
            'fields': ('planted_date', 'expected_harvest_date', 'actual_harvest_date')
        }),
        ('Status', {
            'fields': ('harvest_status_display', 'days_remaining'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_location(self, obj):
        """Display grid position"""
        return f"({obj.row}, {obj.col})"
    get_location.short_description = 'Position'

    def harvest_status_display(self, obj):
        """Display harvest status with color coding"""
        status = obj.harvest_status()
        colors = {
            'harvested': '#28a745',  # green
            'ready': '#28a745',      # green
            'soon': '#ffc107',       # yellow
            'growing': '#17a2b8',    # blue
            'overdue': '#dc3545',    # red
            'no_date': '#6c757d'     # gray
        }
        labels = {
            'harvested': '✓ Harvested',
            'ready': '🌟 Ready to Harvest',
            'soon': '⏰ Soon',
            'growing': '🌱 Growing',
            'overdue': '⚠️ Overdue',
            'no_date': '— No Date'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(status, '#000'),
            labels.get(status, status)
        )
    harvest_status_display.short_description = 'Status'

    def days_remaining(self, obj):
        """Display days until harvest"""
        days = obj.days_until_harvest()
        if days is None:
            return '—'
        if days < 0:
            return format_html('<span style="color: #dc3545;">{} days overdue</span>', abs(days))
        elif days == 0:
            return format_html('<span style="color: #28a745;">Today!</span>')
        else:
            return f"{days} days"
    days_remaining.short_description = 'Days to Harvest'


@admin.register(GardenShare)
class GardenShareAdmin(admin.ModelAdmin):
    """Admin interface for GardenShare model"""

    list_display = ['garden', 'shared_with_email', 'permission', 'shared_by', 'status', 'created_at']
    list_filter = ['permission', 'created_at', 'accepted_at']
    search_fields = ['garden__name', 'shared_with_email', 'shared_by__username']
    readonly_fields = ['created_at', 'accepted_at']
    autocomplete_fields = ['garden', 'shared_by', 'shared_with_user']

    def status(self, obj):
        """Display acceptance status"""
        if obj.accepted_at:
            return format_html('<span style="color: green;">✓ Accepted</span>')
        return format_html('<span style="color: orange;">⏳ Pending</span>')
    status.short_description = 'Status'


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


@admin.register(UserPlantNote)
class UserPlantNoteAdmin(admin.ModelAdmin):
    """Admin interface for UserPlantNote model"""

    list_display = ['get_title', 'user', 'plant', 'growing_season', 'success_rating_display', 'would_grow_again', 'created_at']
    list_filter = ['success_rating', 'would_grow_again', 'growing_season', 'created_at']
    search_fields = ['title', 'note_text', 'user__username', 'plant__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['user', 'plant']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('User & Plant', {
            'fields': ('user', 'plant')
        }),
        ('Growing Experience', {
            'fields': ('title', 'note_text', 'growing_season', 'success_rating', 'would_grow_again')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_title(self, obj):
        """Display title or truncated note"""
        if obj.title:
            return obj.title
        return obj.note_text[:50] + '...' if len(obj.note_text) > 50 else obj.note_text
    get_title.short_description = 'Title/Note'

    def success_rating_display(self, obj):
        """Display success rating with stars"""
        if obj.success_rating:
            stars = '⭐' * obj.success_rating + '☆' * (5 - obj.success_rating)
            colors = {1: '#dc3545', 2: '#fd7e14', 3: '#ffc107', 4: '#28a745', 5: '#28a745'}
            return format_html(
                '<span style="color: {};">{} ({})</span>',
                colors.get(obj.success_rating, '#6c757d'),
                stars,
                obj.get_success_rating_display()
            )
        return '—'
    success_rating_display.short_description = 'Success Rating'


@admin.register(DataMigration)
class DataMigrationAdmin(admin.ModelAdmin):
    """Admin interface for DataMigration tracking"""
    list_display = ['command_name', 'version', 'last_run', 'created_at']
    list_filter = ['command_name', 'version']
    search_fields = ['command_name', 'version']
    readonly_fields = ['last_run', 'created_at']
    ordering = ['-last_run']

    def has_add_permission(self, request):
        # Don't allow manual creation - commands manage this
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow deletion to force re-run of commands
        return True


# Customize admin site headers
admin.site.site_header = 'Chicago Garden Planner Admin'
admin.site.site_title = 'Garden Admin'
admin.site.index_title = 'Garden Management Dashboard'