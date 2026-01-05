# 📁 새로 생성된 파일: app/api/v1/users.py
# 사용자 관련 API 엔드포인트

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user, get_current_active_user, common_parameters, CommonQueryParams
from app.crud.user import user_crud
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse, UserStatsResponse
)
from app.schemas.common import SuccessResponse, ErrorResponse, PaginatedResponse, PaginationInfo
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="사용자 생성",
    description="새로운 사용자를 생성합니다. AWS Cognito 회원가입 후 호출하여 사용자 프로필을 생성합니다."
)
async def create_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate
) -> SuccessResponse[UserResponse]:
    """
    사용자 생성 API
    - AWS Cognito 회원가입 후 사용자 프로필 생성
    - username은 Cognito User ID를 사용
    """
    try:
        # 사용자 생성
        user = await user_crud.create_user(db, user_in=user_in)
        
        logger.info(f"새 사용자 생성: {user.username} ({user.nickname})")
        
        return SuccessResponse(
            data=UserResponse.from_orm(user),
            message="사용자가 성공적으로 생성되었습니다"
        )
        
    except ValueError as e:
        logger.warning(f"사용자 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"사용자 생성 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 생성 중 오류가 발생했습니다"
        )


@router.get(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="현재 사용자 정보 조회",
    description="현재 로그인한 사용자의 정보를 조회합니다."
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> SuccessResponse[UserResponse]:
    """
    현재 사용자 정보 조회 API
    """
    return SuccessResponse(
        data=UserResponse.from_orm(current_user),
        message="사용자 정보 조회 성공"
    )


@router.put(
    "/me",
    response_model=SuccessResponse[UserResponse],
    summary="현재 사용자 정보 수정",
    description="현재 로그인한 사용자의 정보를 수정합니다."
)
async def update_current_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user)
) -> SuccessResponse[UserResponse]:
    """
    현재 사용자 정보 수정 API
    """
    try:
        # 사용자 정보 수정
        updated_user = await user_crud.update_user(
            db, user_id=str(current_user.id), user_in=user_in
        )
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        logger.info(f"사용자 정보 수정: {updated_user.username}")
        
        return SuccessResponse(
            data=UserResponse.from_orm(updated_user),
            message="사용자 정보가 성공적으로 수정되었습니다"
        )
        
    except ValueError as e:
        logger.warning(f"사용자 정보 수정 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"사용자 정보 수정 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 수정 중 오류가 발생했습니다"
        )


@router.get(
    "/me/stats",
    response_model=SuccessResponse[UserStatsResponse],
    summary="현재 사용자 통계 조회",
    description="현재 로그인한 사용자의 라이브러리 통계를 조회합니다."
)
async def get_current_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> SuccessResponse[UserStatsResponse]:
    """
    현재 사용자 통계 조회 API
    """
    try:
        # 사용자 통계 조회
        user_with_stats = await user_crud.get_user_with_stats(
            db, user_id=str(current_user.id)
        )
        
        if not user_with_stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        stats = user_with_stats["stats"]
        
        return SuccessResponse(
            data=UserStatsResponse(**stats),
            message="사용자 통계 조회 성공"
        )
        
    except Exception as e:
        logger.error(f"사용자 통계 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 통계 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/{user_id}",
    response_model=SuccessResponse[UserResponse],
    summary="특정 사용자 정보 조회",
    description="특정 사용자의 정보를 조회합니다."
)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[UserResponse]:
    """
    특정 사용자 정보 조회 API
    """
    try:
        user = await user_crud.get(db, id=user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        return SuccessResponse(
            data=UserResponse.from_orm(user),
            message="사용자 정보 조회 성공"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse],
    summary="사용자 목록 조회",
    description="사용자 목록을 조회합니다. (관리자용)"
)
async def get_users(
    db: AsyncSession = Depends(get_db),
    commons: CommonQueryParams = Depends(common_parameters),
    search: Optional[str] = Query(None, description="검색 키워드 (닉네임)")
) -> PaginatedResponse[UserResponse]:
    """
    사용자 목록 조회 API (관리자용)
    """
    try:
        if search:
            # 검색 모드
            users = await user_crud.search_users(
                db, query=search, skip=commons.skip, limit=commons.limit
            )
            total = len(users)  # 검색 결과는 정확한 총 개수 계산이 복잡하므로 근사치 사용
        else:
            # 일반 목록 조회
            users = await user_crud.get_multi(
                db, skip=commons.skip, limit=commons.limit
            )
            total = await user_crud.count(db)
        
        # 페이지네이션 정보 계산
        pages = (total + commons.limit - 1) // commons.limit
        current_page = (commons.skip // commons.limit) + 1
        
        pagination_info = PaginationInfo(
            page=current_page,
            size=commons.limit,
            total=total,
            pages=pages,
            has_next=current_page < pages,
            has_prev=current_page > 1
        )
        
        return PaginatedResponse(
            data=[UserResponse.from_orm(user) for user in users],
            pagination=pagination_info,
            message="사용자 목록 조회 성공"
        )
        
    except Exception as e:
        logger.error(f"사용자 목록 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 목록 조회 중 오류가 발생했습니다"
        )


@router.get(
    "/check/username/{username}",
    response_model=SuccessResponse[dict],
    summary="사용자명 사용 가능 여부 확인",
    description="사용자명(Cognito User ID)이 사용 가능한지 확인합니다."
)
async def check_username_availability(
    username: str,
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse[dict]:
    """
    사용자명 사용 가능 여부 확인 API
    """
    try:
        is_available = await user_crud.is_username_available(db, username=username)
        
        return SuccessResponse(
            data={"available": is_available},
            message="사용자명 확인 완료"
        )
        
    except Exception as e:
        logger.error(f"사용자명 확인 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자명 확인 중 오류가 발생했습니다"
        )


@router.get(
    "/check/nickname/{nickname}",
    response_model=SuccessResponse[dict],
    summary="닉네임 사용 가능 여부 확인",
    description="닉네임이 사용 가능한지 확인합니다."
)
async def check_nickname_availability(
    nickname: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> SuccessResponse[dict]:
    """
    닉네임 사용 가능 여부 확인 API
    """
    try:
        exclude_user_id = str(current_user.id) if current_user else None
        is_available = await user_crud.is_nickname_available(
            db, nickname=nickname, exclude_user_id=exclude_user_id
        )
        
        return SuccessResponse(
            data={"available": is_available},
            message="닉네임 확인 완료"
        )
        
    except Exception as e:
        logger.error(f"닉네임 확인 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="닉네임 확인 중 오류가 발생했습니다"
        )