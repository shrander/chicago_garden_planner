from django.core.management.base import BaseCommand
from gardens.models import Plant, DataMigration

class Command(BaseCommand):
    help = 'Create companion planting relationship between plants'
    VERSION = '1.0.0'  # Increment when companion relationships change

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if version matches',
        )

    def handle(self, *args, **options):
        force = options['force']

        # Check version tracking
        migration, _ = DataMigration.objects.get_or_create(
            command_name='create_companion_relationship',
            defaults={'version': '0.0.0'}
        )

        if migration.version == self.VERSION and not force:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Companion relationships already at version {self.VERSION} (use --force to update)'
            ))
            return

        self.stdout.write(f'Updating companion relationships from v{migration.version} to v{self.VERSION}...')

        try: 
            # get plants
            tomatoes = Plant.objects.get(name='Tomatoes', is_default=True)
            basil = Plant.objects.get(name='Basil', is_default=True)
            marigolds = Plant.objects.get(name='Marigolds', is_default=True)
            garlic = Plant.objects.get(name='Garlic', is_default=True)
            carrots = Plant.objects.get(name='Carrots', is_default=True)
            radishes = Plant.objects.get(name='Radishes', is_default=True)
            kale = Plant.objects.get(name='Kale', is_default=True)
            brussels = Plant.objects.get(name='Brussels Sprouts', is_default=True)
            sage = Plant.objects.get(name='Sage', is_default=True)

            # Create companion relationships
            companions = [
                (tomatoes, [basil, marigolds, garlic]),
                (carrots, [radishes, garlic]),
                (kale, [garlic, sage]),
                (brussels, [sage, garlic]),
                (basil, [tomatoes]),
                (marigolds, [tomatoes]),
                (garlic, [tomatoes, carrots, kale, brussels]),
                (sage, [kale, brussels]),
                (radishes, [carrots]),
            ]

            relationship_count = 0
            for plant, companion_list in companions:
                for companion in companion_list:
                    plant.companion_plants.add(companion)
                    relationship_count +=1
                    self.stdout.write(f'  ✓ {plant.name} ↔ {companion.name}')

            # Update version tracking
            migration.version = self.VERSION
            migration.save()

            self.stdout.write(
                self.style.SUCCESS(f'🌿 Created {relationship_count} companion relationships! (v{self.VERSION})')
            )

        except Plant.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: Required plant not found. Run populate_default_plants first.')
            )
            return