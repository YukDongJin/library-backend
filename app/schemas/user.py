# 📁 새로 생성된 파일: app/schemas/user.py
# 사용자 관련 Pydantic 스키마

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid


class UserBase(BaseModel):
    """
    사용자 기본 스키마
    - 공통 필드 정의
    """
    nickname: str = Field(..., min_length=1, max_length=100, description="사용자 닉네임")
    
    @validator('nickname')
    def validate_nickname(cls, v):
        """닉네임 검증"""
        if not v or not v.strip():
            raise ValueError('닉네임은 필수입니다')
        return v.strip()


class UserCreate(UserBase):
    """
    사용자 생성 요청 스키마
    - 회원가입 시 사용
    """
    username: str = Field(..., description="AWS Cognito User ID")
    
    @validator('username')
    def validate_username(cls, v):
        """Cognito User ID 검증"""
        if not v or not v.strip():
            raise ValueError('Cognito User ID는 필수입니다')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "username": "cognito-user-id-12345",
                "nickname": "홍길동"
            }
        }


class UserUpdate(BaseModel):
    """
    사용자 정보 수정 요청 스키마
    - 프로필 수정 시 사용
    """
    nickname: Optional[str] = Field(None, min_length=1, max_length=100, description="사용자 닉네임")
    
    @validator('nickname')
    def validate_nickname(cls, v):
        """닉네임 검증"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('닉네임은 비어있을 수 없습니다')
        return v.strip() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "nickname": "새로운닉네임"
            }
        }


class UserResponse(UserBase):
    """
    사용자 정보 응답 스키마
    - API 응답에서 사용
    """
    id: uuid.UUID = Field(description="사용자 고유 ID")
    username: str = Field(description="AWS Cognito User ID")
    created_at: datetime = Field(description="계정 생성 시간")
    updated_at: datetime = Field(description="마지막 수정 시간")
    
    class Config:
        from_attributes = True  # SQLAlchemy 모델에서 자동 변환
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "cognito-user-id-12345",
                "nickname": "홍길동",
                "created_at": "2024-12-29T10:30:00Z",
                "updated_at": "2024-12-29T10:30:00Z"
            }
        }


class UserInDB(UserResponse):
    """
    데이터베이스 내부 사용자 스키마
    - 내부 로직에서 사용 (민감한 정보 포함 가능)
    """
    pass


class UserListResponse(BaseModel):
    """
    사용자 목록 응답 스키마
    - 관리자용 사용자 목록 조회
    """
    users: list[UserResponse] = Field(description="사용자 목록")
    total: int = Field(description="전체 사용자 수")
    
    class Config:
        schema_extra = {
            "example": {
                "users": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "username": "cognito-user-id-12345",
                        "nickname": "홍길동",
                        "created_at": "2024-12-29T10:30:00Z",
                        "updated_at": "2024-12-29T10:30:00Z"
                    }
                ],
                "total": 1
            }
        }


class UserStatsResponse(BaseModel):
    """
    사용자 통계 응답 스키마
    - 사용자의 라이브러리 통계 정보
    """
    total_items: int = Field(description="총 아이템 수")
    items_by_type: dict = Field(description="타입별 아이템 수")
    total_file_size: int = Field(description="총 파일 크기 (bytes)")
    recent_uploads: int = Field(description="최근 7일 업로드 수")
    
    class Config:
        schema_extra = {
            "example": {
                "total_items": 25,
                "items_by_type": {
                    "image": 15,
                    "document": 8,
                    "video": 2,
                    "file": 0
                },
                "total_file_size": 104857600,
                "recent_uploads": 3
            }
        }