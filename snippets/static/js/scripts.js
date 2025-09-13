// TODO: Improve blur overlay so that background content is truly blurred when setTint(true) is called.
//       Current implementation does not blur app content as intended. Consider advanced CSS or alternate overlay strategies.


// // Toggle blur overlay for modals/loaders
// function setTint(on) {
//     var overlay = document.getElementById('blur-overlay');
//     if (overlay) overlay.style.display = on ? 'block' : 'none';
// }


// // Fade-out before HTMX request, fade-in after swap
// document.addEventListener('htmx:beforeRequest', function(evt) {
//     var target = document.querySelector('#main-content');
//     if (target) {
//         target.classList.remove('fade-in');
//         target.classList.add('fade-out');
//     }
// });
// document.addEventListener('htmx:afterSwap', function(evt) {
//     var target = document.querySelector('#main-content');
//     if (target) {
//         target.classList.remove('fade-out');
//         target.classList.add('fade-in');
//     }
// });


// // htmx loading overlay logic
// document.addEventListener('htmx:beforeRequest', function () {
//     const main = document.getElementById('main-content');
//     const ov = document.getElementById('mainLoadingOverlay');
//     if (main) main.classList.add('is-loading');
//     if (ov) ov.classList.add('show');
// });

// document.addEventListener('htmx:afterRequest', function () {
//     const main = document.getElementById('main');
//     const ov = document.getElementById('mainLoadingOverlay');
//     if (main) main.classList.remove('is-loading');
//     if (ov) ov.classList.remove('show');
// });

// Animate On Scroll (AOS) init
document.addEventListener('DOMContentLoaded', function () {
    if (window.AOS) {
        AOS.init({
            disable: 'mobile',
            duration: 600,
            once: true,
        });
    }

    // Enable tooltips globally
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable popovers globally
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.forEach(function (popoverTriggerEl) {
        new bootstrap.Popover(popoverTriggerEl);
    });

    // Activate Bootstrap scrollspy for the sticky nav component
    const navStick = document.getElementById('navStick');
    if (navStick) {
        new bootstrap.ScrollSpy(document.body, {
            target: '#navStick',
            offset: 82,
        });
    }


//   document.getElementById('footyear').textContent = new Date().getFullYear();



    // Enable footnote tooltips
    var footnoteTriggerList = [].slice.call(document.querySelectorAll('.footnote'));
    footnoteTriggerList.forEach(function (footnoteTriggerEl) {
        new bootstrap.Tooltip(footnoteTriggerEl, {
            title: footnoteTriggerEl.innerHTML,
            html: true,
            placement: 'top',
        });
    });

    // // Collapse Navbar on scroll
    // var navbarCollapse = function() {
    //     const navbarMarketingTransparentFixed = document.body.querySelector('.navbar-marketing.bg-transparent.fixed-top');
    //     if (!navbarMarketingTransparentFixed) {
    //         return;
    //     }
    //     if (window.scrollY === 0) {
    //         navbarMarketingTransparentFixed.classList.remove('navbar-scrolled');
    //     } else {
    //         navbarMarketingTransparentFixed.classList.add('navbar-scrolled');
    //     }
    // };
    // navbarCollapse();
    // document.addEventListener('scroll', navbarCollapse);

    // if (window.feather) feather.replace();

    // Show Bootstrap modal after htmx swaps in modal content
    document.body.addEventListener('htmx:afterSwap', function(evt) {
        // Only act if the swap target is the modal content
        if (evt.detail.target && evt.detail.target.classList.contains('modal-content')) {
            var modal = document.getElementById('modal');
            if (modal) {
                var bsModal = bootstrap.Modal.getOrCreateInstance(modal);
                bsModal.show();
            }
        }
    });

    // Nav-link active state for HTMX tab navigation
    document.body.addEventListener('click', function(e) {
        // Only handle nav-link clicks
        if (e.target.classList.contains('nav-link')) {
            // Remove 'active' from all nav-links in the same nav
            var nav = e.target.closest('.nav');
            if (nav) {
                nav.querySelectorAll('.nav-link').forEach(function(link) {
                    link.classList.remove('active');
                });
            }
            // Add 'active' to the clicked link
            e.target.classList.add('active');
        }
    });
});
