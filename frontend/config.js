/**
 * VeriSight Extension Configuration
 * Configure API URL for production deployment
 */

// Default API URL (for development)
const DEFAULT_API_URL = 'http://localhost:8001/api/check-scam';

// Get API URL from storage or use default
async function getApiUrl() {
    return new Promise((resolve) => {
        chrome.storage.sync.get(['apiUrl'], (result) => {
            const apiUrl = result.apiUrl || DEFAULT_API_URL;
            resolve(apiUrl);
        });
    });
}

// Set API URL in storage
async function setApiUrl(url) {
    return new Promise((resolve) => {
        chrome.storage.sync.set({ apiUrl: url }, () => {
            resolve();
        });
    });
}

// Export for use in background.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getApiUrl, setApiUrl, DEFAULT_API_URL };
}
