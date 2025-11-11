/**
 * General form utilities for quest_ciq levels
 */

// Toast notification helper
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} shadow-lg fixed bottom-4 right-4 max-w-sm z-50 animate-fade-in`;
    toast.innerHTML = `
        <div>
            <span>${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Form validation helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;

    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('input-error');
            isValid = false;
        } else {
            field.classList.remove('input-error');
        }
    });

    return isValid;
}

// Confetti trigger on form success (called from template)
function triggerSuccessConfetti() {
    if (typeof confetti !== 'undefined') {
        confetti({
            particleCount: 150,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
}

// Character counter for textareas
document.addEventListener('DOMContentLoaded', function() {
    const textareas = document.querySelectorAll('textarea[maxlength]');

    textareas.forEach(textarea => {
        const maxLength = textarea.getAttribute('maxlength');
        const counterDiv = document.createElement('div');
        counterDiv.className = 'text-xs text-base-content/50 text-right mt-1';
        counterDiv.textContent = `0 / ${maxLength}`;

        textarea.parentElement.appendChild(counterDiv);

        textarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            counterDiv.textContent = `${currentLength} / ${maxLength}`;

            if (currentLength >= maxLength * 0.9) {
                counterDiv.classList.add('text-warning');
            } else {
                counterDiv.classList.remove('text-warning');
            }
        });
    });
});

// Auto-save to localStorage (optional feature)
function enableAutoSave(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    const inputs = form.querySelectorAll('input, textarea, select');

    // Load saved data
    inputs.forEach(input => {
        const savedValue = localStorage.getItem(`ciq_${formId}_${input.name}`);
        if (savedValue && !input.value) {
            input.value = savedValue;
        }
    });

    // Save on change
    inputs.forEach(input => {
        input.addEventListener('change', function() {
            localStorage.setItem(`ciq_${formId}_${this.name}`, this.value);
        });
    });

    // Clear on submit
    form.addEventListener('submit', function() {
        inputs.forEach(input => {
            localStorage.removeItem(`ciq_${formId}_${input.name}`);
        });
    });
}

// Enable auto-save for level forms
document.addEventListener('DOMContentLoaded', function() {
    const levelForm = document.getElementById('level-form');
    if (levelForm) {
        enableAutoSave('level-form');
    }
});
