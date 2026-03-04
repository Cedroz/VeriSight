/**
 * VeriSight Popup Script
 */

document.addEventListener('DOMContentLoaded', async () => {
    const statusDiv = document.getElementById('status');
    const checkBtn = document.getElementById('checkNow');
    const unblockBtn = document.getElementById('unblockInputs');
    
    // Get current tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Check current page status
    checkCurrentPage(tab.url);
    
    checkBtn.addEventListener('click', () => {
        checkCurrentPage(tab.url);
    });
    
    // Handle unblock button
    unblockBtn.addEventListener('click', async () => {
        if (confirm('Are you absolutely sure? This site has been flagged as dangerous. Unblock inputs at your own risk.')) {
            try {
                // Get current tab again (might have changed)
                const [currentTab] = await chrome.tabs.query({ active: true, currentWindow: true });
                
                // Send message to content script to unblock inputs
                const response = await new Promise((resolve, reject) => {
                    chrome.tabs.sendMessage(currentTab.id, { action: 'unblock' }, (response) => {
                        if (chrome.runtime.lastError) {
                            reject(new Error(chrome.runtime.lastError.message));
                        } else {
                            resolve(response);
                        }
                    });
                });
                
                statusDiv.className = 'status warning';
                statusDiv.innerHTML = `
                    <p>Inputs Unblocked</p>
                    <p style="font-size: 11px; margin-top: 5px;">Proceeding at your own risk</p>
                `;
                unblockBtn.style.display = 'none';
            } catch (error) {
                console.error('Error unblocking inputs:', error);
                // Try alternative: inject script to unblock
                try {
                    const [currentTab] = await chrome.tabs.query({ active: true, currentWindow: true });
                    await chrome.scripting.executeScript({
                        target: { tabId: currentTab.id },
                        func: () => {
                            // Call unblock function directly if it exists in page context
                            const inputs = document.querySelectorAll('.verisight-blocked');
                            inputs.forEach(input => {
                                input.removeAttribute('readonly');
                                input.removeAttribute('disabled');
                                input.removeAttribute('tabindex');
                                input.classList.remove('verisight-blocked');
                                input.style.cursor = '';
                                input.style.opacity = '';
                                input.style.backgroundColor = '';
                                const wrapper = input.parentNode;
                                if (wrapper) {
                                    const lockOverlay = wrapper.querySelector('.verisight-lock-overlay');
                                    if (lockOverlay) {
                                        const grandParent = wrapper.parentNode;
                                        if (grandParent) {
                                            grandParent.insertBefore(input, wrapper);
                                            wrapper.remove();
                                        }
                                    }
                                }
                            });
                            window.isBlocked = false;
                        }
                    });
                    statusDiv.className = 'status warning';
                    statusDiv.innerHTML = `
                        <p>Inputs Unblocked</p>
                        <p style="font-size: 11px; margin-top: 5px;">Proceeding at your own risk</p>
                    `;
                    unblockBtn.style.display = 'none';
                } catch (injectError) {
                    console.error('Failed to inject unblock script:', injectError);
                    alert('Could not unblock inputs. Try reloading the page or use the Emergency Override button on the page itself.');
                }
            }
        }
    });
});

async function checkCurrentPage(url) {
    const statusDiv = document.getElementById('status');
    statusDiv.className = 'status';
    statusDiv.innerHTML = '<p>Checking...</p>';
    
    try {
        // chrome.runtime.sendMessage returns a promise in Manifest V3
        const response = await new Promise((resolve, reject) => {
            chrome.runtime.sendMessage({
                action: 'checkScam',
                url: url
            }, (response) => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                } else {
                    resolve(response);
                }
            });
        });
        
        // Check if response is valid
        if (!response) {
            statusDiv.className = 'status warning';
            statusDiv.innerHTML = `<p>No response from extension</p><p style="font-size: 12px;">Check if backend is running on localhost:8001</p>`;
            return;
        }
        
        if (response.error) {
            statusDiv.className = 'status warning';
            statusDiv.innerHTML = `<p>Unable to check</p><p style="font-size: 12px;">${response.error}</p>`;
            return;
        }
        
        const unblockBtn = document.getElementById('unblockInputs');
        
        if (response.is_scam) {
            statusDiv.className = 'status danger';
            statusDiv.innerHTML = `
                <p>DANGER DETECTED</p>
                <p style="font-size: 12px; margin-top: 10px;">Score: ${response.score}/100</p>
                <p style="font-size: 11px; margin-top: 5px;">Input fields have been blocked</p>
            `;
            // Show unblock button if site is flagged
            if (unblockBtn) unblockBtn.style.display = 'block';
        } else if (response.score !== undefined) {
            statusDiv.className = 'status safe';
            statusDiv.innerHTML = `
                <p>Site Appears Safe</p>
                <p style="font-size: 12px; margin-top: 10px;">Score: ${response.score}/100</p>
            `;
            // Hide unblock button for safe sites
            if (unblockBtn) unblockBtn.style.display = 'none';
        } else {
            statusDiv.className = 'status warning';
            statusDiv.innerHTML = `<p>Unexpected response</p><p style="font-size: 12px;">${JSON.stringify(response)}</p>`;
        }
    } catch (error) {
        statusDiv.className = 'status warning';
        statusDiv.innerHTML = `<p>Check Failed</p><p style="font-size: 12px;">${error.message}</p>`;
    }
}
