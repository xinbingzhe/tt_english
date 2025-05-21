# app/db/models/event_signup_model.py
from datetime import datetime, date
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

# 为了避免循环导入，在类型检查时使用字符串引用 User
if TYPE_CHECKING:
    from app.db.models.user_model import User

class EventSignupBase(SQLModel):
    user_id: int = Field(foreign_key="user.id", index=True)
    event_date: date = Field(index=True, description="活动日期")
    signup_time: datetime = Field(default_factory=datetime.utcnow, description="报名时间 (UTC)")
    # 可以在这里添加其他与报名相关的信息，例如用户报名时的英语水平快照（如果需要）
    # english_level_at_signup: Optional[int] = Field(default=None)

class EventSignup(EventSignupBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # 建立与 User 模型的关系
    # user: Optional["User"] = Relationship(back_populates="signups")
    # 注意：如果要在 User 模型中也定义反向关系 "signups",
    # 需要在 user_model.py 中的 User 类里添加:
    # signups: List["EventSignup"] = Relationship(back_populates="user")

class EventSignupCreate(EventSignupBase):
    pass

class EventSignupRead(EventSignupBase):
    id: int
    # 如果需要返回用户信息，可以添加
    # user: Optional["UserRead"] = None # 假设 UserRead 定义在 user_model.py

class EventStatusResponse(SQLModel):
    is_signup_open: bool
    user_signed_up_today: bool
    signup_details: Optional[EventSignupRead] = None
    server_time_utc: datetime
    signup_start_time_local: str # 例如 "19:00"
    signup_end_time_local: str   # 例如 "20:00"
    local_timezone_name: str     # 例如 "Asia/Shanghai"