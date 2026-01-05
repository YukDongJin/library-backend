# 📁 새로 생성된 파일: app/schemas/common.py
# 공통 Pydantic 스키마 정의

from pydantic import BaseModel, Field
from typing import Any, Optional, List, Generic, TypeVar
from datetime import datetime

# 제네릭 타입 변수
T = TypeVar('T')


class BaseResponse(BaseModel):
    """
    기본 API 응답 스키마
    - 모든 API 응답의 기본 구조
    """
    success: bool = Field(description="요청 성공 여부")
    message: Optional[str] = Field(None, description="응답 메시지")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseResponse):
    """
    에러 응답 스키마
    - API 에러 발생 시 사용
    """
    success: bool = Field(False, description="요청 성공 여부 (항상 False)")
    error_code: Optional[str] = Field(None, description="에러 코드")
    details: Optional[dict] = Field(None, description="에러 상세 정보")


class SuccessResponse(BaseResponse, Generic[T]):
    """
    성공 응답 스키마 (제네릭)
    - 데이터를 포함한 성공 응답
    """
    success: bool = Field(True, description="요청 성공 여부 (항상 True)")
    data: T = Field(description="응답 데이터")


class PaginationParams(BaseModel):
    """
    페이지네이션 파라미터
    - 목록 조회 시 사용
    """
    page: int = Field(1, ge=1, description="페이지 번호 (1부터 시작)")
    size: int = Field(20, ge=1, le=100, description="페이지 크기 (1-100)")
    
    @property
    def offset(self) -> int:
        """데이터베이스 OFFSET 계산"""
        return (self.page - 1) * self.size


class PaginationInfo(BaseModel):
    """
    페이지네이션 정보
    - 페이지네이션 메타데이터
    """
    page: int = Field(description="현재 페이지 번호")
    size: int = Field(description="페이지 크기")
    total: int = Field(description="전체 항목 수")
    pages: int = Field(description="전체 페이지 수")
    has_next: bool = Field(description="다음 페이지 존재 여부")
    has_prev: bool = Field(description="이전 페이지 존재 여부")


class PaginatedResponse(BaseResponse, Generic[T]):
    """
    페이지네이션된 응답 스키마
    - 목록 데이터와 페이지네이션 정보 포함
    """
    success: bool = Field(True, description="요청 성공 여부")
    data: List[T] = Field(description="데이터 목록")
    pagination: PaginationInfo = Field(description="페이지네이션 정보")


class FilterParams(BaseModel):
    """
    필터링 파라미터
    - 검색 및 필터링 시 사용
    """
    search: Optional[str] = Field(None, description="검색 키워드")
    sort_by: Optional[str] = Field("created_at", description="정렬 기준 필드")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="정렬 순서")
    
    def get_sort_column(self, model_class):
        """모델 클래스에서 정렬 컬럼 가져오기"""
        if hasattr(model_class, self.sort_by):
            return getattr(model_class, self.sort_by)
        return getattr(model_class, "created_at")  # 기본값


class HealthCheckResponse(BaseModel):
    """
    헬스체크 응답 스키마
    """
    status: str = Field("healthy", description="서비스 상태")
    timestamp: datetime = Field(description="응답 시간")
    version: str = Field(description="API 버전")
    database: str = Field(description="데이터베이스 연결 상태")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }