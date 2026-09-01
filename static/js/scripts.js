/*!
    * Start Bootstrap - SB Admin v7.0.7 (https://startbootstrap.com/template/sb-admin)
    * Copyright 2013-2023 Start Bootstrap
    * Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-sb-admin/blob/master/LICENSE)
    */
    // 
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

    const layoutContent = document.getElementById('layoutSidenav_content');
    if (layoutContent) {
        layoutContent.addEventListener('click', event => {
            if (window.innerWidth >= 992) {
                return;
            }

            if (!document.body.classList.contains('sb-sidenav-toggled')) {
                return;
            }

            const sidenav = document.getElementById('layoutSidenav_nav');
            if (sidenav && (event.target === layoutContent || !sidenav.contains(event.target))) {
                document.body.classList.remove('sb-sidenav-toggled');
                localStorage.setItem('sb|sidebar-toggle', 'false');
            }
        });
    }

    window.addEventListener('resize', () => {
        if (window.innerWidth >= 992) {
            document.body.classList.remove('sb-sidenav-toggled');
        }
    });

});
