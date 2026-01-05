# 📁 새로 생성된 파일: app/models/user.py
# 사용자 테이블 SQLAlchemy 모델

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.models_config import Base
import uuid


class User(Base):
    """
    사용자 테이블 모델
    - 사용자가 제공한 테이블 구조를 정확히 반영
    - users_youk 테이블: id(uuid), username(uuid/cognito_id), nickname(text), created_at, updated_at
    """
    __tablename__ = "users_youk"

    # Primary Key: UUID 타입
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        comment="사용자 고유 ID (UUID)"
    )
    
    # AWS Cognito User ID를 저장하는 필드
    # 사용자 이미지에서 'username' 필드로 표시됨 (cognito_id 역할)
    username = Column(
        String(255), 
        unique=True, 
        nullable=False,
        comment="AWS Cognito User ID (username 필드명이지만 cognito_id 역할)"
    )
    
    # 사용자 닉네임
    nickname = Column(
        Text, 
        nullable=False,
        comment="사용자 표시 닉네임"
    )
    
    # 생성 시간 (자동 설정)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="계정 생성 시간"
    )
    
    # 수정 시간 (자동 업데이트)
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="마지막 수정 시간"
    )

    # 관계 설정: 사용자가 소유한 라이브러리 아이템들
    library_items = relationship(
        "LibraryItem", 
        back_populates="user",
        cascade="all, delete-orphan",  # 사용자 삭제 시 관련 아이템도 삭제
        lazy="dynamic"  # 필요할 때만 로드
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, nickname={self.nickname})>"

    def __str__(self):
        return f"User: {self.nickname} ({self.username})"

    @property
    def cognito_user_id(self):
        """
        호환성을 위한 프로퍼티
        username 필드가 실제로는 cognito_user_id 역할을 함
        """
        return self.username

    def to_dict(self):
        """
        모델을 딕셔너리로 변환 (API 응답용)
        """
        return {
            "id": str(self.id),
            "username": self.username,
            "nickname": self.nickname,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }