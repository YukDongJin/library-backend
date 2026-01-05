# 📁 새로 생성된 파일: app/database/models_config.py
# 팀장님 방식에 맞춘 데이터베이스 설정

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# SQLAlchemy 설정 
Base = declarative_base()

# 데이터베이스 연결 설정 (팀장님이 제공한 실제 정보)
# 형식: postgresql+asyncpg://사용자명:비밀번호@호스트:포트/데이터베이스명
DATABASE_URL = "postgresql+asyncpg://tuser:test123@192.168.0.163:5432/testdb"

# 동기 엔진 (마이그레이션용)
sync_database_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
sync_engine = create_engine(sync_database_url, echo=True)

# 비동기 엔진 (FastAPI용)
async_engine = create_async_engine(DATABASE_URL, echo=True)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

async def get_async_session():
    """비동기 데이터베이스 세션 의존성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_sync_session():
    """동기 데이터베이스 세션"""
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()