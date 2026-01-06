# 📁 app/crud/user.py
# 사용자 CRUD 작업 (팀원 users 테이블 사용)

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.crud.base import CRUDBase
from app.models.user import User
from app.models.library_item import LibraryItem
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """사용자 CRUD 작업 클래스"""

    async def get_by_user_id(self, db: AsyncSession, *, user_id: str) -> Optional[User]:
        """
        user_id (Cognito sub)로 사용자 조회
        """
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_nickname(self, db: AsyncSession, *, nickname: str) -> Optional[User]:
        """닉네임으로 사용자 조회"""
        result = await db.execute(
            select(User).where(User.nickname == nickname)
        )
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """
        새 사용자 생성
        - Cognito 로그인 후 첫 API 호출 시 자동 생성
        """
        # 중복 확인
        existing_user = await self.get_by_user_id(db, user_id=user_in.user_id)
        if existing_user:
            raise ValueError(f"이미 존재하는 사용자입니다: {user_in.user_id}")
        
        # 사용자 생성
        db_user = User(
            user_id=user_in.user_id,
            email=user_in.email,
            nickname=user_in.nickname,
            status="active"
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def update_user(
        self, 
        db: AsyncSession, 
        *, 
        user_id: str, 
        user_in: UserUpdate
    ) -> Optional[User]:
        """사용자 정보 수정"""
        user = await self.get_by_user_id(db, user_id=user_id)
        if not user:
            return None
        
        update_data = user_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user

    async def get_user_with_stats(self, db: AsyncSession, *, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 정보와 통계 함께 조회"""
        user = await self.get_by_user_id(db, user_id=user_id)
        if not user:
            return None
        
        # 라이브러리 아이템 통계 조회
        stats_query = select(
            func.count(LibraryItem.id).label('total_items'),
            func.sum(LibraryItem.file_size).label('total_file_size')
        ).where(
            and_(
                LibraryItem.user_id == user_id,
                LibraryItem.deleted_at.is_(None)
            )
        )
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.first()
        
        return {
            "user": user,
            "stats": {
                "total_items": stats.total_items or 0,
                "total_file_size": stats.total_file_size or 0
            }
        }

    # 호환성을 위한 별칭 메서드
    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """get_by_user_id의 별칭 (호환성)"""
        return await self.get_by_user_id(db, user_id=username)


# 전역 CRUD 인스턴스
user_crud = CRUDUser(User)
