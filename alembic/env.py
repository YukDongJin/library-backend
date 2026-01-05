# 📁 새로 생성된 파일: alembic/env.py
# Alembic 환경 설정 파일

from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 애플리케이션 설정 및 모델 import
from app.core.config import settings
from app.database.base import Base
from app.models import User, LibraryItem  # 모든 모델을 import해야 마이그레이션에 포함됨

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 메타데이터 설정 (모든 테이블 정보 포함)
target_metadata = Base.metadata

def get_database_url():
    """
    환경에 따른 데이터베이스 URL 반환
    - 개발: .env 파일의 DATABASE_URL 사용
    - 운영: 환경 변수 사용
    """
    return settings.database_url_sync

def run_migrations_offline() -> None:
    """
    오프라인 모드에서 마이그레이션 실행
    - 실제 데이터베이스 연결 없이 SQL 스크립트만 생성
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # 컬럼 타입 변경 감지
        compare_server_default=True,  # 기본값 변경 감지
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """
    온라인 모드에서 마이그레이션 실행
    - 실제 데이터베이스에 연결하여 마이그레이션 적용
    """
    # 데이터베이스 URL 설정
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    # 엔진 생성
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True,  # 컬럼 타입 변경 감지
            compare_server_default=True,  # 기본값 변경 감지
        )

        with context.begin_transaction():
            context.run_migrations()

# 실행 모드 결정
if context.is_offline_mode():
    print("🔄 오프라인 모드에서 마이그레이션 실행")
    run_migrations_offline()
else:
    print("🔄 온라인 모드에서 마이그레이션 실행")
    run_migrations_online()