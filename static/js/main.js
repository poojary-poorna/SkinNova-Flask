// SkinNova - Main JavaScript File

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize quiz functionality
    initializeQuizzes();
    
    // Initialize price comparison
    initializePriceComparison();
    
    // Initialize dermatologist finder
    initializeDermatologistFinder();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize animations
    initializeAnimations();
}

// Quiz Functionality
function initializeQuizzes() {
    const quizForms = document.querySelectorAll('.quiz-form');
    
    quizForms.forEach(form => {
        const options = form.querySelectorAll('.quiz-option');
        const checkboxes = form.querySelectorAll('input[type="checkbox"]');
        const radios = form.querySelectorAll('input[type="radio"]');
        
        // Handle quiz option selection
        options.forEach(option => {
            option.addEventListener('click', function() {
                const input = this.querySelector('input');
                if (input) {
                    if (input.type === 'radio') {
                        // Clear other selections in the same group
                        const groupName = input.name;
                        const otherOptions = form.querySelectorAll(`input[name="${groupName}"]`);
                        otherOptions.forEach(other => {
                            other.closest('.quiz-option').classList.remove('selected');
                        });
                        
                        // Select current option
                        input.checked = true;
                        this.classList.add('selected');
                    } else if (input.type === 'checkbox') {
                        // Toggle checkbox selection
                        input.checked = !input.checked;
                        this.classList.toggle('selected');
                    }
                }
            });
        });
        
        // Validate quiz before submission
        form.addEventListener('submit', function(e) {
            if (!validateQuiz(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateQuiz(form) {
    const requiredGroups = form.querySelectorAll('.quiz-question[data-required="true"]');
    let isValid = true;
    
    requiredGroups.forEach(question => {
        const inputs = question.querySelectorAll('input');
        let hasSelection = false;
        
        inputs.forEach(input => {
            if (input.checked) {
                hasSelection = true;
            }
        });
        
        if (!hasSelection) {
            isValid = false;
            question.classList.add('error');
            showError('Please answer all required questions.');
        } else {
            question.classList.remove('error');
        }
    });
    
    return isValid;
}

// Price Comparison
function initializePriceComparison() {
    const priceButtons = document.querySelectorAll('.compare-prices');
    
    priceButtons.forEach(button => {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            showPriceComparison(productId);
        });
    });
}

function showPriceComparison(productId) {
    showSpinner();
    
    fetch(`/price-compare/${productId}`)
        .then(response => response.json())
        .then(data => {
            hideSpinner();
            displayPriceComparison(data);
        })
        .catch(error => {
            hideSpinner();
            showError('Error loading price comparison');
            console.error('Error:', error);
        });
}

function displayPriceComparison(priceData) {
    const modal = createModal('Price Comparison');
    const content = modal.querySelector('.modal-content');
    
    let priceHTML = '<div class="price-comparison-modal">';
    
    Object.entries(priceData).forEach(([platform, data]) => {
        priceHTML += `
            <div class="price-item">
                <div class="platform-name">${platform.toUpperCase()}</div>
                <div class="platform-price">$${data.price}</div>
                <a href="${data.url}" target="_blank" class="btn btn-outline">View Product</a>
            </div>
        `;
    });
    
    priceHTML += '</div>';
    content.innerHTML += priceHTML;
    
    showModal(modal);
}

// Dermatologist Finder
function initializeDermatologistFinder() {
    const findButton = document.getElementById('find-dermatologists-btn');
    
    if (findButton) {
        findButton.addEventListener('click', function() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    findNearbyDermatologists,
                    handleLocationError
                );
            } else {
                showError('Geolocation is not supported by this browser.');
            }
        });
    }
}

function findNearbyDermatologists(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    
    showSpinner();
    
    fetch(`/api/dermatologists?lat=${lat}&lng=${lng}`)
        .then(response => response.json())
        .then(data => {
            hideSpinner();
            displayDermatologists(data);
        })
        .catch(error => {
            hideSpinner();
            showError('Error finding dermatologists');
            console.error('Error:', error);
        });
}

function displayDermatologists(dermatologists) {
    const container = document.getElementById('dermatologists-list');
    
    if (!container) return;
    
    container.innerHTML = '';
    
    dermatologists.forEach(derm => {
        const dermCard = document.createElement('div');
        dermCard.className = 'dermatologist-card';
        
        dermCard.innerHTML = `
            <div class="dermatologist-info">
                <h4>${derm.name}</h4>
                <p>${derm.address}</p>
                <p>${derm.phone}</p>
                <p class="distance">${derm.distance}</p>
            </div>
            <div class="dermatologist-rating">
                ${derm.rating} ★
            </div>
        `;
        
        container.appendChild(dermCard);
    });
}

function handleLocationError(error) {
    let message = 'An error occurred while retrieving your location.';
    
    switch (error.code) {
        case error.PERMISSION_DENIED:
            message = 'Location access denied by user.';
            break;
        case error.POSITION_UNAVAILABLE:
            message = 'Location information is unavailable.';
            break;
        case error.TIMEOUT:
            message = 'Location request timed out.';
            break;
    }
    
    showError(message);
}

// Form Validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateInput(this);
            });
            
            input.addEventListener('input', function() {
                clearValidationError(this);
            });
        });
    });
}

function validateInput(input) {
    const value = input.value.trim();
    let isValid = true;
    let message = '';
    
    // Required field validation
    if (input.hasAttribute('required') && !value) {
        isValid = false;
        message = 'This field is required.';
    }
    
    // Email validation
    if (input.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            message = 'Please enter a valid email address.';
        }
    }
    
    // Password validation
    if (input.type === 'password' && value) {
        if (value.length < 6) {
            isValid = false;
            message = 'Password must be at least 6 characters long.';
        }
    }
    
    // Confirm password validation
    if (input.name === 'confirm_password') {
        const passwordField = document.querySelector('input[name="password"]');
        if (passwordField && value !== passwordField.value) {
            isValid = false;
            message = 'Passwords do not match.';
        }
    }
    
    if (!isValid) {
        showInputError(input, message);
    } else {
        clearValidationError(input);
    }
    
    return isValid;
}

function showInputError(input, message) {
    clearValidationError(input);
    
    input.classList.add('error');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.textContent = message;
    
    input.parentNode.appendChild(errorDiv);
}

function clearValidationError(input) {
    input.classList.remove('error');
    
    const existingError = input.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

// Animations
function initializeAnimations() {
    // Fade in animations for cards
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    const animatedElements = document.querySelectorAll('.card, .product-card, .dashboard-card');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Utility Functions
function showSpinner() {
    let spinner = document.getElementById('global-spinner');
    if (!spinner) {
        spinner = document.createElement('div');
        spinner.id = 'global-spinner';
        spinner.className = 'spinner';
        document.body.appendChild(spinner);
    }
    spinner.style.display = 'block';
}

function hideSpinner() {
    const spinner = document.getElementById('global-spinner');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

function showError(message) {
    showAlert(message, 'error');
}

function showSuccess(message) {
    showAlert(message, 'success');
}

function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-toast');
    existingAlerts.forEach(alert => alert.remove());
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-toast`;
    alert.textContent = message;
    alert.style.position = 'fixed';
    alert.style.top = '100px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.style.maxWidth = '400px';
    alert.style.animation = 'slideIn 0.3s ease';
    
    document.body.appendChild(alert);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        alert.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 300);
    }, 5000);
}

function createModal(title) {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-backdrop"></div>
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${title}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body"></div>
            </div>
        </div>
    `;
    
    // Add modal close functionality
    modal.querySelector('.modal-close').addEventListener('click', () => {
        hideModal(modal);
    });
    
    modal.querySelector('.modal-backdrop').addEventListener('click', () => {
        hideModal(modal);
    });
    
    return modal;
}

function showModal(modal) {
    document.body.appendChild(modal);
    modal.style.display = 'flex';
    modal.style.alignItems = 'center';
    modal.style.justifyContent = 'center';
    modal.style.position = 'fixed';
    modal.style.top = '0';
    modal.style.left = '0';
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    modal.style.zIndex = '9999';
    
    // Animate in
    modal.style.opacity = '0';
    setTimeout(() => {
        modal.style.opacity = '1';
        modal.style.transition = 'opacity 0.3s ease';
    }, 10);
}

function hideModal(modal) {
    modal.style.opacity = '0';
    setTimeout(() => {
        if (modal.parentNode) {
            modal.remove();
        }
    }, 300);
}

// Color Analysis Helper
function updateColorPreview() {
    const questions = document.querySelectorAll('.color-question');
    const preview = document.getElementById('color-preview');
    
    if (!preview) return;
    
    let selectedColors = [];
    questions.forEach(question => {
        const selected = question.querySelector('input:checked');
        if (selected) {
            selectedColors.push(selected.value);
        }
    });
    
    // Update preview based on selections
    updateColorPalette(selectedColors);
}

function updateColorPalette(colors) {
    const palette = document.getElementById('color-preview');
    if (!palette) return;
    
    palette.innerHTML = '';
    colors.forEach(color => {
        const swatch = document.createElement('div');
        swatch.className = 'color-preview-swatch';
        swatch.style.backgroundColor = color;
        palette.appendChild(swatch);
    });
}

// Recommendation filters
function initializeFilters() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterType = this.dataset.filter;
            const products = document.querySelectorAll('.product-card');
            
            // Update active button
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Filter products
            products.forEach(product => {
                if (filterType === 'all' || product.dataset.category === filterType) {
                    product.style.display = 'block';
                } else {
                    product.style.display = 'none';
                }
            });
        });
    });
}

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('product-search');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const products = document.querySelectorAll('.product-card');
            
            products.forEach(product => {
                const title = product.querySelector('.product-title').textContent.toLowerCase();
                const brand = product.querySelector('.product-brand').textContent.toLowerCase();
                
                if (title.includes(query) || brand.includes(query)) {
                    product.style.display = 'block';
                } else {
                    product.style.display = 'none';
                }
            });
        });
    }
}

// Initialize additional features
document.addEventListener('DOMContentLoaded', function() {
    initializeFilters();
    initializeSearch();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .field-error {
        color: var(--error);
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    
    .form-control.error {
        border-color: var(--error);
        box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.1);
    }
    
    .quiz-question.error {
        border-left: 4px solid var(--error);
        background: rgba(244, 67, 54, 0.05);
    }
    
    .modal-dialog {
        background: white;
        border-radius: var(--border-radius);
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #eee;
    }
    
    .modal-close {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0;
        width: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .modal-body {
        padding: 1.5rem;
    }
    
    .price-comparison-modal {
        display: grid;
        gap: 1rem;
    }
    
    .price-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        border: 1px solid #eee;
        border-radius: 8px;
    }
    
    .platform-name {
        font-weight: 600;
    }
    
    .platform-price {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--success);
    }
`;

document.head.appendChild(style);