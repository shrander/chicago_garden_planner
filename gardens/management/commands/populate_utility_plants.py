from django.core.management.base import BaseCommand
from gardens.models import Plant, DataMigration


class Command(BaseCommand):
    help = 'Populate database with utility plants (Empty Space and Path)'
    VERSION = '1.0.0'  # Increment when utility plant data changes

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if version matches',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        # Check version tracking
        migration, _ = DataMigration.objects.get_or_create(  # type: ignore[attr-defined]
            command_name='populate_utility_plants',
            defaults={'version': '0.0.0'}
        )

        if migration.version == self.VERSION and not force:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Utility plants already at version {self.VERSION} (use --force to update)'
            ))
            return

        self.stdout.write(f'Updating utility plants from v{migration.version} to v{self.VERSION}...')

        # Create or update Empty Space utility plant
        empty_space, created = Plant.objects.update_or_create(  # type: ignore[attr-defined]
            name='Empty Space',
            is_default=True,
            defaults={
                'latin_name': 'Vacuus spatium',
                'symbol': '•',
                'color': '#8FBC8F',
                'plant_type': 'utility',
                'planting_seasons': ['year_round'],
                'spacing_inches': 0,
                'is_default': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created utility plant: {empty_space.name}'))
        else:
            self.stdout.write(f'Updated utility plant: {empty_space.name}')

        # Create or update Path utility plant
        path, created = Plant.objects.update_or_create(  # type: ignore[attr-defined]
            name='Path',
            is_default=True,
            defaults={
                'latin_name': 'Via hortus',
                'symbol': '=',
                'color': '#D2B48C',
                'plant_type': 'utility',
                'planting_seasons': ['year_round'],
                'spacing_inches': 0,
                'is_default': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created utility plant: {path.name}'))
        else:
            self.stdout.write(f'Updated utility plant: {path.name}')

        # Update version tracking
        migration.version = self.VERSION
        migration.save()  # type: ignore[attr-defined]

        self.stdout.write(self.style.SUCCESS(f'\nUtility plants setup complete! (v{self.VERSION})'))