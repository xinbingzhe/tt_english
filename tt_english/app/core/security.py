from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
# from passlib.context import CryptContext

from app.core.config import settings
from app.db.models.user_model import TokenData

ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token_and_get_openid(token: str) -> Optional[str]: # 改为 async 以便 FastAPI 依赖项中调用
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        openid: Optional[str] = payload.get("sub") # 我们将用 openid 作为 subject
        if openid is None:
            return None
        # token_data = TokenData(openid=openid) # 可以用 Pydantic 模型验证 payload 结构
    except JWTError:
        return None
    return openid