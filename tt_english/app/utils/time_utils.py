# app/utils/time_utils.py
from datetime import datetime, time, timedelta
import pytz # pip install pytz
from typing import Tuple # <--- 导入 Tuple

from app.core.config import settings

def get_local_timezone():
    return pytz.timezone(settings.LOCAL_TIMEZONE)

def get_current_time_in_local_tz() -> datetime:
    local_tz = get_local_timezone()
    return datetime.now(local_tz)

# 修改返回类型注解
def is_signup_window_open() -> tuple[bool, datetime, time, time]: # <--- 修改这里
    """
    检查当前是否在报名窗口期（基于配置的本地时间）。
    返回: (是否开放, 当前本地时间, 开始时间对象, 结束时间对象)
    元组元素依次为: is_open (bool), now_local (datetime), signup_start_time_obj (time), signup_end_time_obj (time)
    """
    local_tz = get_local_timezone()
    now_local = datetime.now(local_tz) # 当前本地时区的 datetime 对象

    # 创建不带日期的 time 对象，但包含时区信息，用于比较
    signup_start_time_obj = time(settings.EVENT_SIGNUP_START_HOUR_LOCAL, 0, 0, tzinfo=local_tz)
    signup_end_time_obj = time(settings.EVENT_SIGNUP_END_HOUR_LOCAL, 0, 0, tzinfo=local_tz)

    # 获取当前本地时间的 time 部分 (包含时区)
    current_local_timetz = now_local.timetz()

    # 比较 time 对象
    # 报名开始时间 <= 当前时间 < 报名结束时间
    is_open = signup_start_time_obj <= current_local_timetz < signup_end_time_obj
    
    return is_open, now_local, signup_start_time_obj, signup_end_time_obj

def get_current_utc_time() -> datetime:
    return datetime.now(pytz.utc)