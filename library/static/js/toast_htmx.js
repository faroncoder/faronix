// static/js/toasts.js
(function () {
  // Find/create the container once
  function getContainer() {
    var c = document.querySelector('.toast-container');
    if (c) return c;
    c = document.createElement('div');
    c.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    c.style.zIndex = '1100';
    document.body.appendChild(c);
    return c;
  }
  var container = null;
  function ensureContainer() { return (container ||= getContainer()); }

  // Map types to Bootstrap classes (BS 5.x)
  function clsFor(type) {
    var t = (type || 'primary').toLowerCase();
    // bg-* still fine; if you use BS5.3, you can swap to text-bg-*
    return 'toast align-items-center text-white bg-' + t + ' border-0';
  }

  function createToastEl(message, type, opts) {
    var el = document.createElement('div');
    el.className = clsFor(type);
    el.setAttribute('role', 'alert');
    el.setAttribute('aria-live', 'assertive');
    el.setAttribute('aria-atomic', 'true');
    el.innerHTML =
      '<div class="d-flex">' +
        '<div class="toast-body"></div>' +
        '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>' +
      '</div>';
    el.querySelector('.toast-body').textContent = message;
    ensureContainer().appendChild(el);
    var delay = (opts && typeof opts.delay === 'number')
                  ? opts.delay
                  : (type === 'danger' || type === 'warning' ? 7000 : 4000);
    var autohide = (opts && 'autohide' in opts)
                  ? !!opts.autohide
                  : !(type === 'danger' || type === 'warning'); // sticky errors by default
    var t = new bootstrap.Toast(el, { delay: delay, autohide: autohide });
    el.addEventListener('hidden.bs.toast', function () { el.remove(); });
    return { el: el, api: t };
  }

  function showToast(message, type, opts) {
    var { api } = createToastEl(message, type, opts || {});
    api.show();
    return api;
  }

  // Public helpers
  window.toasts = {
    show:   function (o) { return showToast(o.message, o.type || 'primary', o); },
    success:function (m,o){ return showToast(m, 'success', o); },
    info:   function (m,o){ return showToast(m, 'info',    o); },
    warn:   function (m,o){ return showToast(m, 'warning', o); },
    error:  function (m,o){ return showToast(m, 'danger',  o || { autohide:false }); }
  };

  // --- HTMX integration: server-driven and error toasts ---

  // 1) Read HX-Trigger payloads like:
  //    resp['HX-Trigger'] = json.dumps({"toast": {"message":"Saved","type":"success","delay":3000}})
  document.body.addEventListener('htmx:afterRequest', function (e) {
    var xhr = e.detail && e.detail.xhr;
    if (!xhr) return;

    // Server-sent toast via HX-Trigger
    try {
      var trig = xhr.getResponseHeader && xhr.getResponseHeader('HX-Trigger');
      if (trig) {
        var data = JSON.parse(trig);
        var t = data.toast || data['toast:show']; // support either key
        if (t && t.message) window.toasts.show(t);
      }
    } catch (_) {}

    // Generic error toast (skip 401 because you swap login partials)
    var s = xhr.status | 0;
    if (s >= 400 && s !== 401) {
      // Customize message if you like:
      window.toasts.error('Request failed (' + s + ').');
    }
  });
})();
