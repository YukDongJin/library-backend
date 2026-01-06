# 📁 새로 생성된 파일: app/core/config.py
# 애플리케이션 설정 관리

from pydantic_settings import BaseSettings
from typing import List
import os
import boto3
import json


def get_secret_from_aws(secret_name: str, region: str = "us-east-1") -> str:
    """AWS Secrets Manager에서 비밀번호 가져오기"""
    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secret = response.get("SecretString", "")
        # JSON 형식이면 파싱
        try:
            secret_dict = json.loads(secret)
            return secret_dict.get("password", secret)
        except json.JSONDecodeError:
            return secret
    except Exception as e:
        print(f"⚠️ Secrets Manager 호출 실패: {e}")
        return ""


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
    
    # 데이터베이스 설정 (AWS RDS)
    DATABASE_URL: str = "postgresql://fproject_user@fproject-dev-postgres.c9eksq6cmh3c.us-east-1.rds.amazonaws.com:5432/fproject_db"
    DB_HOST: str = "fproject-dev-postgres.c9eksq6cmh3c.us-east-1.rds.amazonaws.com"
    DB_PORT: int = 5432
    DB_NAME: str = "fproject_db"
    DB_USER: str = "fproject_user"
    DB_PASSWORD: str = ""
    
    # AWS Secrets Manager 설정
    USE_SECRETS_MANAGER: bool = True
    DB_SECRET_NAME: str = "library-api/db-password"
    
    # AWS Cognito 설정
    AWS_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: str = "us-east-1_oesTGe9D5"
    COGNITO_CLIENT_ID: str = "6ugujl077j6fmcqgptjmn91b7e"
    
    # AWS S3 설정 (IRSA 사용 - Access Key 불필요)
    S3_BUCKET_NAME: str = "library-bucket-youkkk"
    S3_REGION: str = "us-east-1"
    
    # 백엔드 기본 URL (파일 프록시용)
    BACKEND_BASE_URL: str = "https://library.aws11.shop"
    
    # JWT 설정
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS 설정 (main.py에서 환경변수로 직접 처리)
    # ALLOWED_ORIGINS는 k8s-deployment.yaml에서 설정
    
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
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def database_url_async(self) -> str:
        """비동기 데이터베이스 URL (FastAPI용)"""
        # asyncpg 드라이버 사용 (비동기)
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


# 전역 설정 인스턴스
settings = Settings()

# Secrets Manager에서 DB 비밀번호 가져오기
if settings.USE_SECRETS_MANAGER and not settings.DB_PASSWORD:
    print("🔐 AWS Secrets Manager에서 DB 비밀번호 가져오는 중...")
    settings.DB_PASSWORD = get_secret_from_aws(
        settings.DB_SECRET_NAME, 
        settings.AWS_REGION
    )
    if settings.DB_PASSWORD:
        print("✅ DB 비밀번호 로드 완료")
    else:
        print("⚠️ DB 비밀번호를 가져오지 못했습니다")

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
