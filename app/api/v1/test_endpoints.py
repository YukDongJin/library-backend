# 📁 새로 생성된 파일: app/api/v1/test_endpoints.py
# Cognito 없이 테스트할 수 있는 엔드포인트들

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import get_async_session
from app.crud.user import user_crud
from app.crud.library_item import library_item_crud
from app.schemas.user import UserCreate, UserResponse
from app.schemas.library_item import LibraryItemCreate, LibraryItemResponse
from app.schemas.common import SuccessResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/test_user",
    response_model=SuccessResponse[UserResponse],
    summary="테스트용 사용자 생성",
    description="Cognito 없이 테스트할 수 있는 사용자 생성 API"
)
async def create_test_user(
    *,
    db: AsyncSession = Depends(get_async_session),
    user_data: UserCreate
) -> SuccessResponse[UserResponse]:
    """
    테스트용 사용자 생성 API
    - Cognito 인증 없이 사용자 생성
    """
    try:
        user = await user_crud.create_user(db, user_in=user_data)
        
        logger.info(f"테스트 사용자 생성: {user.username} ({user.nickname})")
        
        return SuccessResponse(
            data=UserResponse.from_orm(user),
            message="테스트 사용자가 성공적으로 생성되었습니다"
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
    "/test_users",
    response_model=SuccessResponse[List[UserResponse]],
    summary="모든 사용자 조회",
    description="데이터베이스의 모든 사용자 조회 (테스트용)"
)
async def get_all_users(
    db: AsyncSession = Depends(get_async_session)
) -> SuccessResponse[List[UserResponse]]:
    """
    모든 사용자 조회 API (테스트용)
    """
    try:
        users = await user_crud.get_multi(db, skip=0, limit=100)
        
        return SuccessResponse(
            data=[UserResponse.from_orm(user) for user in users],
            message=f"총 {len(users)}명의 사용자를 조회했습니다"
        )
        
    except Exception as e:
        logger.error(f"사용자 목록 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 목록 조회 중 오류가 발생했습니다"
        )


@router.post(
    "/test_item/{user_id}",
    response_model=SuccessResponse[LibraryItemResponse],
    summary="테스트용 라이브러리 아이템 생성",
    description="특정 사용자의 라이브러리 아이템 생성 (테스트용)"
)
async def create_test_library_item(
    user_id: str,
    *,
    db: AsyncSession = Depends(get_async_session),
    item_data: LibraryItemCreate
) -> SuccessResponse[LibraryItemResponse]:
    """
    테스트용 라이브러리 아이템 생성 API
    """
    try:
        # 사용자 존재 확인
        user = await user_crud.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 아이템 생성
        item = await library_item_crud.create_item(
            db, user_id=user_id, item_in=item_data
        )
        
        logger.info(f"테스트 아이템 생성: {item.name} (사용자: {user.username})")
        
        return SuccessResponse(
            data=LibraryItemResponse.from_orm(item),
            message="테스트 아이템이 성공적으로 생성되었습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"아이템 생성 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="아이템 생성 중 오류가 발생했습니다"
        )


@router.get(
    "/test_items/{user_id}",
    response_model=SuccessResponse[List[LibraryItemResponse]],
    summary="사용자의 라이브러리 아이템 조회",
    description="특정 사용자의 모든 라이브러리 아이템 조회 (테스트용)"
)
async def get_user_library_items(
    user_id: str,
    db: AsyncSession = Depends(get_async_session)
) -> SuccessResponse[List[LibraryItemResponse]]:
    """
    사용자의 라이브러리 아이템 조회 API (테스트용)
    """
    try:
        # 사용자 존재 확인
        user = await user_crud.get(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # 아이템 조회
        items = await library_item_crud.get_by_user(
            db, user_id=user_id, skip=0, limit=100
        )
        
        return SuccessResponse(
            data=[LibraryItemResponse.from_orm(item) for item in items],
            message=f"사용자 {user.nickname}의 아이템 {len(items)}개를 조회했습니다"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"아이템 조회 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="아이템 조회 중 오류가 발생했습니다"
        )