"""
Management command to populate square foot and row spacing data for plants.

Usage:
    python manage.py populate_plant_spacing
    python manage.py populate_plant_spacing --force
"""

from django.core.management.base import BaseCommand
from gardens.models import Plant, DataMigration


class Command(BaseCommand):
    help = 'Populate square foot and row spacing data for all plants'
    VERSION = '1.0.0'  # Increment when spacing data changes

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if version matches',
        )

    def handle(self, *args, **options):
        force = options['force']

        # Check version tracking
        migration, _ = DataMigration.objects.get_or_create(  # type: ignore[attr-defined]
            command_name='populate_plant_spacing',
            defaults={'version': '0.0.0'}
        )

        if migration.version == self.VERSION and not force:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Plant spacing already at version {self.VERSION} (use --force to update)'
            ))
            return

        self.stdout.write(f'Updating plant spacing data from v{migration.version} to v{self.VERSION}...')

        # Spacing data for all plants
        # Format: plant_name: (sq_ft_spacing, row_spacing_inches, row_spacing_between_rows)
        spacing_data = {
            # Vegetables
            'Tomatoes': (1, 24, 36),  # 1 per sq ft, 24" apart in row, 36" between rows
            'Tomato (Cherry)': (1, 24, 36),
            'Plum Tomato': (1, 24, 36),
            'Kale': (1, 18, 24),  # 1 per sq ft, 18" apart, 24" rows
            'Lacinato Kale': (1, 18, 24),
            'Carrots': (16, 3, 12),  # 16 per sq ft, 3" apart, 12" rows
            'Radishes': (16, 2, 6),  # 16 per sq ft, 2" apart, 6" rows
            'Brussels Sprouts': (1, 24, 30),  # 1 per sq ft, 24" apart, 30" rows
            'Yukon Gold Potatoes': (1, 12, 30),  # 1 per sq ft, 12" apart, 30" rows
            'Lettuce': (4, 6, 12),  # 4 per sq ft, 6" apart, 12" rows
            'Lettuce (Leaf)': (4, 6, 12),
            'Spinach': (9, 4, 12),  # 9 per sq ft, 4" apart, 12" rows
            'Basil': (4, 6, 12),  # 4 per sq ft, 6" apart, 12" rows
            'Garlic': (4, 4, 12),  # 4 per sq ft, 4" apart (cloves), 12" rows
            'Jalapeno': (1, 18, 24),  # 1 per sq ft, 18" apart, 24" rows

            # Herbs
            'Sage': (1, 18, 24),  # 1 per sq ft, 18" apart, 24" rows
            'Thyme': (4, 6, 12),  # 4 per sq ft, 6" apart, 12" rows
            'Chives': (16, 3, 6),  # 16 per sq ft, 3" apart, 6" rows
            'Dill': (4, 6, 12),  # 4 per sq ft, 6" apart, 12" rows
            'Horseradish': (1, 18, 30),  # 1 per sq ft, 18" apart, 30" rows

            # Flowers & Companions
            'Marigolds': (4, 6, 12),  # 4 per sq ft, 6" apart, 12" rows
            'Marigold': (4, 6, 12),
            'Nasturtiums': (4, 6, 12),  # 4 per sq ft, 6" apart, 12" rows

            # Fruits
            'Strawberries': (4, 6, 12),  # 4 per sq ft, 6" apart, 12" rows

            # Utility (doesn't matter, they're markers)
            'Empty Space': (0, 0, 0),
            'Path': (0, 0, 0),
        }

        updated_count = 0
        not_found_count = 0

        for plant_name, (sq_ft, row_in, row_between) in spacing_data.items():
            try:
                plant = Plant.objects.get(name=plant_name, is_default=True)  # type: ignore[attr-defined]
                plant.sq_ft_spacing = sq_ft
                plant.row_spacing_inches = row_in
                plant.row_spacing_between_rows = row_between
                plant.save()  # type: ignore[attr-defined]
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f'✓ {plant_name}: {sq_ft}/sq ft, {row_in}" in-row, {row_between}" between rows'
                ))
            except Plant.DoesNotExist:
                not_found_count += 1
                self.stdout.write(self.style.WARNING(f'⊘ Plant "{plant_name}" not found'))

        # Update version tracking
        migration.version = self.VERSION
        migration.save()  # type: ignore[attr-defined]

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(f'Plant Spacing Population Complete (v{self.VERSION})'))
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Not Found: {not_found_count}')
        self.stdout.write('='*70)
