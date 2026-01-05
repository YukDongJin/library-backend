# 📁 새로 생성된 파일: alembic/versions/001_initial_migration.py
# 초기 마이그레이션: users 및 library_items 테이블 생성

"""Initial migration: users and library_items tables

Revision ID: 001
Revises: 
Create Date: 2024-12-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """마이그레이션 적용 (업그레이드)"""
    
    # users 테이블 생성
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='사용자 고유 ID (UUID)'),
        sa.Column('username', sa.String(length=255), nullable=False, comment='AWS Cognito User ID (username 필드명이지만 cognito_id 역할)'),
        sa.Column('nickname', sa.Text(), nullable=False, comment='사용자 표시 닉네임'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='계정 생성 시간'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='마지막 수정 시간'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    
    # users 테이블 인덱스 생성
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    
    # library_items 테이블 생성
    op.create_table('library_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, comment='라이브러리 아이템 고유 ID (UUID)'),
        sa.Column('user_profile_id', postgresql.UUID(as_uuid=True), nullable=False, comment='소유자 사용자 ID (users 테이블 참조)'),
        sa.Column('name', sa.Text(), nullable=False, comment='사용자가 지정한 아이템 표시명'),
        sa.Column('type', sa.Enum('image', 'document', 'file', 'video', name='itemtype'), nullable=False, comment='아이템 타입 (image, document, file, video)'),
        sa.Column('mime_type', sa.String(length=255), nullable=False, comment='파일의 MIME 타입 (예: image/jpeg, application/pdf)'),
        sa.Column('visibility', sa.Enum('public', 'private', name='visibilitytype'), nullable=False, comment='아이템 공개 범위 (public, private)'),
        sa.Column('s3_thumbnail_key', sa.String(length=500), nullable=True, comment='S3 썸네일 파일 키 (이미지/비디오만)'),
        sa.Column('s3_key', sa.String(length=500), nullable=False, comment='S3 원본 파일 키'),
        sa.Column('file_size', sa.BigInteger(), nullable=False, comment='파일 크기 (bytes)'),
        sa.Column('preview_text', sa.Text(), nullable=True, comment='문서 파일의 미리보기 텍스트'),
        sa.Column('original_filename', sa.String(length=255), nullable=False, comment='업로드 시 원본 파일명'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='아이템 생성 시간'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='마지막 수정 시간'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True, comment='소프트 삭제 시간 (NULL이면 활성 상태)'),
        sa.ForeignKeyConstraint(['user_profile_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # library_items 테이블 인덱스 생성
    op.create_index(op.f('ix_library_items_user_profile_id'), 'library_items', ['user_profile_id'], unique=False)
    op.create_index(op.f('ix_library_items_type'), 'library_items', ['type'], unique=False)
    op.create_index(op.f('ix_library_items_visibility'), 'library_items', ['visibility'], unique=False)
    op.create_index(op.f('ix_library_items_created_at'), 'library_items', ['created_at'], unique=False)
    op.create_index(op.f('ix_library_items_deleted_at'), 'library_items', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_library_items_user_type'), 'library_items', ['user_profile_id', 'type'], unique=False)


def downgrade() -> None:
    """마이그레이션 롤백 (다운그레이드)"""
    
    # 인덱스 삭제
    op.drop_index(op.f('ix_library_items_user_type'), table_name='library_items')
    op.drop_index(op.f('ix_library_items_deleted_at'), table_name='library_items')
    op.drop_index(op.f('ix_library_items_created_at'), table_name='library_items')
    op.drop_index(op.f('ix_library_items_visibility'), table_name='library_items')
    op.drop_index(op.f('ix_library_items_type'), table_name='library_items')
    op.drop_index(op.f('ix_library_items_user_profile_id'), table_name='library_items')
    
    # 테이블 삭제
    op.drop_table('library_items')
    
    # users 테이블 인덱스 삭제
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    
    # users 테이블 삭제
    op.drop_table('users')
    
    # Enum 타입 삭제
    op.execute('DROP TYPE IF EXISTS itemtype')
    op.execute('DROP TYPE IF EXISTS visibilitytype')