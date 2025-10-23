# Refactoring Plan for Chicago Garden Planner

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

### Phase 1: JavaScript Extraction (Week 1)
**Impact:** High | **Risk:** Low | **Effort:** Medium

1. Create `static/gardens/js/api.js` with GardenAPI class
2. Create `static/gardens/js/utils.js` with ButtonStateManager
3. Create `static/gardens/js/garden-detail.js` for page logic
4. Update `garden_detail.html` to use `<script src="...">`

**Estimated Reduction:** 800 lines → 50 lines in template

---

### Phase 2: Template Partials (Week 2)
**Impact:** Medium | **Risk:** Low | **Effort:** Low

1. Extract each modal to `partials/` folder
2. Extract garden grid to partial
3. Extract plant library to partial
4. Update main template with includes

**Estimated Reduction:** 1,396 lines → 300 lines

---

### Phase 3: CSS Extraction (Week 2)
**Impact:** Low | **Risk:** Very Low | **Effort:** Low

1. Move inline styles to `garden-detail.css`
2. Link stylesheet in template

**Estimated Reduction:** 200 lines → 10 lines

---

### Phase 4: Django Refactoring (Week 3)
**Impact:** Medium | **Risk:** Medium | **Effort:** Medium

1. Create mixin classes
2. Convert function views to class-based views
3. Add view tests

**Estimated Reduction:** Code reuse, not line reduction

---

## Metrics

### Current State:
- **garden_detail.html:** 1,396 lines
- **Embedded JavaScript:** ~800 lines
- **Embedded CSS:** ~200 lines
- **Actual HTML:** ~400 lines
- **Reusability:** Low
- **Testability:** None (JS not testable)

### After Refactoring:
- **garden_detail.html:** ~300 lines (includes only)
- **JavaScript files:** 4 files, ~600 lines total (testable!)
- **CSS files:** 1 file, ~200 lines (minifiable!)
- **Template partials:** 7 files, ~600 lines total (reusable!)
- **Reusability:** High
- **Testability:** High

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

## Quick Wins (Can Do Now)

### 1. Extract getCSRFToken() (5 minutes)
```javascript
// Used 10+ times in template
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}
```

### 2. Extract Modal Utilities (10 minutes)
```javascript
function showModal(modalId) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
    return modal;
}

// Usage:
showModal('clearConfirmModal');
```

### 3. Extract Fetch Wrapper (15 minutes)
```javascript
async function gardenFetch(endpoint, options = {}) {
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        ...options
    });
    return response.json();
}
```

---

## Decision: What Should We Do Now?

I recommend we start with **Phase 1 (JavaScript Extraction)** because:

✅ **Highest Impact:** Reduces template by 800 lines
✅ **Lowest Risk:** Doesn't change functionality
✅ **Enables Testing:** Can write unit tests
✅ **Foundation:** Makes future refactoring easier

Would you like me to:
1. **Implement Phase 1 now** (extract JavaScript to separate files)?
2. **Do quick wins first** (extract small utilities)?
3. **Continue as-is** and refactor later?

Let me know your preference!
