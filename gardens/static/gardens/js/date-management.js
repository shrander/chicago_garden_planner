/**
 * Date Management for Garden Plants
 * Handles planting dates, harvest tracking, and visual highlighting
 */

function setupDateManagement() {
    const plantDateModal = document.getElementById('plantDateModal');
    if (!plantDateModal) return;

    const modal = new bootstrap.Modal(plantDateModal);
    const seedStartedDateInput = document.getElementById('seedStartedDateInput');
    const plantedDateInput = document.getElementById('plantedDateInput');
    const actualHarvestDateInput = document.getElementById('actualHarvestDateInput');
    const markHarvestedCheck = document.getElementById('markHarvestedCheck');
    const saveDatesBtn = document.getElementById('saveDatesBtn');
    const clearDatesBtn = document.getElementById('clearDatesBtn');
    const actualHarvestGroup = document.getElementById('actualHarvestGroup');
    const expectedHarvestInfo = document.getElementById('expectedHarvestInfo');
    const expectedTransplantInfo = document.getElementById('expectedTransplantInfo');
    const plantedDateLabel = document.getElementById('plantedDateLabel');
    const plantedDateHelp = document.getElementById('plantedDateHelp');

    let currentRow, currentCol, currentPlantName, currentPlantData;
    let isDragging = false;

    // Helper function to calculate expected transplant date
    function calculateExpectedTransplantDate(seedStartedDate, plantData) {
        if (!seedStartedDate || !plantData || plantData.direct_sow) return null;

        const seedDate = new Date(seedStartedDate);
        let totalDays = 0;
        if (plantData.days_to_germination) totalDays += plantData.days_to_germination;
        if (plantData.days_before_transplant_ready) totalDays += plantData.days_before_transplant_ready;

        if (totalDays > 0) {
            const transplantDate = new Date(seedDate);
            transplantDate.setDate(transplantDate.getDate() + totalDays);
            return transplantDate;
        }
        return null;
    }

    // Helper function to calculate expected harvest date
    function calculateExpectedHarvestDate(plantedDate, plantData) {
        if (!plantedDate || !plantData) return null;

        const planted = new Date(plantedDate);
        const days = plantData.transplant_to_harvest_days || plantData.days_to_harvest;

        if (days) {
            const harvestDate = new Date(planted);
            harvestDate.setDate(harvestDate.getDate() + days);
            return harvestDate;
        }
        return null;
    }

    // Helper function to calculate days until date
    function daysUntil(targetDate) {
        if (!targetDate) return null;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const target = new Date(targetDate);
        target.setHours(0, 0, 0, 0);
        const diffTime = target - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays;
    }

    // Add click handlers to all plant cells
    const gardenCells = document.querySelectorAll('.garden-cell');
    gardenCells.forEach(cell => {
        // Track drag state using the existing drag events
        cell.addEventListener('dragstart', function(e) {
            isDragging = true;
        });

        cell.addEventListener('dragend', function(e) {
            // Reset drag state after a short delay to ensure click event sees it
            setTimeout(() => {
                isDragging = false;
            }, 50);
        });

        cell.addEventListener('click', function(e) {
            // Ignore clicks that were actually drags
            if (isDragging) {
                return;
            }

            const plantName = this.dataset.plant;

            // Skip empty cells and paths
            if (!plantName || plantName === 'empty space' || plantName === 'path') {
                return;
            }

            // Get row and col from the cell's position
            const tr = this.closest('tr');
            const rowIndex = Array.from(tr.parentNode.children).indexOf(tr);
            const colIndex = Array.from(tr.children).indexOf(this.closest('td'));

            currentRow = rowIndex;
            currentCol = colIndex;
            currentPlantName = plantName;

            // Get instance data if exists
            const instanceKey = `${rowIndex},${colIndex}`;
            const currentInstanceData = window.INSTANCE_MAP && window.INSTANCE_MAP[instanceKey] ? window.INSTANCE_MAP[instanceKey] : null;

            // Get plant data from PLANT_MAP and store it
            currentPlantData = window.PLANT_MAP && window.PLANT_MAP[plantName.toLowerCase()] ? window.PLANT_MAP[plantName.toLowerCase()] : null;
            const plantData = currentPlantData;

            // Populate modal
            document.getElementById('selectedPlantName').textContent = plantName;
            document.getElementById('selectedPlantPosition').textContent = `Row ${rowIndex + 1}, Column ${colIndex + 1}`;

            if (currentInstanceData) {
                // Populate date fields
                seedStartedDateInput.value = currentInstanceData.seed_started_date || '';
                plantedDateInput.value = currentInstanceData.planted_date || '';
                actualHarvestDateInput.value = currentInstanceData.actual_harvest_date || '';

                // Update UI based on whether plant is direct sown
                const isDirectSown = plantData ? plantData.direct_sow : false;
                if (isDirectSown) {
                    plantedDateLabel.textContent = 'Direct Sown Date';
                    plantedDateHelp.textContent = 'When were seeds sown directly in the garden?';
                    expectedTransplantInfo.style.display = 'none';
                } else {
                    plantedDateLabel.textContent = 'Actual Planted Date';
                    plantedDateHelp.textContent = 'When was this actually transplanted to the garden plot?';

                    // Show expected transplant date if available
                    if (currentInstanceData.expected_transplant_date) {
                        expectedTransplantInfo.style.display = 'block';
                        document.getElementById('expectedTransplantDate').textContent =
                            new Date(currentInstanceData.expected_transplant_date).toLocaleDateString();
                    } else {
                        expectedTransplantInfo.style.display = 'none';
                    }
                }

                // Show clear button if any date is set
                if (currentInstanceData.seed_started_date || currentInstanceData.planted_date) {
                    clearDatesBtn.style.display = 'inline-block';
                } else {
                    clearDatesBtn.style.display = 'none';
                }

                // Show expected harvest info
                if (currentInstanceData.expected_harvest_date) {
                    expectedHarvestInfo.style.display = 'block';
                    document.getElementById('expectedHarvestDate').textContent = new Date(currentInstanceData.expected_harvest_date).toLocaleDateString();
                    if (currentInstanceData.days_until_harvest !== null) {
                        document.getElementById('daysToHarvest').textContent = currentInstanceData.days_until_harvest;
                    }
                } else {
                    expectedHarvestInfo.style.display = 'none';
                }

                // Show harvest section if harvested
                if (currentInstanceData.actual_harvest_date) {
                    markHarvestedCheck.checked = true;
                    actualHarvestGroup.style.display = 'block';
                } else {
                    markHarvestedCheck.checked = false;
                    actualHarvestGroup.style.display = 'none';
                }
            } else {
                // Clear all fields for new plant
                seedStartedDateInput.value = '';
                plantedDateInput.value = '';
                actualHarvestDateInput.value = '';
                markHarvestedCheck.checked = false;
                actualHarvestGroup.style.display = 'none';
                expectedHarvestInfo.style.display = 'none';
                expectedTransplantInfo.style.display = 'none';
                clearDatesBtn.style.display = 'none';

                // Set up UI based on plant type even for new instances
                const isDirectSown = plantData ? plantData.direct_sow : false;
                if (isDirectSown) {
                    plantedDateLabel.textContent = 'Direct Sown Date';
                    plantedDateHelp.textContent = 'When were seeds sown directly in the garden?';
                } else {
                    plantedDateLabel.textContent = 'Actual Planted Date';
                    plantedDateHelp.textContent = 'When was this actually transplanted to the garden plot?';
                }
            }

            modal.show();
        });
    });

    // Show/hide actual harvest date input based on checkbox
    markHarvestedCheck.addEventListener('change', function() {
        actualHarvestGroup.style.display = this.checked ? 'block' : 'none';
        if (this.checked && !actualHarvestDateInput.value) {
            // Set to today by default
            actualHarvestDateInput.value = new Date().toISOString().split('T')[0];
        }
    });

    // Real-time calculation when seed started date changes
    seedStartedDateInput.addEventListener('change', function() {
        if (!currentPlantData) return;

        // Calculate and show expected transplant date
        if (!currentPlantData.direct_sow) {
            const expectedTransplant = calculateExpectedTransplantDate(this.value, currentPlantData);
            if (expectedTransplant) {
                expectedTransplantInfo.style.display = 'block';
                document.getElementById('expectedTransplantDate').textContent = expectedTransplant.toLocaleDateString();
            } else {
                expectedTransplantInfo.style.display = 'none';
            }
        }

        // For direct sown plants, auto-fill planted date
        if (currentPlantData.direct_sow && this.value && !plantedDateInput.value) {
            plantedDateInput.value = this.value;
            // Trigger planted date change to calculate harvest
            plantedDateInput.dispatchEvent(new Event('change'));
        }
    });

    // Real-time calculation when planted date changes
    plantedDateInput.addEventListener('change', function() {
        if (!currentPlantData) return;

        // Calculate and show expected harvest date
        const expectedHarvest = calculateExpectedHarvestDate(this.value, currentPlantData);
        if (expectedHarvest) {
            const daysRemaining = daysUntil(expectedHarvest);
            expectedHarvestInfo.style.display = 'block';
            document.getElementById('expectedHarvestDate').textContent = expectedHarvest.toLocaleDateString();
            if (daysRemaining !== null) {
                document.getElementById('daysToHarvest').textContent = daysRemaining;
            }
        } else {
            expectedHarvestInfo.style.display = 'none';
        }
    });

    // Save dates
    saveDatesBtn.addEventListener('click', async function() {
        const btnManager = new ButtonStateManager(saveDatesBtn);
        btnManager.setLoading('Saving...');

        try {
            // Save all planting dates if any are provided
            if (seedStartedDateInput.value || plantedDateInput.value) {
                const response = await fetch(`/gardens/${window.GARDEN_ID}/set-planting-date/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        row: currentRow,
                        col: currentCol,
                        seed_started_date: seedStartedDateInput.value || null,
                        planted_date: plantedDateInput.value || null
                    })
                });

                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error || 'Failed to save planting dates');
                }

                // Update instance map
                const instanceKey = `${currentRow},${currentCol}`;
                if (!window.INSTANCE_MAP) window.INSTANCE_MAP = {};
                window.INSTANCE_MAP[instanceKey] = data.instance;
            }

            // Then, mark as harvested if checked
            if (markHarvestedCheck.checked) {
                const response = await fetch(`/gardens/${window.GARDEN_ID}/mark-harvested/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        row: currentRow,
                        col: currentCol,
                        actual_harvest_date: actualHarvestDateInput.value
                    })
                });

                const data = await response.json();
                if (!data.success) {
                    throw new Error(data.error || 'Failed to mark as harvested');
                }

                // Update instance map
                const instanceKey = `${currentRow},${currentCol}`;
                window.INSTANCE_MAP[instanceKey] = data.instance;
            }

            // Update cell visual appearance
            updateCellHarvestStatus(currentRow, currentCol);

            modal.hide();
            btnManager.reset();

        } catch (error) {
            console.error('Error saving dates:', error);
            const dateStatus = document.getElementById('dateStatus');
            dateStatus.textContent = 'Error: ' + error.message;
            dateStatus.className = 'alert alert-danger';
            dateStatus.classList.remove('d-none');
            btnManager.reset();
        }
    });

    // Clear dates
    clearDatesBtn.addEventListener('click', async function() {
        if (!confirm('Clear all dates for this plant?')) return;

        const btnManager = new ButtonStateManager(clearDatesBtn);
        btnManager.setLoading('Clearing...');

        try {
            const response = await fetch(`/gardens/${window.GARDEN_ID}/set-planting-date/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({
                    row: currentRow,
                    col: currentCol,
                    planted_date: null
                })
            });

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Failed to clear dates');
            }

            // Update instance map
            const instanceKey = `${currentRow},${currentCol}`;
            if (window.INSTANCE_MAP && window.INSTANCE_MAP[instanceKey]) {
                delete window.INSTANCE_MAP[instanceKey];
            }

            // Update cell visual appearance
            updateCellHarvestStatus(currentRow, currentCol);

            modal.hide();
            btnManager.reset();

        } catch (error) {
            console.error('Error clearing dates:', error);
            alert('Error: ' + error.message);
            btnManager.reset();
        }
    });
}

function updateCellHarvestStatus(row, col) {
    const instanceKey = `${row},${col}`;
    const instance = window.INSTANCE_MAP && window.INSTANCE_MAP[instanceKey];

    // Find the cell
    const gardenGrid = document.getElementById('gardenGrid');
    const tr = gardenGrid.querySelectorAll('tr')[row];
    if (!tr) return;

    const cell = tr.querySelectorAll('.garden-cell')[col];
    if (!cell) return;

    // Remove all harvest status classes
    cell.classList.remove('harvest-overdue', 'harvest-ready', 'harvest-soon', 'harvest-growing', 'harvest-harvested');

    // Remove existing date badge if any
    const existingBadge = cell.querySelector('.date-badge');
    if (existingBadge) {
        existingBadge.remove();
    }

    if (instance && instance.harvest_status) {
        // Add harvest status class
        cell.classList.add(`harvest-${instance.harvest_status}`);

        // Add date badge
        if (instance.days_until_harvest !== null) {
            const badge = document.createElement('span');
            badge.className = 'date-badge';

            if (instance.harvest_status === 'ready') {
                badge.classList.add('ready');
                badge.textContent = 'Ready!';
            } else if (instance.harvest_status === 'soon') {
                badge.classList.add('soon');
                badge.textContent = `${instance.days_until_harvest}d`;
            } else if (instance.harvest_status === 'overdue') {
                badge.classList.add('overdue');
                badge.textContent = 'Overdue';
            } else if (instance.harvest_status === 'growing' && instance.days_until_harvest > 0) {
                badge.textContent = `${instance.days_until_harvest}d`;
            }

            if (badge.textContent) {
                cell.appendChild(badge);
            }
        } else if (instance.harvest_status === 'harvested') {
            const badge = document.createElement('span');
            badge.className = 'date-badge ready';
            badge.textContent = 'Harvested';
            cell.appendChild(badge);
        }
    }
}

// Apply harvest status on page load
function initializeHarvestHighlighting() {
    if (!window.INSTANCE_MAP) return;

    Object.keys(window.INSTANCE_MAP).forEach(key => {
        const [row, col] = key.split(',').map(Number);
        updateCellHarvestStatus(row, col);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    setupDateManagement();
    initializeHarvestHighlighting();
});
