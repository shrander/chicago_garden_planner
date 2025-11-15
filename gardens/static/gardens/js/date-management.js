/**
 * Date Management for Garden Plants
 * Handles planting dates, harvest tracking, and visual highlighting
 */

function setupDateManagement() {
    const plantDateModal = document.getElementById('plantDateModal');
    if (!plantDateModal) return;

    const modal = new bootstrap.Modal(plantDateModal);
    const seedStartedDateInput = document.getElementById('seedStartedDateInput');
    const transplantedDateInput = document.getElementById('transplantedDateInput');
    const plantedDateInput = document.getElementById('plantedDateInput');
    const actualHarvestDateInput = document.getElementById('actualHarvestDateInput');
    const markHarvestedCheck = document.getElementById('markHarvestedCheck');
    const saveDatesBtn = document.getElementById('saveDatesBtn');
    const clearDatesBtn = document.getElementById('clearDatesBtn');
    const actualHarvestGroup = document.getElementById('actualHarvestGroup');
    const expectedHarvestInfo = document.getElementById('expectedHarvestInfo');

    let currentRow, currentCol, currentPlantName;

    // Add click handlers to all plant cells
    const gardenCells = document.querySelectorAll('.garden-cell');
    gardenCells.forEach(cell => {
        cell.addEventListener('click', function(e) {
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

            // Populate modal
            document.getElementById('selectedPlantName').textContent = plantName;
            document.getElementById('selectedPlantPosition').textContent = `Row ${rowIndex + 1}, Column ${colIndex + 1}`;

            if (currentInstanceData) {
                // Populate all date fields
                seedStartedDateInput.value = currentInstanceData.seed_started_date || '';
                transplantedDateInput.value = currentInstanceData.transplanted_date || '';
                plantedDateInput.value = currentInstanceData.planted_date || '';
                actualHarvestDateInput.value = currentInstanceData.actual_harvest_date || '';

                // Show clear button if any date is set
                if (currentInstanceData.seed_started_date || currentInstanceData.transplanted_date || currentInstanceData.planted_date) {
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
                transplantedDateInput.value = '';
                plantedDateInput.value = '';
                actualHarvestDateInput.value = '';
                markHarvestedCheck.checked = false;
                actualHarvestGroup.style.display = 'none';
                expectedHarvestInfo.style.display = 'none';
                clearDatesBtn.style.display = 'none';
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

    // Save dates
    saveDatesBtn.addEventListener('click', async function() {
        const btnManager = new ButtonStateManager(saveDatesBtn);
        btnManager.setLoading('Saving...');

        try {
            // Save all planting dates if any are provided
            if (seedStartedDateInput.value || transplantedDateInput.value || plantedDateInput.value) {
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
                        transplanted_date: transplantedDateInput.value || null,
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
