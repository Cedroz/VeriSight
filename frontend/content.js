/**
 * VeriSight Content Script
 * Blocks input fields on suspicious websites
 */

const API_URL = 'http://localhost:8001/api/check-scam';
let isBlocked = false;
let scamScore = 0;
let reasons = [];
let mutationObserver = null; // Store observer so we can stop it

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

async function init() {
    const url = window.location.href;
    console.log('[VeriSight] Analyzing page...', url);
    
    // Show loading indicator immediately
    showLoadingIndicator();
    
    // Capture screenshot and send to backend
    try {
        // Request screenshot from background script
        chrome.runtime.sendMessage({ action: 'checkScam', url }, async (response) => {
            // Remove loading indicator on any response/error
            const loadingIndicator = document.getElementById('verisight-loading-indicator');
            if (loadingIndicator) loadingIndicator.remove();
            
            if (chrome.runtime.lastError) {
                console.error('[VeriSight] Extension Error:', chrome.runtime.lastError.message);
                console.error('[VeriSight] Make sure extension is properly loaded and backend is running on http://localhost:8001');
                showErrorIndicator(chrome.runtime.lastError.message);
                return;
            }
            
            if (!response) {
                console.error('[VeriSight] No response from background script');
                showErrorIndicator('No response from extension');
                return;
            }
            
            if (response.error) {
                console.error('[VeriSight] Backend Error:', response.error);
                showErrorIndicator(response.error);
                return;
            }
            
            // Log full response for debugging
            console.log('[VeriSight] Full response object:', response);
            console.log('[VeriSight] Response details:', {
                score: response.score,
                is_scam: response.is_scam,
                domain: response.domain,
                recommendation: response.recommendation,
                reasons: response.reasons
            });
            
            // Check both is_scam flag and score threshold
            const shouldBlock = response.is_scam === true || (response.score >= 80);
            
            if (shouldBlock) {
                scamScore = response.score;
                reasons = response.reasons || [];
                console.log('[VeriSight] SITE FLAGGED AS SCAM! Score:', response.score, 'Blocking inputs...');
                blockInputs();
                showWarningOverlay(response);
            } else if (response) {
                console.log('[VeriSight] Site appears safe. Score:', response.score);
                showSafeIndicator();
            } else {
                console.warn('[VeriSight] Unexpected response format:', response);
            }
        });
    } catch (error) {
        console.error('[VeriSight] Error checking scam:', error);
        showErrorIndicator(error.message);
    }
}

function blockInputs() {
    if (isBlocked) return;
    isBlocked = true;
    
    // Find all input fields - more comprehensive selector
    const inputSelectors = [
        'input[type="text"]',
        'input[type="password"]',
        'input[type="email"]',
        'input[type="tel"]',
        'input[type="number"]',
        'input[name*="card"]',
        'input[name*="cc"]',
        'input[name*="cvv"]',
        'input[name*="ssn"]',
        'textarea',
        'input:not([type="button"]):not([type="submit"]):not([type="reset"]):not([type="checkbox"]):not([type="radio"])'
    ].join(', ');
    
    const inputs = document.querySelectorAll(inputSelectors);
    
    console.log(`[VeriSight] Found ${inputs.length} input fields to block`);
    
    inputs.forEach((input, index) => {
        // Skip if already blocked
        if (input.classList.contains('verisight-blocked')) {
            return;
        }
        
        // Store original value to restore
        const originalValue = input.value;
        
        // Make input readonly and disabled
        input.setAttribute('readonly', 'true');
        input.setAttribute('disabled', 'true');
        input.setAttribute('tabindex', '-1'); // Prevent tab focus
        input.classList.add('verisight-blocked');
        
        // Add visual styling
        input.style.position = 'relative';
        input.style.cursor = 'not-allowed';
        input.style.opacity = '0.6';
        input.style.backgroundColor = '#ffebee';
        // Don't use pointer-events: none - it prevents event listeners from working
        
        // Create padlock overlay
        const lockOverlay = document.createElement('div');
        lockOverlay.className = 'verisight-lock-overlay';
        lockOverlay.innerHTML = 'LOCKED';
        lockOverlay.title = 'VeriSight has blocked this field - Site flagged as suspicious';
        lockOverlay.style.cssText = `
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 18px;
            pointer-events: none;
            z-index: 1000;
        `;
        
        // Wrap input for positioning
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.style.width = '100%';
        wrapper.style.display = 'inline-block';
        
        if (input.parentNode) {
            const parent = input.parentNode;
            parent.insertBefore(wrapper, input);
            wrapper.appendChild(input);
            wrapper.appendChild(lockOverlay);
        }
        
        // Aggressive blocking - prevent ALL input methods
        const blockEvent = (e) => {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            input.value = originalValue; // Reset to original value
            input.blur(); // Remove focus
            return false;
        };
        
        // Block all possible input events in capture phase
        const eventTypes = ['keydown', 'keypress', 'keyup', 'input', 'beforeinput', 'paste', 'cut', 'focus', 'click', 'mousedown', 'mouseup', 'touchstart', 'touchend'];
        eventTypes.forEach(eventType => {
            input.addEventListener(eventType, blockEvent, true); // Capture phase = true
            input.addEventListener(eventType, blockEvent, false); // Also bubble phase
        });
        
        // Override value setter
        const inputProto = Object.getPrototypeOf(input);
        const originalValueSetter = Object.getOwnPropertyDescriptor(inputProto, 'value')?.set;
        if (originalValueSetter) {
            Object.defineProperty(input, 'value', {
                set: function(newValue) {
                    if (!this.classList.contains('verisight-blocked')) {
                        originalValueSetter.call(this, newValue);
                    }
                },
                get: function() {
                    return originalValue;
                },
                configurable: true
            });
        }
        
        // Watch for value changes and reset
        const valueObserver = new MutationObserver(() => {
            if (input.value !== originalValue) {
                input.value = originalValue;
            }
        });
        
        const inputObserver = new MutationObserver(() => {
            if (input.value !== originalValue) {
                input.value = originalValue;
            }
        });
        
        valueObserver.observe(input, { attributes: true, attributeFilter: ['value'] });
        inputObserver.observe(input, { childList: true, subtree: true, characterData: true });
        
        // Also prevent autofill/autocomplete
        input.setAttribute('autocomplete', 'off');
        input.setAttribute('autocapitalize', 'off');
        input.setAttribute('autocorrect', 'off');
    });
    
    // Also watch for dynamically added inputs (only if we're still blocking)
    mutationObserver = new MutationObserver((mutations) => {
        // Don't block if we're not in blocking mode anymore
        if (!isBlocked) {
            return;
        }
        
        const newInputs = document.querySelectorAll(inputSelectors + ':not(.verisight-blocked)');
        if (newInputs.length > 0) {
            console.log(`[VeriSight] Found ${newInputs.length} new inputs, blocking...`);
            // Re-run blocking on new inputs (but skip the observer check to avoid recursion)
            blockInputsDirect(newInputs);
        }
    });
    
    mutationObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log(`[VeriSight] Blocked ${inputs.length} input fields`);
}

// Helper function to block specific inputs without recursion
function blockInputsDirect(inputs) {
    inputs.forEach(input => {
        if (input.classList.contains('verisight-blocked')) return;
        
        input.setAttribute('readonly', 'true');
        input.setAttribute('disabled', 'true');
        input.setAttribute('tabindex', '-1');
        input.classList.add('verisight-blocked');
        input.style.cursor = 'not-allowed';
        input.style.opacity = '0.6';
        input.style.backgroundColor = '#ffebee';
        
        const blockEvent = (e) => {
            e.preventDefault();
            e.stopPropagation();
            input.blur();
            return false;
        };
        
        ['keydown', 'keypress', 'input', 'paste', 'focus'].forEach(eventType => {
            input.addEventListener(eventType, blockEvent, true);
        });
    });
}

function showWarningOverlay(response) {
    // Remove existing overlay if any
    const existing = document.getElementById('verisight-overlay');
    if (existing) existing.remove();
    
    const overlay = document.createElement('div');
    overlay.id = 'verisight-overlay';
    overlay.innerHTML = `
        <div class="verisight-warning-content">
            <div class="verisight-header">
                <h1>VERISIGHT SAFETY LOCK ENGAGED</h1>
            </div>
            <div class="verisight-body">
                <p class="verisight-score">SCAM SCORE: ${response.score}/100</p>
                <p class="verisight-message">You are attempting to enter sensitive information on a website that has been flagged as suspicious.</p>
                <div class="verisight-reasons">
                    <h3>Why this site was flagged:</h3>
                    <ul>
                        ${response.reasons.map(r => `<li>${r}</li>`).join('')}
                    </ul>
                </div>
                <div class="verisight-details">
                    <p><strong>Domain:</strong> ${response.domain}</p>
                    ${response.domain_age_days !== null ? `<p><strong>Domain Age:</strong> ${response.domain_age_days} days</p>` : ''}
                    ${response.detected_brand ? `<p><strong>Detected Brand:</strong> ${response.detected_brand}</p>` : ''}
                </div>
                <div class="verisight-actions">
                    <button id="verisight-override" class="verisight-override-btn">Emergency Override (Not Recommended)</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(overlay);
    
    // Handle override button
    document.getElementById('verisight-override').addEventListener('click', () => {
        if (confirm('This will dismiss the warning overlay, but inputs will remain blocked for your protection. To unblock inputs, use the VeriSight extension popup. Continue?')) {
            // Just close the overlay, but keep inputs blocked
            overlay.remove();
            console.log('[VeriSight] Warning overlay dismissed. Inputs remain blocked. Use extension popup to unblock.');
            
            // Show a small indicator that inputs are still blocked
            const reminder = document.createElement('div');
            reminder.id = 'verisight-override-reminder';
            reminder.innerHTML = 'Inputs still blocked. Use VeriSight extension popup to unblock.';
            reminder.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                background: #ff9800;
                color: white;
                padding: 10px 15px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 999997;
                font-family: Arial, sans-serif;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                max-width: 300px;
                animation: verisight-pulse 2s ease-in-out infinite;
            `;
            document.body.appendChild(reminder);
            
            // Remove reminder after 5 seconds
            setTimeout(() => reminder.remove(), 5000);
        }
    });
}

function showLoadingIndicator() {
    // Remove any existing indicators first
    const existing = document.getElementById('verisight-loading-indicator');
    if (existing) existing.remove();
    
    const indicator = document.createElement('div');
    indicator.id = 'verisight-loading-indicator';
    indicator.innerHTML = 'VeriSight: Checking site...';
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: #2196F3;
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 999999;
        font-family: Arial, sans-serif;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        animation: verisight-pulse 1.5s ease-in-out infinite;
    `;
    document.body.appendChild(indicator);
}

function showSafeIndicator() {
    // Remove loading indicator first
    const loading = document.getElementById('verisight-loading-indicator');
    if (loading) loading.remove();
    
    // Optional: Show a small green indicator for safe sites
    const indicator = document.createElement('div');
    indicator.id = 'verisight-safe-indicator';
    indicator.innerHTML = '✓ VeriSight: Site appears safe';
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: #4CAF50;
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 999999;
        font-family: Arial, sans-serif;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    `;
    document.body.appendChild(indicator);
    
    // Remove after 5 seconds
    setTimeout(() => indicator.remove(), 5000);
}

function showErrorIndicator(errorMsg) {
    // Show error indicator if extension/backend has issues
    const indicator = document.createElement('div');
    indicator.id = 'verisight-error-indicator';
    indicator.innerHTML = `VeriSight: ${errorMsg || 'Error connecting to backend'}`;
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: #ff9800;
        color: white;
        padding: 8px 12px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 999999;
        font-family: Arial, sans-serif;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        max-width: 300px;
    `;
    document.body.appendChild(indicator);
    
    // Remove after 10 seconds
    setTimeout(() => indicator.remove(), 10000);
}

function unblockInputs() {
    // Stop the mutation observer to prevent re-blocking
    if (mutationObserver) {
        mutationObserver.disconnect();
        mutationObserver = null;
        console.log('[VeriSight] MutationObserver stopped');
    }
    
    isBlocked = false;
    const inputs = document.querySelectorAll('.verisight-blocked');
    
    console.log(`[VeriSight] Unblocking ${inputs.length} input fields (Emergency Override)`);
    
    inputs.forEach(input => {
        // Store current value before cloning
        const currentValue = input.value;
        const currentName = input.name;
        const currentId = input.id;
        const currentType = input.type;
        const currentPlaceholder = input.placeholder;
        
        // Remove readonly/disabled attributes
        input.removeAttribute('readonly');
        input.removeAttribute('disabled');
        input.removeAttribute('tabindex');
        input.classList.remove('verisight-blocked');
        
        // Remove visual styling
        input.style.cursor = '';
        input.style.opacity = '';
        input.style.backgroundColor = '';
        input.style.position = '';
        
        // Clone the input FIRST to remove all event listeners
        // This is the most reliable way to remove all event handlers
        const clonedInput = input.cloneNode(true);
        
        // Restore all attributes and properties
        clonedInput.value = currentValue;
        if (currentName) clonedInput.name = currentName;
        if (currentId) clonedInput.id = currentId;
        clonedInput.type = currentType;
        if (currentPlaceholder) clonedInput.placeholder = currentPlaceholder;
        if (input.required !== undefined) clonedInput.required = input.required;
        
        // Remove blocking attributes
        clonedInput.removeAttribute('autocomplete');
        clonedInput.removeAttribute('autocapitalize');
        clonedInput.removeAttribute('autocorrect');
        
        // Replace the original input with the clean clone
        const wrapper = input.parentNode;
        if (wrapper) {
            wrapper.replaceChild(clonedInput, input);
            
            // Now check if wrapper is one we created and unwrap it
            const lockOverlay = wrapper.querySelector('.verisight-lock-overlay');
            if (lockOverlay || (wrapper.style.position === 'relative' && wrapper.style.width === '100%')) {
                // This is our wrapper - unwrap it
                const grandParent = wrapper.parentNode;
                if (grandParent) {
                    grandParent.insertBefore(clonedInput, wrapper);
                    wrapper.remove();
                }
            }
        } else if (input.parentNode) {
            input.parentNode.replaceChild(clonedInput, input);
        }
        
        // Make sure the cloned input is fully functional
        // Test that it can receive focus and input
        setTimeout(() => {
            clonedInput.focus();
            setTimeout(() => clonedInput.blur(), 10);
        }, 10);
    });
    
    // Show notification that override was used
    const overrideIndicator = document.createElement('div');
    overrideIndicator.innerHTML = 'VeriSight Override Active - Inputs Unblocked (You are proceeding at your own risk)';
    overrideIndicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: #ff9800;
        color: white;
        padding: 10px 15px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 999998;
        font-family: Arial, sans-serif;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        max-width: 300px;
        animation: verisight-pulse 2s ease-in-out infinite;
    `;
    document.body.appendChild(overrideIndicator);
    
    // Remove indicator after 5 seconds
    setTimeout(() => overrideIndicator.remove(), 5000);
    
    console.log('[VeriSight] Inputs have been unblocked (Emergency Override)');
}

// Listen for messages from background script and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'unblock') {
        // Unblock inputs
        unblockInputs();
        
        // Send response synchronously if possible
        try {
            sendResponse({ success: true, message: 'Inputs unblocked' });
        } catch (e) {
            // If sendResponse fails (channel closed), ignore - this is OK
            console.log('[VeriSight] Response already sent or channel closed');
        }
        
        // Return true to indicate we will send response asynchronously
        return true;
    }
    
    // Return false if we don't handle the message
    return false;
});
