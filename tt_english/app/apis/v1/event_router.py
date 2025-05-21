# app/apis/v1/event_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from datetime import date
from typing import Optional

from app.db.database import get_session
from app.db.models.user_model import User
from app.db.models.event_signup_model import EventSignupRead, EventStatusResponse
from app.crud import event_signup_crud
from app.apis.deps import get_current_active_user
from app.utils import time_utils # 导入时间工具
from app.core.config import settings # 导入配置

router = APIRouter()

@router.post("/signup", response_model=EventSignupRead, status_code=status.HTTP_201_CREATED)
async def signup_for_tonights_event(
    *,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user)
):
    """
    用户报名参加当晚的活动。
    活动时间为配置中的 EVENT_SIGNUP_START_HOUR_LOCAL 到 EVENT_SIGNUP_END_HOUR_LOCAL (本地时间)。
    """
    is_open, now_local, _, _ = time_utils.is_signup_window_open()

    if not is_open:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"报名通道未开放。开放时间：每天 {settings.EVENT_SIGNUP_START_HOUR_LOCAL}:00 - {settings.EVENT_SIGNUP_END_HOUR_LOCAL}:00 ({settings.LOCAL_TIMEZONE})。"
        )

    today_date_local = now_local.date() # 获取本地日期的date对象

    existing_signup = event_signup_crud.get_event_signup_by_user_and_date(
        db, user_id=current_user.id, event_date=today_date_local
    )
    if existing_signup:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="你今天已经报名过了。"
        )
    
    # # 确保用户已填写英语水平
    # if current_user.english_level is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="请先在个人信息中设置您的英语水平才能报名。"
    #     )
    # # 也可以在这里检查行业信息是否已填写，如果需要的话

    new_signup = event_signup_crud.create_event_signup(db, user=current_user, event_date=today_date_local)
    return new_signup


@router.get("/status", response_model=EventStatusResponse)
async def get_event_signup_status(
    *,
    db: Session = Depends(get_session),
    current_user: Optional[User] = Depends(get_current_active_user) # 用户可能未登录也想看状态
):
    """
    获取当晚活动的报名状态。
    """
    is_open, now_local, start_time_local, end_time_local = time_utils.is_signup_window_open()
    today_date_local = now_local.date()
    user_signed_up_today = False
    signup_details_read = None

    if current_user:
        signup = event_signup_crud.get_event_signup_by_user_and_date(
            db, user_id=current_user.id, event_date=today_date_local
        )
        if signup:
            user_signed_up_today = True
            # 你可能需要将 EventSignup 转换为 EventSignupRead
            # 如果 EventSignupRead 需要关联对象，确保在 CRUD 或这里处理
            signup_details_read = EventSignupRead.model_validate(signup)


    return EventStatusResponse(
        is_signup_open=is_open,
        user_signed_up_today=user_signed_up_today,
        signup_details=signup_details_read,
        server_time_utc=time_utils.get_current_utc_time(),
        signup_start_time_local=start_time_local.strftime("%H:%M"),
        signup_end_time_local=end_time_local.strftime("%H:%M"),
        local_timezone_name=settings.LOCAL_TIMEZONE
    )