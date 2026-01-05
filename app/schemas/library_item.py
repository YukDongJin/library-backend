# 📁 새로 생성된 파일: app/schemas/library_item.py
# 라이브러리 아이템 관련 Pydantic 스키마

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid
from enum import Enum


class ItemType(str, Enum):
    """아이템 타입 열거형"""
    image = "image"
    document = "document"
    file = "file"
    video = "video"


class VisibilityType(str, Enum):
    """공개 범위 열거형"""
    public = "public"
    private = "private"


class LibraryItemBase(BaseModel):
    """
    라이브러리 아이템 기본 스키마
    - 공통 필드 정의
    """
    name: str = Field(..., min_length=1, max_length=255, description="아이템 표시명")
    type: ItemType = Field(..., description="아이템 타입")
    visibility: VisibilityType = Field(VisibilityType.private, description="공개 범위")
    
    @validator('name')
    def validate_name(cls, v):
        """아이템 이름 검증"""
        if not v or not v.strip():
            raise ValueError('아이템 이름은 필수입니다')
        return v.strip()


class LibraryItemCreate(LibraryItemBase):
    """
    라이브러리 아이템 생성 요청 스키마
    - 파일 업로드 후 메타데이터 저장 시 사용
    """
    mime_type: str = Field(..., description="MIME 타입")
    s3_key: str = Field(..., description="S3 파일 키")
    s3_thumbnail_key: Optional[str] = Field(None, description="S3 썸네일 키")
    file_size: int = Field(..., gt=0, description="파일 크기 (bytes)")
    original_filename: str = Field(..., description="원본 파일명")
    preview_text: Optional[str] = Field(None, description="미리보기 텍스트")
    
    @validator('mime_type')
    def validate_mime_type(cls, v):
        """MIME 타입 검증"""
        if not v or not v.strip():
            raise ValueError('MIME 타입은 필수입니다')
        return v.strip()
    
    @validator('s3_key')
    def validate_s3_key(cls, v):
        """S3 키 검증"""
        if not v or not v.strip():
            raise ValueError('S3 키는 필수입니다')
        return v.strip()
    
    @validator('original_filename')
    def validate_original_filename(cls, v):
        """원본 파일명 검증"""
        if not v or not v.strip():
            raise ValueError('원본 파일명은 필수입니다')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "name": "제주도 여행 사진",
                "type": "image",
                "visibility": "private",
                "mime_type": "image/jpeg",
                "s3_key": "uploads/2024/12/a1b2c3d4-e5f6-7890.jpg",
                "s3_thumbnail_key": "thumbnails/2024/12/a1b2c3d4-e5f6-7890_thumb.jpg",
                "file_size": 2400000,
                "original_filename": "IMG_20241224.jpg",
                "preview_text": None
            }
        }


class LibraryItemUpdate(BaseModel):
    """
    라이브러리 아이템 수정 요청 스키마
    - 아이템 정보 수정 시 사용
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="아이템 표시명")
    visibility: Optional[VisibilityType] = Field(None, description="공개 범위")
    preview_text: Optional[str] = Field(None, description="미리보기 텍스트")
    
    @validator('name')
    def validate_name(cls, v):
        """아이템 이름 검증"""
        if v is not None and (not v or not v.strip()):
            raise ValueError('아이템 이름은 비어있을 수 없습니다')
        return v.strip() if v else v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "수정된 아이템 이름",
                "visibility": "public",
                "preview_text": "수정된 미리보기 텍스트"
            }
        }


class LibraryItemResponse(LibraryItemBase):
    """
    라이브러리 아이템 응답 스키마
    - API 응답에서 사용
    """
    id: uuid.UUID = Field(description="아이템 고유 ID")
    user_profile_id: uuid.UUID = Field(description="소유자 사용자 ID")
    mime_type: str = Field(description="MIME 타입")
    s3_key: str = Field(description="S3 파일 키")
    s3_thumbnail_key: Optional[str] = Field(None, description="S3 썸네일 키")
    file_size: int = Field(description="파일 크기 (bytes)")
    original_filename: str = Field(description="원본 파일명")
    preview_text: Optional[str] = Field(None, description="미리보기 텍스트")
    file_url: Optional[str] = Field(None, description="파일 다운로드 URL")
    thumbnail_url: Optional[str] = Field(None, description="썸네일 URL")
    is_deleted: bool = Field(description="삭제 여부")
    created_at: datetime = Field(description="생성 시간")
    updated_at: datetime = Field(description="수정 시간")
    deleted_at: Optional[datetime] = Field(None, description="삭제 시간")
    
    class Config:
        from_attributes = True  # SQLAlchemy 모델에서 자동 변환
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_profile_id": "456e7890-e89b-12d3-a456-426614174001",
                "name": "제주도 여행 사진",
                "type": "image",
                "visibility": "private",
                "mime_type": "image/jpeg",
                "s3_key": "uploads/2024/12/a1b2c3d4-e5f6-7890.jpg",
                "s3_thumbnail_key": "thumbnails/2024/12/a1b2c3d4-e5f6-7890_thumb.jpg",
                "file_size": 2400000,
                "original_filename": "IMG_20241224.jpg",
                "preview_text": None,
                "file_url": "https://bucket.s3.amazonaws.com/uploads/2024/12/a1b2c3d4-e5f6-7890.jpg",
                "thumbnail_url": "https://bucket.s3.amazonaws.com/thumbnails/2024/12/a1b2c3d4-e5f6-7890_thumb.jpg",
                "is_deleted": False,
                "created_at": "2024-12-29T10:30:00Z",
                "updated_at": "2024-12-29T10:30:00Z",
                "deleted_at": None
            }
        }


class LibraryItemInDB(LibraryItemResponse):
    """
    데이터베이스 내부 라이브러리 아이템 스키마
    - 내부 로직에서 사용
    """
    pass


class LibraryItemListResponse(BaseModel):
    """
    라이브러리 아이템 목록 응답 스키마
    """
    items: list[LibraryItemResponse] = Field(description="아이템 목록")
    total: int = Field(description="전체 아이템 수")
    
    class Config:
        schema_extra = {
            "example": {
                "items": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_profile_id": "456e7890-e89b-12d3-a456-426614174001",
                        "name": "제주도 여행 사진",
                        "type": "image",
                        "visibility": "private",
                        "mime_type": "image/jpeg",
                        "file_size": 2400000,
                        "original_filename": "IMG_20241224.jpg",
                        "is_deleted": False,
                        "created_at": "2024-12-29T10:30:00Z",
                        "updated_at": "2024-12-29T10:30:00Z"
                    }
                ],
                "total": 1
            }
        }


class PresignedUrlRequest(BaseModel):
    """
    Presigned URL 요청 스키마
    - S3 업로드용 URL 생성 요청
    """
    filename: str = Field(..., description="업로드할 파일명")
    content_type: str = Field(..., description="파일 MIME 타입")
    file_size: int = Field(..., gt=0, description="파일 크기 (bytes)")
    
    @validator('filename')
    def validate_filename(cls, v):
        """파일명 검증"""
        if not v or not v.strip():
            raise ValueError('파일명은 필수입니다')
        return v.strip()
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """MIME 타입 검증"""
        if not v or not v.strip():
            raise ValueError('Content-Type은 필수입니다')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "filename": "IMG_20241224.jpg",
                "content_type": "image/jpeg",
                "file_size": 2400000
            }
        }


class PresignedUrlResponse(BaseModel):
    """
    Presigned URL 응답 스키마
    """
    upload_url: str = Field(description="S3 업로드 URL")
    s3_key: str = Field(description="S3 파일 키")
    expires_in: int = Field(description="URL 만료 시간 (초)")
    fields: Optional[dict] = Field(default={}, description="추가 업로드 필드")
    file_info: Optional[dict] = Field(default={}, description="파일 정보")
    
    class Config:
        schema_extra = {
            "example": {
                "upload_url": "https://bucket.s3.amazonaws.com/uploads/2024/12/user123/a1b2c3d4-e5f6-7890.jpg?X-Amz-Algorithm=...",
                "s3_key": "uploads/2024/12/user123/a1b2c3d4-e5f6-7890.jpg",
                "expires_in": 3600,
                "fields": {
                    "Content-Type": "image/jpeg",
                    "x-amz-meta-user-id": "user123"
                },
                "file_info": {
                    "item_type": "image",
                    "formatted_size": "2.4 MB",
                    "needs_thumbnail": True
                }
            }
        }