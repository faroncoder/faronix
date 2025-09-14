
(function () {
  if (window.__drawerInit) return; // prevent double init
  window.__drawerInit = true;

  var IDS = {
    menu: 'sidemenu',
    backdrop: 'sidemenu-backdrop',
    tabOpen: 'drawer-tab-open',
  };

  function $id(id) { return document.getElementById(id); }
  function bodyNoScroll(on) { document.body.classList.toggle('no-scroll', !!on); }

  function openDrawer() {
    var menu = $id(IDS.menu);
    var backdrop = $id(IDS.backdrop);
    var tabOpen = $id(IDS.tabOpen);
    if (!menu || !backdrop) return;

    if (!menu.classList.contains('open')) {
      menu.classList.add('open');
      backdrop.classList.add('show');
      bodyNoScroll(true);
      if (tabOpen) tabOpen.style.display = 'none';
      menu.setAttribute('aria-hidden', 'false');
      menu.setAttribute('aria-expanded', 'true');
    }
  }

  function closeDrawer() {
    var menu = $id(IDS.menu);
    var backdrop = $id(IDS.backdrop);
    var tabOpen = $id(IDS.tabOpen);
    if (!menu || !backdrop) return;

    menu.classList.remove('open');
    backdrop.classList.remove('show');
    bodyNoScroll(false);
    if (tabOpen) tabOpen.style.display = '';
    menu.setAttribute('aria-hidden', 'true');
    menu.setAttribute('aria-expanded', 'false');
  }

  function toggleDrawer() {
    var menu = $id(IDS.menu);
    if (!menu) return;
    if (menu.classList.contains('open')) closeDrawer(); else openDrawer();
  }

  // Expose for inline onClick or other scripts
  window.openDrawer = openDrawer;
  window.closeDrawer = closeDrawer;
  window.toggleDrawer = toggleDrawer;

  // Event delegation so newly-swapped HTMX content just works
  function wireDelegates(root) {
    root = root || document;
    root.addEventListener('click', function (e) {
      var el = e.target.closest('[data-drawer-open],[data-drawer-close],[data-drawer-toggle]');
      if (!el) return;
      if (el.hasAttribute('data-drawer-open')) { e.preventDefault(); openDrawer(); }
      else if (el.hasAttribute('data-drawer-close')) { e.preventDefault(); closeDrawer(); }
      else if (el.hasAttribute('data-drawer-toggle')) { e.preventDefault(); toggleDrawer(); }
    });
  }

  // Backdrop click + ESC to close
  function wireBackdropAndEsc() {
    var backdrop = $id(IDS.backdrop);
    if (backdrop) backdrop.onclick = closeDrawer;

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeDrawer();
    });
  }

  // Initial wiring
  document.addEventListener('DOMContentLoaded', function () {
    wireDelegates(document);
    wireBackdropAndEsc();
  });

  // Re-wire after HTMX swaps (new buttons/links may appear)
  document.body.addEventListener('htmx:afterSwap', function (e) {
    wireDelegates(e.target || document);
  });
})();

