"""
Management command to populate or update ClimateZone data.
Usage: python manage.py populate_climate_zones
"""

from django.core.management.base import BaseCommand
from gardens.models import ClimateZone, DataMigration


class Command(BaseCommand):
    help = 'Populate or update ClimateZone table with all USDA hardiness zones'
    VERSION = '1.0.0'  # Increment this when zone data changes

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if version matches',
        )

    def handle(self, *args, **options):
        force = options['force']

        # Check version tracking
        migration, created = DataMigration.objects.get_or_create(  # type: ignore[attr-defined]
            command_name='populate_climate_zones',
            defaults={'version': '0.0.0'}
        )

        if migration.version == self.VERSION and not force:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Climate zones already at version {self.VERSION} (use --force to update)'
            ))
            return

        self.stdout.write(f'Updating climate zones from v{migration.version} to v{self.VERSION}...')

        zones_data = [
            # Zone 3a - Coldest
            {
                'zone': '3a',
                'region_examples': 'International Falls MN, Duluth MN, Fargo ND',
                'typical_last_frost': '05-30',
                'typical_first_frost': '09-15',
                'avg_annual_min_temp_f': -40,
                'avg_summer_high_f': 76,
                'growing_season_days': 107,
                'common_soil_types': 'Loam, Clay',
                'humidity_level': 'moderate',
                'special_considerations': 'Very short growing season. Focus on cold-hardy varieties and season extension with cold frames. Early-maturing vegetables essential.',
            },
            # Zone 3b
            {
                'zone': '3b',
                'region_examples': 'Bemidji MN, Marquette MI, Bangor ME',
                'typical_last_frost': '05-25',
                'typical_first_frost': '09-20',
                'avg_annual_min_temp_f': -35,
                'avg_summer_high_f': 78,
                'growing_season_days': 118,
                'common_soil_types': 'Loam, Sandy Loam',
                'humidity_level': 'moderate',
                'special_considerations': 'Short growing season requires early-maturing cultivars. Cold frames and row covers extend season.',
            },
            # Zone 4a
            {
                'zone': '4a',
                'region_examples': 'Minneapolis MN, Green Bay WI, Portland ME',
                'typical_last_frost': '05-15',
                'typical_first_frost': '10-01',
                'avg_annual_min_temp_f': -30,
                'avg_summer_high_f': 81,
                'growing_season_days': 139,
                'common_soil_types': 'Loam, Clay Loam',
                'humidity_level': 'moderate',
                'special_considerations': 'Cold winters require winter protection for perennials. Choose cold-hardy varieties.',
            },
            # Zone 4b
            {
                'zone': '4b',
                'region_examples': 'Boise ID, Casper WY, Burlington VT',
                'typical_last_frost': '05-10',
                'typical_first_frost': '10-05',
                'avg_annual_min_temp_f': -25,
                'avg_summer_high_f': 83,
                'growing_season_days': 148,
                'common_soil_types': 'Loam, Sandy Loam',
                'humidity_level': 'moderate',
                'special_considerations': 'Good range of vegetables possible. Protect tender plants from late/early frosts.',
            },
            # Zone 5a
            {
                'zone': '5a',
                'region_examples': 'Des Moines IA, Cleveland OH, Buffalo NY',
                'typical_last_frost': '05-10',
                'typical_first_frost': '10-10',
                'avg_annual_min_temp_f': -20,
                'avg_summer_high_f': 84,
                'growing_season_days': 153,
                'common_soil_types': 'Clay, Loam',
                'humidity_level': 'moderate',
                'special_considerations': 'Wide variety of vegetables possible. Succession planting recommended.',
            },
            # Zone 5b - Chicago
            {
                'zone': '5b',
                'region_examples': 'Chicago IL, Denver CO, Boston MA',
                'typical_last_frost': '05-15',
                'typical_first_frost': '10-15',
                'avg_annual_min_temp_f': -15,
                'avg_summer_high_f': 85,
                'growing_season_days': 153,
                'common_soil_types': 'Clay, Loam',
                'humidity_level': 'high',
                'special_considerations': 'High humidity requires disease-resistant varieties. Clay soil benefits from organic matter amendments. Good zone for most common vegetables.',
            },
            # Zone 6a - Chicago suburbs
            {
                'zone': '6a',
                'region_examples': 'St. Louis MO, Cincinnati OH, Philadelphia PA',
                'typical_last_frost': '05-01',
                'typical_first_frost': '10-30',
                'avg_annual_min_temp_f': -10,
                'avg_summer_high_f': 87,
                'growing_season_days': 182,
                'common_soil_types': 'Loam, Clay',
                'humidity_level': 'high',
                'special_considerations': 'Longer growing season allows for succession planting and fall crops. Watch for fungal diseases in humid conditions.',
            },
            # Zone 6b
            {
                'zone': '6b',
                'region_examples': 'Kansas City MO, Louisville KY, New York NY',
                'typical_last_frost': '04-25',
                'typical_first_frost': '11-05',
                'avg_annual_min_temp_f': -5,
                'avg_summer_high_f': 88,
                'growing_season_days': 194,
                'common_soil_types': 'Loam, Clay Loam',
                'humidity_level': 'moderate',
                'special_considerations': 'Extended season allows multiple succession plantings. Good zone for diverse crop selection.',
            },
            # Zone 7a
            {
                'zone': '7a',
                'region_examples': 'Oklahoma City OK, Memphis TN, Richmond VA',
                'typical_last_frost': '04-15',
                'typical_first_frost': '11-10',
                'avg_annual_min_temp_f': 0,
                'avg_summer_high_f': 92,
                'growing_season_days': 209,
                'common_soil_types': 'Clay, Loam',
                'humidity_level': 'moderate',
                'special_considerations': 'Long season excellent for warm-season crops. Hot summers - provide shade for cool-season crops. Spring and fall gardens very productive.',
            },
            # Zone 7b
            {
                'zone': '7b',
                'region_examples': 'Little Rock AR, Raleigh NC, Seattle WA',
                'typical_last_frost': '04-10',
                'typical_first_frost': '11-15',
                'avg_annual_min_temp_f': 5,
                'avg_summer_high_f': 89,
                'growing_season_days': 219,
                'common_soil_types': 'Loam, Sandy Loam',
                'humidity_level': 'moderate',
                'special_considerations': 'Very long growing season. Year-round gardening possible with protection. Choose heat-tolerant varieties for summer.',
            },
            # Zone 8a
            {
                'zone': '8a',
                'region_examples': 'Dallas TX, Atlanta GA, Portland OR',
                'typical_last_frost': '03-25',
                'typical_first_frost': '11-25',
                'avg_annual_min_temp_f': 10,
                'avg_summer_high_f': 94,
                'growing_season_days': 245,
                'common_soil_types': 'Clay, Sandy Loam',
                'humidity_level': 'moderate',
                'special_considerations': 'Nearly year-round growing possible. Hot summers require heat-tolerant varieties and consistent watering. Excellent for fall/winter gardens.',
            },
            # Zone 8b
            {
                'zone': '8b',
                'region_examples': 'Austin TX, Charleston SC, Phoenix AZ',
                'typical_last_frost': '03-15',
                'typical_first_frost': '12-01',
                'avg_annual_min_temp_f': 15,
                'avg_summer_high_f': 96,
                'growing_season_days': 261,
                'common_soil_types': 'Sandy, Clay',
                'humidity_level': 'low',
                'special_considerations': 'Year-round gardening in most years. Extreme summer heat - focus on cool-season crops fall through spring. Excellent citrus zone.',
            },
            # Zone 9a
            {
                'zone': '9a',
                'region_examples': 'Houston TX, Orlando FL, Los Angeles CA',
                'typical_last_frost': '02-28',
                'typical_first_frost': '12-15',
                'avg_annual_min_temp_f': 20,
                'avg_summer_high_f': 93,
                'growing_season_days': 290,
                'common_soil_types': 'Sandy, Clay',
                'humidity_level': 'high',
                'special_considerations': 'Year-round growing. Cool-season crops Oct-March, warm-season spring/fall. Summer too hot for many crops. Humidity encourages disease.',
            },
            # Zone 9b
            {
                'zone': '9b',
                'region_examples': 'Miami FL, San Diego CA, Brownsville TX',
                'typical_last_frost': '02-15',
                'typical_first_frost': '12-31',
                'avg_annual_min_temp_f': 25,
                'avg_summer_high_f': 90,
                'growing_season_days': 319,
                'common_soil_types': 'Sandy, Limestone',
                'humidity_level': 'high',
                'special_considerations': 'Frost-free in most years. Heat limits tomatoes, peppers to cooler months. Tropical fruits thrive. Focus on heat-adapted varieties.',
            },
            # Zone 10a
            {
                'zone': '10a',
                'region_examples': 'Naples FL, San Juan PR, Key West FL',
                'typical_last_frost': '01-31',
                'typical_first_frost': '12-31',
                'avg_annual_min_temp_f': 30,
                'avg_summer_high_f': 89,
                'growing_season_days': 365,
                'common_soil_types': 'Sandy, Coral',
                'humidity_level': 'high',
                'special_considerations': 'Frost-free. Cool-season crops Dec-Feb only. Focus on tropical vegetables and fruits. High pest/disease pressure year-round.',
            },
            # Zone 10b - Warmest
            {
                'zone': '10b',
                'region_examples': 'South Miami FL, Hawaii, Southern California coast',
                'typical_last_frost': '01-01',
                'typical_first_frost': '12-31',
                'avg_annual_min_temp_f': 35,
                'avg_summer_high_f': 87,
                'growing_season_days': 365,
                'common_soil_types': 'Sandy, Volcanic',
                'humidity_level': 'high',
                'special_considerations': 'No frost. Traditional vegetables struggle - use tropical alternatives. Continuous pest management needed. Excellent for tropical fruits.',
            },
        ]

        created_count = 0
        updated_count = 0

        # Use update_or_create for idempotent operation
        for zone_info in zones_data:
            zone_code = zone_info['zone']
            zone, was_created = ClimateZone.objects.update_or_create(  # type: ignore[attr-defined]
                zone=zone_code,
                defaults=zone_info
            )

            if was_created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created zone {zone_code}'))
            else:
                updated_count += 1
                self.stdout.write(f'Updated zone {zone_code}')

        # Update version tracking
        migration.version = self.VERSION
        migration.save()  # type: ignore[attr-defined]

        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Climate Zone Population Complete (v{self.VERSION})'))
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Total zones in database: {ClimateZone.objects.count()}')  # type: ignore[attr-defined]
        self.stdout.write('='*60)
