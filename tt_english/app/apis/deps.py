from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # 用于从 Header 获取 token
from sqlmodel import Session
from jose import JWTError

from app.core import security
from app.core.config import settings
from app.db.database import get_session
from app.db.models.user_model import User, TokenData
from app.crud import user_crud

# 定义 OAuth2PasswordBearer，它会从请求的 Authorization header 中提取 Bearer token
# tokenUrl 只是一个形式上的参数，指向登录接口的URL，FastAPI用它来生成 OpenAPI 文档
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login") # 确保路径正确

async def get_current_user(
    db: Session = Depends(get_session), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    openid = await security.verify_token_and_get_openid(token)
    if openid is None:
        raise credentials_exception
    
    user = user_crud.get_user_by_openid(db, openid=openid)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    # 这里可以添加用户是否激活的检查，如果需要的话
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user