from django.core.management.base import BaseCommand
from gardens.models import Plant


class Command(BaseCommand):
    help = 'Populate database with utility plants (Empty Space and Path)'

    def handle(self, *args, **kwargs):
        # Create or update Empty Space utility plant
        empty_space, created = Plant.objects.get_or_create(
            name='Empty Space',
            defaults={
                'latin_name': 'Vacuus spatium',
                'symbol': '•',
                'color': '#8FBC8F',
                'plant_type': 'utility',
                'planting_season': 'year_round',
                'spacing_inches': 0,
                'chicago_notes': 'Use to clear grid cells or mark open space in your garden layout.',
                'is_default': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created utility plant: {empty_space.name}'))
        else:
            # Update existing if needed
            empty_space.plant_type = 'utility'
            empty_space.is_default = True
            empty_space.save()
            self.stdout.write(self.style.WARNING(f'Updated existing plant: {empty_space.name}'))

        # Create or update Path utility plant
        path, created = Plant.objects.get_or_create(
            name='Path',
            defaults={
                'latin_name': 'Via hortus',
                'symbol': '=',
                'color': '#D2B48C',
                'plant_type': 'utility',
                'planting_season': 'year_round',
                'spacing_inches': 0,
                'chicago_notes': 'Mark pathways and walking areas in your garden layout.',
                'is_default': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created utility plant: {path.name}'))
        else:
            # Update existing if needed
            path.plant_type = 'utility'
            path.is_default = True
            path.save()
            self.stdout.write(self.style.WARNING(f'Updated existing plant: {path.name}'))

        self.stdout.write(self.style.SUCCESS('\nUtility plants setup complete!'))