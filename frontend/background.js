/**
 * VeriSight Background Service Worker
 * Handles API communication and screenshot capture
 */

// Get API URL from config or storage
let API_URL = 'http://localhost:8001/api/check-scam'; // Default for development

// Load API URL from storage on startup
chrome.storage.sync.get(['apiUrl'], (result) => {
    if (result.apiUrl) {
        API_URL = result.apiUrl;
        console.log('[VeriSight] Using API URL from storage:', API_URL);
    } else {
        console.log('[VeriSight] Using default API URL:', API_URL);
    }
});

// Listen for API URL updates
chrome.storage.onChanged.addListener((changes) => {
    if (changes.apiUrl) {
        API_URL = changes.apiUrl.newValue;
        console.log('[VeriSight] API URL updated:', API_URL);
    }
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'checkScam') {
        // Defensive check: sender might be undefined in some contexts
        // sender.tab might be undefined if message comes from popup or other context
        const tabId = (sender && sender.tab && sender.tab.id) ? sender.tab.id : null;
        
        // Make sure we have a URL
        if (!request.url) {
            console.error('[VeriSight] No URL provided in request');
            sendResponse({ error: 'No URL provided' });
            return true;
        }
        
        checkScam(request.url, tabId)
            .then(response => sendResponse(response))
            .catch(error => {
                console.error('[VeriSight] Error:', error);
                sendResponse({ error: error.message });
            });
        return true; // Keep channel open for async response
    }
    
    // Return false if we don't handle the message
    return false;
});

async function checkScam(url, tabId) {
    try {
        console.log('[VeriSight Background] Starting check for URL:', url);
        
        // Capture screenshot - try different methods based on available permissions
        let screenshotDataUrl;
        try {
            // Method 1: Try captureVisibleTab (requires activeTab permission)
            if (tabId === null) {
                // If no tab ID, try to get active tab first
                const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
                if (tabs.length > 0) {
                    tabId = tabs[0].id;
                }
            }
            
            if (tabId !== null) {
                // Method 2: Use specific tab ID (might require tabs permission)
                try {
                    screenshotDataUrl = await chrome.tabs.captureVisibleTab(null, {
                        format: 'png',
                        quality: 100
                    });
                } catch (e) {
                    // Fallback: Try with explicit window ID
                    const window = await chrome.windows.getCurrent();
                    screenshotDataUrl = await chrome.tabs.captureVisibleTab(window.id, {
                        format: 'png',
                        quality: 100
                    });
                }
            } else {
                // Fallback: Try without tab ID
                screenshotDataUrl = await chrome.tabs.captureVisibleTab(null, {
                    format: 'png',
                    quality: 100
                });
            }
        } catch (captureError) {
            // Screenshot capture might fail due to permissions or context
            // This is OK - backend can still detect scams based on URL alone
            console.warn('[VeriSight Background] Screenshot capture not available (this is OK):', captureError.message);
            // Continue without screenshot - backend can still check based on URL
            screenshotDataUrl = null;
        }
        
        if (!screenshotDataUrl) {
            console.warn('[VeriSight Background] No screenshot available, sending URL only');
        } else {
            console.log('[VeriSight Background] Screenshot captured, length:', screenshotDataUrl.length);
        }
        
        // Prepare request body
        const requestBody = {
            url: url
        };
        
        // Add screenshot if available
        if (screenshotDataUrl) {
            const base64Data = screenshotDataUrl.split(',')[1];
            requestBody.screenshot_base64 = base64Data;
        }
        
        console.log('[VeriSight Background] Sending request to:', API_URL);
        
        // Send to backend API
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('[VeriSight Background] API response status:', response.status, response.statusText);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('[VeriSight Background] API error response:', errorText);
            throw new Error(`API error: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        console.log('[VeriSight Background] API response received:', result);
        return result;
        
    } catch (error) {
        console.error('[VeriSight] Error checking scam:', error);
        console.error('[VeriSight] Error details:', error.message, error.stack);
        // Return safe default if API is unavailable
        const fallback = {
            score: 0,
            is_scam: false,
            reasons: ['API check failed - allowing access'],
            recommendation: 'ALLOW',
            domain: new URL(url).hostname
        };
        console.warn('[VeriSight] Returning fallback response:', fallback);
        return fallback;
    }
}

// Listen for tab updates to check new pages
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        // Page loaded, content script will handle the check
        console.log('[VeriSight] Tab updated:', tab.url);
    }
});
