"""
Management command to update yield information for all plants in the database.
Usage: python manage.py update_plant_yields
"""
from django.core.management.base import BaseCommand
from gardens.models import Plant


class Command(BaseCommand):
    help = 'Update yield information for all plants in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Define yield data for all plants
        # Format: 'plant_name': 'yield_value'
        # Yields should be per plant unless otherwise specified
        yield_data = {
            # Vegetables
            'tomatoes': '10-15 lbs',
            'lettuce': '4-6 oz',
            'carrots': '1-2 lbs per sq ft',
            'radishes': '1-2 oz',
            'spinach': '4-6 oz (continuous)',
            'kale': '1-2 lbs (continuous)',
            'brussels sprouts': '1-2 lbs',
            'yukon gold potatoes': '5-10 lbs',

            # Herbs
            'basil': '1 cup per week (continuous)',
            'dill': '1/2 cup per week (continuous)',
            'chives': '1/4 cup per week (continuous)',
            'thyme': '1/4 cup per week (continuous)',
            'sage': '1/2 cup per month (continuous)',
            'garlic': '1 bulb (8-10 cloves)',
            'horseradish': '2-4 lbs',

            # Fruits & Berries
            'strawberries': '1-2 quarts per season',

            # Flowers
            'marigolds': '20-30 blooms (continuous)',
            'nasturtiums': '15-25 flowers',

            # Special cases (no yield)
            'empty space': 'N/A',
            'path': 'N/A',
        }

        updated_count = 0
        not_found_count = 0

        for plant_name, yield_value in yield_data.items():
            try:
                # Try to find plant by name (case-insensitive)
                plant = Plant.objects.get(name__iexact=plant_name)

                old_yield = plant.yield_per_plant
                plant.yield_per_plant = yield_value

                if dry_run:
                    self.stdout.write(
                        f'Would update {plant.name}: '
                        f'"{old_yield}" -> "{yield_value}"'
                    )
                else:
                    plant.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Updated {plant.name}: '
                            f'"{old_yield}" -> "{yield_value}"'
                        )
                    )

                updated_count += 1

            except Plant.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'✗ Plant not found: {plant_name}'
                    )
                )
                not_found_count += 1

        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN COMPLETE: Would update {updated_count} plants'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Successfully updated {updated_count} plants'
                )
            )

        if not_found_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'✗ {not_found_count} plants not found in database'
                )
            )

        self.stdout.write('='*60)
