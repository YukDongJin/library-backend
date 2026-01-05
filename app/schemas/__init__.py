# 📁 새로 생성된 파일: app/schemas/__init__.py
# Pydantic 스키마 패키지 초기화

"""
API 요청/응답 스키마 패키지
- 데이터 검증 및 직렬화를 위한 Pydantic 모델들
- 사용자 및 라이브러리 아이템 관련 스키마 정의
"""

from .user import UserCreate, UserUpdate, UserResponse, UserInDB
from .library_item import (
    LibraryItemCreate, 
    LibraryItemUpdate, 
    LibraryItemResponse, 
    LibraryItemInDB,
    ItemType,
    VisibilityType
)
from .common import BaseResponse, ErrorResponse, PaginationParams, PaginatedResponse

# 모든 스키마를 한 곳에서 import할 수 있도록 export
__all__ = [
    # User schemas
    "UserCreate", "UserUpdate", "UserResponse", "UserInDB",
    # Library item schemas
    "LibraryItemCreate", "LibraryItemUpdate", "LibraryItemResponse", "LibraryItemInDB",
    "ItemType", "VisibilityType",
    # Common schemas
    "BaseResponse", "ErrorResponse", "PaginationParams", "PaginatedResponse"
]