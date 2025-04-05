from django import template

register = template.Library()

@register.filter(name='percentage')
def percentage(value, total):
    """计算百分比"""
    try:
        if total == 0:
            return 0
        return (value / total) * 100
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def get_item(dictionary, key):
    """从字典中获取指定键的值"""
    if dictionary is None:
        return None
    return dictionary.get(key) 