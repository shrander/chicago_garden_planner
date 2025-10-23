from django import template

register = template.Library()


@register.filter
def get_plant_info(plant_map, plant_name):
    """Get plant info from plant_map dictionary by plant name."""
    if not plant_name or not plant_map:
        return None
    return plant_map.get(plant_name.lower(), None)


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key."""
    if not dictionary or not key:
        return None
    return dictionary.get(key, None)


@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0