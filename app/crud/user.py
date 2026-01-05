# 📁 새로 생성된 파일: app/crud/user.py
# 사용자 CRUD 작업

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.user import User
from app.models.library_item import LibraryItem
from app.schemas.user import UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """
    사용자 CRUD 작업 클래스
    - 사용자 관련 데이터베이스 작업 수행
    """

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[User]:
        """
        Cognito User ID(username)로 사용자 조회
        
        Args:
            db: 데이터베이스 세션
            username: AWS Cognito User ID
            
        Returns:
            조회된 사용자 또는 None
        """
        result = await db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_nickname(self, db: AsyncSession, *, nickname: str) -> Optional[User]:
        """
        닉네임으로 사용자 조회
        
        Args:
            db: 데이터베이스 세션
            nickname: 사용자 닉네임
            
        Returns:
            조회된 사용자 또는 None
        """
        result = await db.execute(
            select(User).where(User.nickname == nickname)
        )
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """
        새 사용자 생성
        
        Args:
            db: 데이터베이스 세션
            user_in: 사용자 생성 데이터
            
        Returns:
            생성된 사용자
            
        Raises:
            ValueError: 이미 존재하는 username 또는 nickname인 경우
        """
        # 중복 확인
        existing_user = await self.get_by_username(db, username=user_in.username)
        if existing_user:
            raise ValueError(f"이미 존재하는 사용자입니다: {user_in.username}")
        
        existing_nickname = await self.get_by_nickname(db, nickname=user_in.nickname)
        if existing_nickname:
            raise ValueError(f"이미 사용 중인 닉네임입니다: {user_in.nickname}")
        
        return await self.create(db, obj_in=user_in)

    async def update_user(
        self, 
        db: AsyncSession, 
        *, 
        user_id: str, 
        user_in: UserUpdate
    ) -> Optional[User]:
        """
        사용자 정보 수정
        
        Args:
            db: 데이터베이스 세션
            user_id: 수정할 사용자 ID
            user_in: 수정할 데이터
            
        Returns:
            수정된 사용자 또는 None
            
        Raises:
            ValueError: 이미 사용 중인 닉네임인 경우
        """
        user = await self.get(db, id=user_id)
        if not user:
            return None
        
        # 닉네임 중복 확인 (자신 제외)
        if user_in.nickname and user_in.nickname != user.nickname:
            existing_nickname = await self.get_by_nickname(db, nickname=user_in.nickname)
            if existing_nickname and existing_nickname.id != user.id:
                raise ValueError(f"이미 사용 중인 닉네임입니다: {user_in.nickname}")
        
        return await self.update(db, db_obj=user, obj_in=user_in)

    async def get_user_with_stats(self, db: AsyncSession, *, user_id: str) -> Optional[Dict[str, Any]]:
        """
        사용자 정보와 통계 함께 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            
        Returns:
            사용자 정보와 통계 딕셔너리
        """
        user = await self.get(db, id=user_id)
        if not user:
            return None
        
        # 라이브러리 아이템 통계 조회
        stats_query = select(
            func.count(LibraryItem.id).label('total_items'),
            func.sum(LibraryItem.file_size).label('total_file_size')
        ).where(
            and_(
                LibraryItem.user_profile_id == user_id,
                LibraryItem.deleted_at.is_(None)  # 삭제되지 않은 아이템만
            )
        )
        
        stats_result = await db.execute(stats_query)
        stats = stats_result.first()
        
        # 타입별 아이템 수 조회
        type_stats_query = select(
            LibraryItem.type,
            func.count(LibraryItem.id).label('count')
        ).where(
            and_(
                LibraryItem.user_profile_id == user_id,
                LibraryItem.deleted_at.is_(None)
            )
        ).group_by(LibraryItem.type)
        
        type_stats_result = await db.execute(type_stats_query)
        type_stats = {row.type.value: row.count for row in type_stats_result}
        
        # 최근 7일 업로드 수 조회
        from datetime import datetime, timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        recent_query = select(func.count(LibraryItem.id)).where(
            and_(
                LibraryItem.user_profile_id == user_id,
                LibraryItem.created_at >= recent_date,
                LibraryItem.deleted_at.is_(None)
            )
        )
        
        recent_result = await db.execute(recent_query)
        recent_uploads = recent_result.scalar()
        
        return {
            "user": user,
            "stats": {
                "total_items": stats.total_items or 0,
                "total_file_size": stats.total_file_size or 0,
                "items_by_type": type_stats,
                "recent_uploads": recent_uploads or 0
            }
        }

    async def search_users(
        self,
        db: AsyncSession,
        *,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        사용자 검색 (닉네임 기준)
        
        Args:
            db: 데이터베이스 세션
            query: 검색 쿼리
            skip: 건너뛸 레코드 수
            limit: 최대 조회 레코드 수
            
        Returns:
            검색된 사용자 리스트
        """
        return await self.search(
            db,
            query=query,
            search_fields=["nickname"],
            skip=skip,
            limit=limit
        )

    async def get_users_by_date_range(
        self,
        db: AsyncSession,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        날짜 범위로 사용자 조회
        
        Args:
            db: 데이터베이스 세션
            start_date: 시작 날짜 (ISO 형식)
            end_date: 종료 날짜 (ISO 형식)
            skip: 건너뛸 레코드 수
            limit: 최대 조회 레코드 수
            
        Returns:
            조회된 사용자 리스트
        """
        query = select(User)
        
        if start_date:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(User.created_at >= start_dt)
        
        if end_date:
            from datetime import datetime
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(User.created_at <= end_dt)
        
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def is_username_available(self, db: AsyncSession, *, username: str) -> bool:
        """
        사용자명 사용 가능 여부 확인
        
        Args:
            db: 데이터베이스 세션
            username: 확인할 사용자명
            
        Returns:
            사용 가능하면 True, 이미 사용 중이면 False
        """
        existing_user = await self.get_by_username(db, username=username)
        return existing_user is None

    async def is_nickname_available(self, db: AsyncSession, *, nickname: str, exclude_user_id: Optional[str] = None) -> bool:
        """
        닉네임 사용 가능 여부 확인
        
        Args:
            db: 데이터베이스 세션
            nickname: 확인할 닉네임
            exclude_user_id: 제외할 사용자 ID (수정 시 자신 제외)
            
        Returns:
            사용 가능하면 True, 이미 사용 중이면 False
        """
        query = select(User).where(User.nickname == nickname)
        
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        result = await db.execute(query)
        existing_user = result.scalar_one_or_none()
        return existing_user is None


# 전역 CRUD 인스턴스
user_crud = CRUDUser(User)