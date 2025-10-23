# Refactoring Plan for Chicago Garden Planner

## ✅ Progress Update

**Date Started:** 2025-10-23
**Current Status:** Quick Wins Phase Complete

### Completed Work

**Quick Wins (Phase 0) - COMPLETED** ✅
- ✅ Created `gardens/static/gardens/js/utils.js` with reusable utilities
- ✅ Created `gardens/static/gardens/css/garden-detail.css`
- ✅ Extracted all CSS from template (60 lines)
- ✅ Removed duplicate `getCSRFToken()` function from template
- ✅ Updated template to load external JS and CSS files
- ✅ Updated CLAUDE.md with architecture guidelines
- ✅ **Template reduced: 1,396 → 1,334 lines (62 lines saved)**

**Utilities Now Available:**
- `getCSRFToken()` - Centralized CSRF token retrieval
- `gardenFetch(url, options)` - Django-ready fetch wrapper
- `ButtonStateManager` class - Button state management
- `showModal(id)` / `hideModal(id)` - Modal helpers

**Impact:**
- Template maintainability improved
- Foundation for future refactoring established
- Clear guidelines documented for all developers
- Browser caching enabled for CSS
- External JavaScript testable

---

## Priority: High-Impact, Low-Risk Refactorings

### 1. Extract JavaScript to Separate Files (HIGHEST PRIORITY)

**Current Problem:**
- `garden_detail.html`: 1,396 lines (800+ lines of JavaScript embedded)
- Impossible to reuse code across pages
- No syntax highlighting or linting for JS
- Difficult to debug

**Solution:**
Create `gardens/static/gardens/js/` with:

```
gardens/static/gardens/js/
├── api.js              # Reusable fetch utilities
├── modals.js           # Modal management utilities
├── garden-grid.js      # Drag-drop and grid interactions
├── garden-detail.js    # Page-specific logic
└── utils.js            # General utilities (CSRF, etc.)
```

**Benefits:**
- DRY: Reusable API client across all pages
- Testable: Can unit test JS functions
- Maintainable: Find code easily by feature
- Performance: Can minify/bundle for production

---

### 2. Create Reusable API Utilities

**Create `api.js`:**
```javascript
// Reusable API client
class GardenAPI {
    constructor(gardenId) {
        this.gardenId = gardenId;
        this.baseUrl = `/gardens/${gardenId}`;
    }

    async fetch(endpoint, options = {}) {
        const defaultOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            }
        };

        const response = await fetch(
            `${this.baseUrl}${endpoint}`,
            {...defaultOptions, ...options}
        );
        return response.json();
    }

    async saveLayout(grid) {
        return this.fetch('/save-layout/', {
            body: JSON.stringify({ grid })
        });
    }

    async clearGarden() {
        return this.fetch('/clear/');
    }

    async duplicateGarden() {
        return this.fetch('/duplicate/');
    }

    async getAISuggestions() {
        return this.fetch('/ai-suggest/');
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}
```

**Usage:**
```javascript
const api = new GardenAPI(gardenId);

// Instead of 20 lines of fetch code:
api.clearGarden()
    .then(data => console.log(data))
    .catch(err => console.error(err));
```

---

### 3. Create Button State Manager

**Create `utils.js`:**
```javascript
class ButtonStateManager {
    constructor(button) {
        this.button = button;
        this.originalHTML = button.innerHTML;
    }

    setLoading(message = 'Loading...') {
        this.button.disabled = true;
        this.button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>${message}
        `;
    }

    setError(message) {
        this.button.classList.add('btn-danger');
        this.button.innerHTML = `<i class="bi bi-exclamation-circle"></i> ${message}`;
        setTimeout(() => this.reset(), 3000);
    }

    setSuccess(message) {
        this.button.classList.add('btn-success');
        this.button.innerHTML = `<i class="bi bi-check-circle"></i> ${message}`;
        setTimeout(() => this.reset(), 2000);
    }

    reset() {
        this.button.disabled = false;
        this.button.className = this.button.dataset.originalClass || this.button.className;
        this.button.innerHTML = this.originalHTML;
    }
}

// Usage:
const btnManager = new ButtonStateManager(clearButton);
btnManager.setLoading('Clearing...');
// ... after operation ...
btnManager.setSuccess('Cleared!');
```

---

### 4. Extract Template Partials

**Current:**
- Modals, cards, and repeated UI all in one file

**Solution:**
Create `gardens/templates/gardens/partials/`:

```
partials/
├── _ai_assistant_modal.html
├── _clear_confirm_modal.html
├── _delete_confirm_modal.html
├── _export_modal.html
├── _import_modal.html
├── _garden_grid.html
└── _plant_library.html
```

**Usage in `garden_detail.html`:**
```django
{% include 'gardens/partials/_ai_assistant_modal.html' %}
{% include 'gardens/partials/_clear_confirm_modal.html' %}
{% include 'gardens/partials/_garden_grid.html' with grid=grid_data %}
```

**Benefits:**
- Each modal is self-contained
- Easier to find and edit
- Can reuse across pages
- Reduced main template to ~300 lines

---

### 5. Django View Mixins

**Current Problem:**
```python
# Repeated in multiple views:
return JsonResponse({
    'success': False,
    'error': str(e)
}, status=500)
```

**Solution:**
```python
# gardens/mixins.py
from django.http import JsonResponse

class JSONResponseMixin:
    def json_success(self, data=None, message=None):
        response = {'success': True}
        if message:
            response['message'] = message
        if data:
            response.update(data)
        return JsonResponse(response)

    def json_error(self, error, status=400):
        return JsonResponse({
            'success': False,
            'error': str(error)
        }, status=status)

class OwnerRequiredMixin:
    def get_garden(self, pk):
        return get_object_or_404(Garden, pk=pk, owner=self.request.user)

# Usage in views:
class GardenClearView(JSONResponseMixin, OwnerRequiredMixin, View):
    def post(self, request, pk):
        try:
            garden = self.get_garden(pk)
            garden.layout_data = {'grid': [[''] * garden.width for _ in range(garden.height)]}
            garden.save()
            return self.json_success(message='Garden cleared')
        except Exception as e:
            return self.json_error(e, status=500)
```

---

### 6. CSS Organization

**Current:**
- 200+ lines of CSS embedded in `<style>` tags

**Solution:**
Create `gardens/static/gardens/css/garden-detail.css`

**Benefits:**
- Syntax highlighting
- Can minify for production
- Reusable across pages
- Cacheable by browser

---

## Implementation Order (Recommended)

### ✅ Phase 0: Quick Wins - COMPLETED
**Impact:** Medium | **Risk:** Very Low | **Effort:** Low (1.5 hours)

**Completed:**
1. ✅ Created `static/gardens/js/utils.js` with utilities
2. ✅ Created `static/gardens/css/garden-detail.css`
3. ✅ Removed duplicate `getCSRFToken()` function
4. ✅ Updated template to load external files
5. ✅ Updated CLAUDE.md with guidelines

**Actual Results:**
- Template: 1,396 → 1,334 lines (62 lines saved)
- Utilities ready for reuse across entire app
- Foundation established for Phase 1

---

### Phase 1: JavaScript Extraction (Next - Week 1)
**Impact:** High | **Risk:** Low | **Effort:** Medium

**Remaining Work:**
1. Create `static/gardens/js/api.js` with GardenAPI class
2. Extract all inline JavaScript to `static/gardens/js/garden-detail.js`
3. Update template to use external JS files
4. Refactor to use `gardenFetch()` and `ButtonStateManager` utilities

**Estimated Reduction:** 1,334 lines → ~600 lines (700+ lines saved)

**Dependencies:** ✅ Phase 0 complete (utils.js exists)

---

### Phase 2: Template Partials (Week 2)
**Impact:** Medium | **Risk:** Low | **Effort:** Low

**To Do:**
1. Extract modals to `partials/_modals/` folder:
   - `_ai_assistant.html`
   - `_clear_confirm.html`
   - `_delete_confirm.html`
   - `_export.html`
   - `_import.html`
2. Extract `_garden_grid.html` to partial
3. Extract `_plant_library.html` to partial
4. Update main template with `{% include %}` tags

**Estimated Reduction:** ~600 lines → 300 lines

---

### Phase 3: Django Refactoring (Week 3)
**Impact:** Medium | **Risk:** Medium | **Effort:** Medium

**To Do:**
1. Create `gardens/mixins.py` with JSONResponseMixin
2. Optionally convert function views to class-based views
3. Add view tests

**Estimated Impact:** Code reuse, not line reduction

---

## Metrics

### Original State (Before Refactoring):
- **garden_detail.html:** 1,396 lines
- **Embedded JavaScript:** ~800 lines
- **Embedded CSS:** ~60 lines
- **Actual HTML:** ~536 lines
- **Reusability:** Low
- **Testability:** None (JS not testable)

### Current State (After Phase 0):
- **garden_detail.html:** 1,334 lines ✅
- **External JavaScript:** utils.js (140 lines)
- **External CSS:** garden-detail.css (70 lines)
- **Embedded JavaScript:** ~760 lines (still need to extract)
- **Actual HTML:** ~364 lines
- **Reusability:** Medium (utilities available)
- **Testability:** Partial (utils.js testable)

### Target State (After All Phases):
- **garden_detail.html:** ~300 lines (includes only)
- **JavaScript files:** 4 files, ~900 lines total (testable!)
- **CSS files:** 1 file, ~70 lines (cacheable!)
- **Template partials:** 7 files, ~600 lines total (reusable!)
- **Reusability:** High
- **Testability:** High

### Progress: **Phase 0 Complete** (4.6% line reduction, foundation established)

---

## Long-term Benefits

1. **Onboarding:** New developers can understand the code structure quickly
2. **Testing:** Can write unit tests for JavaScript functions
3. **Performance:** Can minify/bundle assets for production
4. **Debugging:** Browser DevTools work better with separate JS files
5. **Reusability:** API client can be used in other pages (plant library, garden list)
6. **Maintenance:** Bug fixes in one place instead of copy-paste
7. **Scalability:** Easy to add new features without bloating one file

---

## Next Steps

### Recommended: Phase 1 (JavaScript Extraction)

**Why Phase 1 Next:**
✅ **Highest Impact:** Will reduce template by 700+ lines
✅ **Low Risk:** Doesn't change functionality
✅ **Enables Testing:** Can write unit tests for JS
✅ **Foundation Ready:** utils.js utilities already available

**What Phase 1 Includes:**
1. Create `GardenAPI` class in `api.js` for all fetch operations
2. Extract all inline JavaScript from template to `garden-detail.js`
3. Refactor to use existing utilities (`gardenFetch`, `ButtonStateManager`, etc.)
4. Test thoroughly to ensure no regressions

**Estimated Time:** 3-5 hours
**Estimated Impact:** 1,334 lines → ~600 lines

---

## How to Continue This Refactoring

When ready to proceed with Phase 1:

1. Review the utilities already available in `utils.js`
2. Create `api.js` with GardenAPI class (see example in section above)
3. Create `garden-detail.js` and move all inline `<script>` code there
4. Update template to load both JS files
5. Test all interactive features (drag-drop, modals, AI assistant, etc.)

See CLAUDE.md for the coding standards and guidelines to follow.
