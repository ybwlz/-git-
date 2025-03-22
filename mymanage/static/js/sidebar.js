// 苗韵琴行管理系统 - 侧边栏交互功能

document.addEventListener('DOMContentLoaded', function() {
    // 侧边栏切换功能
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    // 点击页面其他区域关闭侧边栏（仅在移动设备上）
    document.addEventListener('click', function(event) {
        const isSmallScreen = window.innerWidth < 992;
        const clickedOutsideSidebar = !sidebar.contains(event.target);
        const clickedToggleButton = sidebarToggle && sidebarToggle.contains(event.target);
        
        if (isSmallScreen && sidebar.classList.contains('show') && clickedOutsideSidebar && !clickedToggleButton) {
            sidebar.classList.remove('show');
        }
    });
    
    // 子菜单切换功能
    const submenuToggles = document.querySelectorAll('.sidebar-menu .has-submenu > a');
    
    submenuToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            
            const parent = this.parentElement;
            const submenu = parent.querySelector('.submenu');
            
            // 关闭其他打开的子菜单
            if (!parent.classList.contains('open')) {
                document.querySelectorAll('.sidebar-menu .has-submenu.open').forEach(function(item) {
                    if (item !== parent) {
                        item.classList.remove('open');
                        item.querySelector('.submenu').classList.remove('show');
                    }
                });
            }
            
            // 切换当前子菜单
            parent.classList.toggle('open');
            submenu.classList.toggle('show');
        });
    });
    
    // 设置当前活动菜单项
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.sidebar-menu a');
    
    menuLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        
        // 检查链接是否匹配当前路径
        if (href === currentPath || currentPath.includes(href) && href !== '#') {
            link.classList.add('active');
            
            // 如果是子菜单项，展开父菜单
            const parentSubmenu = link.closest('.submenu');
            if (parentSubmenu) {
                parentSubmenu.classList.add('show');
                parentSubmenu.parentElement.classList.add('open');
            }
        }
    });
}); 