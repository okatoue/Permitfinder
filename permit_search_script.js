// Vancouver Permit Search Script
// Opens the permit search page, enters today's date in the Created Date From field, and clicks Search

(async function() {
    const PAGE_URL = 'https://plposweb.vancouver.ca/Public/Default.aspx?PossePresentation=PermitSearchByDate&IconName=form_yellow_search.png';

    // Format today's date as "Mon dd, yyyy" (e.g., "Feb 01, 2026")
    function getTodayFormatted() {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const today = new Date();
        const month = months[today.getMonth()];
        const day = String(today.getDate()).padStart(2, '0');
        const year = today.getFullYear();
        return `${month} ${day}, ${year}`;
    }

    // Find element by partial ID match
    function findElementByPartialId(partialId) {
        return document.querySelector(`[id*="${partialId}"]`);
    }

    // Main execution
    function run() {
        // Find the Created Date From field (first date field)
        const createdDateFromField = findElementByPartialId('CreatedDateFrom');

        if (!createdDateFromField) {
            console.error('Could not find Created Date From field');
            return;
        }

        // Clear the field and enter today's date
        const todayDate = getTodayFormatted();
        createdDateFromField.value = todayDate;

        // Trigger change event to ensure the form recognizes the input
        createdDateFromField.dispatchEvent(new Event('change', { bubbles: true }));
        createdDateFromField.dispatchEvent(new Event('input', { bubbles: true }));

        console.log(`Entered date: ${todayDate}`);

        // Find and click the Search button
        const searchButton = findElementByPartialId('PerformSearch');

        if (!searchButton) {
            console.error('Could not find Search button');
            return;
        }

        // Click the search button
        searchButton.click();
        console.log('Search button clicked');
    }

    // Check if we're already on the page
    if (window.location.href.includes('plposweb.vancouver.ca') &&
        window.location.href.includes('PermitSearchByDate')) {
        run();
    } else {
        // Navigate to the page first
        window.location.href = PAGE_URL;
        // Note: The script will need to be re-run after navigation
    }
})();
