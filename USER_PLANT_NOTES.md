# User Plant Notes Feature

## Overview

The `growing_notes` field has been removed from the Plant model as it contained Chicago-specific information that doesn't make sense for global distribution across all USDA hardiness zones. Instead, a new `UserPlantNote` model has been created to allow users to document their own growing experiences.

## Architecture Changes

### Removed: Plant.growing_notes
- **Why**: This field contained location-specific information that only applied to Chicago (zones 5b/6a)
- **Problem**: With multi-zone support (zones 3a-10b), generic notes don't make sense
- **Solution**: Zone-specific data is now in `PlantZoneData`, user experiences in `UserPlantNote`

### Added: UserPlantNote Model

A new model for user-specific growing experiences:

```python
class UserPlantNote(models.Model):
    user = ForeignKey(User)                      # Who wrote this note
    plant = ForeignKey(Plant)                    # Which plant it's about
    title = CharField(max_length=200, blank=True)
    note_text = TextField()                      # User's experience/tips
    growing_season = IntegerField(null=True)     # Year (e.g., 2024)
    success_rating = IntegerField(1-5, null=True)
    would_grow_again = BooleanField(null=True)

    # Unique constraint: (user, plant, growing_season)
```

**Features:**
- Users can track multiple seasons for the same plant
- Success ratings help users remember what worked
- Personal notes capture zone-specific experiences
- Related to both User and Plant via ForeignKeys

## Data Structure

### Before (Chicago-centric):
```
Plant
├── name: "Tomatoes"
├── chicago_notes: "Plant after May 15. Stake tall varieties..."  # Only valid for 5b!
└── companion_plants: [Basil, Marigold]
```

### After (Multi-zone + User notes):
```
Plant
├── name: "Tomatoes"
└── zone_data (PlantZoneData)
    ├── Zone 3a: ⭐⭐ "Very challenging. Early-maturing varieties only..."
    ├── Zone 5b: ⭐⭐⭐⭐⭐ "Excellent. Disease-resistant varieties recommended..."
    └── Zone 9a: ⭐⭐ "Oct-May only. Summer far too hot..."

UserPlantNote
├── user: john_gardener
├── plant: Tomatoes
├── growing_season: 2024
├── success_rating: 5 (Excellent)
├── would_grow_again: True
└── note_text: "Grew 'Early Girl' variety. Staked with 6ft stakes. Got 30lbs from 4 plants!"
```

## User Interface

### Where Users Can Add Notes

Users will be able to add growing notes from:
1. **Plant detail pages** - "Share Your Experience" button
2. **Garden detail pages** - Notes for plants in their garden
3. **User dashboard** - Review past growing seasons

### Admin Interface

Admins can view/manage user notes at `/admin/gardens/userplantnote/`:
- List view shows: user, plant, season, rating (with stars ⭐), would_grow_again
- Filter by: success_rating, would_grow_again, growing_season, created_at
- Search by: title, note_text, user, plant

## Forms

### UserPlantNoteForm
Available for use in views:

```python
from gardens.forms import UserPlantNoteForm

# In your view:
form = UserPlantNoteForm(request.POST)
if form.is_valid():
    note = form.save(commit=False)
    note.user = request.user
    note.plant = plant
    note.save()
```

**Fields:**
- `title` - Optional title (e.g., "Great harvest in 2024")
- `note_text` - Main experience/tips (required)
- `growing_season` - Year (e.g., 2024)
- `success_rating` - 1-5 stars
- `would_grow_again` - Yes/No

## Database Migrations

Two migrations were created:

1. **0016_add_user_plant_note.py**
   - Creates the UserPlantNote model
   - Adds indexes on (user, plant) and (plant)
   - Sets unique_together constraint on (user, plant, growing_season)

2. **0017_remove_growing_notes.py**
   - Removes the growing_notes field from Plant model

## Files Changed

### Models
- `gardens/models.py` - Removed growing_notes, added UserPlantNote

### Forms
- `gardens/forms.py` - Removed growing_notes from PlantForm, added UserPlantNoteForm

### Admin
- `gardens/admin.py` - Removed growing_notes from PlantAdmin, added UserPlantNoteAdmin

### Views
- `gardens/views.py` - Removed growing_notes from:
  - garden_detail (line 206) - AI assistant plant data
  - plant_library (line 411) - Search filter
  - AI assistant export (line 852) - Garden export data

### Templates
- `plant_detail.html` - Removed generic growing_notes display
- `plant_form.html` - Removed growing_notes card section
- `plant_library.html` - Removed growing_notes truncated preview
- `admin/gardens/plant/import_csv.html` - Removed growing_notes from CSV field list

## Future Development

### Recommended Views to Implement

1. **Add User Note View** (`/plants/<pk>/add-note/`)
   ```python
   @login_required
   def add_plant_note(request, pk):
       plant = get_object_or_404(Plant, pk=pk)
       if request.method == 'POST':
           form = UserPlantNoteForm(request.POST)
           if form.is_valid():
               note = form.save(commit=False)
               note.user = request.user
               note.plant = plant
               note.save()
               return redirect('gardens:plant_detail', pk=pk)
       else:
           form = UserPlantNoteForm()
       return render(request, 'gardens/add_plant_note.html', {'form': form, 'plant': plant})
   ```

2. **Display User Notes on Plant Detail Page**
   - Show the logged-in user's notes for this plant
   - Show community notes (other users' experiences)
   - Filter by growing season, success rating

3. **My Growing Journal** (`/my-notes/`)
   - List all user's plant notes
   - Filter by season, plant type, success rating
   - Export to PDF/CSV

### Template Snippet for Plant Detail

Add this to `plant_detail.html` to show user notes:

```django
<!-- User Growing Experiences -->
{% if request.user.is_authenticated %}
<div class="card mt-4">
    <div class="card-header bg-success text-white">
        <h5 class="mb-0"><i class="bi bi-journal-text"></i> Growing Experiences</h5>
    </div>
    <div class="card-body">
        {% with user_notes=plant.user_notes.filter(user=request.user) %}
            {% if user_notes %}
                {% for note in user_notes %}
                <div class="mb-3">
                    <h6>{{ note.title|default:"My Experience" }}
                        {% if note.growing_season %}({{ note.growing_season }}){% endif %}
                    </h6>
                    {% if note.success_rating %}
                    <div class="mb-2">
                        {% for i in "12345" %}
                            {% if forloop.counter <= note.success_rating %}⭐{% else %}☆{% endif %}
                        {% endfor %}
                    </div>
                    {% endif %}
                    <p>{{ note.note_text }}</p>
                    {% if note.would_grow_again is not None %}
                    <small class="text-muted">
                        Would grow again:
                        {% if note.would_grow_again %}
                            <span class="text-success">✓ Yes</span>
                        {% else %}
                            <span class="text-danger">✗ No</span>
                        {% endif %}
                    </small>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <p class="text-muted">You haven't shared your experience with this plant yet.</p>
            {% endif %}
        {% endwith %}
        <a href="{% url 'gardens:add_plant_note' plant.pk %}" class="btn btn-success">
            <i class="bi bi-plus-circle"></i> Share Your Experience
        </a>
    </div>
</div>
{% endif %}
```

## Benefits

1. **Global Relevance**: No more Chicago-specific notes on plant records
2. **User Empowerment**: Users share their own experiences in their zone
3. **Community Knowledge**: Build a database of real user experiences
4. **Personalization**: Users track what works in their specific conditions
5. **Historical Tracking**: Users can review past seasons and learn
6. **Zone Accuracy**: PlantZoneData provides zone-specific guidance, UserPlantNote provides real-world confirmation

## Data Migration Notes

- Existing plants no longer have growing_notes
- Zone-specific data is in PlantZoneData (already populated)
- No data loss - Chicago notes were not migrated (they're replaced by zone-specific data)
- All plants have complete zone data (3a-10b) from Phase 5 of multi-zone expansion

---

**Date**: 2025-11-18
**Author**: Claude Code
**Related**: Multi-Zone Expansion, DRY Improvements
