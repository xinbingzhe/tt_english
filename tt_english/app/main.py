from fastapi import FastAPI
from contextlib import asynccontextmanager # 用于 FastAPI lifespan

from app.db.database import create_db_and_tables, engine # 导入数据库相关
from app.apis.v1 import user_router, event_router, match_router # 导入路由
from app.core.config import settings
# from app.apis.v1 import event_router # 未来导入其他路由

# Lifespan for application startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Application startup...")
    # 在开发环境中，可以在启动时创建表。生产环境建议使用Alembic。
    # 注意：如果表已存在，create_all 不会重复创建或修改。
    # 如果模型有变动，需要数据库迁移工具。
    create_db_and_tables()
    print("Database tables checked/created.")
    yield
    # Shutdown
    print("Application shutdown...")
    if hasattr(engine, 'dispose'): # 确保引擎有 dispose 方法
        # await engine.dispose() # 异步关闭连接池（如果引擎支持异步）
        # 对于同步引擎，可能是 engine.dispose()，且不需要 await
        #TODO 这里很显然使用的是同步引擎，那么后续有没有必要换成异步引擎呢？
        engine.dispose()
    print("Database connections closed.")


app = FastAPI(lifespan=lifespan, title=settings.APP_NAME, version="0.1.0")

# 包含 API 路由
app.include_router(user_router.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(event_router.router, prefix="/api/v1/events", tags=["Events"])
app.include_router(match_router.router, prefix="/api/v1/matches", tags=["Matches"])
# app.include_router(event_router.router, prefix="/api/v1/events", tags=["Events"]) # 未来



@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}"}
