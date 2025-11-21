from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from gardens.models import Plant, Garden, DataMigration
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'populate db with default plants and sample garden'
    VERSION = '1.0.0'  # Increment when default plant data changes

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-sample-user',
            action='store_true',
            help='Create a sample user with a demo garden'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if version matches',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)

        # Check version tracking
        migration, _ = DataMigration.objects.get_or_create(
            command_name='populate_default_plants',
            defaults={'version': '0.0.0'}
        )

        if migration.version == self.VERSION and not force and not options.get('create_sample_user'):
            self.stdout.write(self.style.SUCCESS(
                f'✓ Default plants already at version {self.VERSION} (use --force to update)'
            ))
            return

        self.stdout.write(self.style.SUCCESS('🌱 Populating Chicago Garden Database...'))

        # create default plants
        self.create_default_plants()

        #optionally create sample user and garden
        if options['create_sample_user']:
            self.create_sample_user_and_garden()

        # Update version tracking
        migration.version = self.VERSION
        migration.save()

        self.stdout.write(
            self.style.SUCCESS(f'✅ Successfully populated database with Chicago garden data! (v{self.VERSION})')
        )

    def create_default_plants(self):
        """Create all the default plants"""

        default_plants = [
            {
                'name': 'Strawberries',
                'latin_name': 'Fragaria × ananassa',
                'symbol': 'S',
                'color': '#FFB6C1',
                'plant_type': 'fruit',
                'life_cycle': 'perennial',
                'planting_seasons': ['spring'],
                'days_to_harvest': 60,
                'spacing_inches': 6.0,
                'yield_per_plant': '1-2 quarts per plant per season',
                'chicago_notes': 'Plant in early spring after last frost danger. June-bearing varieties work best in Chicago. Protect from late frosts with row covers. Harvest peak season: June-July.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
            {
                'name': 'Tomatoes',
                'latin_name': 'Solanum lycopersicum',
                'symbol': 'T',
                'color': '#FF6347',
                'plant_type': 'vegetable',
                'life_cycle': 'annual',
                'planting_seasons': ['summer'],
                'days_to_harvest': 75,
                'spacing_inches': 24.0,
                'chicago_notes': 'Start indoors 6-8 weeks before last frost (mid-March). Transplant after soil reaches 65°F (late May). Choose disease-resistant varieties for Chicago humidity. Stake or cage for support.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
            {
                'name': 'Kale',
                'latin_name': 'Brassica oleracea (Acephala Group)',
                'symbol': 'K',
                'color': '#006400',
                'plant_type': 'vegetable',
                'life_cycle': 'biennial',
                'planting_seasons': ['spring', 'fall'],
                'days_to_harvest': 55,
                'spacing_inches': 15.0,
                'chicago_notes': 'Cool-season crop that thrives in Chicago springs and falls. Plant 2-4 weeks before last frost. Heat-tolerant varieties for summer growing. Sweetens after light frost.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
            {
                'name': 'Carrots',
                'latin_name': 'Daucus carota subsp. sativus',
                'symbol': 'C',
                'color': '#FF8C00',
                'plant_type': 'vegetable',
                'life_cycle': 'biennial',
                'planting_seasons': ['spring', 'summer', 'fall'],
                'days_to_harvest': 70,
                'spacing_inches': 2.0,
                'chicago_notes': 'Direct seed 2-3 weeks before last frost. Succession plant every 2-3 weeks through August. Choose shorter varieties for clay soil common in Chicago area.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
            {
                'name': 'Brussels Sprouts',
                'latin_name': 'Brassica oleracea (Gemmifera Group)',
                'symbol': 'B',
                'color': '#90EE90',
                'plant_type': 'vegetable',
                'life_cycle': 'biennial',
                'planting_seasons': ['summer'],
                'days_to_harvest': 100,
                'spacing_inches': 18.0,
                'chicago_notes': 'Start indoors in June for fall harvest. Transplant in July. Flavor improves after frost. Harvest from bottom up through winter in Chicago.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
            {
                'name': 'Yukon Gold Potatoes',
                'latin_name': 'Solanum tuberosum \'Yukon Gold\'',
                'symbol': 'P',
                'color': '#DEB887',
                'plant_type': 'vegetable',
                'life_cycle': 'annual',
                'planting_seasons': ['spring'],
                'days_to_harvest': 90,
                'spacing_inches': 18.0,
                'chicago_notes': 'Plant 2 weeks before last frost in Chicago (early April). Hill soil around plants as they grow. Harvest new potatoes in July, storage potatoes in September.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
            {
                'name': 'Lettuce',
                'latin_name': 'Lactuca sativa',
                'symbol': 'L',
                'color': '#ADFF2F',
                'plant_type': 'vegetable',
                'life_cycle': 'annual',
                'planting_seasons': ['spring', 'summer', 'fall'],
                'days_to_harvest': 45,
                'spacing_inches': 6.0,
                'chicago_notes': 'Cool-season crop. Plant early spring and late summer in Chicago. Use heat-tolerant varieties for summer succession. Provide afternoon shade in hot weather.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
            {
                'name': 'Garlic',
                'latin_name': 'Allium sativum',
                'symbol': 'G',
                'color': '#F5F5DC',
                'plant_type': 'vegetable',
                'life_cycle': 'perennial',
                'planting_seasons': ['fall'],
                'days_to_harvest': 240,
                'spacing_inches': 4.0,
                'chicago_notes': 'Plant hardneck varieties in October in Chicago. Harvest scapes in June, bulbs in July. Cure in ventilated area. Excellent companion plant.',
                'pest_deterrent_for': 'aphids, cabbage worms, Japanese beetles, carrot flies',
                'is_default': True,
            },
            {
                'name': 'Basil',
                'latin_name': 'Ocimum basilicum',
                'symbol': 'Ba',
                'color': '#6B46C1',
                'plant_type': 'herb',
                'life_cycle': 'annual',
                'planting_seasons': ['summer'],
                'days_to_harvest': 60,
                'spacing_inches': 12.0,
                'chicago_notes': 'Heat-loving herb. Plant after soil warms to 65°F in Chicago (late May). Pinch flowers to encourage leaf growth. Excellent companion to tomatoes.',
                'pest_deterrent_for': 'hornworms, aphids, spider mites',
                'is_default': True,
            },
            {
                'name': 'Radishes',
                'latin_name': 'Raphanus sativus',
                'symbol': 'Ra',
                'color': '#EC4899',
                'plant_type': 'vegetable',
                'life_cycle': 'annual',
                'planting_seasons': ['spring', 'fall'],
                'days_to_harvest': 25,
                'spacing_inches': 1.0,
                'chicago_notes': 'Fast-growing crop perfect for Chicago springs and falls. Direct seed 4 weeks before last frost. Succession plant every 2 weeks. Natural soil cultivator.',
                'pest_deterrent_for': 'root maggots, flea beetles',
                'is_default': True,
            },
            {
                'name': 'Marigolds',
                'latin_name': 'Tagetes patula',
                'symbol': 'Ma',
                'color': '#F59E0B',
                'plant_type': 'flower',
                'life_cycle': 'annual',
                'planting_seasons': ['spring'],
                'days_to_harvest': 50,
                'spacing_inches': 8.0,
                'chicago_notes': 'Heat-loving annual flowers. Plant after last frost in Chicago. Excellent companion plants. Deadhead for continuous blooms through first frost.',
                'pest_deterrent_for': 'nematodes, aphids, whiteflies, Mexican bean beetles',
                'is_default': True,
            },
            {
                'name': 'Sage',
                'latin_name': 'Salvia officinalis',
                'symbol': 'Sa',
                'color': '#10B981',
                'plant_type': 'herb',
                'life_cycle': 'perennial',
                'planting_seasons': ['spring'],
                'days_to_harvest': 75,
                'spacing_inches': 18.0,
                'chicago_notes': 'Perennial herb hardy in Chicago Zone 5b. Plant in spring. Harvest leaves before flowering. Cut back in fall. Survives Chicago winters with mulch.',
                'pest_deterrent_for': 'cabbage moths, flea beetles, carrot flies',
                'is_default': True,
            },
            # Additional Chicago-friendly plants
            {
                'name': 'Spinach',
                'latin_name': 'Spinacia oleracea',
                'symbol': 'Sp',
                'color': '#228B22',
                'plant_type': 'vegetable',
                'life_cycle': 'annual',
                'planting_seasons': ['spring', 'fall'],
                'days_to_harvest': 40,
                'spacing_inches': 4.0,
                'chicago_notes': 'Cool-season green perfect for Chicago springs and falls. Plant 4-6 weeks before last frost. Bolt-resistant varieties for longer harvest.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
            {
                'name': 'Chives',
                'latin_name': 'Allium schoenoprasum',
                'symbol': 'Ch',
                'color': '#9370DB',
                'plant_type': 'herb',
                'life_cycle': 'perennial',
                'planting_seasons': ['spring'],
                'days_to_harvest': 30,
                'spacing_inches': 6.0,
                'chicago_notes': 'Hardy perennial herb. Plant once and harvest for years. Divides easily. Purple flowers attract beneficial insects. Cut back after blooming.',
                'pest_deterrent_for': 'aphids, Japanese beetles',
                'is_default': True,
            },
            {
                'name': 'Nasturtiums',
                'latin_name': 'Tropaeolum majus',
                'symbol': 'Na',
                'color': '#FF4500',
                'plant_type': 'flower',
                'life_cycle': 'annual',
                'planting_seasons': ['spring'],
                'days_to_harvest': 45,
                'spacing_inches': 10.0,
                'chicago_notes': 'Annual flowers with edible blooms. Direct seed after last frost. Thrives in poor soil. Excellent trap crop for aphids. Climbing varieties save space.',
                'pest_deterrent_for': 'squash bugs, cucumber beetles',
                'is_default': True,
            },
            {
                'name': 'Dill',
                'latin_name': 'Anethum graveolens',
                'symbol': 'Di',
                'color': '#32CD32',
                'plant_type': 'herb',
                'life_cycle': 'annual',
                'planting_seasons': ['spring'],
                'days_to_harvest': 40,
                'spacing_inches': 8.0,
                'chicago_notes': 'Annual herb that self-seeds readily in Chicago gardens. Direct seed in spring. Attracts beneficial wasps and swallowtail butterflies.',
                'pest_deterrent_for': 'aphids, spider mites, cabbage loopers',
                'is_default': True,
            },
            {
                'name': 'Horseradish',
                'latin_name': 'Armoracia rusticana',
                'symbol': 'Hr',
                'color': '#F5DEB3',
                'plant_type': 'herb',
                'life_cycle': 'perennial',
                'planting_seasons': ['spring', 'fall'],
                'days_to_harvest': 150,
                'spacing_inches': 24.0,
                'chicago_notes': 'Hardy perennial root vegetable. Plant crowns in early spring or fall. Harvest roots in late fall after first frost for best flavor. Can be invasive - contain in dedicated bed. Thrives in Chicago climate.',
                'pest_deterrent_for': 'potato beetles, blister beetles, aphids',
                'is_default': True,
            },
            {
                'name': 'Thyme',
                'latin_name': 'Thymus vulgaris',
                'symbol': 'Th',
                'color': '#8FBC8F',
                'plant_type': 'herb',
                'life_cycle': 'perennial',
                'planting_seasons': ['spring'],
                'days_to_harvest': 75,
                'spacing_inches': 12.0,
                'chicago_notes': 'Hardy perennial herb for Chicago Zone 5b. Plant in spring after frost. Drought-tolerant once established. Harvest before flowering. Mulch heavily for winter protection. Attracts beneficial insects.',
                'pest_deterrent_for': 'cabbage worms, whiteflies',
                'is_default': True,
            },
            # System plants
            {
                'name': 'Path',
                'latin_name': 'Walking space',
                'symbol': '=',
                'color': '#D2B48C',
                'plant_type': 'companion',
                'life_cycle': 'annual',
                'planting_seasons': ['year_round'],
                'spacing_inches': 12.0,
                'chicago_notes': 'Designated walking paths prevent soil compaction in garden beds.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
            {
                'name': 'Empty Space',
                'latin_name': 'Available for planting',
                'symbol': '•',
                'color': '#8FBC8F',
                'plant_type': 'companion',
                'life_cycle': 'annual',
                'planting_seasons': ['year_round'],
                'spacing_inches': 0.0,
                'chicago_notes': 'Open space ready for planting or succession crops.',
                'pest_deterrent_for': '',
                'is_default': True,
            },
        ]

        created_count=0
        for plant_data in default_plants:
            plant, created = Plant.objects.get_or_create(
                name=plant_data['name'],
                is_default=True,
                defaults=plant_data
            )
            if created: 
                created_count+=1
                self.stdout.write(f'  ✓ Created: {plant.name}')
            else:
                self.stdout.write(f'  - Already exists: {plant.name}')

        self.stdout.write(
            self.style.SUCCESS(f'📦 Created {created_count} new plants out of {len(default_plants)} total')
        )

    def create_sample_user_and_garden(self):
        """Create a demo user with a sample garden layout"""

        # create demo user
        demo_user, created = User.objects.get_or_create(
            username='demo_garden',
            defaults={
                'email': 'demo@passwordspace.com',
                'first_name': 'Demo',
                'last_name': 'Gardener',
            }
        )

        if created: 
            demo_user.set_password('chicago2025')
            demo_user.save()
            self.stdout.write(' ✓ Created demo user: demo_gardener (password: chicago2025)')
        else:
            self.stdout.write('  - Demo user already exists')

        # create sample garden with optimized Chicago layout
        chicago_layout = [
            ['strawberries','strawberries','strawberries','path','tomatoes','basil','tomatoes','garlic','kale','sage'],
            ['strawberries','strawberries','strawberries','marigolds','tomatoes','tomatoes','tomatoes','garlic','kale','kale'],
            ['strawberries','strawberries','strawberries','path','tomatoes','tomatoes','tomatoes','garlic','kale','kale'],
            ['garlic','path','path','path','path','path','path','path','path','garlic'],
            ['carrots','radishes','carrots','carrots','garlic','brussels','brussels','garlic','lettuce','lettuce'],
            ['carrots','carrots','radishes','carrots','garlic','brussels','sage','garlic','lettuce','lettuce'],
            ['carrots','carrots','carrots','radishes','garlic','brussels','brussels','garlic','lettuce','lettuce'],
            ['garlic','potatoes','potatoes','potatoes','potatoes','potatoes','potatoes','potatoes','lettuce','lettuce'],
            ['garlic','potatoes','potatoes','potatoes','potatoes','potatoes','potatoes','potatoes','garlic','garlic'],
            ['garlic','potatoes','potatoes','potatoes','potatoes','potatoes','potatoes','potatoes','garlic','garlic']
        ]

        sample_garden, created = Garden.objects.get_or_create(
            name='Chicago Companion Garden',
            owner=demo_user,
            defaults={
                'description': 'Optimized 10×10 companion planting layout for Chicago Zone 5b/6a. Features strategic garlic placement, succession crops, and pest-deterrent flowers.',
                'size': '10x10',
                'width': 10,
                'height': 10,
                'layout_data': {'grid': chicago_layout},
                'is_public': True,
            }
        )

        if created:
            self.stdout.write('  ✓ Created sample garden: Chicago Companion Garden')
        else:
            self.stdout.write('  - Sample garden already exists')

        # create a second smaller garden example
        small_garden_layout = [
            ['lettuce','lettuce','radishes','carrots'],
            ['lettuce','lettuce','radishes','carrots'],
            ['basil','tomatoes','tomatoes','marigolds'],
            ['garlic','path','path','garlic']
        ]

        small_garden, created = Garden.objects.get_or_create(
            name='Beginner 4×4 Garden',
            owner=demo_user,
            defaults={
                'description': 'Perfect starter garden for Chicago beginners. Easy-to-grow plants with natural pest control.',
                'size': '4x4',
                'width': 4,
                'height': 4,
                'layout_data': {'grid': small_garden_layout},
                'is_public': True,
            }
        )

        if created:
            self.stdout.write('  ✓ Created sample garden: Beginner 4×4 Garden')
        else:
            self.stdout.write('  - Small garden already exists')

        self.stdout.write(
            self.style.SUCCESS('👤 Demo user and sample gardens ready!')
        )
