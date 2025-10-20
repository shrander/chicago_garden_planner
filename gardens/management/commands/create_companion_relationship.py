from django.core.management.base import BaseCommand
from gardens.models import Plant

class Command(BaseCommand):
    help = 'Create companion planting relationship between plants'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🤝 Creating companion plant relationships...'))

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

            self.stdout.write(
                self.style.SUCCESS(f'🌿 Created {relationship_count} companion relationships!')
            )

        except Plant.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error: Required plant not found. Run populate_default_plants first.')
            )
            return