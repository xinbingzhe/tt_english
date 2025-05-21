from sqlmodel import Session, select
from typing import Optional

from app.db.models.user_model import User, UserCreate

def get_user_by_openid(db: Session, openid: str) -> Optional[User]:
    statement = select(User).where(User.openid == openid)
    return db.exec(statement).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    db_user = User.model_validate(user_in)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, db_user: User, user_in_data: dict) -> User:
    user_data = db_user.model_dump(exclude_unset=True) # 获取现有用户数据
    for key, value in user_in_data.items():
        if hasattr(db_user, key) and value is not None: # 确保字段存在且值不是None
            setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

#? 这里为什么需要返回user

def update_introduction_by_openid(db: Session, openid: str, changed_introduction: str) -> User:
    statement = select(User).where(User.openid == openid)
    user = db.exec(statement)
    user.introduction = changed_introduction
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
    
def get_introduction_by_openid(db: Session, openid: str) -> str:
    statement = select(User.introduction).where(User.openid == openid)
    introduction = db.exec(statement).first()
    return introduction