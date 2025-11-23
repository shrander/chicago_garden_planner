"""
Notification calculators for garden tasks.

This module contains functions that calculate when plants need attention
based on their planting and harvest schedules.
"""

from datetime import date
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
