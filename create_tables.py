#!/usr/bin/env python3
"""
SQLAlchemy로 직접 테이블 생성하는 스크립트
Alembic 없이 간단하게 테이블을 만들 수 있습니다.
"""

import asyncio
from sqlalchemy import create_engine
from app.core.config import settings
from app.database.models_config import Base

# 모든 모델 import (테이블 생성을 위해 필요)
from app.models.user import User
from app.models.library_item import LibraryItem

def create_tables():
    """동기 방식으로 테이블 생성"""
    print("🔄 SQLAlchemy로 테이블 생성 중...")
    
    # 동기 엔진 생성
    engine = create_engine(settings.database_url_sync)
    
    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    print("✅ 테이블 생성 완료!")
    print("📊 생성된 테이블:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

if __name__ == "__main__":
    create_tables()