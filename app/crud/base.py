# 📁 새로 생성된 파일: app/crud/base.py
# 기본 CRUD 클래스 정의

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from app.database.base import Base

# 제네릭 타입 변수
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    기본 CRUD 클래스
    - 공통 데이터베이스 작업 메서드 제공
    - 제네릭을 사용하여 타입 안전성 보장
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        CRUD 객체 초기화
        
        Args:
            model: SQLAlchemy 모델 클래스
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        ID로 단일 객체 조회
        
        Args:
            db: 데이터베이스 세션
            id: 조회할 객체의 ID
            
        Returns:
            조회된 객체 또는 None
        """
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, 
        db: AsyncSession, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> List[ModelType]:
        """
        여러 객체 조회 (페이지네이션 지원)
        
        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 레코드 수
            limit: 최대 조회 레코드 수
            filters: 필터 조건 딕셔너리
            order_by: 정렬 기준 필드명
            
        Returns:
            조회된 객체 리스트
        """
        query = select(self.model)
        
        # 필터 적용
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        
        # 정렬 적용
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by).desc())
        elif hasattr(self.model, 'created_at'):
            query = query.order_by(self.model.created_at.desc())
        
        # 페이지네이션 적용
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    async def count(
        self, 
        db: AsyncSession, 
        *, 
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        조건에 맞는 레코드 수 조회
        
        Args:
            db: 데이터베이스 세션
            filters: 필터 조건 딕셔너리
            
        Returns:
            레코드 수
        """
        query = select(func.count(self.model.id))
        
        # 필터 적용
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        
        result = await db.execute(query)
        return result.scalar()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        새 객체 생성
        
        Args:
            db: 데이터베이스 세션
            obj_in: 생성할 객체 데이터
            
        Returns:
            생성된 객체
        """
        obj_in_data = obj_in.dict()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        기존 객체 수정
        
        Args:
            db: 데이터베이스 세션
            db_obj: 수정할 데이터베이스 객체
            obj_in: 수정할 데이터
            
        Returns:
            수정된 객체
        """
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        객체 삭제 (하드 삭제)
        
        Args:
            db: 데이터베이스 세션
            id: 삭제할 객체의 ID
            
        Returns:
            삭제된 객체 또는 None
        """
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def soft_delete(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        객체 소프트 삭제 (deleted_at 필드가 있는 경우)
        
        Args:
            db: 데이터베이스 세션
            id: 삭제할 객체의 ID
            
        Returns:
            삭제된 객체 또는 None
        """
        obj = await self.get(db, id=id)
        if obj and hasattr(obj, 'deleted_at'):
            obj.soft_delete()
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
        return obj

    async def restore(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        소프트 삭제된 객체 복원
        
        Args:
            db: 데이터베이스 세션
            id: 복원할 객체의 ID
            
        Returns:
            복원된 객체 또는 None
        """
        obj = await self.get(db, id=id)
        if obj and hasattr(obj, 'deleted_at') and obj.deleted_at:
            obj.restore()
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
        return obj

    async def search(
        self,
        db: AsyncSession,
        *,
        query: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100
    ) -> List[ModelType]:
        """
        텍스트 검색
        
        Args:
            db: 데이터베이스 세션
            query: 검색 쿼리
            search_fields: 검색할 필드 리스트
            skip: 건너뛸 레코드 수
            limit: 최대 조회 레코드 수
            
        Returns:
            검색 결과 리스트
        """
        search_query = select(self.model)
        
        # 검색 조건 생성
        search_conditions = []
        for field in search_fields:
            if hasattr(self.model, field):
                field_attr = getattr(self.model, field)
                search_conditions.append(field_attr.ilike(f"%{query}%"))
        
        if search_conditions:
            search_query = search_query.where(or_(*search_conditions))
        
        # 정렬 및 페이지네이션
        if hasattr(self.model, 'created_at'):
            search_query = search_query.order_by(self.model.created_at.desc())
        
        search_query = search_query.offset(skip).limit(limit)
        
        result = await db.execute(search_query)
        return result.scalars().all()