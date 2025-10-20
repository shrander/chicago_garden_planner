from django.contrib import admin
# from .models import Plant, Garden, PlantingNote  # Uncomment when models are implemented

# Register your models here.

# TODO: Uncomment and configure these admin classes when models are implemented
#
# @admin.register(Plant)
# class PlantAdmin(admin.ModelAdmin):
#     list_display = ['name', 'latin_name', 'plant_type', 'planting_season', 'days_to_harvest', 'is_default']
#     list_filter = ['plant_type', 'planting_season', 'is_default']
#     search_fields = ['name', 'latin_name', 'chicago_notes']
#     readonly_fields = ['symbol', 'color']
#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('name', 'latin_name', 'symbol', 'color', 'plant_type')
#         }),
#         ('Growing Information', {
#             'fields': ('planting_season', 'days_to_harvest', 'spacing_inches')
#         }),
#         ('Chicago-Specific Notes', {
#             'fields': ('chicago_notes',),
#             'classes': ('wide',)
#         }),
#         ('Companion Planting', {
#             'fields': ('pest_deterrent_for', 'companions', 'antagonists')
#         }),
#         ('Settings', {
#             'fields': ('is_default', 'created_by')
#         }),
#     )
#
# @admin.register(Garden)
# class GardenAdmin(admin.ModelAdmin):
#     list_display = ['name', 'owner', 'width', 'height', 'is_public', 'created_at', 'updated_at']
#     list_filter = ['is_public', 'created_at', 'updated_at']
#     search_fields = ['name', 'description', 'owner__username']
#     readonly_fields = ['created_at', 'updated_at']
#     fieldsets = (
#         ('Garden Details', {
#             'fields': ('name', 'description', 'owner', 'is_public')
#         }),
#         ('Dimensions', {
#             'fields': ('width', 'height')
#         }),
#         ('Layout Data', {
#             'fields': ('layout_data',),
#             'classes': ('collapse',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#
# @admin.register(PlantingNote)
# class PlantingNoteAdmin(admin.ModelAdmin):
#     list_display = ['garden', 'plant', 'planting_date', 'status', 'created_at']
#     list_filter = ['status', 'planting_date', 'created_at']
#     search_fields = ['garden__name', 'plant__name', 'notes']
#     readonly_fields = ['created_at', 'updated_at']
#     fieldsets = (
#         ('Planting Information', {
#             'fields': ('garden', 'plant', 'planting_date', 'status')
#         }),
#         ('Notes', {
#             'fields': ('notes',),
#             'classes': ('wide',)
#         }),
#         ('Harvest Information', {
#             'fields': ('harvest_date', 'harvest_amount')
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at'),
#             'classes': ('collapse',)
#         }),
#     )
#     date_hierarchy = 'planting_date'
