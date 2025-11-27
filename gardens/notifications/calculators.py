"""
Notification calculators for garden tasks.

This module contains functions that calculate when plants need attention
based on their planting and harvest schedules.
"""

from datetime import date, timedelta
from typing import Dict, List, Any


def calculate_garden_notifications(garden, user) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate harvest and planting notifications for a garden.

    Analyzes all plant instances in the garden to determine which plants
    need attention for harvesting, planting, or other tasks.

    Args:
        garden: Garden instance to calculate notifications for
        user: User instance (for future user-specific preferences)

    Returns:
        Dictionary with notification categories:
        {
            'harvest_ready': [...],      # Plants ready to harvest now
            'harvest_soon': [...],       # Plants approaching harvest (≤7 days)
            'harvest_overdue': [...],    # Plants past harvest date
            'planting_ready': []         # Reserved for future planting reminders
        }

        Each notification item contains:
        {
            'plant_name': str,
            'row': int,
            'col': int,
            'expected_date': date,
            'days_until': int (for soon) or 'days_overdue': int (for overdue),
            'instance_id': int
        }
    """
    notifications = {
        'harvest_ready': [],
        'harvest_soon': [],
        'harvest_overdue': [],
        'planting_ready': []
    }

    today = date.today()

    # Get plant instances with dates
    instances = garden.plant_instances.select_related('plant').all()

    for instance in instances:
        # Skip if no planted date or already harvested
        if not instance.planted_date or instance.actual_harvest_date:
            continue

        expected_harvest = instance.expected_harvest_date
        if not expected_harvest:
            continue

        days_until = (expected_harvest - today).days

        # Categorize based on days until harvest
        if days_until < 0:
            # Overdue
            notifications['harvest_overdue'].append({
                'plant_name': instance.plant.name,
                'row': instance.row,
                'col': instance.col,
                'expected_date': expected_harvest,
                'days_overdue': abs(days_until),
                'instance_id': instance.id
            })
        elif days_until == 0:
            # Ready today
            notifications['harvest_ready'].append({
                'plant_name': instance.plant.name,
                'row': instance.row,
                'col': instance.col,
                'expected_date': expected_harvest,
                'instance_id': instance.id
            })
        elif days_until <= 7:
            # Coming up within 7 days
            notifications['harvest_soon'].append({
                'plant_name': instance.plant.name,
                'row': instance.row,
                'col': instance.col,
                'expected_date': expected_harvest,
                'days_until': days_until,
                'instance_id': instance.id
            })

    return notifications


def calculate_all_notifications(user) -> Dict[str, Any]:
    """
    Calculate ALL notifications for a user across all their gardens.

    This is the comprehensive notification function for email digests.
    Checks all date types: seed start, transplant, planting/sowing, harvest.

    Args:
        user: User instance to calculate notifications for

    Returns:
        Dictionary organized by garden with all notification types:
        {
            'user': User instance,
            'notification_date': date.today(),
            'has_notifications': bool,
            'gardens': [
                {
                    'garden': Garden instance,
                    'overdue': [notification_items],      # Any overdue tasks (1-7 days late)
                    'due_today': [notification_items],    # Tasks due today
                    'coming_up': [notification_items],    # Tasks within next 7 days
                },
                ...
            ],
            'total_overdue': int,
            'total_due_today': int,
            'total_coming_up': int,
        }

        Each notification item contains:
        {
            'type': 'seed_start' | 'transplant' | 'planting' | 'harvest',
            'plant_instance': PlantInstance,
            'plant_name': str,
            'position': '(row,col)',
            'date': date,
            'days_overdue': int (for overdue),
            'days_until': int (for coming_up),
        }
    """
    from gardens.models import Garden

    result = {
        'user': user,
        'notification_date': date.today(),
        'has_notifications': False,
        'gardens': [],
        'total_overdue': 0,
        'total_due_today': 0,
        'total_coming_up': 0,
    }

    today = date.today()

    # Get all user's gardens
    gardens = Garden.objects.filter(owner=user).prefetch_related('plant_instances__plant')

    for garden in gardens:
        garden_notifications = {
            'garden': garden,
            'overdue': [],
            'due_today': [],
            'coming_up': [],
        }

        instances = garden.plant_instances.select_related('plant').all()

        for instance in instances:
            # 1. Check Seed Start (pot-started plants only)
            if (instance.seed_starting_method == 'pot' and
                instance.planned_seed_start_date and
                not instance.seed_started_date):

                days_diff = (instance.planned_seed_start_date - today).days

                if -7 <= days_diff < 0:
                    # Overdue (up to 7 days late)
                    garden_notifications['overdue'].append({
                        'type': 'seed_start',
                        'plant_instance': instance,
                        'plant_name': instance.plant.name,
                        'position': f'({instance.row},{instance.col})',
                        'date': instance.planned_seed_start_date,
                        'days_overdue': abs(days_diff),
                    })
                elif days_diff == 0:
                    # Due today
                    garden_notifications['due_today'].append({
                        'type': 'seed_start',
                        'plant_instance': instance,
                        'plant_name': instance.plant.name,
                        'position': f'({instance.row},{instance.col})',
                        'date': instance.planned_seed_start_date,
                    })
                elif 0 < days_diff <= 7:
                    # Coming up
                    garden_notifications['coming_up'].append({
                        'type': 'seed_start',
                        'plant_instance': instance,
                        'plant_name': instance.plant.name,
                        'position': f'({instance.row},{instance.col})',
                        'date': instance.planned_seed_start_date,
                        'days_until': days_diff,
                    })

            # 2. Check Transplant (pot-started plants with seeds started)
            if (instance.seed_starting_method == 'pot' and
                instance.seed_started_date and
                not instance.planted_date):

                expected_transplant = instance.calculate_expected_transplant_date()
                if expected_transplant:
                    days_diff = (expected_transplant - today).days

                    if -7 <= days_diff < 0:
                        garden_notifications['overdue'].append({
                            'type': 'transplant',
                            'plant_instance': instance,
                            'plant_name': instance.plant.name,
                            'position': f'({instance.row},{instance.col})',
                            'date': expected_transplant,
                            'days_overdue': abs(days_diff),
                        })
                    elif days_diff == 0:
                        garden_notifications['due_today'].append({
                            'type': 'transplant',
                            'plant_instance': instance,
                            'plant_name': instance.plant.name,
                            'position': f'({instance.row},{instance.col})',
                            'date': expected_transplant,
                        })
                    elif 0 < days_diff <= 7:
                        garden_notifications['coming_up'].append({
                            'type': 'transplant',
                            'plant_instance': instance,
                            'plant_name': instance.plant.name,
                            'position': f'({instance.row},{instance.col})',
                            'date': expected_transplant,
                            'days_until': days_diff,
                        })

            # 3. Check Planting/Sowing (planned planting date, not yet planted)
            if instance.planned_planting_date and not instance.planted_date:
                days_diff = (instance.planned_planting_date - today).days

                if -7 <= days_diff < 0:
                    garden_notifications['overdue'].append({
                        'type': 'planting',
                        'plant_instance': instance,
                        'plant_name': instance.plant.name,
                        'position': f'({instance.row},{instance.col})',
                        'date': instance.planned_planting_date,
                        'days_overdue': abs(days_diff),
                        'is_direct_sown': instance.seed_starting_method == 'direct',
                    })
                elif days_diff == 0:
                    garden_notifications['due_today'].append({
                        'type': 'planting',
                        'plant_instance': instance,
                        'plant_name': instance.plant.name,
                        'position': f'({instance.row},{instance.col})',
                        'date': instance.planned_planting_date,
                        'is_direct_sown': instance.seed_starting_method == 'direct',
                    })
                elif 0 < days_diff <= 7:
                    garden_notifications['coming_up'].append({
                        'type': 'planting',
                        'plant_instance': instance,
                        'plant_name': instance.plant.name,
                        'position': f'({instance.row},{instance.col})',
                        'date': instance.planned_planting_date,
                        'days_until': days_diff,
                        'is_direct_sown': instance.seed_starting_method == 'direct',
                    })

            # 4. Check Harvest (planted, not harvested)
            if instance.planted_date and not instance.actual_harvest_date:
                expected_harvest = instance.expected_harvest_date
                if expected_harvest:
                    days_diff = (expected_harvest - today).days

                    if -7 <= days_diff < 0:
                        garden_notifications['overdue'].append({
                            'type': 'harvest',
                            'plant_instance': instance,
                            'plant_name': instance.plant.name,
                            'position': f'({instance.row},{instance.col})',
                            'date': expected_harvest,
                            'days_overdue': abs(days_diff),
                        })
                    elif days_diff == 0:
                        garden_notifications['due_today'].append({
                            'type': 'harvest',
                            'plant_instance': instance,
                            'plant_name': instance.plant.name,
                            'position': f'({instance.row},{instance.col})',
                            'date': expected_harvest,
                        })
                    elif 0 < days_diff <= 7:
                        garden_notifications['coming_up'].append({
                            'type': 'harvest',
                            'plant_instance': instance,
                            'plant_name': instance.plant.name,
                            'position': f'({instance.row},{instance.col})',
                            'date': expected_harvest,
                            'days_until': days_diff,
                        })

        # Only include garden if it has notifications
        if garden_notifications['overdue'] or garden_notifications['due_today'] or garden_notifications['coming_up']:
            # Sort each category by days (overdue: most overdue first, coming_up: soonest first)
            garden_notifications['overdue'].sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
            garden_notifications['coming_up'].sort(key=lambda x: x.get('days_until', 999))

            result['gardens'].append(garden_notifications)
            result['total_overdue'] += len(garden_notifications['overdue'])
            result['total_due_today'] += len(garden_notifications['due_today'])
            result['total_coming_up'] += len(garden_notifications['coming_up'])

    result['has_notifications'] = (result['total_overdue'] > 0 or
                                   result['total_due_today'] > 0 or
                                   result['total_coming_up'] > 0)

    return result
