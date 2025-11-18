"""
Utility functions for garden planning and zone-based calculations.
"""

from datetime import datetime, timedelta, date
from typing import Dict, Optional
from django.contrib.auth import get_user_model

User = get_user_model()


def get_user_frost_dates(user) -> Dict[str, date]:
    """
    Get frost dates for a user, prioritizing custom dates over zone defaults.

    Args:
        user: User instance

    Returns:
        dict with 'last_frost' and 'first_frost' as datetime.date objects
    """
    if hasattr(user, 'profile'):
        return user.profile.get_frost_dates()

    # Fallback to Chicago dates (5b/6a) if no profile
    current_year = datetime.now().year
    return {
        'last_frost': datetime.strptime(f"{current_year}-05-15", '%Y-%m-%d').date(),
        'first_frost': datetime.strptime(f"{current_year}-10-15", '%Y-%m-%d').date(),
    }


def calculate_planting_dates(plant, user_zone: str, reference_date: Optional[date] = None) -> Dict[str, date]:
    """
    Calculate recommended planting dates based on frost-relative timing.

    Args:
        plant: Plant model instance
        user_zone: User's hardiness zone (e.g., '5b', '6a')
        reference_date: Optional date to calculate from (defaults to today)

    Returns:
        dict with recommended dates (keys: 'start_seeds_indoors', 'transplant_outdoors', 'expected_harvest')
    """
    from gardens.models import ClimateZone

    if reference_date is None:
        reference_date = datetime.now().date()

    dates = {}

    try:
        climate = ClimateZone.objects.get(zone=user_zone)
        last_frost = datetime.strptime(f"{reference_date.year}-{climate.typical_last_frost}", '%Y-%m-%d').date()

        # Calculate seed starting date (weeks before last frost)
        if plant.weeks_before_last_frost_start:
            dates['start_seeds_indoors'] = last_frost - timedelta(weeks=plant.weeks_before_last_frost_start)

        # Calculate transplant date (weeks after last frost)
        if plant.weeks_after_last_frost_transplant is not None:
            dates['transplant_outdoors'] = last_frost + timedelta(weeks=plant.weeks_after_last_frost_transplant)

        # Calculate harvest date
        if plant.days_to_harvest:
            if dates.get('transplant_outdoors'):
                # If transplanting, calculate from transplant date
                dates['expected_harvest'] = dates['transplant_outdoors'] + timedelta(days=plant.days_to_harvest)
            elif plant.direct_sow and dates.get('start_seeds_indoors'):
                # If direct sowing, calculate from seed starting date
                dates['expected_harvest'] = dates['start_seeds_indoors'] + timedelta(days=plant.days_to_harvest)

    except ClimateZone.DoesNotExist:
        # Return empty dict if zone not found
        pass

    return dates


def get_growing_season_info(zone: str) -> Optional[Dict]:
    """
    Get growing season information for a specific zone.

    Args:
        zone: USDA hardiness zone (e.g., '5b', '6a')

    Returns:
        dict with zone info or None if not found
    """
    from gardens.models import ClimateZone

    try:
        climate = ClimateZone.objects.get(zone=zone)
        current_year = datetime.now().year

        return {
            'zone': climate.zone,
            'region_examples': climate.region_examples,
            'last_frost': datetime.strptime(f"{current_year}-{climate.typical_last_frost}", '%Y-%m-%d').date(),
            'first_frost': datetime.strptime(f"{current_year}-{climate.typical_first_frost}", '%Y-%m-%d').date(),
            'growing_season_days': climate.growing_season_days,
            'growing_season_weeks': climate.growing_season_days // 7,
            'avg_annual_min_temp_f': climate.avg_annual_min_temp_f,
            'avg_summer_high_f': climate.avg_summer_high_f,
            'common_soil_types': climate.common_soil_types,
            'humidity_level': climate.humidity_level,
            'special_considerations': climate.special_considerations,
        }
    except ClimateZone.DoesNotExist:
        return None


def format_frost_date(frost_date: date) -> str:
    """
    Format a frost date for display (e.g., "May 15" or "October 15").

    Args:
        frost_date: datetime.date object

    Returns:
        Formatted string (e.g., "May 15")
    """
    return frost_date.strftime("%B %d")


def is_planting_season(plant, user_zone: str, check_date: Optional[date] = None) -> bool:
    """
    Check if today (or a specific date) is within the planting season for a plant in a zone.

    Args:
        plant: Plant model instance
        user_zone: User's hardiness zone
        check_date: Date to check (defaults to today)

    Returns:
        True if within planting season, False otherwise
    """
    if check_date is None:
        check_date = datetime.now().date()

    planting_dates = calculate_planting_dates(plant, user_zone, check_date)

    if not planting_dates:
        return False

    # Check if we're within the planting window
    start_date = planting_dates.get('start_seeds_indoors') or planting_dates.get('transplant_outdoors')
    end_date = planting_dates.get('expected_harvest')

    if start_date and end_date:
        return start_date <= check_date <= end_date

    return False
