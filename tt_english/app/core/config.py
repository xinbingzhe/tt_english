from pydantic_settings import BaseSettings
from functools import lru_cache

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

    class Config:
        env_file = "config.env" # 从 config.env 文件加载配置

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()