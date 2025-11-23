/**
 * Date Management for Garden Plants
 * Handles planting dates, harvest tracking, and visual highlighting
 */

function setupDateManagement() {
    const plantDateModal = document.getElementById('plantDateModal');
    if (!plantDateModal) return;

    const modal = new bootstrap.Modal(plantDateModal);

    // Checkbox for seed starting method
    const directSownCheck = document.getElementById('directSownCheck');

    // Planned date inputs
    const plannedSeedStartInput = document.getElementById('plannedSeedStartInput');
    const plannedPlantingInput = document.getElementById('plannedPlantingInput');

    // Actual date inputs
    const seedStartedDateInput = document.getElementById('seedStartedDateInput');
    const plantedDateInput = document.getElementById('plantedDateInput');
    const actualHarvestDateInput = document.getElementById('actualHarvestDateInput');

    // Other controls
    const markHarvestedCheck = document.getElementById('markHarvestedCheck');
    const saveDatesBtn = document.getElementById('saveDatesBtn');
    const clearDatesBtn = document.getElementById('clearDatesBtn');
    const actualHarvestGroup = document.getElementById('actualHarvestGroup');
    const expectedHarvestInfo = document.getElementById('expectedHarvestInfo');
    const expectedTransplantInfo = document.getElementById('expectedTransplantInfo');
    const plantedDateLabel = document.getElementById('plantedDateLabel');
    const plantedDateHelp = document.getElementById('plantedDateHelp');
    const plannedPlantingLabel = document.getElementById('plannedPlantingLabel');
    const plannedPlantingHelp = document.getElementById('plannedPlantingHelp');

    let currentRow, currentCol, currentPlantName, currentPlantData;
    let isDragging = false;

    // Helper function to calculate expected transplant date
    // Takes either planned or actual seed start date
    function calculateExpectedTransplantDate(seedStartedDate, plantData, isDirectSown) {
        if (!seedStartedDate || !plantData || isDirectSown) return null;

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

    // Helper function to update modal notifications
    function updateModalNotifications(instanceData, plantData, isDirectSown) {
        // Get notification elements
        const seedStartNotification = document.getElementById('seedStartNotification');
        const transplantNotification = document.getElementById('transplantNotification');
        const plantingNotification = document.getElementById('plantingNotification');
        const harvestNotification = document.getElementById('harvestNotification');

        // Hide all notifications by default
        seedStartNotification.style.display = 'none';
        transplantNotification.style.display = 'none';
        plantingNotification.style.display = 'none';
        harvestNotification.style.display = 'none';

        if (!plantData) return;

        // Build current state from form inputs (may differ from saved instanceData)
        const currentState = {
            planned_seed_start_date: plannedSeedStartInput.value || instanceData?.planned_seed_start_date || null,
            seed_started_date: seedStartedDateInput.value || instanceData?.seed_started_date || null,
            planned_planting_date: plannedPlantingInput.value || instanceData?.planned_planting_date || null,
            planted_date: plantedDateInput.value || instanceData?.planted_date || null,
            actual_harvest_date: actualHarvestDateInput.value || instanceData?.actual_harvest_date || null,
        };

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // 1. Seed Start Notifications (only if not direct sown and not started yet)
        if (!isDirectSown && !currentState.seed_started_date) {
            const plannedSeedStart = currentState.planned_seed_start_date;
            if (plannedSeedStart) {
                const daysTillSeedStart = daysUntil(plannedSeedStart);

                if (daysTillSeedStart < 0) {
                    // Overdue
                    seedStartNotification.className = 'alert alert-danger';
                    seedStartNotification.querySelector('#seedStartNotificationTitle').textContent = 'Seed Starting Overdue';
                    seedStartNotification.querySelector('#seedStartNotificationText').textContent =
                        `Planned seed start was ${Math.abs(daysTillSeedStart)} day${Math.abs(daysTillSeedStart) === 1 ? '' : 's'} ago. Start seeds soon or adjust planned date.`;
                    seedStartNotification.style.display = 'block';
                } else if (daysTillSeedStart === 0) {
                    // Due today
                    seedStartNotification.className = 'alert alert-success';
                    seedStartNotification.querySelector('#seedStartNotificationTitle').textContent = 'Start Seeds Today!';
                    seedStartNotification.querySelector('#seedStartNotificationText').textContent =
                        'Today is your planned seed starting date. Get those seeds started!';
                    seedStartNotification.style.display = 'block';
                } else if (daysTillSeedStart <= 7) {
                    // Coming up soon
                    seedStartNotification.className = 'alert alert-warning';
                    seedStartNotification.querySelector('#seedStartNotificationTitle').textContent = 'Seed Starting Soon';
                    seedStartNotification.querySelector('#seedStartNotificationText').textContent =
                        `Start seeds in ${daysTillSeedStart} day${daysTillSeedStart === 1 ? '' : 's'}. Get your supplies ready!`;
                    seedStartNotification.style.display = 'block';
                }
            }
        }

        // 2. Transplant Notifications (only if pot-started and seeds started but not planted yet)
        if (!isDirectSown && currentState.seed_started_date && !currentState.planted_date) {
            const expectedTransplant = calculateExpectedTransplantDate(currentState.seed_started_date, plantData, false);
            if (expectedTransplant) {
                const daysTillTransplant = daysUntil(expectedTransplant);

                if (daysTillTransplant < 0) {
                    // Overdue
                    transplantNotification.className = 'alert alert-danger';
                    transplantNotification.querySelector('#transplantNotificationTitle').textContent = 'Transplant Overdue';
                    transplantNotification.querySelector('#transplantNotificationText').textContent =
                        `Ready to transplant ${Math.abs(daysTillTransplant)} day${Math.abs(daysTillTransplant) === 1 ? '' : 's'} ago. Transplant soon or seedlings may become root-bound.`;
                    transplantNotification.style.display = 'block';
                } else if (daysTillTransplant === 0) {
                    // Ready today
                    transplantNotification.className = 'alert alert-success';
                    transplantNotification.querySelector('#transplantNotificationTitle').textContent = 'Ready to Transplant!';
                    transplantNotification.querySelector('#transplantNotificationText').textContent =
                        'Seedlings are ready to transplant to the garden today!';
                    transplantNotification.style.display = 'block';
                } else if (daysTillTransplant <= 7) {
                    // Coming up soon
                    transplantNotification.className = 'alert alert-info';
                    transplantNotification.querySelector('#transplantNotificationTitle').textContent = 'Transplant Soon';
                    transplantNotification.querySelector('#transplantNotificationText').textContent =
                        `Seedlings will be ready to transplant in ${daysTillTransplant} day${daysTillTransplant === 1 ? '' : 's'}.`;
                    transplantNotification.style.display = 'block';
                }
            }
        }

        // 3. Planting Notifications (for direct sown or if planned planting exists but not planted)
        if (!currentState.planted_date && currentState.planned_planting_date) {
            const daysTillPlanting = daysUntil(currentState.planned_planting_date);
            const plantingType = isDirectSown ? 'sowing' : 'planting';

            if (daysTillPlanting < 0) {
                // Overdue
                plantingNotification.className = 'alert alert-danger';
                plantingNotification.querySelector('#plantingNotificationTitle').textContent = `${isDirectSown ? 'Sowing' : 'Planting'} Overdue`;
                plantingNotification.querySelector('#plantingNotificationText').textContent =
                    `Planned ${plantingType} was ${Math.abs(daysTillPlanting)} day${Math.abs(daysTillPlanting) === 1 ? '' : 's'} ago. ${isDirectSown ? 'Sow' : 'Plant'} soon or adjust date.`;
                plantingNotification.style.display = 'block';
            } else if (daysTillPlanting === 0) {
                // Due today
                plantingNotification.className = 'alert alert-success';
                plantingNotification.querySelector('#plantingNotificationTitle').textContent = `${isDirectSown ? 'Sow' : 'Plant'} Today!`;
                plantingNotification.querySelector('#plantingNotificationText').textContent =
                    `Today is your planned ${plantingType} date!`;
                plantingNotification.style.display = 'block';
            } else if (daysTillPlanting <= 7) {
                // Coming up soon
                plantingNotification.className = 'alert alert-warning';
                plantingNotification.querySelector('#plantingNotificationTitle').textContent = `${isDirectSown ? 'Sowing' : 'Planting'} Soon`;
                plantingNotification.querySelector('#plantingNotificationText').textContent =
                    `${isDirectSown ? 'Sow' : 'Plant'} in ${daysTillPlanting} day${daysTillPlanting === 1 ? '' : 's'}.`;
                plantingNotification.style.display = 'block';
            }
        }

        // 4. Harvest Notifications (only if planted and not harvested yet)
        if (currentState.planted_date && !currentState.actual_harvest_date) {
            const expectedHarvest = calculateExpectedHarvestDate(currentState.planted_date, plantData);
            if (expectedHarvest) {
                const daysTillHarvest = daysUntil(expectedHarvest);

                if (daysTillHarvest < 0) {
                    // Overdue
                    harvestNotification.className = 'alert alert-danger';
                    harvestNotification.querySelector('#harvestNotificationTitle').textContent = 'Harvest Overdue';
                    harvestNotification.querySelector('#harvestNotificationText').textContent =
                        `Expected harvest was ${Math.abs(daysTillHarvest)} day${Math.abs(daysTillHarvest) === 1 ? '' : 's'} ago. Check your plants!`;
                    harvestNotification.style.display = 'block';
                } else if (daysTillHarvest === 0) {
                    // Ready today
                    harvestNotification.className = 'alert alert-success';
                    harvestNotification.querySelector('#harvestNotificationTitle').textContent = 'Ready to Harvest!';
                    harvestNotification.querySelector('#harvestNotificationText').textContent =
                        'Your plants are ready to harvest today!';
                    harvestNotification.style.display = 'block';
                } else if (daysTillHarvest <= 7) {
                    // Coming up soon
                    harvestNotification.className = 'alert alert-warning';
                    harvestNotification.querySelector('#harvestNotificationTitle').textContent = 'Harvest Soon';
                    harvestNotification.querySelector('#harvestNotificationText').textContent =
                        `Harvest in ${daysTillHarvest} day${daysTillHarvest === 1 ? '' : 's'}. Start monitoring!`;
                    harvestNotification.style.display = 'block';
                }
            }
        }
    }

    // Helper function to update UI based on seed starting method
    function updateUIForSeedingMethod(isDirectSown) {
        if (isDirectSown) {
            // Direct sown: disable actual planted date (syncs with seed started)
            plantedDateInput.disabled = true;
            plantedDateLabel.textContent = 'Actual Direct Sown';
            plantedDateHelp.textContent = 'Auto-syncs with actual seed started date';
            plannedPlantingLabel.textContent = 'Planned Direct Sow';
            plannedPlantingHelp.textContent = 'When do you plan to sow directly?';
            expectedTransplantInfo.style.display = 'none';
        } else {
            // Pot started: enable actual planted date
            plantedDateInput.disabled = false;
            plantedDateLabel.textContent = 'Actual Transplanted';
            plantedDateHelp.textContent = 'When was this transplanted to the garden?';
            plannedPlantingLabel.textContent = 'Planned Transplant';
            plannedPlantingHelp.textContent = 'When do you plan to transplant?';
        }
    }

    // Checkbox change handler for seed starting method
    directSownCheck.addEventListener('change', function() {
        const isDirectSown = this.checked;
        updateUIForSeedingMethod(isDirectSown);

        // If switching to direct sown and actual seed started exists, sync planted date
        if (isDirectSown && seedStartedDateInput.value) {
            plantedDateInput.value = seedStartedDateInput.value;
            // Recalculate harvest
            plantedDateInput.dispatchEvent(new Event('change'));
        }

        // If switching to direct sown and planned seed start exists, sync planned planting
        if (isDirectSown && plannedSeedStartInput.value) {
            plannedPlantingInput.value = plannedSeedStartInput.value;
            // Recalculate harvest with planned date
            const expectedHarvest = calculateExpectedHarvestDate(plannedPlantingInput.value, currentPlantData);
            if (expectedHarvest) {
                const daysRemaining = daysUntil(expectedHarvest);
                expectedHarvestInfo.style.display = 'block';
                document.getElementById('expectedHarvestDate').textContent = expectedHarvest.toLocaleDateString();
                if (daysRemaining !== null) {
                    document.getElementById('daysToHarvest').textContent = daysRemaining;
                }
            }
        }

        // Hide transplant info when direct sown
        if (isDirectSown) {
            expectedTransplantInfo.style.display = 'none';
        }

        // Update notifications based on new seeding method
        const instanceKey = `${currentRow},${currentCol}`;
        const currentInstanceData = window.INSTANCE_MAP && window.INSTANCE_MAP[instanceKey] ? window.INSTANCE_MAP[instanceKey] : null;
        updateModalNotifications(currentInstanceData, currentPlantData, isDirectSown);
    });

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
                // Populate seed starting method checkbox
                const isDirectSown = currentInstanceData.seed_starting_method === 'direct';
                directSownCheck.checked = isDirectSown;

                // Populate planned date fields
                plannedSeedStartInput.value = currentInstanceData.planned_seed_start_date || '';
                plannedPlantingInput.value = currentInstanceData.planned_planting_date || '';

                // Populate actual date fields
                seedStartedDateInput.value = currentInstanceData.seed_started_date || '';
                plantedDateInput.value = currentInstanceData.planted_date || '';
                actualHarvestDateInput.value = currentInstanceData.actual_harvest_date || '';

                // Update UI based on direct sown checkbox
                updateUIForSeedingMethod(isDirectSown);

                // Calculate and show expected transplant date if not direct sown
                if (!isDirectSown) {
                    const seedDate = currentInstanceData.seed_started_date || currentInstanceData.planned_seed_start_date;
                    if (seedDate) {
                        const expectedTransplant = calculateExpectedTransplantDate(seedDate, plantData, false);
                        if (expectedTransplant) {
                            expectedTransplantInfo.style.display = 'block';
                            document.getElementById('expectedTransplantDate').textContent = expectedTransplant.toLocaleDateString();
                        } else {
                            expectedTransplantInfo.style.display = 'none';
                        }
                    } else {
                        expectedTransplantInfo.style.display = 'none';
                    }
                } else {
                    expectedTransplantInfo.style.display = 'none';
                }

                // Show clear button if any date is set
                if (currentInstanceData.seed_started_date || currentInstanceData.planted_date ||
                    currentInstanceData.planned_seed_start_date || currentInstanceData.planned_planting_date) {
                    clearDatesBtn.style.display = 'inline-block';
                } else {
                    clearDatesBtn.style.display = 'none';
                }

                // Show expected harvest info using actual OR planned dates
                const effectivePlantedDate = currentInstanceData.planted_date || currentInstanceData.planned_planting_date;
                if (effectivePlantedDate) {
                    const expectedHarvest = calculateExpectedHarvestDate(effectivePlantedDate, plantData);
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
                directSownCheck.checked = false;
                plannedSeedStartInput.value = '';
                plannedPlantingInput.value = '';
                seedStartedDateInput.value = '';
                plantedDateInput.value = '';
                actualHarvestDateInput.value = '';
                markHarvestedCheck.checked = false;
                actualHarvestGroup.style.display = 'none';
                expectedHarvestInfo.style.display = 'none';
                expectedTransplantInfo.style.display = 'none';
                clearDatesBtn.style.display = 'none';

                // Set up UI for pot-started by default
                updateUIForSeedingMethod(false);
            }

            // Update modal notifications
            updateModalNotifications(currentInstanceData, plantData, currentInstanceData?.seed_starting_method === 'direct' || false);

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

    // Real-time calculation when planned seed start date changes
    plannedSeedStartInput.addEventListener('change', function() {
        if (!currentPlantData) return;

        const isDirectSown = directSownCheck.checked;

        // For direct sown, auto-sync planned planting with planned seed start
        if (isDirectSown && this.value) {
            plannedPlantingInput.value = this.value;
            // Recalculate harvest based on planned planting
            plannedPlantingInput.dispatchEvent(new Event('change'));
        } else if (!isDirectSown) {
            // For pot-started, calculate expected transplant date
            const expectedTransplant = calculateExpectedTransplantDate(this.value, currentPlantData, false);
            if (expectedTransplant) {
                expectedTransplantInfo.style.display = 'block';
                document.getElementById('expectedTransplantDate').textContent = expectedTransplant.toLocaleDateString();
            } else {
                expectedTransplantInfo.style.display = 'none';
            }
        }

        // Update notifications
        const instanceKey = `${currentRow},${currentCol}`;
        const currentInstanceData = window.INSTANCE_MAP && window.INSTANCE_MAP[instanceKey] ? window.INSTANCE_MAP[instanceKey] : null;
        updateModalNotifications(currentInstanceData, currentPlantData, isDirectSown);
    });

    // Real-time calculation when actual seed started date changes
    seedStartedDateInput.addEventListener('change', function() {
        if (!currentPlantData) return;

        const isDirectSown = directSownCheck.checked;

        // For direct sown, auto-sync actual planted with actual seed started
        if (isDirectSown && this.value) {
            plantedDateInput.value = this.value;
            // Trigger planted date change to calculate harvest
            plantedDateInput.dispatchEvent(new Event('change'));
        } else if (!isDirectSown) {
            // For pot-started, calculate expected transplant date
            const expectedTransplant = calculateExpectedTransplantDate(this.value, currentPlantData, false);
            if (expectedTransplant) {
                expectedTransplantInfo.style.display = 'block';
                document.getElementById('expectedTransplantDate').textContent = expectedTransplant.toLocaleDateString();
            } else {
                expectedTransplantInfo.style.display = 'none';
            }
        }

        // Update notifications
        const instanceKey = `${currentRow},${currentCol}`;
        const currentInstanceData = window.INSTANCE_MAP && window.INSTANCE_MAP[instanceKey] ? window.INSTANCE_MAP[instanceKey] : null;
        updateModalNotifications(currentInstanceData, currentPlantData, isDirectSown);
    });

    // Real-time calculation when planned planting date changes
    plannedPlantingInput.addEventListener('change', function() {
        if (!currentPlantData) return;

        // Only calculate if no actual planted date (actual takes precedence)
        if (!plantedDateInput.value && this.value) {
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
        }

        // Update notifications
        const instanceKey = `${currentRow},${currentCol}`;
        const currentInstanceData = window.INSTANCE_MAP && window.INSTANCE_MAP[instanceKey] ? window.INSTANCE_MAP[instanceKey] : null;
        const isDirectSown = directSownCheck.checked;
        updateModalNotifications(currentInstanceData, currentPlantData, isDirectSown);
    });

    // Real-time calculation when actual planted date changes
    plantedDateInput.addEventListener('change', function() {
        if (!currentPlantData) return;

        // Actual planted date takes precedence over planned
        if (this.value) {
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
        } else {
            // If cleared, fall back to planned date if available
            if (plannedPlantingInput.value) {
                plannedPlantingInput.dispatchEvent(new Event('change'));
            } else {
                expectedHarvestInfo.style.display = 'none';
            }
        }

        // Update notifications
        const instanceKey = `${currentRow},${currentCol}`;
        const currentInstanceData = window.INSTANCE_MAP && window.INSTANCE_MAP[instanceKey] ? window.INSTANCE_MAP[instanceKey] : null;
        const isDirectSown = directSownCheck.checked;
        updateModalNotifications(currentInstanceData, currentPlantData, isDirectSown);
    });

    // Save dates
    saveDatesBtn.addEventListener('click', async function() {
        const btnManager = new ButtonStateManager(saveDatesBtn);
        btnManager.setLoading('Saving...');

        try {
            // Determine seed starting method
            const seedStartingMethod = directSownCheck.checked ? 'direct' : 'pot';

            // Save all planting dates and method if any are provided
            if (plannedSeedStartInput.value || seedStartedDateInput.value ||
                plannedPlantingInput.value || plantedDateInput.value) {
                const response = await fetch(`/gardens/${window.GARDEN_ID}/set-planting-date/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCSRFToken()
                    },
                    body: JSON.stringify({
                        row: currentRow,
                        col: currentCol,
                        seed_starting_method: seedStartingMethod,
                        planned_seed_start_date: plannedSeedStartInput.value || null,
                        planned_planting_date: plannedPlantingInput.value || null,
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
                    seed_starting_method: null,
                    planned_seed_start_date: null,
                    planned_planting_date: null,
                    seed_started_date: null,
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

    if (instance) {
        // Determine plant stage
        const isDirectSown = instance.seed_starting_method === 'direct';
        const hasSeedStarted = !!instance.seed_started_date;
        const hasPlanted = !!instance.planted_date;
        const hasHarvested = !!instance.actual_harvest_date;

        // Add harvest status class if available
        if (instance.harvest_status) {
            cell.classList.add(`harvest-${instance.harvest_status}`);
        }

        // Determine stage and create appropriate badge
        const badge = document.createElement('span');
        badge.className = 'date-badge';

        if (hasHarvested) {
            // Stage: Harvested
            badge.classList.add('ready');
            badge.textContent = 'Harvested';
            cell.appendChild(badge);
        } else if (hasPlanted) {
            // Stage: In ground growing - only show actionable harvest states
            if (instance.days_until_harvest !== null) {
                if (instance.harvest_status === 'ready') {
                    badge.classList.add('ready');
                    badge.textContent = 'Ready!';
                    cell.appendChild(badge);
                } else if (instance.harvest_status === 'soon') {
                    badge.classList.add('soon');
                    badge.textContent = `${instance.days_until_harvest}d`;
                    cell.appendChild(badge);
                } else if (instance.harvest_status === 'overdue') {
                    badge.classList.add('overdue');
                    badge.textContent = 'Overdue';
                    cell.appendChild(badge);
                }
                // For "growing" status, don't show badge to reduce clutter
            }
        } else if (!isDirectSown && hasSeedStarted) {
            // Stage: Seed started, awaiting transplant (pot-started only)
            badge.classList.add('seedling');
            badge.textContent = '🌱';
            badge.title = 'Seedling - ready for transplant';
            cell.appendChild(badge);
        }
        // No badge for: planned but not started, or direct sown not yet planted
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
