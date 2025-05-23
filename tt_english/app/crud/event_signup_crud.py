# app/crud/event_signup_crud.py
from datetime import date, datetime
from typing import List, Optional
from sqlmodel import Session, select
from app.utils.time_utils import get_current_time_in_local_tz

from app.db.models.event_signup_model import EventSignup, EventSignupCreate
from app.db.models.user_model import User # 用于类型提示

def create_event_signup(db: Session, user: User, event_date: date) -> EventSignup:
    # 检查用户当天是否已报名 (理论上API层会做，但CRUD也可以加一道保险)
    existing_signup = get_event_signup_by_user_and_date(db, user_id=user.id, event_date=event_date)
    if existing_signup:
        #TODO
        # 可以选择抛出异常或返回现有报名信息，具体取决于业务逻辑
        # 这里假设API层已经处理了重复报名，所以直接创建
        # 或者在这里进行更严格的控制
        pass

    # 获取时间
    # beijing_tz = zoneinfo.ZoneInfo(settings.LOCAL_TIMEZONE)
    # beijing_time = datetime.datetime.now(beijing_tz)
    print(f"报名时间：{get_current_time_in_local_tz().strftime('%Y-%m-%d %H:%M:%S')}")
    db_signup = EventSignup(
        user_id=user.id,
        event_date=event_date,
        signup_time=get_current_time_in_local_tz().strftime('%Y-%m-%d %H:%M:%S')
        # english_level_at_signup=user.english_level # 如果需要快照
    )
    db.add(db_signup)
    db.commit()
    db.refresh(db_signup)
    return db_signup

def get_event_signup_by_user_and_date(db: Session, user_id: int, event_date: date) -> Optional[EventSignup]:
    statement = select(EventSignup).where(EventSignup.user_id == user_id, EventSignup.event_date == event_date)
    return db.exec(statement).first()

def get_signups_for_date(db: Session, event_date: date) -> List[EventSignup]:
    """获取指定日期的所有报名记录"""
    statement = select(EventSignup).where(EventSignup.event_date == event_date)
    return db.exec(statement).all()

def get_all_active_users_signed_up_for_date(db: Session, event_date: date) -> List[User]:
    """获取指定日期已报名的所有活跃用户信息 (用于匹配)"""
    # 这需要 EventSignup 和 User 之间的联接查询
    # 假设 User 模型有 is_active 字段，或者我们只选择 User
    statement = (
        select(User)
        .join(EventSignup, User.id == EventSignup.user_id)
        .where(EventSignup.event_date == event_date)
        # 如果 User 有 is_active 字段: .where(User.is_active == True)
    )
    users = db.exec(statement).all()
    return users