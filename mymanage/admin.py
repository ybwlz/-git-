from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

class MyManageAdminSite(AdminSite):
    """自定义管理站点，控制应用显示顺序"""
    site_title = _('苗韵钢琴管理系统')
    site_header = _('苗韵钢琴管理系统')
    index_title = _('管理中心')
    
    def get_app_list(self, request):
        """自定义应用排序，将学生和教师放在最前面"""
        app_list = super().get_app_list(request)
        
        # 定义应用优先级
        app_order = {
            'students': 1,
            'teachers': 2,
            'courses': 3,
            'attendance': 4,
            'finance': 5,
            'users': 6,
            'auth': 7,
        }
        
        # 按照优先级排序
        app_list.sort(key=lambda app: app_order.get(app['app_label'], 99))
        
        return app_list


# 创建自定义管理站点实例
mymanage_admin_site = MyManageAdminSite(name='myadmin')

# 导入并注册所有模型
from django.apps import apps
from django.contrib.auth.models import Group
from django.contrib.admin.sites import site as default_admin_site

# 复制默认admin站点的所有已注册模型
for model, admin_class in default_admin_site._registry.items():
    # 在我们的自定义管理站点中注册相同的模型
    mymanage_admin_site.register(model, admin_class.__class__) 