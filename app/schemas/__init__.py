# 📁 app/schemas/__init__.py
# Pydantic 스키마 패키지 초기화

"""
API 요청/응답 스키마 패키지
"""

from .user import UserCreate, UserUpdate, UserResponse
from .library_item import (
    LibraryItemCreate, 
    LibraryItemUpdate, 
    LibraryItemResponse, 
    LibraryItemInDB,
    ItemType,
    VisibilityType
)
from .common import BaseResponse, ErrorResponse, PaginationParams, PaginatedResponse

__all__ = [
    # User schemas
    "UserCreate", "UserUpdate", "UserResponse",
    # Library item schemas
    "LibraryItemCreate", "LibraryItemUpdate", "LibraryItemResponse", "LibraryItemInDB",
    "ItemType", "VisibilityType",
    # Common schemas
    "BaseResponse", "ErrorResponse", "PaginationParams", "PaginatedResponse"
]