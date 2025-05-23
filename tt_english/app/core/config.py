from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "tt_english"
    WECHAT_APPID: str
    WECHAT_APPSECRET: str
    DATABASE_URL: str = "mysql+mysqlconnector://tt_english:Passwd123@localhost:3306/tt_english" #TODO 示例，实际应为云托管MySQL的连接串
    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-key" # 必须修改为一个强随机字符串
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # Token有效期7天

    # 新增配置项，用于控制是否模拟微信API
    MOCK_WECHAT_API: bool = False # 在 .env 中设置为 True 来启用模拟

    # 活动报名时间 (本地时间，例如北京时间)
    EVENT_SIGNUP_START_HOUR_LOCAL: int = 6 # 19点 (7 PM)
    EVENT_SIGNUP_END_HOUR_LOCAL: int = 20   # 20点 (8 PM)
    # 服务器运行时区 (用于将本地时间转换为UTC或进行比较)
    # 如果云托管服务器是 UTC，但逻辑时间是北京时间，则需要这个
    LOCAL_TIMEZONE: str = "Asia/Shanghai" # IANA Time Zone Name

    INTERNAL_TRIGGER_TOKEN: Optional[str] = "a-very-secret-internal-token" # 用于保护触发器端点
    class Config:
        env_file = "config.env" # 从 config.env 文件加载配置

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()