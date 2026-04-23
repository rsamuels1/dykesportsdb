(function () {
    const path = window.location.pathname;

    function isActive(href) {
        if (href === '/sports-database') return path === '/sports-database' || path.startsWith('/sports-database/');
        return path === href || path === href.replace(/\.html$/, '');
    }

    function a(href, label, cls) {
        const active = isActive(href);
        const classes = [cls, active ? 'active' : ''].filter(Boolean).join(' ');
        return '<a href="' + href + '"' + (classes ? ' class="' + classes + '"' : '') + '>' + label + '</a>';
    }

    const nav = document.querySelector('nav');
    if (nav) {
        nav.innerHTML =
            '<a href="/" class="logo">QUEER SPORTS DB</a>' +
            '<button class="hamburger" aria-label="Toggle menu" aria-expanded="false">☰</button>' +
            '<ul class="nav-links">' +
            '<li>' + a('/sports-database', 'Database') + '</li>' +
            '<li>' + a('/stats.html', 'Stats') + '</li>' +
            '<li>' + a('/about.html', 'About') + '</li>' +
            '<li>' + a('/submit', '+ Add a Club', 'pill') + '</li>' +
            '</ul>';

        const hamburger = nav.querySelector('.hamburger');
        const navLinks = nav.querySelector('.nav-links');
        if (hamburger && navLinks) {
            hamburger.addEventListener('click', () => {
                const isOpen = navLinks.classList.toggle('active');
                hamburger.setAttribute('aria-expanded', isOpen);
            });
        }
    }

    const footer = document.querySelector('footer');
    if (footer) {
        footer.innerHTML =
            '<div class="footer-logo">QUEER SPORTS DB</div>' +
            '<div class="footer-right">' +
            '<a href="https://github.com/dykesportsdb/" target="_blank">GitHub</a>' +
            '<span class="footer-sep">·</span>' +
            '<span>© 2026</span>' +
            '</div>';
    }
})();
