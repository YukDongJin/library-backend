# 📁 새로 생성된 파일: app/crud/library_item.py
# 라이브러리 아이템 CRUD 작업

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.library_item import LibraryItem, ItemType, VisibilityType
from app.models.user import User
from app.schemas.library_item import LibraryItemCreate, LibraryItemUpdate


class CRUDLibraryItem(CRUDBase[LibraryItem, LibraryItemCreate, LibraryItemUpdate]):
    """
    라이브러리 아이템 CRUD 작업 클래스
    - 라이브러리 아이템 관련 데이터베이스 작업 수행
    """

    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[LibraryItem]:
        """
        사용자의 라이브러리 아이템 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            skip: 건너뛸 레코드 수
            limit: 최대 조회 레코드 수
            include_deleted: 삭제된 아이템 포함 여부
            
        Returns:
            사용자의 라이브러리 아이템 리스트
        """
        query = select(LibraryItem).where(LibraryItem.user_id == user_id)
        
        if not include_deleted:
            query = query.where(LibraryItem.deleted_at.is_(None))
        
        query = query.order_by(desc(LibraryItem.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_type(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        item_type: ItemType,
        skip: int = 0,
        limit: int = 100
    ) -> List[LibraryItem]:
        """
        타입별 라이브러리 아이템 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            item_type: 아이템 타입
            skip: 건너뛸 레코드 수
            limit: 최대 조회 레코드 수
            
        Returns:
            해당 타입의 라이브러리 아이템 리스트
        """
        query = select(LibraryItem).where(
            and_(
                LibraryItem.user_id == user_id,
                LibraryItem.type == item_type,
                LibraryItem.deleted_at.is_(None)
            )
        ).order_by(desc(LibraryItem.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_public_items(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        item_type: Optional[ItemType] = None
    ) -> List[LibraryItem]:
        """
        공개 라이브러리 아이템 조회
        
        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 레코드 수
            limit: 최대 조회 레코드 수
            item_type: 필터링할 아이템 타입 (선택사항)
            
        Returns:
            공개 라이브러리 아이템 리스트
        """
        query = select(LibraryItem).where(
            and_(
                LibraryItem.visibility == VisibilityType.public,
                LibraryItem.deleted_at.is_(None)
            )
        )
        
        if item_type:
            query = query.where(LibraryItem.type == item_type)
        
        query = query.order_by(desc(LibraryItem.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def create_item(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        item_in: LibraryItemCreate
    ) -> LibraryItem:
        """
        새 라이브러리 아이템 생성
        
        Args:
            db: 데이터베이스 세션
            user_id: 소유자 사용자 ID
            item_in: 아이템 생성 데이터
            
        Returns:
            생성된 라이브러리 아이템
        """
        item_data = item_in.dict()
        item_data["user_id"] = user_id
        
        db_item = LibraryItem(**item_data)
        db.add(db_item)
        await db.commit()
        await db.refresh(db_item)
        return db_item

    async def update_item(
        self,
        db: AsyncSession,
        *,
        item_id: str,
        user_id: str,
        item_in: LibraryItemUpdate
    ) -> Optional[LibraryItem]:
        """
        라이브러리 아이템 수정 (소유자만 가능)
        
        Args:
            db: 데이터베이스 세션
            item_id: 수정할 아이템 ID
            user_id: 요청 사용자 ID
            item_in: 수정할 데이터
            
        Returns:
            수정된 라이브러리 아이템 또는 None
        """
        item = await self.get(db, id=item_id)
        if not item or str(item.user_id) != user_id:
            return None
        
        return await self.update(db, db_obj=item, obj_in=item_in)

    async def delete_item(
        self,
        db: AsyncSession,
        *,
        item_id: str,
        user_id: str,
        soft_delete: bool = True
    ) -> Optional[LibraryItem]:
        """
        라이브러리 아이템 삭제 (소유자만 가능)
        
        Args:
            db: 데이터베이스 세션
            item_id: 삭제할 아이템 ID
            user_id: 요청 사용자 ID
            soft_delete: 소프트 삭제 여부
            
        Returns:
            삭제된 라이브러리 아이템 또는 None
        """
        item = await self.get(db, id=item_id)
        if not item or str(item.user_id) != user_id:
            return None
        
        # S3 파일 삭제 (소프트 삭제든 영구 삭제든 S3 파일은 삭제)
        from app.services.s3_service import s3_service
        
        # 메인 파일 삭제
        if item.s3_key:
            await s3_service.delete_file(item.s3_key)
        
        # 썸네일 파일 삭제 (있는 경우)
        if item.s3_thumbnail_key:
            await s3_service.delete_file(item.s3_thumbnail_key)
        
        if soft_delete:
            return await self.soft_delete(db, id=item_id)
        else:
            return await self.remove(db, id=item_id)

    async def restore_item(
        self,
        db: AsyncSession,
        *,
        item_id: str,
        user_id: str
    ) -> Optional[LibraryItem]:
        """
        삭제된 라이브러리 아이템 복원 (소유자만 가능)
        
        Args:
            db: 데이터베이스 세션
            item_id: 복원할 아이템 ID
            user_id: 요청 사용자 ID
            
        Returns:
            복원된 라이브러리 아이템 또는 None
        """
        item = await self.get(db, id=item_id)
        if not item or str(item.user_id) != user_id:
            return None
        
        return await self.restore(db, id=item_id)

    async def search_items(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[LibraryItem]:
        """
        사용자의 라이브러리 아이템 검색
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            query: 검색 쿼리
            skip: 건너뛸 레코드 수
            limit: 최대 조회 레코드 수
            
        Returns:
            검색된 라이브러리 아이템 리스트
        """
        search_query = select(LibraryItem).where(
            and_(
                LibraryItem.user_id == user_id,
                LibraryItem.deleted_at.is_(None),
                or_(
                    LibraryItem.name.ilike(f"%{query}%"),
                    LibraryItem.original_filename.ilike(f"%{query}%"),
                    LibraryItem.preview_text.ilike(f"%{query}%")
                )
            )
        ).order_by(desc(LibraryItem.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(search_query)
        return result.scalars().all()

    async def get_user_stats(
        self,
        db: AsyncSession,
        *,
        user_id: str
    ) -> Dict[str, Any]:
        """
        사용자의 라이브러리 통계 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            
        Returns:
            통계 정보 딕셔너리
        """
        # 전체 아이템 수 및 파일 크기
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
        
        # 타입별 아이템 수
        type_stats_query = select(
            LibraryItem.type,
            func.count(LibraryItem.id).label('count')
        ).where(
            and_(
                LibraryItem.user_id == user_id,
                LibraryItem.deleted_at.is_(None)
            )
        ).group_by(LibraryItem.type)
        
        type_stats_result = await db.execute(type_stats_query)
        type_stats = {row.type.value: row.count for row in type_stats_result}
        
        # 최근 7일 업로드 수
        from datetime import datetime, timedelta
        recent_date = datetime.utcnow() - timedelta(days=7)
        
        recent_query = select(func.count(LibraryItem.id)).where(
            and_(
                LibraryItem.user_id == user_id,
                LibraryItem.created_at >= recent_date,
                LibraryItem.deleted_at.is_(None)
            )
        )
        
        recent_result = await db.execute(recent_query)
        recent_uploads = recent_result.scalar()
        
        return {
            "total_items": stats.total_items or 0,
            "total_file_size": stats.total_file_size or 0,
            "items_by_type": type_stats,
            "recent_uploads": recent_uploads or 0
        }

    async def get_items_by_date_range(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[LibraryItem]:
        """
        날짜 범위로 라이브러리 아이템 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            start_date: 시작 날짜 (ISO 형식)
            end_date: 종료 날짜 (ISO 형식)
            skip: 건너뛸 레코드 수
            limit: 최대 조회 레코드 수
            
        Returns:
            조회된 라이브러리 아이템 리스트
        """
        query = select(LibraryItem).where(
            and_(
                LibraryItem.user_id == user_id,
                LibraryItem.deleted_at.is_(None)
            )
        )
        
        if start_date:
            from datetime import datetime
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(LibraryItem.created_at >= start_dt)
        
        if end_date:
            from datetime import datetime
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(LibraryItem.created_at <= end_dt)
        
        query = query.order_by(desc(LibraryItem.created_at)).offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def count_user_items(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        item_type: Optional[ItemType] = None,
        include_deleted: bool = False
    ) -> int:
        """
        사용자의 라이브러리 아이템 수 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            item_type: 필터링할 아이템 타입 (선택사항)
            include_deleted: 삭제된 아이템 포함 여부
            
        Returns:
            아이템 수
        """
        query = select(func.count(LibraryItem.id)).where(
            LibraryItem.user_id == user_id
        )
        
        if not include_deleted:
            query = query.where(LibraryItem.deleted_at.is_(None))
        
        if item_type:
            query = query.where(LibraryItem.type == item_type)
        
        result = await db.execute(query)
        return result.scalar()


# 전역 CRUD 인스턴스
library_item_crud = CRUDLibraryItem(LibraryItem)