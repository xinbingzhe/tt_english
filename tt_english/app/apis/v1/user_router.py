# import httpx # 这里不再直接需要 httpx 来调用微信接口
from fastapi import APIRouter, Depends, HTTPException, status, Body, Security
from sqlmodel import Session

from app.db.database import get_session
from app.db.models.user_model import User, UserCreate, UserRead, UserUpdate, Token, LoginRequest, OrigianlInfo
from app.crud import user_crud
from app.core import security
# from app.core.config import settings # settings 现在由 wechat_service 内部使用
from app.apis.deps import get_current_active_user

# 导入微信服务
from app.services.wechat_service import wechat_service # 导入实例

router = APIRouter()

@router.post("/login", response_model=Token)
async def login_for_access_token(
    db: Session = Depends(get_session),
    login_data: LoginRequest = Body(...)
):
    # 1. 调用微信服务 (模拟或真实) 获取 openid
    try:
        # 使用服务，它内部处理模拟/真实逻辑
        wechat_data = await wechat_service.code_to_session(login_data.code)
    except HTTPException as e: # 捕获由服务层抛出的 HTTPException
        raise e # 重新抛出
    except Exception as e: # 捕获任何其他意外错误
        # 记录这个意外错误
        print(f"调用 code_to_session 时发生意外错误: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="处理微信登录时发生意外错误。")

    openid = wechat_data.get("openid")
    # session_key = wechat_data.get("session_key") # 仍然重要：妥善保管，不要发给前端

    if not openid: # 如果 _real_code_to_session 和 _mock_code_to_session 总是抛出异常或返回有效结构，此检查可能多余
        err_msg = wechat_data.get("errmsg", "获取 openid 失败 (模拟或真实 API 未返回)")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"微信处理错误: {err_msg}")

    # 2. 根据 openid 查找或创建用户 (逻辑保持不变)
    user = user_crud.get_user_by_openid(db, openid=openid)
    is_new_user = False
    if user:
        update_data = {}
        if login_data.nickname and login_data.nickname != user.nickname:
            update_data["nickname"] = login_data.nickname
        if login_data.avatar_url and login_data.avatar_url != user.avatar_url:
            update_data["avatar_url"] = login_data.avatar_url
        if update_data:
            user = user_crud.update_user(db=db, db_user=user, user_in_data=update_data)
    else:
        user_in = UserCreate(
            openid=openid,
            nickname=login_data.nickname,
            avatar_url=login_data.avatar_url
        )
        user = user_crud.create_user(db, user_in=user_in)
        is_new_user = True

    # 3. 创建 access token (逻辑保持不变)
    access_token = security.create_access_token(data={"sub": openid})

    return Token(
        access_token=access_token,
        token_type="bearer",
        user_info=UserRead.model_validate(user),
        is_new_user=is_new_user
    )

# ... user_router.py 的其余部分 (PUT /me, GET /me) 保持不变 ...
@router.put("/me", response_model=UserRead)
async def update_user_me(
    *,
    db: Session = Depends(get_session),
    user_update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    updated_user = user_crud.update_user(db=db, db_user=current_user, user_in_data=user_update_data.model_dump(exclude_unset=True))
    return UserRead.model_validate(updated_user)

# 新用户填写英语水平和所在行业信息 仅仅调用一次
@router.patch("/original", response_model=UserRead)
async def get_original_user_info(
    *,
    db: Session = Depends(get_session),
    oi: OrigianlInfo,
    current_user: User = Depends(get_current_active_user)
):
    oi_data = oi.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(oi_data)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return UserRead.model_validate(current_user)