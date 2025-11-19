# Zone Data Template

This template helps you quickly add zone-specific growing information for new plants.

## How to Use This Template

1. Copy the plant template below
2. Fill in ratings (1-5) and zone-specific notes for each zone
3. Add to `populate_plant_zone_ratings.py` or `add_remaining_zone_data.py`
4. Run the management command to populate the database

## Rating Scale

- **5 ⭐⭐⭐⭐⭐** - Excellent: Thrives with minimal care
- **4 ⭐⭐⭐⭐** - Good: Grows well with standard care
- **3 ⭐⭐⭐** - Moderate: Possible but requires extra effort
- **2 ⭐⭐** - Challenging: Difficult, marginal success
- **1 ⭐** - Not Recommended: Poor performance, not worth the effort

## Plant Template

```python
'Plant Name Here': {
    # ZONE 3: Very Cold (-40°F to -30°F)
    # Last Frost: May 25-30, First Frost: Sept 15-20, Season: 107-118 days
    '3a': (rating, 'Zone-specific notes here. Focus on: cold hardiness, short season varieties, season extension needs.'),
    '3b': (rating, 'Similar to 3a but slightly longer season. Mention early-maturing varieties.'),

    # ZONE 4: Cold (-30°F to -20°F)
    # Last Frost: May 10-15, First Frost: Oct 1-5, Season: 139-148 days
    '4a': (rating, 'Cold but manageable. Note: winter protection needs, cold-hardy varieties.'),
    '4b': (rating, 'Transition zone. Mention: variety selection, frost protection strategies.'),

    # ZONE 5: Cool (-20°F to -10°F)
    # Last Frost: May 10-15, First Frost: Oct 10-15, Season: 153 days
    '5a': (rating, 'Good growing conditions. Mention: succession planting, season length benefits.'),
    '5b': (rating, 'Chicago zone! Note: humidity issues, clay soil, disease-resistant varieties.'),

    # ZONE 6: Moderate (-10°F to 0°F)
    # Last Frost: April 25 - May 1, First Frost: Oct 30 - Nov 5, Season: 182-194 days
    '6a': (rating, 'Longer season. Focus on: multiple plantings, fall crops, succession.'),
    '6b': (rating, 'Extended season. Mention: heat tolerance needs, diverse varieties possible.'),

    # ZONE 7: Mild (0°F to 10°F)
    # Last Frost: April 10-15, First Frost: Nov 10-15, Season: 209-219 days
    '7a': (rating, 'Long season. Note: heat tolerance, cool-season timing, spring/fall best.'),
    '7b': (rating, 'Very long season. Mention: year-round potential, heat management, winter growing.'),

    # ZONE 8: Warm (10°F to 20°F)
    # Last Frost: March 15-25, First Frost: Nov 25 - Dec 1, Season: 245-261 days
    '8a': (rating, 'Nearly year-round. Focus on: heat tolerance, cool-season timing, watering needs.'),
    '8b': (rating, 'Year-round in most years. Mention: extreme heat management, cool-season focus.'),

    # ZONE 9: Hot (20°F to 30°F)
    # Last Frost: Feb 15-28, First Frost: Dec 15-31, Season: 290-319 days
    '9a': (rating, 'Frost-free most years. Note: cool-season crops Oct-Mar, heat-adapted varieties, summer challenges.'),
    '9b': (rating, 'Essentially frost-free. Mention: traditional crops struggle, cool-season only, tropical alternatives.'),

    # ZONE 10: Tropical (30°F to 40°F)
    # Last Frost: Jan 1-31, First Frost: Dec 31, Season: 365 days
    '10a': (rating, 'No frost. Focus on: tropical alternatives, cool-season Dec-Feb, traditional crops struggle.'),
    '10b': (rating, 'Truly tropical. Mention: tropical vegetables/fruits excel, traditional crops fail, continuous pest pressure.'),
},
```

## Example: Real-World Plant (Peppers)

```python
'Bell Peppers': {
    '3a': (2, 'Very challenging. Start indoors 10 weeks early. Short-season varieties only (55-65 days). Use season extenders and black plastic mulch.'),
    '3b': (2, 'Difficult but possible. Early varieties essential. Transplant late May. Protection from cold snaps critical.'),
    '4a': (3, 'Moderate success. Choose short-season types. Start indoors April. Black plastic mulch helps warm soil.'),
    '4b': (4, 'Good with proper variety selection. 65-75 day varieties work well. Start indoors mid-April.'),
    '5a': (4, 'Very good. Wide variety selection. Start indoors 8 weeks before last frost. Most types succeed.'),
    '5b': (5, 'Excellent zone for peppers. Choose disease-resistant varieties due to humidity. Stake tall plants.'),
    '6a': (5, 'Ideal growing conditions. Long season allows large-fruited varieties. Succession planting possible.'),
    '6b': (5, 'Perfect for all pepper types. Hot peppers especially productive. Extended harvest season.'),
    '7a': (5, 'Excellent. Very productive. May need shade cloth in peak summer. Fall crop possible.'),
    '7b': (4, 'Very good but watch heat stress. Afternoon shade beneficial. Spring and fall planting best.'),
    '8a': (4, 'Good with heat management. Plant early spring or fall. Summer too hot for fruit set.'),
    '8b': (3, 'Moderate. Cool-season crop. Oct-May growing. Summer heat prevents fruit development.'),
    '9a': (3, 'Challenging. Oct-April only. Summer far too hot. Choose heat-tolerant varieties.'),
    '9b': (2, 'Very difficult. Nov-March window only. Poor fruit set even in cool season.'),
    '10a': (2, 'Not recommended. Use heat-adapted Asian or tropical pepper varieties instead.'),
    '10b': (1, 'Traditional bell peppers fail. Use Thai peppers, habaneros, or other tropical types.'),
},
```

## Guidelines for Writing Zone Notes

### Cold Zones (3a-4b)
- Emphasize: season length, early varieties, frost protection
- Mention: cold frames, row covers, black plastic mulch
- Specify: days to maturity needed (e.g., "60-day varieties only")

### Moderate Zones (5a-6b)
- Emphasize: variety selection, succession planting
- Mention: pest/disease management, soil amendments
- Specify: optimal planting windows

### Warm Zones (7a-8b)
- Emphasize: heat tolerance, cool-season timing
- Mention: afternoon shade, consistent watering
- Specify: planting seasons (spring/fall vs summer)

### Hot/Tropical Zones (9a-10b)
- Emphasize: alternatives to traditional crops
- Mention: tropical/heat-adapted varieties
- Specify: narrow growing windows for cool-season crops

## Quick Reference: Zone Characteristics

| Zone | Avg Min Temp | Last Frost | First Frost | Days | Key Challenge |
|------|--------------|------------|-------------|------|---------------|
| 3a   | -40°F        | May 30     | Sept 15     | 107  | Very short season |
| 3b   | -35°F        | May 25     | Sept 20     | 118  | Short season |
| 4a   | -30°F        | May 15     | Oct 1       | 139  | Cold winters |
| 4b   | -25°F        | May 10     | Oct 5       | 148  | Late spring frosts |
| 5a   | -20°F        | May 10     | Oct 10      | 153  | Cold snaps |
| 5b   | -15°F        | May 15     | Oct 15      | 153  | Humidity/clay soil |
| 6a   | -10°F        | May 1      | Oct 30      | 182  | Variable springs |
| 6b   | -5°F         | April 25   | Nov 5       | 194  | Mild overall |
| 7a   | 0°F          | April 15   | Nov 10      | 209  | Hot summers |
| 7b   | 5°F          | April 10   | Nov 15      | 219  | Long hot season |
| 8a   | 10°F         | March 25   | Nov 25      | 245  | Extreme heat |
| 8b   | 15°F         | March 15   | Dec 1       | 261  | Very hot summers |
| 9a   | 20°F         | Feb 28     | Dec 15      | 290  | Too hot for many |
| 9b   | 25°F         | Feb 15     | Dec 31      | 319  | Essentially tropical |
| 10a  | 30°F         | Jan 31     | Dec 31      | 365  | Frost-free |
| 10b  | 35°F         | Jan 1      | Dec 31      | 365  | Truly tropical |

## Common Patterns by Plant Type

### Cool-Season Vegetables (Lettuce, Kale, Broccoli)
- Zones 3-6: ⭐⭐⭐⭐⭐ Excellent
- Zones 7-8: ⭐⭐⭐ Moderate (cool-season only)
- Zones 9-10: ⭐⭐ or ⭐ Challenging (winter only)

### Warm-Season Vegetables (Tomatoes, Peppers, Squash)
- Zones 3-4: ⭐⭐ Challenging (short season)
- Zones 5-7: ⭐⭐⭐⭐⭐ Excellent
- Zones 8-10: ⭐⭐⭐ Moderate (too hot in summer)

### Cold-Hardy Perennials (Garlic, Chives, Thyme)
- Zones 3-6: ⭐⭐⭐⭐⭐ Excellent
- Zones 7-8: ⭐⭐⭐⭐ Good
- Zones 9-10: ⭐⭐ or ⭐ Challenging (too warm)

### Tender Perennials (Basil, Heat-Loving Herbs)
- Zones 3-4: ⭐⭐ Challenging (annuals only)
- Zones 5-8: ⭐⭐⭐⭐⭐ Excellent (annuals)
- Zones 9-10: ⭐⭐⭐⭐ Good (may be perennial)

## Resources

- USDA Plant Hardiness Zone Map: https://planthardiness.ars.usda.gov/
- Cooperative Extension Services by state
- Seed company zone recommendations
- Local gardening groups and forums
