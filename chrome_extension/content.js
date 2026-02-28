chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'extract') {
        try {
            // Clone the document to avoid modifying the actual page DOM when Readability runs
            const documentClone = document.cloneNode(true);

            const reader = new Readability(documentClone);
            const article = reader.parse();

            if (article) {
                sendResponse({
                    success: true,
                    title: article.title,
                    content: article.content, // This is a clean HTML string
                    textContent: article.textContent,
                    byline: article.byline,
                    url: window.location.href,
                    siteName: article.siteName
                });
            } else {
                sendResponse({
                    success: false,
                    error: 'Readability.js failed to extract article content. Ensure this is an article page.'
                });
            }
        } catch (e) {
            sendResponse({ success: false, error: e.toString() });
        }
    }
    return true; // Keeps the message channel open for async responses
});
