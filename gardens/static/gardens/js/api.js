/**
 * Garden API Client
 * Handles all AJAX communication with the backend for garden operations
 */

class GardenAPI {
    /**
     * @param {number} gardenId - The ID of the garden
     */
    constructor(gardenId) {
        this.gardenId = gardenId;
        this.baseUrl = `/gardens/${gardenId}`;
    }

    /**
     * Save the garden layout grid
     * @param {Array} grid - 2D array representing the garden grid
     * @param {Object} plantedDates - Optional object mapping "row,col" to planted_date strings
     * @returns {Promise<Object>} Response data
     */
    async saveLayout(grid, plantedDates = null) {
        const payload = { grid };
        if (plantedDates) {
            payload.planted_dates = plantedDates;
        }
        return gardenFetch(`${this.baseUrl}/save-layout/`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    }

    /**
     * Update the garden name
     * @param {string} name - New garden name
     * @returns {Promise<Object>} Response data
     */
    async updateName(name) {
        return gardenFetch(`${this.baseUrl}/update-name/`, {
            method: 'POST',
            body: JSON.stringify({ name })
        });
    }

    /**
     * Clear all plants from the garden
     * @returns {Promise<Object>} Response data
     */
    async clearGarden() {
        return gardenFetch(`${this.baseUrl}/clear/`, {
            method: 'POST'
        });
    }

    /**
     * Duplicate the garden
     * @returns {Promise<Object>} Response data with new garden ID
     */
    async duplicateGarden() {
        return gardenFetch(`${this.baseUrl}/duplicate/`, {
            method: 'POST'
        });
    }

    /**
     * Get AI planting suggestions
     * @returns {Promise<Object>} Response data with suggestions
     */
    async getAISuggestions() {
        return gardenFetch(`${this.baseUrl}/ai-suggest/`, {
            method: 'POST'
        });
    }
}
