from datetime import datetime


def get_now_str(now: datetime):
    chinese_months = [
        '一月',
        '二月',
        '三月',
        '四月',
        '五月',
        '六月',
        '七月',
        '八月',
        '九月',
        '十月',
        '十一月',
        '十二月',
    ]

    chinese_weekdays = ['一', '二', '三', '四', '五', '六', '日']

    month = now.month
    day = now.day
    weekday = chinese_weekdays[now.weekday()]

    return f'{month}月{day}日({weekday})'
