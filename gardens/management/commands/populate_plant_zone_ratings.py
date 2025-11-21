"""
Management command to populate PlantZoneData with success ratings for existing plants.
Usage: python manage.py populate_plant_zone_ratings [--force]
"""

from django.core.management.base import BaseCommand
from gardens.models import Plant, PlantZoneData, DataMigration


class Command(BaseCommand):
    help = 'Populate PlantZoneData with success ratings for common vegetables across all zones'
    VERSION = '1.0.0'  # Increment when plant zone ratings change

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if version matches',
        )

    def handle(self, *args, **options):
        force = options['force']

        # Check version tracking
        migration, created = DataMigration.objects.get_or_create(
            command_name='populate_plant_zone_ratings',
            defaults={'version': '0.0.0'}
        )

        if migration.version == self.VERSION and not force:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Plant zone ratings already at version {self.VERSION} (use --force to update)'
            ))
            return

        self.stdout.write(f'Updating plant zone ratings from v{migration.version} to v{self.VERSION}...')

        # Define success ratings for common vegetables by zone
        # Rating scale: 1=Not Recommended, 2=Challenging, 3=Moderate, 4=Good, 5=Excellent

        plant_zone_ratings = {
            # Cool-season leafy greens
            'Kale': {
                '3a': (5, 'Excellent cold-hardy crop. Can overwinter with protection.'),
                '3b': (5, 'Thrives in cool weather. Frost improves flavor.'),
                '4a': (5, 'Perfect zone for kale. Spring and fall crops.'),
                '4b': (5, 'Excellent performer. Grows spring through fall.'),
                '5a': (5, 'Ideal for spring and fall planting.'),
                '5b': (5, 'Grows well spring and fall. Heat-tolerant varieties recommended for summer.'),
                '6a': (4, 'Good spring and fall crop. Provide shade in summer.'),
                '6b': (4, 'Best in cooler months. Bolts in summer heat.'),
                '7a': (3, 'Challenging in summer heat. Best as fall/winter crop.'),
                '7b': (3, 'Grow in fall through spring only.'),
                '8a': (3, 'Winter crop only. Plant October-February.'),
                '8b': (2, 'Difficult. Cool-season only (Nov-Feb).'),
                '9a': (2, 'Very challenging. Brief winter window only.'),
                '9b': (1, 'Not recommended. Too hot year-round.'),
                '10a': (1, 'Not suitable for this climate.'),
                '10b': (1, 'Not suitable for this climate.'),
            },

            'Lettuce': {
                '3a': (4, 'Good spring crop. Quick-maturing varieties essential.'),
                '3b': (4, 'Excellent spring and fall crop with protection.'),
                '4a': (5, 'Perfect for spring and fall. Succession plant.'),
                '4b': (5, 'Ideal conditions. Plant spring through fall.'),
                '5a': (5, 'Excellent spring and fall crop. Some varieties overwinter.'),
                '5b': (5, 'Thrives in cool weather. Provide shade in summer.'),
                '6a': (4, 'Good spring and fall. Heat-resistant varieties for summer.'),
                '6b': (4, 'Best in cooler months. Bolts quickly in heat.'),
                '7a': (3, 'Spring and fall only. Summer too hot.'),
                '7b': (3, 'Cool-season crop. Oct-May growing window.'),
                '8a': (3, 'Fall through spring crop. Challenging in summer.'),
                '8b': (2, 'Winter crop only. Very heat sensitive.'),
                '9a': (2, 'Limited to winter months. Difficult to grow.'),
                '9b': (1, 'Very challenging. Brief winter window.'),
                '10a': (1, 'Not recommended for most varieties.'),
                '10b': (1, 'Tropical alternatives recommended.'),
            },

            # Warm-season crops
            'Tomatoes': {
                '3a': (2, 'Challenging. Early-maturing varieties only. Use season extenders.'),
                '3b': (3, 'Possible with early varieties and season extension.'),
                '4a': (3, 'Moderate success. Choose short-season varieties (60-70 days).'),
                '4b': (4, 'Good with proper variety selection. Start indoors early.'),
                '5a': (4, 'Very good. Wide variety selection possible.'),
                '5b': (5, 'Excellent zone for tomatoes. Disease-resistant varieties recommended.'),
                '6a': (5, 'Ideal growing conditions. Long season allows succession planting.'),
                '6b': (5, 'Perfect for tomatoes. Extended season for large varieties.'),
                '7a': (4, 'Very good but provide afternoon shade. Heat can reduce fruit set.'),
                '7b': (4, 'Good but watch for heat stress. Plenty of water needed.'),
                '8a': (3, 'Moderate. Plant early spring or fall. Summer heat reduces yields.'),
                '8b': (3, 'Challenging in summer. Best as spring and fall crop.'),
                '9a': (2, 'Difficult. Oct-May only. Summer far too hot.'),
                '9b': (2, 'Very challenging. Cool-season only (Nov-Apr).'),
                '10a': (1, 'Not recommended. Use heat-adapted varieties only.'),
                '10b': (1, 'Tropical alternatives recommended.'),
            },

            'Carrots': {
                '3a': (4, 'Good spring and fall crop. Short-season varieties.'),
                '3b': (4, 'Very good. Cool weather improves sweetness.'),
                '4a': (5, 'Excellent. Spring and fall plantings.'),
                '4b': (5, 'Ideal zone. Succession plant for continuous harvest.'),
                '5a': (5, 'Perfect conditions. Long season for full-size varieties.'),
                '5b': (5, 'Excellent. Loose soil amendment recommended.'),
                '6a': (5, 'Ideal growing zone. Fall carrots especially sweet.'),
                '6b': (4, 'Very good. Best spring and fall.'),
                '7a': (4, 'Good. Focus on fall through spring planting.'),
                '7b': (4, 'Good. Oct-May planting window.'),
                '8a': (3, 'Moderate. Cool-season crop. Can overwinter.'),
                '8b': (3, 'Fall through spring crop. Summer too hot.'),
                '9a': (3, 'Challenging. Winter crop only (Oct-Mar).'),
                '9b': (2, 'Difficult. Brief cool-season window.'),
                '10a': (2, 'Very challenging. Limited success.'),
                '10b': (1, 'Not recommended for most varieties.'),
            },

            'Radishes': {
                '3a': (5, 'Excellent quick crop. Plant spring and fall.'),
                '3b': (5, 'Perfect for short season. Succession plant.'),
                '4a': (5, 'Ideal. Multiple plantings from spring through fall.'),
                '4b': (5, 'Excellent. Ready in 25-30 days.'),
                '5a': (5, 'Perfect zone. Plant every 2 weeks.'),
                '5b': (5, 'Ideal conditions. Spring and fall best.'),
                '6a': (4, 'Very good. Best in cooler months.'),
                '6b': (4, 'Good spring and fall. Bolts quickly in heat.'),
                '7a': (4, 'Good fall through spring crop. Summer too hot.'),
                '7b': (3, 'Moderate. Oct-May planting. Bolts in heat.'),
                '8a': (3, 'Challenging. Cool-season only (Oct-Apr).'),
                '8b': (3, 'Winter crop. Quick harvest before heat.'),
                '9a': (2, 'Difficult. Limited to winter months.'),
                '9b': (2, 'Very challenging. Brief cool window.'),
                '10a': (1, 'Not recommended. Too hot.'),
                '10b': (1, 'Not suitable for most varieties.'),
            },

            'Strawberries': {
                '3a': (3, 'Challenging. Use June-bearing varieties with winter protection.'),
                '3b': (3, 'Moderate. Heavy mulching required for winter.'),
                '4a': (4, 'Good. Choose cold-hardy varieties. Mulch heavily.'),
                '4b': (4, 'Very good. Proper winter protection essential.'),
                '5a': (5, 'Excellent. Wide variety selection. June and everbearing types.'),
                '5b': (5, 'Ideal zone. Both June-bearing and everbearing do well.'),
                '6a': (5, 'Perfect conditions. Multiple harvest opportunities.'),
                '6b': (5, 'Excellent. Extended season for everbearing types.'),
                '7a': (4, 'Very good. Provide afternoon shade and consistent water.'),
                '7b': (4, 'Good. Heat can reduce production. Mulch to keep roots cool.'),
                '8a': (3, 'Moderate. Heat-tolerant varieties recommended. Challenging.'),
                '8b': (3, 'Difficult. Requires careful variety selection and shade.'),
                '9a': (2, 'Very challenging. Limited success even with heat-tolerant types.'),
                '9b': (2, 'Not recommended for most varieties. Try alpine strawberries.'),
                '10a': (1, 'Very difficult. Too hot for traditional varieties.'),
                '10b': (1, 'Not suitable. Use tropical berry alternatives.'),
            },

            'Basil': {
                '3a': (2, 'Very challenging. Short outdoor season. Container recommended.'),
                '3b': (2, 'Difficult. Must wait until well after last frost.'),
                '4a': (3, 'Moderate. Short season but possible with care.'),
                '4b': (3, 'Good as annual. Start indoors, transplant late spring.'),
                '5a': (4, 'Very good. Long enough season for multiple cuttings.'),
                '5b': (5, 'Excellent. Multiple succession plantings recommended.'),
                '6a': (5, 'Perfect zone. Prolific growth all summer.'),
                '6b': (5, 'Ideal conditions. Harvest regularly for bushier plants.'),
                '7a': (5, 'Exceptional. Long hot season = huge yields.'),
                '7b': (5, 'Perfect. Hot weather promotes growth.'),
                '8a': (5, 'Excellent. Can grow spring through fall.'),
                '8b': (4, 'Very good. May need afternoon shade in peak summer.'),
                '9a': (4, 'Good. Grow spring and fall. Summer heat can stress.'),
                '9b': (3, 'Moderate. Provide shade and consistent moisture.'),
                '10a': (3, 'Challenging. Perennial in ideal microclimates.'),
                '10b': (3, 'Difficult. Thai basil varieties perform better.'),
            },

            'Spinach': {
                '3a': (5, 'Excellent cold-hardy crop. Can overwinter.'),
                '3b': (5, 'Perfect for this zone. Spring and fall.'),
                '4a': (5, 'Ideal. Very cold tolerant.'),
                '4b': (5, 'Excellent spring and fall crop.'),
                '5a': (5, 'Perfect zone. Plant early spring and fall.'),
                '5b': (5, 'Ideal. Succession plant for continuous harvest.'),
                '6a': (4, 'Very good spring and fall. Bolts in heat.'),
                '6b': (4, 'Good cool-season crop. Provide shade if planting late.'),
                '7a': (3, 'Moderate. Fall through spring only.'),
                '7b': (3, 'Cool-season crop. Oct-Apr planting.'),
                '8a': (3, 'Winter crop only. Bolts quickly in heat.'),
                '8b': (2, 'Challenging. Very narrow planting window.'),
                '9a': (2, 'Difficult. Brief winter window (Dec-Feb).'),
                '9b': (1, 'Very challenging. Heat-tolerant alternatives better.'),
                '10a': (1, 'Not recommended. Use tropical greens.'),
                '10b': (1, 'Not suitable. Use amaranth or similar.'),
            },

            # Herbs
            'Thyme': {
                '3a': (3, 'Moderate. Requires heavy winter mulch. Container recommended.'),
                '3b': (3, 'Challenging. Protect in winter. Good drainage essential.'),
                '4a': (4, 'Good. Mulch well for winter protection.'),
                '4b': (4, 'Very good. Hardy perennial with protection.'),
                '5a': (5, 'Excellent. Overwinters with minimal care.'),
                '5b': (5, 'Ideal zone. Low maintenance perennial herb.'),
                '6a': (5, 'Perfect. Thrives year-round.'),
                '6b': (5, 'Excellent. Evergreen in mild winters.'),
                '7a': (5, 'Ideal. Grows year-round.'),
                '7b': (5, 'Perfect zone. Nearly evergreen.'),
                '8a': (5, 'Excellent. Evergreen herb.'),
                '8b': (4, 'Very good. Provide afternoon shade.'),
                '9a': (4, 'Good. May need summer shade.'),
                '9b': (3, 'Moderate. Heat can stress plants.'),
                '10a': (3, 'Challenging. Requires shade and moisture.'),
                '10b': (2, 'Difficult. Not adapted to tropical conditions.'),
            },

            'Sage': {
                '3a': (2, 'Very challenging. Heavy mulch required. May not survive winter.'),
                '3b': (3, 'Moderate. Protect heavily in winter.'),
                '4a': (4, 'Good with winter protection. Mulch heavily.'),
                '4b': (4, 'Very good. Some winter protection needed.'),
                '5a': (5, 'Excellent. Hardy perennial.'),
                '5b': (5, 'Ideal zone. Reliable perennial herb.'),
                '6a': (5, 'Perfect. Thrives year-round.'),
                '6b': (5, 'Excellent. Evergreen in mild winters.'),
                '7a': (5, 'Ideal. Strong performer.'),
                '7b': (5, 'Perfect. Nearly evergreen.'),
                '8a': (4, 'Very good. May need summer water.'),
                '8b': (4, 'Good. Provide afternoon shade.'),
                '9a': (3, 'Moderate. Heat and humidity challenging.'),
                '9b': (2, 'Difficult. Not well-suited to heat.'),
                '10a': (2, 'Very challenging. Too hot and humid.'),
                '10b': (1, 'Not recommended. Use tropical herbs.'),
            },

            'Chives': {
                '3a': (5, 'Excellent. Very cold hardy perennial.'),
                '3b': (5, 'Perfect. Reliable cold-hardy herb.'),
                '4a': (5, 'Ideal. Extremely hardy.'),
                '4b': (5, 'Excellent. Minimal care needed.'),
                '5a': (5, 'Perfect zone. Self-propagating.'),
                '5b': (5, 'Ideal. Reliable perennial.'),
                '6a': (5, 'Excellent. Nearly evergreen.'),
                '6b': (5, 'Perfect. Low maintenance.'),
                '7a': (4, 'Very good. May need summer water.'),
                '7b': (4, 'Good. Provide moisture in heat.'),
                '8a': (4, 'Good. Consistent watering needed.'),
                '8b': (3, 'Moderate. Heat can reduce vigor.'),
                '9a': (3, 'Challenging. Not heat-adapted.'),
                '9b': (2, 'Difficult. Better herb options available.'),
                '10a': (2, 'Not recommended. Use garlic chives.'),
                '10b': (1, 'Not suitable. Too hot.'),
            },

            'Dill': {
                '3a': (3, 'Moderate. Quick-maturing varieties only. Short season.'),
                '3b': (4, 'Good. Plant in succession for continuous harvest.'),
                '4a': (4, 'Very good. Spring and fall plantings.'),
                '4b': (5, 'Excellent. Multiple succession plantings.'),
                '5a': (5, 'Ideal. Thrives in cool weather.'),
                '5b': (5, 'Perfect zone. Easy to grow.'),
                '6a': (5, 'Excellent. Self-seeds readily.'),
                '6b': (4, 'Very good. Bolts in heat. Plant spring/fall.'),
                '7a': (4, 'Good as cool-season crop. Spring and fall only.'),
                '7b': (3, 'Moderate. Oct-May planting window.'),
                '8a': (3, 'Challenging. Cool-season only.'),
                '8b': (2, 'Difficult. Brief growing window.'),
                '9a': (2, 'Very challenging. Winter crop only.'),
                '9b': (1, 'Not recommended. Bolts immediately.'),
                '10a': (1, 'Not suitable. Too hot.'),
                '10b': (1, 'Not suitable. Use culantro instead.'),
            },

            'Garlic': {
                '3a': (5, 'Excellent. Cold winter improves bulb development.'),
                '3b': (5, 'Perfect. Ideal cold period for vernalization.'),
                '4a': (5, 'Ideal. Hardneck varieties excel.'),
                '4b': (5, 'Excellent. Both hardneck and softneck types.'),
                '5a': (5, 'Perfect. Wide variety selection.'),
                '5b': (5, 'Ideal zone. Softneck varieties especially good.'),
                '6a': (5, 'Excellent. Great for both types.'),
                '6b': (5, 'Perfect for softneck varieties.'),
                '7a': (4, 'Very good. Softneck varieties recommended.'),
                '7b': (4, 'Good. May not get enough chill for hardneck.'),
                '8a': (3, 'Moderate. Softneck only. May not size well.'),
                '8b': (3, 'Challenging. Insufficient cold for best development.'),
                '9a': (2, 'Difficult. Limited vernalization. Small bulbs.'),
                '9b': (1, 'Not recommended. Too warm for proper bulbing.'),
                '10a': (1, 'Not suitable. Use elephant garlic or shallots.'),
                '10b': (1, 'Not suitable. No winter chill.'),
            },
        }

        created_count = 0
        updated_count = 0
        not_found_count = 0

        for plant_name, zone_ratings in plant_zone_ratings.items():
            # Find the plant
            try:
                plant = Plant.objects.get(name__iexact=plant_name, is_default=True)
            except Plant.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Plant "{plant_name}" not found - skipping'))
                not_found_count += 1
                continue

            # Create or update zone data for each zone (idempotent)
            for zone, (rating, notes) in zone_ratings.items():
                zone_data, was_created = PlantZoneData.objects.update_or_create(
                    plant=plant,
                    zone=zone,
                    defaults={
                        'success_rating': rating,
                        'zone_specific_notes': notes
                    }
                )

                if was_created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Created {plant_name} - Zone {zone}'))
                else:
                    updated_count += 1
                    self.stdout.write(f'Updated {plant_name} - Zone {zone}')

        # Update version tracking
        migration.version = self.VERSION
        migration.save()

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Plant Zone Rating Population Complete (v{self.VERSION})'))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Plants not found: {not_found_count}')
        self.stdout.write(f'Total PlantZoneData records in database: {PlantZoneData.objects.count()}')
        self.stdout.write('='*60)
