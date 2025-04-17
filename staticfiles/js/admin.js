document.addEventListener('DOMContentLoaded', function() {
    // 高亮当前页面
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-link');
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}); 