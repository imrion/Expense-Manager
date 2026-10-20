document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('[data-menu-toggle]');
    const menu = document.getElementById('appSidebar');
    const menuClose = document.querySelector('[data-menu-close]');

    if (!menuToggle || !menu || !menuClose) {
        return;
    }

    const closeMenu = function() {
        document.body.classList.remove('sidebar-open');
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.setAttribute('aria-label', 'Open navigation menu');
    };

    const openMenu = function() {
        document.body.classList.add('sidebar-open');
        menuToggle.setAttribute('aria-expanded', 'true');
        menuToggle.setAttribute('aria-label', 'Close navigation menu');
        const firstLink = menu.querySelector('a');
        if (firstLink) {
            firstLink.focus();
        }
    };

    menuToggle.addEventListener('click', function() {
        if (document.body.classList.contains('sidebar-open')) {
            closeMenu();
        } else {
            openMenu();
        }
    });

    menuClose.addEventListener('click', closeMenu);

    menu.addEventListener('click', function(event) {
        if (event.target.closest('a')) {
            closeMenu();
        }
    });

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && document.body.classList.contains('sidebar-open')) {
            closeMenu();
            menuToggle.focus();
        }
    });

    window.addEventListener('resize', function() {
        if (window.innerWidth > 991) {
            closeMenu();
        }
    });
});
