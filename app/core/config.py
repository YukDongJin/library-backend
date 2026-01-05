# 📁 새로 생성된 파일: app/core/config.py
# 애플리케이션 설정 관리

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    - 환경 변수를 자동으로 로드
    - 타입 검증 및 기본값 설정
    - 개발/운영 환경 분리
    """
    
    # 서버 설정
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 데이터베이스 설정 (팀장 공유 환경)
    DATABASE_URL: str = "postgresql://tuser:test123@192.168.0.163:5432/testdb"
    DB_HOST: str = "192.168.0.163"
    DB_PORT: int = 5432
    DB_NAME: str = "testdb"
    DB_USER: str = "tuser"
    DB_PASSWORD: str = "test123"
    
    # AWS Cognito 설정
    AWS_REGION: str = "ap-northeast-2"
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_CLIENT_ID: str = ""
    
    # AWS S3 설정 (실제 값으로 수정하세요)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = ""
    S3_REGION: str = "ap-northeast-2"
    
    # JWT 설정
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS 설정
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # 프로젝트 정보
    PROJECT_NAME: str = "Library Management API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "FastAPI backend for library management system"
    
    class Config:
        # .env 파일에서 환경 변수 로드
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @property
    def database_url_sync(self) -> str:
        """동기 데이터베이스 URL (Alembic 마이그레이션용)"""
        # psycopg2 드라이버 사용 (동기)
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def database_url_async(self) -> str:
        """비동기 데이터베이스 URL (FastAPI용)"""
        # asyncpg 드라이버 사용 (비동기)
        if "postgresql+asyncpg://" in self.DATABASE_URL:
            return self.DATABASE_URL
        return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")


# 전역 설정 인스턴스
settings = Settings()

# 개발 환경에서만 설정 정보 출력
if settings.DEBUG:
    print("🔧 애플리케이션 설정 로드 완료")
    print(f"📊 데이터베이스: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    print(f"🌐 서버: {settings.HOST}:{settings.PORT}")
    print(f"🔐 JWT 알고리즘: {settings.JWT_ALGORITHM}")
    print(f"☁️ AWS 리전: {settings.AWS_REGION}")
    print(f"🪣 S3 버킷: {settings.S3_BUCKET_NAME}")
    
    # AWS 키가 설정되었는지 확인
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        print("✅ AWS 자격 증명 설정됨")
    else:
        print("⚠️ AWS 자격 증명이 설정되지 않음 - 개발 모드로 실행")
