
        document.body.addEventListener('htmx:configRequest', function () {
            document.getElementById('global-loader').style.display = 'flex';
        });
        document.body.addEventListener('htmx:afterSwap', function () {
            document.getElementById('global-loader').style.display = 'none';
        });
        document.body.addEventListener('htmx:responseError', function () {
            document.getElementById('global-loader').style.display = 'none';
        });

        function hideLoaderWhenImagesLoaded(containerSelector) {
    var loader = document.getElementById('global-loader');
    var container = document.querySelector(containerSelector);
    if (!container) return;
    var images = container.querySelectorAll('img');
    if (images.length === 0) {
        hideLoaderWithFade();
        return;
    }
    let loaded = 0;
    images.forEach(function(img) {
        if (img.complete) loaded++;
        else img.addEventListener('load', function() {
            loaded++;
            if (loaded === images.length) hideLoaderWithFade();
        });
    });
    if (loaded === images.length) hideLoaderWithFade();
}

// In your HTMX afterSwap handler:
document.body.addEventListener('htmx:afterSwap', function(evt) {
    hideLoaderWhenImagesLoaded('.main-content'); // or your content selector
});