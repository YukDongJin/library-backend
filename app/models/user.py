# 📁 app/models/user.py
# 사용자 테이블 SQLAlchemy 모델 (팀원 users 테이블 사용)

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.models_config import Base


class User(Base):
    """
    사용자 테이블 모델
    - 팀원의 users 테이블 구조 사용
    - users 테이블: user_id(varchar/PK), email, nickname, status, created_at, updated_at, deleted_at
    - user_id = Cognito sub (사용자 고유 ID)
    """
    __tablename__ = "users"

    # Primary Key: Cognito sub (VARCHAR)
    user_id = Column(
        String(255), 
        primary_key=True,
        comment="Cognito sub (사용자 고유 ID)"
    )
    
    # 이메일
    email = Column(
        String(255),
        nullable=True,
        comment="사용자 이메일"
    )
    
    # 사용자 닉네임
    nickname = Column(
        String(255), 
        nullable=True,
        comment="사용자 표시 닉네임"
    )
    
    # 사용자 상태
    status = Column(
        String(50),
        nullable=True,
        default="active",
        comment="사용자 상태 (active, inactive, suspended)"
    )
    
    # 생성 시간
    created_at = Column(
        DateTime(timezone=False), 
        server_default=func.now(),
        nullable=True,
        comment="계정 생성 시간"
    )
    
    # 수정 시간
    updated_at = Column(
        DateTime(timezone=False), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
        comment="마지막 수정 시간"
    )
    
    # 삭제 시간 (소프트 삭제)
    deleted_at = Column(
        DateTime(timezone=False),
        nullable=True,
        comment="삭제 시간 (소프트 삭제)"
    )

    # 관계 설정: 사용자가 소유한 라이브러리 아이템들
    library_items = relationship(
        "LibraryItem", 
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<User(user_id={self.user_id}, nickname={self.nickname})>"

    def __str__(self):
        return f"User: {self.nickname} ({self.user_id})"

    @property
    def id(self):
        """호환성을 위한 프로퍼티 - user_id를 id로도 접근 가능"""
        return self.user_id

    @property
    def cognito_user_id(self):
        """Cognito sub ID"""
        return self.user_id

    def to_dict(self):
        """모델을 딕셔너리로 변환 (API 응답용)"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "nickname": self.nickname,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None
        }