// static/js/loader-images.js
(function () {
  function waitForImages(root, done) {
    if (!root) return done();
    var imgs = root.querySelectorAll('img');
    if (!imgs.length) return done();

    var left = imgs.length;
    function check(img) {
      if (img.complete) {
        if (--left === 0) done();
      } else {
        img.addEventListener('load', function () {
          if (--left === 0) done();
        }, { once: true });
        img.addEventListener('error', function () {
          if (--left === 0) done(); // treat errors as done to avoid deadlock
        }, { once: true });
      }
    }
    imgs.forEach(check);
  }

  // After any HTMX swap, hold the loader until images inside the swap target are ready
  document.body.addEventListener('htmx:afterSwap', function (e) {
    var target = e.detail && e.detail.target;
    if (!target) return;
    if (!window.hxLoader) return;  // hardened block not loaded yet

    // Start hold, release when images done
    window.hxLoader.hold();
    waitForImages(target, function () {
      window.hxLoader.release();
    });
  });
})();
