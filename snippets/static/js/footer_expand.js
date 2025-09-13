// Expands the footer when user scrolls to bottom, collapses otherwise
document.addEventListener('DOMContentLoaded', function () {
    var footer = document.querySelector('footer');
    if (!footer) return;

    function isPageScrollable() {
        return document.body.scrollHeight > window.innerHeight + 2;
    }

    function checkFooterExpand() {
        if (isPageScrollable()) {
            // If scrollable, respond to scroll position
            var scrollBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - 2;
            if (scrollBottom) {
                footer.classList.remove('footer-collapsed');
                footer.classList.add('footer-expanded');
            } else {
                footer.classList.remove('footer-expanded');
                footer.classList.add('footer-collapsed');
            }
        } else {
            // Not scrollable: always expanded
            footer.classList.remove('footer-collapsed');
            footer.classList.add('footer-expanded');
        }
    }

    checkFooterExpand();
    window.addEventListener('scroll', checkFooterExpand);
    window.addEventListener('resize', checkFooterExpand);
});