
// (function () {
//   var body = document.body;
//   var loader = document.getElementById('global-loader');
//   var nav = document.getElementById('navStick');
//   var collapse = document.getElementById('navbarSupportedContent');

//   var pending = 0, showTimer = null, visibleSince = 0;
//   var SHOW_DELAY = 120, MIN_VISIBLE = 200;

//   // Respect reduced motion
//   try {
//     if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
//       SHOW_DELAY = 0; MIN_VISIBLE = 0;
//     }
//   } catch (_) { }

//   function updateNav() {
//     if (!nav || !collapse) return;
//     var scrolled = window.scrollY > 8;
//     var expanded = collapse.classList.contains('show');
//     nav.classList.toggle('navbar-blur', scrolled || expanded);
//     nav.classList.toggle('is-scrolled', scrolled);
//     nav.classList.toggle('shadow-sm', scrolled || expanded);
//     nav.classList.toggle('bg-transparent', !scrolled && !expanded);
//     nav.classList.toggle('showing', expanded);
//   }

//   function bindCollapseListeners() {
//     collapse = document.getElementById('navbarSupportedContent');
//     if (!collapse) return;
//     // Ensure idempotent binding
//     ['show.bs.collapse', 'shown.bs.collapse', 'hidden.bs.collapse'].forEach(function (evt) {
//       collapse.removeEventListener(evt, updateNav);
//       collapse.addEventListener(evt, updateNav);
//     });
//   }

//   document.addEventListener('DOMContentLoaded', function () {
//     window.addEventListener('scroll', updateNav, { passive: true });
//     bindCollapseListeners();
//     updateNav();

//   });

//   // If nav/collapse content is HTMX-swapped, rebind & refresh icons
//   document.body.addEventListener('htmx:afterSwap', function (e) {
//     if (e.target && (e.target.id === 'navbarSupportedContent' || e.target.closest?.('#navbarSupportedContent'))) {
//       bindCollapseListeners();
//       updateNav();
//     }

//   });

//   // Loader show/hide with fade
//   function scheduleShow() {
//     if (!loader) return;
//     if (showTimer || loader.classList.contains('show')) return;
//     showTimer = setTimeout(function () {
//       showTimer = null;
//       loader.classList.add('show');
//       loader.setAttribute('aria-hidden', 'false');
//       visibleSince = performance.now();
//     }, SHOW_DELAY);
//   }
//   function scheduleHide() {
//     if (!loader) return;
//     if (showTimer) { clearTimeout(showTimer); showTimer = null; }
//     if (!loader.classList.contains('show')) return;
//     var elapsed = performance.now() - visibleSince;
//     var wait = Math.max(0, MIN_VISIBLE - elapsed);
//     setTimeout(function () {
//       loader.classList.remove('show');
//       loader.setAttribute('aria-hidden', 'true');
//     }, wait);
//   }

//   // Helper to end a cycle safely
//   function endOneRequestCycle() {
//     if (pending > 0 && --pending === 0) {
//       body.classList.remove('htmx-busy');
//       body.removeAttribute('aria-busy');
//       scheduleHide();
//     }
//   }

//   // HTMX lifecycle hooks for fade effect
//   document.body.addEventListener('htmx:beforeRequest', function (evt) {
//     // Allow opt-out per trigger element
//     if (evt.target && evt.target.closest && evt.target.closest('[data-skip-loader]')) return;

//     if (++pending === 1) {
//       body.classList.add('htmx-busy');         // fades .main-content via CSS
//       body.setAttribute('aria-busy', 'true');  // a11y hint
//       scheduleShow();                          // fades loader in
//     }
//   });

//   // Always fires after swap & animations
//   document.body.addEventListener('htmx:afterSettle', endOneRequestCycle);

//   // Additional failure modes
//   document.body.addEventListener('htmx:responseError', function () {
//     endOneRequestCycle();
//     alert('A server error occurred while loading content.');
//   });
//   document.body.addEventListener('htmx:sendError', endOneRequestCycle);
//   document.body.addEventListener('htmx:timeout', endOneRequestCycle);

//   // If the tab is hidden, clear pending/loader to avoid a stuck state on return
//   document.addEventListener('visibilitychange', function () {
//     if (document.hidden) {
//       pending = 0;
//       body.classList.remove('htmx-busy');
//       body.removeAttribute('aria-busy');
//       if (showTimer) { clearTimeout(showTimer); showTimer = null; }
//       if (loader) { loader.classList.remove('show'); loader.setAttribute('aria-hidden', 'true'); }
//     }
//   });
// })();

