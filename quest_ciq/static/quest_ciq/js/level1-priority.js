/**
 * Level 1 Priority Selection Logic
 * Dynamically populates priority dropdown based on selected pain points
 */

document.addEventListener('DOMContentLoaded', function() {
    const presetCheckboxes = document.querySelectorAll('.pain-point-checkbox');
    const customInputs = [
        document.querySelector('input[name="custom_pain_1"]'),
        document.querySelector('input[name="custom_pain_2"]'),
        document.querySelector('input[name="custom_pain_3"]')
    ];
    const topPrioritySelect = document.getElementById('id_top_priority');
    const chipsContainer = document.getElementById('pain-points-chips');

    function getAllSelectedPainPoints() {
        const points = [];

        // Get checked presets (exact text match)
        presetCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const label = checkbox.parentElement.querySelector('.label-text').textContent.trim();
                points.push(label);
            }
        });

        // Get custom entries (exact text, no trimming)
        customInputs.forEach(input => {
            const value = input.value.trim();
            if (value) {
                points.push(value);
            }
        });

        return points;
    }

    function updatePriorityDropdown() {
        const painPoints = getAllSelectedPainPoints();
        const currentTop = topPrioritySelect.value;

        // Update top priority dropdown with exact string values
        topPrioritySelect.innerHTML = '<option value="">-- Select your TOP pain point --</option>';
        painPoints.forEach(point => {
            const option = document.createElement('option');
            option.value = point;  // Use exact string value
            option.textContent = point;
            if (point === currentTop) {
                option.selected = true;
            }
            topPrioritySelect.appendChild(option);
        });

        // Update chips display
        updateChipsDisplay(painPoints);
    }

    function updateChipsDisplay(painPoints) {
        chipsContainer.innerHTML = '';

        if (painPoints.length === 0) {
            chipsContainer.innerHTML = '<span class="text-sm text-base-content/50">Select pain points above to see them here...</span>';
            return;
        }

        painPoints.forEach(point => {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.textContent = point;
            chipsContainer.appendChild(chip);
        });

        // Add count badge
        const badge = document.createElement('span');
        badge.className = 'badge badge-primary badge-lg';
        badge.textContent = `${painPoints.length} selected`;
        chipsContainer.appendChild(badge);
    }

    // Listen for changes
    presetCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updatePriorityDropdown);
    });

    customInputs.forEach(input => {
        input.addEventListener('input', updatePriorityDropdown);
    });

    // Initial population
    updatePriorityDropdown();
});
