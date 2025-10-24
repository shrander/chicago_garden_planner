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


@register.filter
def divide(value, arg):
    """Divide the value by the argument."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def calculate_total_yield(yield_str, count):
    """
    Calculate total yield by parsing the yield string and multiplying by count.
    For ranges (e.g., "10-15 lbs"), uses the average.
    For continuous harvests, returns the base yield description.

    Examples:
        "10-15 lbs per plant" × 5 = "62.5 lbs"
        "1-2 quarts per plant per season" × 3 = "4.5 quarts per season"
        "1 cup per week (continuous harvest)" × 2 = "2 cups per week (continuous)"
    """
    import re

    if not yield_str or not count:
        return "No estimate"

    # Handle N/A or special cases
    if yield_str.upper() == 'N/A':
        return 'N/A'

    try:
        count = int(count)
    except (ValueError, TypeError):
        return yield_str

    # Pattern to match ranges like "10-15" or single numbers
    # For ranges, make sure we match at the START and not inside parentheses
    range_pattern = r'^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)'
    single_pattern = r'^(\d+(?:\.\d+)?)'
    fraction_pattern = r'^(\d+)/(\d+)'  # Match fractions like "1/2"

    # Check for fraction first (e.g., "1/2 cup")
    fraction_match = re.match(fraction_pattern, yield_str)
    if fraction_match:
        numerator = float(fraction_match.group(1))
        denominator = float(fraction_match.group(2))
        value = numerator / denominator
        total = value * count

        # Extract everything after the fraction
        rest_of_string = yield_str[fraction_match.end():].strip()

        # Check for continuous harvest in parentheses
        if 'continuous' in rest_of_string.lower():
            # Extract the part before parenthesis
            parts = rest_of_string.split('(')
            if len(parts) > 1:
                unit_part = parts[0].strip()
                # Pluralize if needed
                if total != 1 and 'cup' in unit_part:
                    unit_part = unit_part.replace('cup', 'cups', 1)

                if total == int(total):
                    return f"{int(total)} {unit_part} (continuous)".strip()
                else:
                    return f"{total:.1f} {unit_part} (continuous)".strip()

        # Format normally
        if total == int(total):
            return f"{int(total)} {rest_of_string}"
        else:
            return f"{total:.1f} {rest_of_string}"

    # Check for range (e.g., "10-15 lbs") - must be at start
    range_match = re.match(range_pattern, yield_str)
    if range_match:
        low = float(range_match.group(1))
        high = float(range_match.group(2))
        avg = (low + high) / 2
        total = avg * count

        # Extract the unit (everything after the number range)
        unit_part = yield_str[range_match.end():].strip()
        # Remove "per plant" if present
        unit_part = re.sub(r'\s*per plant\s*', ' ', unit_part).strip()

        # Format the total nicely
        if total == int(total):
            return f"{int(total)} {unit_part}"
        else:
            return f"{total:.1f} {unit_part}"

    # Check for continuous harvest BEFORE single number check
    # (e.g., "1 cup per week (continuous harvest)")
    if 'continuous' in yield_str.lower():
        # Extract just the measurement part (before parenthesis)
        parts = yield_str.split('(')
        if len(parts) > 1:
            measurement = parts[0].strip()
            # Try to find and multiply the number and get the unit word
            num_match = re.search(r'(\d+(?:\.\d+)?)\s+([a-zA-Z]+)', measurement)
            if num_match:
                value = float(num_match.group(1))
                unit_word = num_match.group(2)  # e.g., "cup", "lbs"
                total = value * count

                # Get everything after the unit word
                rest = measurement[num_match.end():].strip()

                # Pluralize unit if needed
                if total != 1:
                    if unit_word == 'cup':
                        unit_word = 'cups'
                    # Add more pluralizations as needed

                if total == int(total):
                    return f"{int(total)} {unit_word} {rest} (continuous)".strip()
                else:
                    return f"{total:.1f} {unit_word} {rest} (continuous)".strip()

    # Check for single number (e.g., "1 bulb")
    single_match = re.match(single_pattern, yield_str)
    if single_match:
        value = float(single_match.group(1))
        total = value * count

        # Extract everything after the number
        rest_of_string = yield_str[single_match.end():].strip()

        # Check if there's a parenthetical note (like "8-10 cloves")
        paren_match = re.search(r'\([^)]+\)', rest_of_string)
        if paren_match:
            # Keep the parenthetical part as-is
            before_paren = rest_of_string[:paren_match.start()].strip()
            paren_part = paren_match.group(0)

            # Remove "per plant" from before_paren
            before_paren = re.sub(r'\s*per plant\s*', ' ', before_paren).strip()

            # Handle pluralization for the unit before parenthesis
            if total != 1 and before_paren:
                if before_paren == 'bulb':
                    before_paren = 'bulbs'
                elif before_paren == 'cup':
                    before_paren = 'cups'

            # Format the total
            if total == int(total):
                return f"{int(total)} {before_paren} {paren_part}".strip()
            else:
                return f"{total:.1f} {before_paren} {paren_part}".strip()

        # No parenthetical - just use the rest
        unit_part = rest_of_string
        # Remove "per plant" if present
        unit_part = re.sub(r'\s*per plant\s*', ' ', unit_part).strip()

        # Handle pluralization for common units
        if total != 1:
            # Simple pluralization
            if unit_part.startswith('bulb'):
                unit_part = unit_part.replace('bulb', 'bulbs', 1)
            elif unit_part.startswith('cup'):
                unit_part = unit_part.replace('cup', 'cups', 1)

        # Format the total
        if total == int(total):
            return f"{int(total)} {unit_part}"
        else:
            return f"{total:.1f} {unit_part}"

    # Fallback: just show count × original
    return f"{count} × {yield_str}"