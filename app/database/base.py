# 📁 수정된 파일: app/database/base.py
# 팀장님 방식에 맞춘 데이터베이스 연결 설정

from app.database.models_config import (
    Base, async_engine, sync_engine, 
    AsyncSessionLocal, SessionLocal,
    get_async_session, get_sync_session
)
from sqlalchemy import text
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_connection():
    """
    데이터베이스 연결 테스트
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            logger.info("✅ PostgreSQL 연결 성공")
            return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL 연결 실패: {e}")
        return False


async def create_tables():
    """
    테이블 생성 (개발용)
    운영 환경에서는 Alembic 마이그레이션 사용 권장
    """
    try:
        async with async_engine.begin() as conn:
            # 모든 모델을 import해야 테이블이 생성됨
            from app.models import User, LibraryItem
            
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ 데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"❌ 테이블 생성 실패: {e}")
        raise


async def drop_tables():
    """
    테이블 삭제 (개발용 - 주의해서 사용!)
    """
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            logger.info("🗑️ 데이터베이스 테이블 삭제 완료")
    except Exception as e:
        logger.error(f"❌ 테이블 삭제 실패: {e}")
        raise


# 애플리케이션 종료 시 연결 정리
async def close_db_connections():
    """
    데이터베이스 연결 정리
    """
    try:
        await async_engine.dispose()
        sync_engine.dispose()
        logger.info("🔌 데이터베이스 연결 정리 완료")
    except Exception as e:
        logger.error(f"❌ 연결 정리 실패: {e}")