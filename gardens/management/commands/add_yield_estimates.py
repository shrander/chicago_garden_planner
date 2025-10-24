from django.core.management.base import BaseCommand
from gardens.models import Plant


class Command(BaseCommand):
    help = 'Add yield estimates to default plants'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌾 Adding yield estimates to plants...'))

        # Yield data for each plant - based on realistic Chicago growing conditions
        yield_data = {
            'Strawberries': '1-2 quarts per plant per season',
            'Tomatoes': '10-15 lbs per plant',
            'Kale': '1-2 lbs per plant (continuous harvest)',
            'Carrots': '1-2 lbs per sq ft',
            'Brussels Sprouts': '1-2 lbs per plant',
            'Yukon Gold Potatoes': '5-10 lbs per plant',
            'Lettuce': '4-6 oz per head',
            'Garlic': '1 bulb (8-10 cloves) per plant',
            'Basil': '1 cup fresh leaves per week (continuous harvest)',
            'Radishes': '1-2 oz per radish',
            'Marigolds': '20-30 blooms per plant (continuous)',
            'Sage': '1/2 cup fresh leaves per month (continuous harvest)',
            'Spinach': '4-6 oz per plant (continuous harvest)',
            'Chives': '1/4 cup per week (continuous harvest)',
            'Nasturtiums': '15-25 edible flowers per plant',
            'Dill': '1/2 cup fresh leaves per plant (continuous harvest)',
            'Horseradish': '2-4 lbs of root per plant',
            'Thyme': '1/4 cup fresh sprigs per week (continuous harvest)',
            'Path': 'N/A',
            'Empty Space': 'N/A',
        }

        updated_count = 0
        for plant_name, yield_estimate in yield_data.items():
            try:
                plant = Plant.objects.get(name=plant_name, is_default=True)
                plant.yield_per_plant = yield_estimate
                plant.save()
                updated_count += 1
                self.stdout.write(f'  ✓ Updated {plant_name}: {yield_estimate}')
            except Plant.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Plant not found: {plant_name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'✅ Updated {updated_count} plants with yield estimates')
        )
