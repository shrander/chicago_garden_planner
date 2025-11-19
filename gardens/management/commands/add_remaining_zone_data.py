"""
Management command to add zone-specific data for plants that only have Chicago zones.

Usage:
    python manage.py add_remaining_zone_data
    python manage.py add_remaining_zone_data --overwrite
"""

from django.core.management.base import BaseCommand
from gardens.models import Plant, PlantZoneData


class Command(BaseCommand):
    help = 'Add zone-specific ratings for plants missing full coverage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing zone data',
        )

    def handle(self, *args, **options):
        overwrite = options['overwrite']

        # Define success ratings for remaining plants by zone
        # Rating scale: 1=Not Recommended, 2=Challenging, 3=Moderate, 4=Good, 5=Excellent

        plant_zone_ratings = {
            'Brussels Sprouts': {
                '3a': (4, 'Excellent cold-hardy crop. Can overwinter in mild years.'),
                '3b': (5, 'Thrives in cold weather. Frost sweetens flavor.'),
                '4a': (5, 'Perfect zone. Plant summer for fall/winter harvest.'),
                '4b': (5, 'Excellent performer. Extended harvest through winter.'),
                '5a': (5, 'Ideal zone. Succession plant for continuous harvest.'),
                # '5b': Already exists from migration
                # '6a': Already exists from migration
                '6b': (4, 'Very good. May bolt in hot summers. Fall crop best.'),
                '7a': (4, 'Good fall through spring crop. Needs cool temps.'),
                '7b': (3, 'Moderate. Limited to winter growing. Oct-March.'),
                '8a': (3, 'Challenging. Winter crop only. Difficult to mature.'),
                '8b': (2, 'Very challenging. Short cool window. Not recommended.'),
                '9a': (2, 'Difficult. Too warm for good sprout development.'),
                '9b': (1, 'Not recommended. Too hot even in winter.'),
                '10a': (1, 'Not suitable. Use cabbage or kale instead.'),
                '10b': (1, 'Not suitable. Too tropical.'),
            },

            'Yukon Gold Potatoes': {
                '3a': (4, 'Good early crop. Choose early varieties (60-70 days).'),
                '3b': (4, 'Very good. Plant early for summer harvest.'),
                '4a': (5, 'Excellent zone. Full-season varieties possible.'),
                '4b': (5, 'Ideal. Plant April-May for late summer harvest.'),
                '5a': (5, 'Perfect conditions. Excellent yields.'),
                # '5b': Already exists from migration
                # '6a': Already exists from migration
                '6b': (4, 'Very good. May need irrigation in hot summers.'),
                '7a': (4, 'Good. Spring planting best. Summer heat can stress.'),
                '7b': (3, 'Moderate. Fall planting for winter crop works better.'),
                '8a': (3, 'Challenging. Fall/winter crop. Summer too hot.'),
                '8b': (3, 'Difficult. Winter crop only in most areas.'),
                '9a': (2, 'Very challenging. Limited success. Winter only.'),
                '9b': (2, 'Not recommended. Too warm year-round.'),
                '10a': (1, 'Not suitable. Try sweet potatoes instead.'),
                '10b': (1, 'Not suitable. Tropical alternatives better.'),
            },

            'Horseradish': {
                '3a': (5, 'Excellent hardy perennial. Vigorous growth.'),
                '3b': (5, 'Perfect. Very cold tolerant. Invasive without control.'),
                '4a': (5, 'Ideal zone. Strong root development.'),
                '4b': (5, 'Excellent. Contains easily with barriers.'),
                '5a': (5, 'Perfect conditions. Harvest roots in fall.'),
                # '5b': Already exists from migration
                # '6a': Already exists from migration
                '6b': (5, 'Excellent. May be more aggressive in warmer zones.'),
                '7a': (4, 'Very good. Needs containment. Vigorous spreader.'),
                '7b': (4, 'Good. Can become weedy. Plant in containers.'),
                '8a': (4, 'Good but very aggressive. Container recommended.'),
                '8b': (3, 'Moderate. Heat can reduce pungency. Spreads fast.'),
                '9a': (3, 'Challenging. Too warm for best quality. Invasive.'),
                '9b': (2, 'Difficult. Poor quality roots. Not recommended.'),
                '10a': (1, 'Not suitable. Too hot for proper development.'),
                '10b': (1, 'Not suitable. Use wasabi or ginger instead.'),
            },

            'Marigolds': {
                '3a': (3, 'Moderate. Annual only. Short season. Start indoors.'),
                '3b': (4, 'Good annual. Plant after frost. Pest deterrent.'),
                '4a': (4, 'Very good. French and signet types best.'),
                '4b': (5, 'Excellent. All types thrive. Blooms until frost.'),
                '5a': (5, 'Perfect zone. Long blooming season.'),
                # '5b': Already exists from migration
                # '6a': Already exists from migration
                '6b': (5, 'Ideal. Heat tolerant. Continuous blooms.'),
                '7a': (5, 'Excellent. Thrives in heat. Deadhead for more blooms.'),
                '7b': (5, 'Perfect. Year-round color possible with protection.'),
                '8a': (5, 'Excellent. Nearly year-round blooms.'),
                '8b': (4, 'Very good. Some varieties struggle in extreme heat.'),
                '9a': (4, 'Good. Choose heat-tolerant varieties. Afternoon shade helps.'),
                '9b': (4, 'Good with care. May need summer break. Fall-spring best.'),
                '10a': (3, 'Moderate. Cool-season annual. Oct-May blooming.'),
                '10b': (3, 'Challenging. Winter annual only. Too hot otherwise.'),
            },

            'Nasturtiums': {
                '3a': (3, 'Moderate. Short season annual. Quick from seed.'),
                '3b': (4, 'Good. Plant after frost. Edible flowers and leaves.'),
                '4a': (4, 'Very good. Trailing varieties excellent.'),
                '4b': (5, 'Excellent. Both bush and trailing types thrive.'),
                '5a': (5, 'Perfect zone. Aphid trap plant. Self-seeds.'),
                # '5b': Already exists from migration
                # '6a': Already exists from migration
                '6b': (5, 'Ideal. Heat tolerant. Continuous blooms.'),
                '7a': (5, 'Excellent. Thrives in warm weather. Edible peppery leaves.'),
                '7b': (4, 'Very good. May need afternoon shade in peak summer.'),
                '8a': (4, 'Good. Afternoon shade beneficial. Fall-spring best.'),
                '8b': (3, 'Moderate. Cool-season annual. Oct-May blooming.'),
                '9a': (3, 'Challenging. Winter crop. Too hot in summer.'),
                '9b': (2, 'Difficult. Brief cool-season window. Dec-Feb only.'),
                '10a': (2, 'Very challenging. Winter annual only.'),
                '10b': (1, 'Not recommended. Too tropical. Use hibiscus instead.'),
            },
        }

        # Note: "Empty Space" and "Path" are utility plants, not real plants
        # They should have minimal/neutral ratings across all zones
        utility_plants = {
            'Empty Space': {
                '3a': (3, 'Placeholder for future planting.'),
                '3b': (3, 'Placeholder for future planting.'),
                '4a': (3, 'Placeholder for future planting.'),
                '4b': (3, 'Placeholder for future planting.'),
                '5a': (3, 'Placeholder for future planting.'),
                # '5b': Already exists
                # '6a': Already exists
                '6b': (3, 'Placeholder for future planting.'),
                '7a': (3, 'Placeholder for future planting.'),
                '7b': (3, 'Placeholder for future planting.'),
                '8a': (3, 'Placeholder for future planting.'),
                '8b': (3, 'Placeholder for future planting.'),
                '9a': (3, 'Placeholder for future planting.'),
                '9b': (3, 'Placeholder for future planting.'),
                '10a': (3, 'Placeholder for future planting.'),
                '10b': (3, 'Placeholder for future planting.'),
            },
            'Path': {
                '3a': (3, 'Garden pathway or walking area.'),
                '3b': (3, 'Garden pathway or walking area.'),
                '4a': (3, 'Garden pathway or walking area.'),
                '4b': (3, 'Garden pathway or walking area.'),
                '5a': (3, 'Garden pathway or walking area.'),
                # '5b': Already exists
                # '6a': Already exists
                '6b': (3, 'Garden pathway or walking area.'),
                '7a': (3, 'Garden pathway or walking area.'),
                '7b': (3, 'Garden pathway or walking area.'),
                '8a': (3, 'Garden pathway or walking area.'),
                '8b': (3, 'Garden pathway or walking area.'),
                '9a': (3, 'Garden pathway or walking area.'),
                '9b': (3, 'Garden pathway or walking area.'),
                '10a': (3, 'Garden pathway or walking area.'),
                '10b': (3, 'Garden pathway or walking area.'),
            },
        }

        # Merge dictionaries
        all_ratings = {**plant_zone_ratings, **utility_plants}

        created_count = 0
        updated_count = 0
        skipped_count = 0
        not_found_count = 0

        for plant_name, zone_ratings in all_ratings.items():
            try:
                plant = Plant.objects.get(name=plant_name, is_default=True)
                self.stdout.write(f'\nProcessing {plant_name}...')

                for zone, (rating, notes) in zone_ratings.items():
                    existing = PlantZoneData.objects.filter(plant=plant, zone=zone).first()

                    if existing and not overwrite:
                        skipped_count += 1
                        self.stdout.write(self.style.WARNING(f'  ⊘ Zone {zone}: Already exists (use --overwrite)'))
                    elif existing and overwrite:
                        existing.success_rating = rating
                        existing.zone_specific_notes = notes
                        existing.save()
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Zone {zone}: Updated'))
                    else:
                        PlantZoneData.objects.create(
                            plant=plant,
                            zone=zone,
                            success_rating=rating,
                            zone_specific_notes=notes
                        )
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  + Zone {zone}: Created ({rating}★)'))

            except Plant.DoesNotExist:
                not_found_count += 1
                self.stdout.write(self.style.ERROR(f'✗ Plant "{plant_name}" not found'))

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Zone Data Population Complete'))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        self.stdout.write(f'Not Found: {not_found_count}')
        self.stdout.write('='*70)
