# Generated manually for populating plant timing data

from django.db import migrations


def populate_plant_timing(apps, schema_editor):
    """
    Populate timing data for default plants based on typical Chicago growing patterns.
    Data sources: University of Illinois Extension, Burpee Seed Company, Johnny's Selected Seeds
    """
    Plant = apps.get_model('gardens', 'Plant')

    # Define timing data for common vegetables (all in days unless noted)
    plant_timing_data = {
        'Tomato': {
            'direct_sow': False,
            'days_to_germination': 7,
            'days_before_transplant_ready': 42,  # 6 weeks from germination
            'transplant_to_harvest_days': 65,
        },
        'Pepper': {
            'direct_sow': False,
            'days_to_germination': 10,
            'days_before_transplant_ready': 49,  # 7 weeks
            'transplant_to_harvest_days': 70,
        },
        'Lettuce': {
            'direct_sow': True,
            'days_to_germination': 7,
            'days_to_harvest': 50,
        },
        'Carrots': {
            'direct_sow': True,
            'days_to_germination': 14,
            'days_to_harvest': 70,
        },
        'Beans': {
            'direct_sow': True,
            'days_to_germination': 7,
            'days_to_harvest': 55,
        },
        'Peas': {
            'direct_sow': True,
            'days_to_germination': 7,
            'days_to_harvest': 60,
        },
        'Cucumber': {
            'direct_sow': True,
            'days_to_germination': 7,
            'days_to_harvest': 55,
        },
        'Zucchini': {
            'direct_sow': True,
            'days_to_germination': 7,
            'days_to_harvest': 50,
        },
        'Radish': {
            'direct_sow': True,
            'days_to_germination': 5,
            'days_to_harvest': 25,
        },
        'Spinach': {
            'direct_sow': True,
            'days_to_germination': 7,
            'days_to_harvest': 45,
        },
        'Kale': {
            'direct_sow': False,
            'days_to_germination': 7,
            'days_before_transplant_ready': 28,  # 4 weeks
            'transplant_to_harvest_days': 60,
        },
        'Broccoli': {
            'direct_sow': False,
            'days_to_germination': 7,
            'days_before_transplant_ready': 35,  # 5 weeks
            'transplant_to_harvest_days': 70,
        },
        'Brussels Sprouts': {
            'direct_sow': False,
            'days_to_germination': 7,
            'days_before_transplant_ready': 35,
            'transplant_to_harvest_days': 100,
        },
        'Basil': {
            'direct_sow': False,
            'days_to_germination': 7,
            'days_before_transplant_ready': 35,
            'transplant_to_harvest_days': 60,
        },
        'Squash': {
            'direct_sow': True,
            'days_to_germination': 7,
            'days_to_harvest': 50,
        },
        'Corn': {
            'direct_sow': True,
            'days_to_germination': 7,
            'days_to_harvest': 75,
        },
        'Onion': {
            'direct_sow': False,
            'days_to_germination': 10,
            'days_before_transplant_ready': 49,  # 7 weeks
            'transplant_to_harvest_days': 100,
        },
        'Garlic': {
            'direct_sow': True,
            'days_to_germination': 14,
            'days_to_harvest': 240,  # Planted in fall, harvested next summer
        },
        'Beets': {
            'direct_sow': True,
            'days_to_germination': 10,
            'days_to_harvest': 55,
        },
        'Swiss Chard': {
            'direct_sow': True,
            'days_to_germination': 7,
            'days_to_harvest': 50,
        },
    }

    # Update plants that exist in the database
    for plant_name, timing_data in plant_timing_data.items():
        try:
            # Find plant by name (case-insensitive)
            plant = Plant.objects.filter(name__iexact=plant_name, is_default=True).first()
            if plant:
                plant.direct_sow = timing_data.get('direct_sow', False)
                plant.days_to_germination = timing_data.get('days_to_germination')
                plant.days_before_transplant_ready = timing_data.get('days_before_transplant_ready')
                plant.transplant_to_harvest_days = timing_data.get('transplant_to_harvest_days')

                # If days_to_harvest not set, use transplant_to_harvest_days or existing value
                if not plant.days_to_harvest and 'days_to_harvest' in timing_data:
                    plant.days_to_harvest = timing_data['days_to_harvest']

                plant.save()
                print(f"Updated timing data for {plant.name}")
        except Exception as e:
            print(f"Could not update {plant_name}: {e}")


def reverse_populate(apps, schema_editor):
    """Reverse migration - clear timing data"""
    Plant = apps.get_model('gardens', 'Plant')
    Plant.objects.filter(is_default=True).update(
        direct_sow=False,
        days_to_germination=None,
        days_before_transplant_ready=None,
        transplant_to_harvest_days=None,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('gardens', '0010_remove_plantinstance_transplanted_date_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_plant_timing, reverse_populate),
    ]
