import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mymanage.settings')
django.setup()

# 导入Piano模型
from mymanage.courses.models import Piano

# 更新所有钢琴状态
for piano in Piano.objects.all():
    piano.is_occupied = False
    piano.save()
    print(f'钢琴{piano.number}状态已更新: 占用={piano.is_occupied}')

print("所有钢琴状态已更新完成") 