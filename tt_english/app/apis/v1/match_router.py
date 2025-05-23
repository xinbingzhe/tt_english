# app/apis/v1/match_router.py
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlmodel import Session
from datetime import date, timedelta
from typing import Optional, List

from app.db.database import get_session
from app.db.models.user_model import User, UserRead # UserRead 用于 MyMatchResult
from app.db.models.chat_room_model import ChatRoomRead # 用于管理员或调试接口
from app.db.models.chat_room_participant_model import MyMatchResult # 导入我们定义好的响应模型
from app.crud import match_crud, event_signup_crud # 确保导入 event_signup_crud
from app.apis.deps import get_current_active_user
from app.services.matching_service import MatchingService
from app.core.config import settings # 用于获取 X-Internal-Auth-Token 等配置
from app.utils import time_utils # 用于获取当前本地日期

router = APIRouter()

# 简单的内部调用认证 (示例)
INTERNAL_TRIGGER_TOKEN = settings.INTERNAL_TRIGGER_TOKEN # 复用一个密钥作为示例，生产环境应使用独立密钥

def verify_internal_token(x_internal_trigger_token: Optional[str] = Header(None)):
    if not x_internal_trigger_token or x_internal_trigger_token != INTERNAL_TRIGGER_TOKEN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for internal action")
    return True


@router.post("/trigger", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_internal_token)])
async def trigger_matching_process(
    db: Session = Depends(get_session),
    # 可以接受一个可选的日期参数用于测试，否则使用当天日期
    event_date_str: Optional[str] = None # 格式 YYYY-MM-DD
):
    """
    触发当天的匹配过程。此接口应由定时任务调用，并受保护。
    如果提供了 event_date_str，则为指定日期执行匹配（主要用于测试）。
    """
    if event_date_str:
        try:
            event_dt = date.fromisoformat(event_date_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式错误，请使用 YYYY-MM-DD")
    else:
        # 获取当前服务器的本地日期 (例如北京时间)
        now_local = time_utils.get_current_time_in_local_tz()
        event_dt = now_local.date()

        # 检查是否在报名截止时间之后才允许触发
        is_open, _, _, end_time_local_obj = time_utils.is_signup_window_open()
        # end_time_local_obj 是 time 对象, now_local.timetz() 也是 time 对象
        # 只有当报名窗口关闭（即当前时间 >= 报名截止时间）或已过当天报名时段，才允许匹配
        if now_local.timetz() < end_time_local_obj and now_local.date() == event_dt:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"报名尚未截止 ({end_time_local_obj.strftime('%H:%M')} {settings.LOCAL_TIMEZONE})，不能触发匹配。"
            )

    # 检查当天是否已生成过匹配，避免重复执行 (MatchingService内部也做了检查)
    if match_crud.check_if_matches_generated_for_date(db, event_dt):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{event_dt} 的匹配已经生成过。如需重新匹配，请先调用清理接口或手动清理。"
        )

    matcher = MatchingService(db)
    try:
        rooms_created = matcher.perform_matching(event_date=event_dt)
        if rooms_created > 0:
            return {"message": f"为日期 {event_dt} 成功创建了 {rooms_created} 个匹配房间。"}
        else:
            return {"message": f"为日期 {event_dt} 未创建任何匹配房间 (可能用户不足或已匹配过)。"}
    except Exception as e:
        # 实际应用中应该更详细地记录错误
        print(f"匹配过程中发生错误: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"匹配过程中发生错误: {str(e)}")


@router.get("/me", response_model=Optional[MyMatchResult]) # 用户可能当天没有匹配
async def get_my_match_result(
    *,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
    # 可选，查询特定日期的匹配，默认为当天
    event_date_str: Optional[str] = None # 格式 YYYY-MM-DD
):
    """
    获取当前用户当天的匹配结果。
    应在匹配完成后调用。
    """
    if event_date_str:
        try:
            query_date = date.fromisoformat(event_date_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式错误，请使用 YYYY-MM-DD")
    else:
        now_local = time_utils.get_current_time_in_local_tz()
        query_date = now_local.date()

    # 1. 检查用户当天是否报名了
    # signup = event_signup_crud.get_event_signup_by_user_and_date(db, user_id=current_user.id, event_date=query_date)
    # if not signup:
    #     # 如果用户当天未报名，理论上不应该有匹配结果
    #     # 但如果匹配逻辑不依赖报名表（而是直接查用户），这里可以省略
    #     # 最好是，只有报名了才会被匹配
    #     return None # 或者返回特定提示，告知未报名

    # 2. 获取用户的匹配房间
    room = match_crud.get_user_match_for_date(db, user_id=current_user.id, event_date=query_date)
    if not room:
        return None # 用户当天没有匹配到房间

    # 3. 获取房间内的所有参与者信息
    participants_users = match_crud.get_participants_for_room(db, room_id=room.id)
    
    # 将 User 对象转换为 UserRead 对象
    participants_read = [UserRead.model_validate(p_user) for p_user in participants_users]

    return MyMatchResult(
        room_identifier=room.room_identifier,
        event_date=room.event_date,
        room_type=room.room_type,
        participants=participants_read
    )

# (可选) 清理接口，用于测试或特殊情况
@router.delete("/cleanup/{event_date_str}", status_code=status.HTTP_200_OK, dependencies=[Depends(verify_internal_token)])
async def cleanup_matches_for_date(
    event_date_str: str,
    db: Session = Depends(get_session)
):
    """为指定日期清理所有匹配数据（房间和参与者）。"""
    try:
        event_dt = date.fromisoformat(event_date_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="日期格式错误，请使用 YYYY-MM-DD")
    
    deleted_count = match_crud.delete_matches_for_date(db, event_dt)
    return {"message": f"为日期 {event_dt} 清理了 {deleted_count} 个匹配房间及其参与者。"}