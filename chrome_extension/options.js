document.addEventListener('DOMContentLoaded', () => {
    // Restore options
    chrome.storage.sync.get(['apiUrl', 'apiToken'], (items) => {
        if (items.apiUrl) document.getElementById('apiUrl').value = items.apiUrl;
        if (items.apiToken) document.getElementById('apiToken').value = items.apiToken;
    });

    // Save options
    document.getElementById('saveBtn').addEventListener('click', () => {
        const apiUrl = document.getElementById('apiUrl').value.replace(/\/$/, ''); // Remove trailing slash
        const apiToken = document.getElementById('apiToken').value;

        chrome.storage.sync.set({ apiUrl, apiToken }, () => {
            const status = document.getElementById('status');
            status.textContent = 'Settings saved.';
            setTimeout(() => { status.textContent = ''; }, 2000);
        });
    });
});
