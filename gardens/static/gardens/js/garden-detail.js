/**
 * Garden Detail Page - Main JavaScript
 * Handles drag-and-drop, auto-save, modals, and all interactive features
 */

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Garden detail JavaScript loaded');

    // Get garden ID from template
    const gardenId = window.GARDEN_ID;  // Will be set by template
    const plantMap = window.PLANT_MAP;  // Will be set by template

    // Initialize API client
    const gardenAPI = new GardenAPI(gardenId);

    // State variables
    let draggedPlant = null;
    let draggedCell = null;
    let hasUnsavedChanges = false;

    // ========================================
    // DRAG AND DROP FUNCTIONALITY
    // ========================================

    /**
     * Extract plant data from a garden cell
     * @param {HTMLElement} cell - The garden cell element
     * @returns {Object|null} Plant data or null if empty
     */
    function getPlantDataFromCell(cell) {
        const plantName = cell.dataset.plant;
        const contentSpan = cell.querySelector('.cell-content');

        if (!plantName || plantName === '' || plantName === 'empty space') {
            return null;
        }

        // Try to get color from the span
        let color = contentSpan.style.backgroundColor || '#90EE90';

        return {
            name: plantName,
            symbol: contentSpan.textContent.trim(),
            color: color
        };
    }

    /**
     * Update cell content visually
     * @param {HTMLElement} cell - The garden cell
     * @param {Object} plant - Plant data with name, symbol, color
     */
    function updateCellContent(cell, plant) {
        const contentSpan = cell.querySelector('.cell-content');

        if (plant.name === 'empty space') {
            contentSpan.className = 'cell-content badge bg-light text-muted w-100 h-100 d-flex align-items-center justify-content-center';
            contentSpan.style.fontSize = '1.5rem';
            contentSpan.style.borderRadius = '4px';
            contentSpan.textContent = '•';
            contentSpan.title = 'Empty Space';
        } else if (plant.name === 'path') {
            contentSpan.className = 'cell-content badge bg-secondary w-100 h-100 d-flex align-items-center justify-content-center';
            contentSpan.style.fontSize = '1.5rem';
            contentSpan.style.borderRadius = '4px';
            contentSpan.textContent = '=';
            contentSpan.title = 'Path';
        } else {
            // Use symbol from plant data, fallback to first letter
            const plantSymbol = plant.symbol || plant.name.substring(0, 1).toUpperCase();

            contentSpan.className = 'cell-content badge w-100 h-100 d-flex align-items-center justify-content-center';
            contentSpan.style.backgroundColor = plant.color || '#90EE90';
            contentSpan.style.color = 'white';
            contentSpan.style.fontSize = '1.8rem';
            contentSpan.style.fontWeight = 'bold';
            contentSpan.style.borderRadius = '4px';
            contentSpan.textContent = plantSymbol;
            contentSpan.title = plant.name;
        }
    }

    /**
     * Setup drag handlers for a garden cell
     * @param {HTMLElement} cell - The garden cell element
     */
    function setupGardenCellDrag(cell) {
        // Make cells draggable if they have plants
        cell.setAttribute('draggable', 'true');

        cell.addEventListener('dragstart', function(e) {
            const plantData = getPlantDataFromCell(this);
            if (plantData) {
                draggedPlant = plantData;
                draggedCell = this;
                this.style.opacity = '0.4';
                e.dataTransfer.effectAllowed = 'move';
            } else {
                e.preventDefault();
            }
        });

        cell.addEventListener('dragend', function(e) {
            this.style.opacity = '1';

            // Check if the drop happened outside the garden grid (drag-off removal)
            if (draggedCell) {
                const gardenGrid = document.getElementById('gardenGrid');
                const rect = gardenGrid.getBoundingClientRect();
                const x = e.clientX;
                const y = e.clientY;

                // If coordinates are outside the grid bounds
                const isOutsideGrid = x < rect.left || x > rect.right || y < rect.top || y > rect.bottom;

                if (isOutsideGrid && draggedCell === this) {
                    // Make the cell empty - plant was dragged off the grid
                    updateCellContent(this, {
                        name: 'empty space',
                        symbol: '•',
                        color: '#8FBC8F'
                    });
                    this.dataset.plant = 'empty space';

                    // Auto-save the layout
                    autoSaveLayout();
                }
            }

            draggedCell = null;
        });

        cell.addEventListener('dragover', function(e) {
            e.preventDefault();
            if (draggedCell) {
                e.dataTransfer.dropEffect = 'move';
            } else {
                e.dataTransfer.dropEffect = 'copy';
            }
            this.classList.add('drag-over');
        });

        cell.addEventListener('dragleave', function(e) {
            this.classList.remove('drag-over');
        });

        cell.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');

            if (draggedPlant) {
                // If dragging from another cell, swap or move
                if (draggedCell && draggedCell !== this) {
                    const targetPlantData = getPlantDataFromCell(this);

                    // Update target cell with dragged plant
                    updateCellContent(this, draggedPlant);
                    this.dataset.plant = draggedPlant.name;

                    // Update source cell with target's plant (swap) or make it empty
                    if (targetPlantData) {
                        updateCellContent(draggedCell, targetPlantData);
                        draggedCell.dataset.plant = targetPlantData.name;
                    } else {
                        // Make source cell empty
                        updateCellContent(draggedCell, {
                            name: 'empty space',
                            symbol: '•',
                            color: '#8FBC8F'
                        });
                        draggedCell.dataset.plant = 'empty space';
                    }
                } else if (!draggedCell) {
                    // Dragging from plant library
                    updateCellContent(this, draggedPlant);
                    this.dataset.plant = draggedPlant.name;
                }

                // Auto-save the layout
                autoSaveLayout();
            }
        });
    }

    // Setup drag handlers for plant library items
    const plantItems = document.querySelectorAll('.plant-item.draggable');
    plantItems.forEach(item => {
        item.addEventListener('dragstart', function(e) {
            draggedPlant = {
                name: this.dataset.plantName,
                symbol: this.dataset.plantSymbol,
                color: this.dataset.plantColor
            };
            draggedCell = null;
            this.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'copy';
        });

        item.addEventListener('dragend', function(e) {
            this.classList.remove('dragging');
        });
    });

    // Setup all garden cells
    const gardenCells = document.querySelectorAll('.garden-cell.droppable');
    gardenCells.forEach(cell => {
        setupGardenCellDrag(cell);
    });

    // ========================================
    // AUTO-SAVE FUNCTIONALITY
    // ========================================

    /**
     * Auto-save the current garden layout
     */
    function autoSaveLayout() {
        const grid = [];
        const rows = document.querySelectorAll('#gardenGrid tr');

        rows.forEach(row => {
            const rowData = [];
            const cells = row.querySelectorAll('.garden-cell');
            cells.forEach(cell => {
                rowData.push(cell.dataset.plant || 'empty space');
            });
            grid.push(rowData);
        });

        const saveStatus = document.getElementById('saveStatus');

        saveStatus.textContent = 'Saving...';
        saveStatus.className = 'badge bg-info ms-2';

        gardenAPI.saveLayout(grid)
            .then(data => {
                hasUnsavedChanges = false;
                saveStatus.textContent = 'Saved';
                saveStatus.className = 'badge bg-success ms-2';
                setTimeout(() => {
                    saveStatus.textContent = '';
                }, 2000);
            })
            .catch(error => {
                console.error('Error:', error);
                saveStatus.textContent = 'Error: ' + (error.error || 'Failed to save');
                saveStatus.className = 'badge bg-danger ms-2';
            });
    }

    function autoSaveLayoutWithDates(plantedDates) {
        const grid = [];
        const rows = document.querySelectorAll('#gardenGrid tr');

        rows.forEach(row => {
            const rowData = [];
            const cells = row.querySelectorAll('.garden-cell');
            cells.forEach(cell => {
                rowData.push(cell.dataset.plant || 'empty space');
            });
            grid.push(rowData);
        });

        const saveStatus = document.getElementById('saveStatus');

        saveStatus.textContent = 'Saving with dates...';
        saveStatus.className = 'badge bg-info ms-2';

        gardenAPI.saveLayout(grid, plantedDates)
            .then(data => {
                hasUnsavedChanges = false;
                saveStatus.textContent = 'Saved with planting dates!';
                saveStatus.className = 'badge bg-success ms-2';
                setTimeout(() => {
                    saveStatus.textContent = '';
                    // Reload page to show updated dates
                    window.location.reload();
                }, 1500);
            })
            .catch(error => {
                console.error('Error:', error);
                saveStatus.textContent = 'Error: ' + (error.error || 'Failed to save');
                saveStatus.className = 'badge bg-danger ms-2';
            });
    }

    // ========================================
    // AI ASSISTANT
    // ========================================

    let currentSuggestions = [];

    /**
     * Initialize AI Assistant functionality
     * Handles fetching suggestions from Claude API and applying them to garden
     */
    function setupAIAssistant() {
        const aiAssistantBtn = document.getElementById('aiAssistantBtn');
        const aiAssistantModalEl = document.getElementById('aiAssistantModal');

        if (!aiAssistantBtn || !aiAssistantModalEl) return;

        const aiAssistantModal = new bootstrap.Modal(aiAssistantModalEl);

        // AI Assistant button click handler
        aiAssistantBtn.addEventListener('click', async function() {
            // Show modal with loading state
            document.getElementById('aiLoadingState').classList.remove('d-none');
            document.getElementById('aiSuggestionsContent').classList.add('d-none');
            document.getElementById('aiErrorState').classList.add('d-none');
            document.getElementById('applyAllSuggestionsBtn').disabled = true;

            aiAssistantModal.show();

            try {
                // Call AI endpoint
                const response = await fetch(`/gardens/${gardenId}/ai-suggest/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    }
                });

                // Store response status for debugging
                const responseStatus = response.status;
                const responseStatusText = response.statusText;

                if (!response.ok) {
                    const err = await response.json().catch(() => ({
                        error: 'Invalid response from server',
                        _rawError: 'JSON parse failed'
                    }));
                    err._httpStatus = responseStatus;
                    err._httpStatusText = responseStatusText;
                    throw err;
                }

                const data = await response.json();
                handleAISuccess(data);

            } catch (error) {
                handleAIError(error);
            }
        });

        // Apply all suggestions button handler
        const applyAllSuggestionsBtn = document.getElementById('applyAllSuggestionsBtn');
        if (applyAllSuggestionsBtn) {
            applyAllSuggestionsBtn.addEventListener('click', function() {
                applyAISuggestions();
            });
        }
    }

    /**
     * Handle successful AI suggestions response
     * @param {Object} data - Response data from AI endpoint
     */
    function handleAISuccess(data) {
        document.getElementById('aiLoadingState').classList.add('d-none');

        if (data.success && data.suggestions) {
            currentSuggestions = data.suggestions.suggestions || [];
            const reasoning = data.suggestions.reasoning || 'No strategy provided.';

            document.getElementById('aiReasoning').textContent = reasoning;

            const suggestionsList = document.getElementById('aiSuggestionsList');
            suggestionsList.innerHTML = '';

            if (currentSuggestions.length === 0) {
                suggestionsList.innerHTML = '<div class="alert alert-info">No suggestions available. Your garden might already be well-planned!</div>';
            } else {
                currentSuggestions.forEach((suggestion) => {
                    const plantInfo = plantMap[suggestion.plant_name.toLowerCase()];
                    const symbol = plantInfo ? plantInfo.symbol : suggestion.plant_name[0].toUpperCase();
                    const color = plantInfo ? plantInfo.color : '#90EE90';

                    const item = document.createElement('div');
                    item.className = 'list-group-item d-flex align-items-center';
                    item.innerHTML = `
                        <div class="d-flex align-items-center justify-content-center me-3"
                             style="min-width: 40px; min-height: 40px; background-color: ${color}; color: white; font-size: 1.2rem; font-weight: bold; border-radius: 4px;">
                            ${symbol}
                        </div>
                        <div class="flex-grow-1">
                            <strong>${suggestion.plant_name}</strong> at Row ${suggestion.row}, Col ${suggestion.col}
                            <br>
                            <small class="text-muted">${suggestion.reason}</small>
                        </div>
                    `;
                    suggestionsList.appendChild(item);
                });

                document.getElementById('applyAllSuggestionsBtn').disabled = false;
            }

            document.getElementById('aiSuggestionsContent').classList.remove('d-none');
        } else {
            document.getElementById('aiErrorMessage').textContent = data.error || 'Failed to get AI suggestions';
            document.getElementById('aiErrorState').classList.remove('d-none');
        }
    }

    /**
     * Handle AI error response
     * @param {Object} error - Error object from fetch or backend
     */
    function handleAIError(error) {
        console.error('Full error object:', error);
        document.getElementById('aiLoadingState').classList.add('d-none');

        // Populate debug information
        const statusEl = document.getElementById('errorStatus');
        const typeEl = document.getElementById('errorType');
        const detailsEl = document.getElementById('errorDetails');

        statusEl.textContent = error._httpStatus ? `${error._httpStatus} ${error._httpStatusText}` : 'N/A';
        typeEl.textContent = error.error_type || 'Unknown';
        detailsEl.textContent = JSON.stringify(error, null, 2);

        const errorContainer = document.getElementById('aiErrorMessage');

        // Check if this is a structured error response from backend
        if (error.error_type) {
            const message = error.message || error.error;

            // Add a link to profile settings for API key errors
            if (error.error_type === 'no_api_key' || error.error_type === 'invalid_api_key') {
                errorContainer.innerHTML = `
                    ${message}
                    <br><br>
                    <a href="${window.location.origin}/accounts/profile/" class="btn btn-warning btn-sm">
                        <i class="bi bi-gear"></i> Go to Profile Settings
                    </a>
                `;
            } else {
                errorContainer.textContent = message;
            }
        } else if (error._httpStatus) {
            // HTTP error without structured response
            errorContainer.innerHTML = `
                <strong>HTTP ${error._httpStatus}</strong>: ${error._httpStatusText || 'Server error'}
                <br>
                ${error.error || error._rawError || 'The server returned an error response'}
            `;
        } else {
            // Generic network error (fetch failed)
            errorContainer.innerHTML = `
                <strong>Network Error:</strong> ${error.message || 'Could not connect to server'}
                <br><br>
                <small class="text-muted">
                    This usually means:
                    <ul class="mb-0 mt-2">
                        <li>The server is not running</li>
                        <li>There's a network connectivity issue</li>
                        <li>The URL endpoint is incorrect</li>
                    </ul>
                </small>
            `;
        }

        document.getElementById('aiErrorState').classList.remove('d-none');
    }

    /**
     * Apply AI suggestions to the garden grid
     */
    function applyAISuggestions() {
        if (currentSuggestions.length === 0) return;

        // Apply each suggestion to the grid
        currentSuggestions.forEach(suggestion => {
            const plantName = suggestion.plant_name.toLowerCase();
            const row = suggestion.row;
            const col = suggestion.col;

            // Find the cell
            const cell = document.querySelector(`.garden-cell[data-row="${row}"][data-col="${col}"]`);
            if (cell) {
                const plantInfo = plantMap[plantName];
                if (plantInfo) {
                    updateCellContent(cell, {
                        name: plantName,
                        symbol: plantInfo.symbol,
                        color: plantInfo.color
                    });
                    cell.dataset.plant = plantName;
                }
            }
        });

        // Auto-save the layout
        autoSaveLayout();

        // Close modal
        const aiAssistantModalEl = document.getElementById('aiAssistantModal');
        const aiAssistantModal = bootstrap.Modal.getInstance(aiAssistantModalEl);
        aiAssistantModal.hide();

        // Show success message
        const saveStatus = document.getElementById('saveStatus');
        saveStatus.textContent = 'AI suggestions applied!';
        saveStatus.className = 'badge bg-success ms-2';
        setTimeout(() => {
            saveStatus.textContent = '';
        }, 3000);
    }

    // ========================================
    // GARDEN NAME INLINE EDITING
    // ========================================

    /**
     * Initialize garden name inline editing functionality
     * Allows clicking the garden name to edit it in place
     */
    function setupGardenNameEditing() {
        const gardenNameDisplay = document.getElementById('gardenNameDisplay');
        const gardenNameInput = document.getElementById('gardenNameInput');
        const gardenNameSaveStatus = document.getElementById('gardenNameSaveStatus');

        if (!gardenNameDisplay || !gardenNameInput) return;

        // Click to edit
        gardenNameDisplay.addEventListener('click', function() {
            gardenNameDisplay.classList.add('d-none');
            gardenNameInput.classList.remove('d-none');
            gardenNameInput.focus();
            gardenNameInput.select();
        });

        // Save on blur (when user clicks away)
        gardenNameInput.addEventListener('blur', function() {
            saveGardenName();
        });

        // Save on Enter key
        gardenNameInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.blur(); // Trigger the blur event to save
            }
        });

        // Cancel on Escape key
        gardenNameInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                e.preventDefault();
                gardenNameInput.value = gardenNameDisplay.textContent.trim().replace(/\s+/g, ' ');
                gardenNameInput.classList.add('d-none');
                gardenNameDisplay.classList.remove('d-none');
            }
        });

        /**
         * Save the garden name to the server
         */
        function saveGardenName() {
            const newName = gardenNameInput.value.trim();

            // Get the old name without the pencil icon
            const displayText = gardenNameDisplay.childNodes[0].textContent.trim();

            if (newName === '' || newName === displayText) {
                // No change or empty, just revert
                gardenNameInput.classList.add('d-none');
                gardenNameDisplay.classList.remove('d-none');
                return;
            }

            // Show saving status
            gardenNameSaveStatus.textContent = 'Saving...';
            gardenNameSaveStatus.className = 'badge bg-info ms-2';

            fetch(`/gardens/${gardenId}/update-name/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ name: newName })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update display - preserve the structure with the pencil icon
                    const textNode = document.createTextNode(newName + ' ');
                    const icon = document.createElement('i');
                    icon.className = 'bi bi-pencil-square ms-2';
                    icon.style.fontSize = '0.7em';
                    icon.style.color = '#6c757d';

                    gardenNameDisplay.innerHTML = '';
                    gardenNameDisplay.appendChild(textNode);
                    gardenNameDisplay.appendChild(icon);

                    gardenNameInput.classList.add('d-none');
                    gardenNameDisplay.classList.remove('d-none');

                    // Show success
                    gardenNameSaveStatus.textContent = 'Saved';
                    gardenNameSaveStatus.className = 'badge bg-success ms-2';
                    setTimeout(() => {
                        gardenNameSaveStatus.textContent = '';
                    }, 2000);
                } else {
                    gardenNameSaveStatus.textContent = 'Error: ' + (data.error || 'Failed to save');
                    gardenNameSaveStatus.className = 'badge bg-danger ms-2';
                    // Keep the input visible so user can try again
                }
            })
            .catch(error => {
                console.error('Error:', error);
                gardenNameSaveStatus.textContent = 'Network error';
                gardenNameSaveStatus.className = 'badge bg-danger ms-2';
            });
        }
    }

    // ========================================
    // GARDEN DESCRIPTION INLINE EDITING
    // ========================================

    /**
     * Initialize garden description inline editing functionality
     */
    function setupGardenDescriptionEditing() {
        const descriptionDisplay = document.getElementById('gardenDescriptionDisplay');
        const descriptionInput = document.getElementById('gardenDescriptionInput');
        const descriptionSave = document.getElementById('gardenDescriptionSave');
        const descriptionCancel = document.getElementById('gardenDescriptionCancel');
        const descriptionStatus = document.getElementById('gardenDescriptionStatus');

        console.log('setupGardenDescriptionEditing called');
        console.log('descriptionDisplay:', descriptionDisplay);
        console.log('descriptionInput:', descriptionInput);

        if (!descriptionDisplay || !descriptionInput) {
            console.warn('Garden description editing elements not found, skipping setup');
            return;
        }

        let originalValue = descriptionInput.value;

        // Click to edit
        descriptionDisplay.addEventListener('click', function() {
            console.log('Description display clicked!');
            originalValue = descriptionInput.value;
            descriptionDisplay.classList.add('d-none');
            descriptionInput.classList.remove('d-none');
            descriptionSave.classList.remove('d-none');
            descriptionCancel.classList.remove('d-none');
            descriptionInput.focus();
        });

        console.log('Garden description editing setup complete');

        // Save button
        descriptionSave.addEventListener('click', function() {
            saveGardenDescription();
        });

        // Cancel button
        descriptionCancel.addEventListener('click', function() {
            descriptionInput.value = originalValue;
            hideDescriptionEditor();
        });

        // Save on Ctrl+Enter
        descriptionInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                saveGardenDescription();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                descriptionInput.value = originalValue;
                hideDescriptionEditor();
            }
        });

        function hideDescriptionEditor() {
            descriptionInput.classList.add('d-none');
            descriptionSave.classList.add('d-none');
            descriptionCancel.classList.add('d-none');
            descriptionDisplay.classList.remove('d-none');
        }

        function saveGardenDescription() {
            const newDescription = descriptionInput.value.trim();

            // Show saving status
            descriptionStatus.textContent = 'Saving...';
            descriptionStatus.className = 'badge bg-info ms-2';

            fetch(`/gardens/${gardenId}/update-info/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ description: newDescription })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update display
                    const displayText = newDescription || 'No description provided. Click to add one.';
                    const p = descriptionDisplay.querySelector('p');
                    p.textContent = displayText;

                    originalValue = newDescription;
                    hideDescriptionEditor();

                    // Show success
                    descriptionStatus.textContent = 'Saved';
                    descriptionStatus.className = 'badge bg-success ms-2';
                    setTimeout(() => {
                        descriptionStatus.textContent = '';
                    }, 2000);
                } else {
                    descriptionStatus.textContent = 'Error: ' + (data.error || 'Failed to save');
                    descriptionStatus.className = 'badge bg-danger ms-2';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                descriptionStatus.textContent = 'Network error';
                descriptionStatus.className = 'badge bg-danger ms-2';
            });
        }
    }

    // ========================================
    // GARDEN TYPE SELECTOR
    // ========================================

    /**
     * Update yield display based on garden type and spacing data
     * Recalculates plant quantities based on spacing method
     * @param {string} gardenType - 'square_foot' or 'row'
     */
    function updateYieldDisplay(gardenType) {
        const yieldTableBody = document.getElementById('yieldTableBody');
        if (!yieldTableBody) return;

        console.log('Updating yield display for garden type:', gardenType);

        // Count plants in the grid by type
        const grid = document.querySelectorAll('#gardenGrid .garden-cell');
        const plantCounts = {};

        grid.forEach(cell => {
            const plantName = cell.dataset.plant;
            if (!plantName || plantName === 'empty space' || plantName === 'path' || plantName === '') {
                return;
            }

            const plantData = window.PLANT_MAP[plantName];
            if (!plantData) return;

            // Calculate how many actual plants per grid cell based on garden type
            let plantsPerCell = 1; // Default

            if (gardenType === 'square_foot' && plantData.sq_ft_spacing) {
                // Square foot: each cell can hold multiple plants
                plantsPerCell = plantData.sq_ft_spacing;
            } else if (gardenType === 'row' && plantData.row_spacing_inches) {
                // Row: typically 1 plant per cell in the grid
                // (grid cells represent spacing, not multiple plants)
                plantsPerCell = 1;
            }

            plantCounts[plantName] = (plantCounts[plantName] || 0) + plantsPerCell;
        });

        // Update the table rows
        const rows = yieldTableBody.querySelectorAll('tr[data-plant]');

        rows.forEach(row => {
            const plantName = row.dataset.plant;
            const plantData = window.PLANT_MAP[plantName];

            if (!plantData) return;

            const newCount = plantCounts[plantName] || 0;
            const quantityCell = row.querySelector('.yield-quantity strong');
            const totalCell = row.querySelector('.yield-total');

            if (!quantityCell || !totalCell) return;

            // Update quantity
            quantityCell.textContent = newCount;

            // Calculate new total yield
            if (plantData.yield_per_plant) {
                const totalYield = calculateTotalYield(plantData.yield_per_plant, newCount);
                totalCell.innerHTML = `<strong>${totalYield}</strong>`;
            } else {
                totalCell.innerHTML = '<span class="text-muted">No estimate</span>';
            }

            console.log(`${plantData.name}: ${newCount} plants (${gardenType})`);
        });
    }

    /**
     * Calculate total yield from yield_per_plant string and count
     * Mirrors the Django template filter calculate_total_yield
     * @param {string} yieldPerPlant - e.g. "10-15 lbs per plant"
     * @param {number} count - number of plants
     * @returns {string} Total yield estimate (compact format)
     */
    function calculateTotalYield(yieldPerPlant, count) {
        // Handle "Continuous harvest" or non-numeric yields
        if (!yieldPerPlant || yieldPerPlant.toLowerCase().includes('continuous')) {
            return 'Continuous';
        }

        if (!count || count === 0) {
            return 'No estimate';
        }

        // Match range pattern (e.g., "4-6 oz per head")
        const rangeMatch = yieldPerPlant.match(/^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s+(.+)$/);
        if (rangeMatch) {
            const low = parseFloat(rangeMatch[1]);
            const high = parseFloat(rangeMatch[2]);
            const totalLow = Math.round(low * count);
            const totalHigh = Math.round(high * count);

            // Extract unit and remove specific "per plant/head/etc" but keep "per season/week"
            let unit = rangeMatch[3];
            const patternsToRemove = [
                /\s*per\s+plant\s*/gi,
                /\s*per\s+head\s*/gi,
                /\s*per\s+radish\s*/gi,
                /\s*per\s+carrot\s*/gi,
                /\s*per\s+vine\s*/gi,
                /\s*per\s+bush\s*/gi,
                /\s*per\s+bulb\s*/gi,
            ];
            patternsToRemove.forEach(pattern => {
                unit = unit.replace(pattern, ' ');
            });
            unit = unit.trim();

            // Compact unit names
            const unitMap = {
                'lbs': 'lb',
                'pounds': 'lb',
                'ounces': 'oz'
            };
            unit = unitMap[unit.toLowerCase()] || unit;

            return `${totalLow}-${totalHigh} ${unit}`;
        }

        // Match single number pattern (e.g., "1 bulb (8-10 cloves)")
        const singleMatch = yieldPerPlant.match(/^(\d+(?:\.\d+)?)\s+(.+)$/);
        if (singleMatch) {
            const value = parseFloat(singleMatch[1]);
            const total = Math.round(value * count);
            let rest = singleMatch[2];

            // Remove specific "per plant/head/etc" but keep "per season/week"
            const patternsToRemove = [
                /\s*per\s+plant\s*/gi,
                /\s*per\s+head\s*/gi,
                /\s*per\s+radish\s*/gi,
                /\s*per\s+carrot\s*/gi,
                /\s*per\s+vine\s*/gi,
                /\s*per\s+bush\s*/gi,
                /\s*per\s+bulb\s*/gi,
            ];
            patternsToRemove.forEach(pattern => {
                rest = rest.replace(pattern, ' ');
            });
            rest = rest.trim();

            // Handle parenthetical notes (keep them)
            const parenMatch = rest.match(/^([^\(]+)(\(.+\))$/);
            if (parenMatch) {
                let unit = parenMatch[1].trim();
                const note = parenMatch[2];

                // Pluralize if needed
                if (total !== 1) {
                    if (unit === 'bulb') unit = 'bulbs';
                    if (unit === 'cup') unit = 'cups';
                }

                return `${total} ${unit} ${note}`;
            }

            return `${total} ${rest}`;
        }

        // Fallback: return original
        return `${count} × ${yieldPerPlant}`;
    }

    /**
     * Initialize garden type selector with auto-save
     */
    function setupGardenTypeSelector() {
        const gardenTypeSelect = document.getElementById('gardenTypeSelect');
        const gardenTypeStatus = document.getElementById('gardenTypeStatus');

        if (!gardenTypeSelect) return;

        gardenTypeSelect.addEventListener('change', function() {
            const newType = this.value;

            // Show saving status
            gardenTypeStatus.textContent = 'Saving...';
            gardenTypeStatus.className = 'badge bg-info ms-2';

            fetch(`/gardens/${gardenId}/update-info/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ garden_type: newType })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update yield display based on new garden type
                    updateYieldDisplay(newType);

                    // Update original value for future reverts
                    gardenTypeSelect.setAttribute('data-original-value', newType);

                    // Show success
                    gardenTypeStatus.textContent = 'Saved';
                    gardenTypeStatus.className = 'badge bg-success ms-2';
                    setTimeout(() => {
                        gardenTypeStatus.textContent = '';
                    }, 2000);
                } else {
                    gardenTypeStatus.textContent = 'Error: ' + (data.error || 'Failed to save');
                    gardenTypeStatus.className = 'badge bg-danger ms-2';
                    // Revert selection on error
                    this.value = this.getAttribute('data-original-value') || 'square_foot';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                gardenTypeStatus.textContent = 'Network error';
                gardenTypeStatus.className = 'badge bg-danger ms-2';
                // Revert selection on error
                this.value = this.getAttribute('data-original-value') || 'square_foot';
            });
        });

        // Store original value for revert on error
        gardenTypeSelect.setAttribute('data-original-value', gardenTypeSelect.value);
    }

    // ========================================
    // EXPORT/IMPORT
    // ========================================

    /**
     * Initialize Export for LLM functionality
     * Generates formatted text for copying to LLM chat
     */
    function setupExportHandler() {
        const exportGardenBtn = document.getElementById('exportGardenBtn');
        const exportGardenModalEl = document.getElementById('exportGardenModal');

        if (!exportGardenBtn || !exportGardenModalEl) return;

        const exportGardenModal = new bootstrap.Modal(exportGardenModalEl);

        exportGardenBtn.addEventListener('click', function() {
            // Get garden grid data
            const grid = [];
            const rows = document.querySelectorAll('#gardenGrid tr');
            rows.forEach(row => {
                const rowData = [];
                const cells = row.querySelectorAll('.garden-cell');
                cells.forEach(cell => {
                    rowData.push(cell.dataset.plant || 'empty space');
                });
                grid.push(rowData);
            });

            // Find empty cells
            const emptyCells = [];
            grid.forEach((row, rowIdx) => {
                row.forEach((cell, colIdx) => {
                    if (!cell || cell.toLowerCase() === 'empty space' || cell === '•') {
                        emptyCells.push({row: rowIdx, col: colIdx});
                    }
                });
            });

            // Create visual grid representation
            const gridVisual = grid.map(row =>
                row.map(cell => {
                    if (!cell || cell.toLowerCase() === 'empty space' || cell === '•') return '___';
                    if (cell.toLowerCase() === 'path' || cell === '=') return '===';
                    return cell.substring(0, 3).toUpperCase().padEnd(3, ' ');
                }).join(' | ')
            ).join('\n');

            // Get garden data first
            const gardenData = window.GARDEN_DATA;

            // Get unique plants in garden with date info and calculate statistics
            const plantsInGarden = new Set();
            const plantedInstances = [];
            const plantCounts = {};
            const plantTypeStats = {};
            let totalPlantedCells = 0;
            let pathCells = 0;

            grid.forEach((row, rowIdx) => {
                row.forEach((cell, colIdx) => {
                    if (cell && cell.toLowerCase() !== 'empty space' && cell !== '•' && cell !== '') {
                        if (cell.toLowerCase() === 'path' || cell === '=') {
                            pathCells++;
                        } else {
                            plantsInGarden.add(cell);
                            totalPlantedCells++;

                            // Count occurrences of each plant
                            const plantLower = cell.toLowerCase();
                            plantCounts[plantLower] = (plantCounts[plantLower] || 0) + 1;

                            // Count by plant type
                            const plantInfo = gardenData.plantDatabase.find(p => p.name.toLowerCase() === plantLower);
                            if (plantInfo) {
                                const type = plantInfo.type || 'unknown';
                                plantTypeStats[type] = (plantTypeStats[type] || 0) + 1;
                            }

                            // Check if there's instance data for this position
                            const instanceKey = `${rowIdx},${colIdx}`;
                            const instance = window.INSTANCE_MAP[instanceKey];
                            if (instance && instance.planted_date) {
                                plantedInstances.push({
                                    plant: cell,
                                    row: rowIdx,
                                    col: colIdx,
                                    planted_date: instance.planted_date,
                                    expected_harvest: instance.expected_harvest_date,
                                    status: instance.harvest_status,
                                    days_until_harvest: instance.days_until_harvest
                                });
                            }
                        }
                    }
                });
            });

            // Build export text
            const totalCells = gardenData.width * gardenData.height;

            // Calculate garden statistics
            const fillRate = ((totalPlantedCells / totalCells) * 100).toFixed(1);
            const diversity = plantsInGarden.size;

            // Format statistics section
            let statsInfo = '\n\nGARDEN STATISTICS:\n';
            statsInfo += `- Total planted cells: ${totalPlantedCells}/${totalCells} (${fillRate}% full)\n`;
            statsInfo += `- Plant diversity: ${diversity} unique species\n`;
            statsInfo += `- Empty spaces: ${emptyCells.length}\n`;
            statsInfo += `- Paths: ${pathCells}\n`;

            if (Object.keys(plantTypeStats).length > 0) {
                statsInfo += '- By type: ';
                const typeList = Object.entries(plantTypeStats)
                    .map(([type, count]) => `${count} ${type}`)
                    .join(', ');
                statsInfo += typeList + '\n';
            }

            if (Object.keys(plantCounts).length > 0) {
                statsInfo += '- Plant counts: ';
                const countList = Object.entries(plantCounts)
                    .sort((a, b) => b[1] - a[1])
                    .map(([plant, count]) => `${count}x ${plant}`)
                    .join(', ');
                statsInfo += countList + '\n';
            }

            // Format planted instances for the prompt
            let plantedInfo = '';
            if (plantedInstances.length > 0) {
                plantedInfo = '\n\nPLANTED CROPS WITH DATES:\n';
                plantedInstances.forEach(inst => {
                    plantedInfo += `- ${inst.plant} at (${inst.row},${inst.col}): planted ${inst.planted_date}`;
                    if (inst.expected_harvest) {
                        plantedInfo += `, expected harvest ${inst.expected_harvest}`;
                        if (inst.days_until_harvest !== null) {
                            plantedInfo += ` (${inst.days_until_harvest} days)`;
                        }
                    }
                    plantedInfo += ` [${inst.status}]\n`;
                });
            }

            // Get zone information from window.GARDEN_DATA
            const userZone = gardenData.userZone || '5b';
            const lastFrostDate = gardenData.lastFrostDate || 'May 15';
            const firstFrostDate = gardenData.firstFrostDate || 'October 15';
            const growingSeasonDays = gardenData.growingSeasonDays || 153;
            const specialConsiderations = gardenData.specialConsiderations || '';

            // Build climate context
            let climateContext = `
CLIMATE ZONE: ${userZone}
- Last Frost Date: ${lastFrostDate}
- First Frost Date: ${firstFrostDate}
- Growing Season: ${growingSeasonDays} days`;

            if (specialConsiderations) {
                climateContext += `\n- Special Considerations: ${specialConsiderations}`;
            }

            const exportText = `I'm planning a garden in USDA zone ${userZone} and need help filling empty spaces with companion plants.
${climateContext}

GARDEN INFORMATION:
- Size: ${gardenData.width} columns × ${gardenData.height} rows (${totalCells} total cells)
- Empty cells to fill: ${emptyCells.length} cells
- Current plants: ${plantsInGarden.size} unique species${statsInfo}

CURRENT GARDEN LAYOUT:
${gridVisual}

(Legend: ___ = empty space, === = path, ABC = plant abbreviation)

EXISTING PLANTS:
${plantsInGarden.size > 0 ? Array.from(plantsInGarden).join(', ') : 'None (empty garden)'}${plantedInfo}

AVAILABLE PLANTS (with companion relationships):
${JSON.stringify(gardenData.plantDatabase, null, 2)}

TASK:
Create a comprehensive garden layout by filling ALL ${emptyCells.length} empty spaces with appropriate companion plants. Consider:

1. Companion Planting: Place companions near existing plants
2. Pest Management: Use pest deterrent plants strategically
3. Plant Spacing: Respect spacing requirements
4. Variety: Include vegetables, herbs, and flowers
5. Climate Zone: All plants are pre-selected for zone ${userZone} - consider the growing season and frost dates above
6. Succession Planting: Consider planting dates and harvest times - suggest plants to replace crops nearing harvest${plantedInstances.length > 0 ? ' (see PLANTED CROPS section above)' : ''}

RESPONSE FORMAT (JSON):
{
    "reasoning": "Brief explanation of your planting strategy (3-4 sentences)",
    "suggestions": [
        {"plant_name": "Plant Name", "row": 0, "col": 1, "reason": "Why this plant here", "planted_date": "2025-04-15"},
        ... (provide ${emptyCells.length} suggestions to fill all empty spaces)
    ]
}

IMPORTANT NOTES:
- Include "planted_date" field (YYYY-MM-DD format) for each suggestion if planting date is relevant
- The system will auto-calculate expected_harvest_date based on the plant's days_to_harvest
- planted_date is OPTIONAL - omit it if you're just suggesting plant placement without dates
- If suggesting succession planting, include planted_date to indicate when to plant (e.g., future date for crops to follow current harvest)

Empty cell coordinates to fill: ${JSON.stringify(emptyCells)}`;


            document.getElementById('exportedGardenData').value = exportText;
            exportGardenModal.show();
        });

        // Copy export to clipboard
        const copyExportBtn = document.getElementById('copyExportBtn');
        if (copyExportBtn) {
            copyExportBtn.addEventListener('click', function() {
                const textarea = document.getElementById('exportedGardenData');
                textarea.select();
                navigator.clipboard.writeText(textarea.value).then(() => {
                    const status = document.getElementById('copyStatus');
                    status.innerHTML = '<span class="badge bg-success"><i class="bi bi-check"></i> Copied!</span>';
                    setTimeout(() => {
                        status.innerHTML = '';
                    }, 2000);
                });
            });
        }
    }

    /**
     * Initialize Import Layout functionality
     * Allows importing JSON layout from external LLM responses
     */
    function setupImportHandler() {
        const importLayoutBtn = document.getElementById('importLayoutBtn');
        const importLayoutModalEl = document.getElementById('importLayoutModal');
        let parsedImportData = null;

        if (!importLayoutBtn || !importLayoutModalEl) return;

        const importLayoutModal = new bootstrap.Modal(importLayoutModalEl);

        importLayoutBtn.addEventListener('click', function() {
            // Reset modal state
            document.getElementById('importLayoutData').value = '';
            document.getElementById('importPreview').classList.add('d-none');
            document.getElementById('importError').classList.add('d-none');
            document.getElementById('applyImportBtn').disabled = true;
            parsedImportData = null;

            importLayoutModal.show();
        });

        // Parse and preview import
        const parseImportBtn = document.getElementById('parseImportBtn');
        if (parseImportBtn) {
            parseImportBtn.addEventListener('click', function() {
                const importTextarea = document.getElementById('importLayoutData');
                const errorDiv = document.getElementById('importError');
                const previewDiv = document.getElementById('importPreview');

                errorDiv.classList.add('d-none');
                previewDiv.classList.add('d-none');

                try {
                    const jsonText = importTextarea.value.trim();

                    // Try to extract JSON if wrapped in markdown code blocks
                    let cleanJson = jsonText;
                    const codeBlockMatch = jsonText.match(/```(?:json)?\s*(\{[\s\S]*\})\s*```/);
                    if (codeBlockMatch) {
                        cleanJson = codeBlockMatch[1];
                    }

                    parsedImportData = JSON.parse(cleanJson);

                    // Validate structure
                    if (!parsedImportData.suggestions || !Array.isArray(parsedImportData.suggestions)) {
                        throw new Error('Invalid format: "suggestions" array is required');
                    }

                    // Display preview
                    document.getElementById('importReasoning').textContent = parsedImportData.reasoning || 'No strategy provided';

                    const suggestionsList = document.getElementById('importSuggestionsList');
                    suggestionsList.innerHTML = '';

                    parsedImportData.suggestions.forEach(suggestion => {
                        const plantInfo = plantMap[suggestion.plant_name.toLowerCase()];
                        const symbol = plantInfo ? plantInfo.symbol : suggestion.plant_name[0].toUpperCase();
                        const color = plantInfo ? plantInfo.color : '#90EE90';

                        // Build date info string if planted_date is present
                        let dateInfo = '';
                        if (suggestion.planted_date) {
                            dateInfo = `<br><small class="text-success"><i class="bi bi-calendar-check"></i> Planting date: ${suggestion.planted_date}</small>`;
                        }

                        const item = document.createElement('div');
                        item.className = 'mb-2 p-2 border rounded d-flex align-items-center';
                        item.innerHTML = `
                            <div class="d-flex align-items-center justify-content-center me-3"
                                 style="min-width: 40px; min-height: 40px; background-color: ${color}; color: white; font-size: 1.2rem; font-weight: bold; border-radius: 4px;">
                                ${symbol}
                            </div>
                            <div class="flex-grow-1">
                                <strong>${suggestion.plant_name}</strong> at Row ${suggestion.row}, Col ${suggestion.col}
                                <br>
                                <small class="text-muted">${suggestion.reason || 'No reason provided'}</small>
                                ${dateInfo}
                            </div>
                        `;
                        suggestionsList.appendChild(item);
                    });

                    previewDiv.classList.remove('d-none');
                    document.getElementById('applyImportBtn').disabled = false;

                } catch (e) {
                    errorDiv.textContent = 'Error parsing JSON: ' + e.message;
                    errorDiv.classList.remove('d-none');
                    parsedImportData = null;
                    document.getElementById('applyImportBtn').disabled = true;
                }
            });
        }

        // Apply imported layout
        const applyImportBtn = document.getElementById('applyImportBtn');
        if (applyImportBtn) {
            applyImportBtn.addEventListener('click', function() {
                if (!parsedImportData || !parsedImportData.suggestions) return;

                // Collect planted_date information
                const plantedDates = {};

                // Apply each suggestion to the grid
                parsedImportData.suggestions.forEach(suggestion => {
                    const plantName = suggestion.plant_name.toLowerCase();
                    const row = suggestion.row;
                    const col = suggestion.col;

                    // Store planted_date if present
                    if (suggestion.planted_date) {
                        const key = `${row},${col}`;
                        plantedDates[key] = suggestion.planted_date;
                    }

                    // Find the cell
                    const cell = document.querySelector(`.garden-cell[data-row="${row}"][data-col="${col}"]`);
                    if (cell) {
                        const plantInfo = plantMap[plantName];
                        if (plantInfo) {
                            updateCellContent(cell, {
                                name: plantName,
                                symbol: plantInfo.symbol,
                                color: plantInfo.color
                            });
                            cell.dataset.plant = plantName;
                        }
                    }
                });

                // Auto-save the layout with planted_date information
                autoSaveLayoutWithDates(plantedDates);

                // Close modal
                importLayoutModal.hide();

                // Show success message
                const saveStatus = document.getElementById('saveStatus');
                saveStatus.textContent = 'Imported layout applied!';
                saveStatus.className = 'badge bg-success ms-2';
                setTimeout(() => {
                    saveStatus.textContent = '';
                }, 3000);
            });
        }
    }

    // ========================================
    // MODAL HANDLERS
    // ========================================

    /**
     * Initialize delete garden button handler
     * Shows Bootstrap modal for delete confirmation
     */
    function setupDeleteHandler() {
        const deleteGardenBtn = document.getElementById('deleteGardenBtn');
        if (deleteGardenBtn) {
            deleteGardenBtn.addEventListener('click', function() {
                const deleteModal = new bootstrap.Modal(document.getElementById('deleteConfirmModal'));
                deleteModal.show();
            });
        }
    }

    /**
     * Initialize duplicate garden button handler
     * Creates a copy of the current garden and redirects to it
     */
    function setupDuplicateHandler() {
        const duplicateGardenBtn = document.getElementById('duplicateGardenBtn');
        if (!duplicateGardenBtn) return;

        duplicateGardenBtn.addEventListener('click', async function() {
            const btnManager = new ButtonStateManager(duplicateGardenBtn);
            btnManager.setLoading('Duplicating...');

            try {
                const data = await gardenAPI.duplicateGarden();
                if (data.success) {
                    // Redirect to the new garden
                    window.location.href = `/gardens/${data.garden_id}/`;
                } else {
                    alert('Error: ' + (data.error || 'Failed to duplicate garden'));
                    btnManager.reset();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Network error: Failed to duplicate garden');
                btnManager.reset();
            }
        });
    }

    /**
     * Initialize clear garden button handler
     * Shows confirmation modal and clears all plants from garden
     */
    function setupClearHandler() {
        const clearGardenBtn = document.getElementById('clearGardenBtn');
        const confirmClearBtn = document.getElementById('confirmClearBtn');
        const clearConfirmModalEl = document.getElementById('clearConfirmModal');

        if (!clearGardenBtn || !confirmClearBtn || !clearConfirmModalEl) return;

        const clearConfirmModal = new bootstrap.Modal(clearConfirmModalEl);

        clearGardenBtn.addEventListener('click', function() {
            clearConfirmModal.show();
        });

        confirmClearBtn.addEventListener('click', async function() {
            const btnManager = new ButtonStateManager(confirmClearBtn);
            btnManager.setLoading('Clearing...');

            try {
                const data = await gardenAPI.clearGarden();
                if (data.success) {
                    // Reload the page to show empty garden
                    window.location.reload();
                } else {
                    clearConfirmModal.hide();
                    alert('Error: ' + (data.error || 'Failed to clear garden'));
                    btnManager.reset();
                }
            } catch (error) {
                console.error('Error:', error);
                clearConfirmModal.hide();
                alert('Network error: Failed to clear garden');
                btnManager.reset();
            }
        });
    }

    /**
     * Initialize share garden button handler
     * Shows modal to share garden via email
     */
    function setupShareHandler() {
        const shareGardenBtn = document.getElementById('shareGardenBtn');
        const shareGardenModalEl = document.getElementById('shareGardenModal');
        const sendShareBtn = document.getElementById('sendShareBtn');
        const shareForm = document.getElementById('shareGardenForm');

        if (!shareGardenBtn || !shareGardenModalEl) return;

        const shareModal = new bootstrap.Modal(shareGardenModalEl);

        // Open modal
        shareGardenBtn.addEventListener('click', function() {
            loadCurrentShares();
            shareModal.show();
        });

        // Send share invitation
        if (sendShareBtn && shareForm) {
            sendShareBtn.addEventListener('click', async function() {
                const email = document.getElementById('shareEmail').value;
                const permission = document.getElementById('sharePermission').value;
                const errorDiv = document.getElementById('shareError');
                const successDiv = document.getElementById('shareSuccess');

                errorDiv.classList.add('d-none');
                successDiv.classList.add('d-none');

                if (!email) {
                    errorDiv.textContent = 'Please enter an email address';
                    errorDiv.classList.remove('d-none');
                    return;
                }

                const btnManager = new ButtonStateManager(sendShareBtn);
                btnManager.setLoading('Sending...');

                try {
                    const response = await fetch(`/gardens/${gardenAPI.gardenId}/share/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({ email, permission })
                    });

                    const data = await response.json();

                    if (data.success) {
                        successDiv.textContent = data.message || 'Garden shared successfully!';
                        successDiv.classList.remove('d-none');
                        shareForm.reset();
                        loadCurrentShares();
                    } else {
                        errorDiv.textContent = data.error || 'Failed to share garden';
                        errorDiv.classList.remove('d-none');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    errorDiv.textContent = 'Network error: Failed to share garden';
                    errorDiv.classList.remove('d-none');
                } finally {
                    btnManager.reset();
                }
            });
        }

        // Load current shares
        async function loadCurrentShares() {
            const sharesList = document.getElementById('sharesList');
            if (!sharesList) return;

            sharesList.innerHTML = '<div class="text-center"><span class="spinner-border spinner-border-sm"></span> Loading...</div>';

            try {
                const response = await fetch(`/gardens/${gardenAPI.gardenId}/shares/`);
                const data = await response.json();

                if (data.shares && data.shares.length > 0) {
                    sharesList.innerHTML = data.shares.map(share => `
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${share.email}</strong>
                                <br>
                                <small class="text-muted">
                                    ${share.permission === 'edit' ? '<i class="bi bi-pencil"></i> Can Edit' : '<i class="bi bi-eye"></i> Can View'}
                                    ${share.accepted ? '<span class="badge bg-success ms-2">Accepted</span>' : '<span class="badge bg-warning ms-2">Pending</span>'}
                                </small>
                            </div>
                            <button class="btn btn-sm btn-outline-danger" onclick="revokeShare(${share.id})">
                                <i class="bi bi-x"></i> Revoke
                            </button>
                        </div>
                    `).join('');
                } else {
                    sharesList.innerHTML = '<div class="text-muted text-center py-3">Not yet shared with anyone</div>';
                }
            } catch (error) {
                console.error('Error loading shares:', error);
                sharesList.innerHTML = '<div class="text-danger text-center">Failed to load shares</div>';
            }
        }

        // Make revoke function global
        window.revokeShare = async function(shareId) {
            if (!confirm('Are you sure you want to revoke this share?')) return;

            try {
                const response = await fetch(`/gardens/${gardenAPI.gardenId}/share/${shareId}/revoke/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });

                const data = await response.json();
                if (data.success) {
                    loadCurrentShares();
                } else {
                    alert('Failed to revoke share: ' + (data.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Network error: Failed to revoke share');
            }
        };
    }

    // Initialize all handlers
    console.log('Initializing all handlers...');
    setupGardenNameEditing();
    setupGardenDescriptionEditing();
    setupGardenTypeSelector();
    setupAIAssistant();
    setupExportHandler();
    setupImportHandler();
    setupDeleteHandler();
    setupDuplicateHandler();
    setupClearHandler();
    setupShareHandler();

    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Make functions available globally for other modules and template code
    window.autoSaveLayout = autoSaveLayout;
    window.updateCellContent = updateCellContent;
});
