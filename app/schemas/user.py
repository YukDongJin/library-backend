# 📁 app/schemas/user.py
# 사용자 관련 Pydantic 스키마 (팀원 users 테이블 사용)

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    nickname: Optional[str] = Field(None, max_length=255, description="사용자 닉네임")
    email: Optional[str] = Field(None, max_length=255, description="이메일")


class UserCreate(UserBase):
    """사용자 생성 요청 스키마 (Cognito 로그인 후 자동 생성)"""
    user_id: str = Field(..., description="Cognito sub (사용자 고유 ID)")
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or not v.strip():
            raise ValueError('user_id는 필수입니다')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
                "email": "user@example.com",
                "nickname": "홍길동"
            }
        }


class UserUpdate(BaseModel):
    """사용자 정보 수정 요청 스키마"""
    nickname: Optional[str] = Field(None, max_length=255, description="사용자 닉네임")
    email: Optional[str] = Field(None, max_length=255, description="이메일")
    status: Optional[str] = Field(None, max_length=50, description="사용자 상태")
    
    class Config:
        schema_extra = {
            "example": {
                "nickname": "새로운닉네임",
                "email": "new@example.com"
            }
        }


class UserResponse(UserBase):
    """사용자 정보 응답 스키마"""
    user_id: str = Field(description="Cognito sub (사용자 고유 ID)")
    status: Optional[str] = Field(None, description="사용자 상태")
    created_at: Optional[datetime] = Field(None, description="계정 생성 시간")
    updated_at: Optional[datetime] = Field(None, description="마지막 수정 시간")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab",
                "email": "user@example.com",
                "nickname": "홍길동",
                "status": "active",
                "created_at": "2024-12-29T10:30:00",
                "updated_at": "2024-12-29T10:30:00"
            }
        }


class UserStatsResponse(BaseModel):
    """사용자 통계 응답 스키마"""
    total_items: int = Field(description="총 아이템 수")
    total_file_size: int = Field(description="총 파일 크기 (bytes)")
    
    class Config:
        schema_extra = {
            "example": {
                "total_items": 25,
                "total_file_size": 104857600
            }
        }
