from django import template

register = template.Library()

@register.filter(name='mul')
def mul(value, arg):
    """乘法过滤器"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='div')
def div(value, arg):
    """除法过滤器"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0  # 避免除以零错误
        return float(value) / arg
    except (ValueError, TypeError):
        return 0

@register.filter(name='sub')
def sub(value, arg):
    """减法过滤器"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='add')
def add(value, arg):
    """加法过滤器"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='percentage')
def percentage(value, arg):
    """计算百分比: (value / arg) * 100"""
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return (float(value) / arg) * 100
    except (ValueError, TypeError):
        return 0 