document.addEventListener('DOMContentLoaded', () => {
    const extractBtn = document.getElementById('extractBtn');
    const statusDiv = document.getElementById('status');
    const settingsLink = document.getElementById('settings-link');

    settingsLink.addEventListener('click', () => {
        if (chrome.runtime.openOptionsPage) {
            chrome.runtime.openOptionsPage();
        } else {
            window.open(chrome.runtime.getURL('options.html'));
        }
    });

    extractBtn.addEventListener('click', async () => {
        extractBtn.disabled = true;
        statusDiv.textContent = 'Extracting text...';
        statusDiv.className = '';

        try {
            // Get current active tab
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            if (!tab) throw new Error("No active tab found");

            // Send message to the content script
            chrome.tabs.sendMessage(tab.id, { action: 'extract' }, async (response) => {
                if (chrome.runtime.lastError) {
                    statusDiv.textContent = "Error: Cannot run on this page. Wait for page load or try another site.";
                    statusDiv.className = 'error';
                    extractBtn.disabled = false;
                    return;
                }

                if (!response || !response.success) {
                    statusDiv.textContent = `Extraction failed: ${response?.error || 'Unknown error'}`;
                    statusDiv.className = 'error';
                    extractBtn.disabled = false;
                    return;
                }

                statusDiv.textContent = 'Saving to Lingua Workbench...';

                // Fetch extension settings to get API URL and Token
                chrome.storage.sync.get({ apiUrl: 'http://127.0.0.1:8000', apiToken: '' }, async (settings) => {
                    let endpoint = `${settings.apiUrl}/api/v1/articles/`;
                    let headers = {
                        'Content-Type': 'application/json'
                    };

                    if (settings.apiToken) {
                        headers['Authorization'] = `Token ${settings.apiToken}`;
                    }

                    try {
                        const res = await fetch(endpoint, {
                            method: 'POST',
                            headers: headers,
                            // If apiToken is empty, assume cookie auth (include credentials)
                            credentials: settings.apiToken ? 'omit' : 'include',
                            body: JSON.stringify({
                                url: response.url,
                                title: response.title,
                                raw_html: response.content, // extracted clean HTML
                                raw_text: response.textContent,
                                author: response.byline || '',
                                site_name: response.siteName || ''
                            })
                        });

                        if (!res.ok) {
                            const errText = await res.text();
                            throw new Error(`HTTP ${res.status}: ${errText.substring(0, 80)}...`);
                        }

                        const data = await res.json();
                        statusDiv.textContent = 'Successfully saved!';
                        statusDiv.className = 'success';

                        // Optionally close popup after successful save
                        setTimeout(() => window.close(), 1500);

                    } catch (fetchErr) {
                        statusDiv.textContent = `Backend Error: ${fetchErr.message}`;
                        statusDiv.className = 'error';
                        extractBtn.disabled = false;
                        console.error('Fetch error:', fetchErr);
                    }
                });
            });
        } catch (err) {
            statusDiv.textContent = `Error: ${err.message}`;
            statusDiv.className = 'error';
            extractBtn.disabled = false;
        }
    });
});
