from sqlmodel import create_engine, Session

from app.core.config import settings

engine_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, echo=True, connect_args=engine_args) # echo=True 用于开发时打印SQL语句

def create_db_and_tables():
    # 在应用启动时可以调用此函数创建表 (对于开发环境)
    #TODO 对于生产环境，通常使用 Alembic 进行数据库迁移管理
    from sqlmodel import SQLModel
    from app.db.models import user_model

    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session