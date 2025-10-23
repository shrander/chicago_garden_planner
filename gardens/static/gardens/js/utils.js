/**
 * Utility functions for Chicago Garden Planner
 * Provides reusable helpers for common operations
 */

/**
 * Get CSRF token from the page for AJAX requests
 * @returns {string} CSRF token value
 */
function getCSRFToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

/**
 * Wrapper for fetch API with default headers for Django
 * Automatically includes CSRF token and JSON headers
 *
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options (method, body, etc.)
 * @returns {Promise} Promise that resolves to JSON response
 */
async function gardenFetch(url, options = {}) {
    const defaultOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    };

    const response = await fetch(url, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...(options.headers || {})
        }
    });

    if (!response.ok) {
        const error = await response.json();
        throw error;
    }

    return response.json();
}

/**
 * Manages button state during async operations
 * Handles loading, success, and error states
 */
class ButtonStateManager {
    /**
     * @param {HTMLElement} button - The button element to manage
     */
    constructor(button) {
        this.button = button;
        this.originalHTML = button.innerHTML;
        this.originalClasses = button.className;
    }

    /**
     * Set button to loading state with spinner
     * @param {string} message - Loading message to display
     */
    setLoading(message = 'Loading...') {
        this.button.disabled = true;
        this.button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>${message}
        `;
    }

    /**
     * Set button to error state
     * @param {string} message - Error message to display
     * @param {number} autoResetMs - Auto-reset after this many ms (0 = no auto-reset)
     */
    setError(message, autoResetMs = 3000) {
        this.button.disabled = false;
        this.button.className = this.originalClasses.replace(/btn-\w+/, 'btn-danger');
        this.button.innerHTML = `<i class="bi bi-exclamation-circle"></i> ${message}`;

        if (autoResetMs > 0) {
            setTimeout(() => this.reset(), autoResetMs);
        }
    }

    /**
     * Set button to success state
     * @param {string} message - Success message to display
     * @param {number} autoResetMs - Auto-reset after this many ms (0 = no auto-reset)
     */
    setSuccess(message, autoResetMs = 2000) {
        this.button.disabled = false;
        this.button.className = this.originalClasses.replace(/btn-\w+/, 'btn-success');
        this.button.innerHTML = `<i class="bi bi-check-circle"></i> ${message}`;

        if (autoResetMs > 0) {
            setTimeout(() => this.reset(), autoResetMs);
        }
    }

    /**
     * Reset button to original state
     */
    reset() {
        this.button.disabled = false;
        this.button.className = this.originalClasses;
        this.button.innerHTML = this.originalHTML;
    }
}

/**
 * Show a Bootstrap modal by ID
 * @param {string} modalId - ID of the modal element
 * @returns {bootstrap.Modal} Modal instance
 */
function showModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) {
        console.error(`Modal with ID '${modalId}' not found`);
        return null;
    }
    const modal = new bootstrap.Modal(modalElement);
    modal.show();
    return modal;
}

/**
 * Hide a Bootstrap modal by ID
 * @param {string} modalId - ID of the modal element
 */
function hideModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (modalElement) {
        const modal = bootstrap.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
    }
}
