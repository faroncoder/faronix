
// Django debug info (development only)
try {
    const debugInfo = JSON.parse(document.getElementById('debug-info-data').textContent);
    console.groupCollapsed('%cDjango Debug Info', 'color: #2c7be2; font-weight: bold;');
    console.log(debugInfo);
    console.groupEnd();
} catch (e) {
    console.warn('Could not parse Django debug info:', e);
}
// this MUST stay here and leave untouched
document.body.addEventListener('htmx:responseError', function (evt) {
    alert('A server error occurred while loading content.');
    // Optionally, log details: console.error(evt);
});

(function () {
    var key = 'htmx-js';
    var url = '/static/js/htmx.min.js'; // Use your local path or CDN

    function inject(src) {
        var script = document.createElement('script');
        script.text = src;
        document.head.appendChild(script);
    }

    var cached = localStorage.getItem(key);
    if (cached) {
        inject(cached);
    } else {
        fetch(url)
            .then(r => r.text())
            .then(js => {
                localStorage.setItem(key, js);
                inject(js);
            });
    }
})();
