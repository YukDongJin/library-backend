import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Allow imports from project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select  # noqa: E402
from app.database.models_config import AsyncSessionLocal  # noqa: E402
from app.crud.user import user_crud  # noqa: E402
from app.models.library_item import LibraryItem, ItemType, VisibilityType  # noqa: E402
from app.schemas.user import UserCreate  # noqa: E402


SEED_ITEMS: List[Dict[str, Any]] = [
    {
        "name": "햇살 사진.jpg",
        "type": ItemType.image,
        "visibility": VisibilityType.public,
        "mime_type": "image/jpeg",
        "original_filename": "햇살 사진.jpg",
        "file_size": 2400000,
    },
    {
        "name": "가족사진.png",
        "type": ItemType.image,
        "visibility": VisibilityType.private,
        "mime_type": "image/png",
        "original_filename": "가족사진.png",
        "file_size": 1800000,
    },
    {
        "name": "풍경 사진.jpg",
        "type": ItemType.image,
        "visibility": VisibilityType.public,
        "mime_type": "image/jpeg",
        "original_filename": "풍경 사진.jpg",
        "file_size": 3200000,
    },
    {
        "name": "오스 이미지 1.jpg",
        "type": ItemType.image,
        "visibility": VisibilityType.public,
        "mime_type": "image/jpeg",
        "original_filename": "오스 이미지 1.jpg",
        "file_size": 2100000,
    },
    {
        "name": "오스 이미지 2.jpg",
        "type": ItemType.image,
        "visibility": VisibilityType.private,
        "mime_type": "image/jpeg",
        "original_filename": "오스 이미지 2.jpg",
        "file_size": 1900000,
    },
    {
        "name": "오스 이미지 3.jpg",
        "type": ItemType.image,
        "visibility": VisibilityType.public,
        "mime_type": "image/jpeg",
        "original_filename": "오스 이미지 3.jpg",
        "file_size": 2000000,
    },
    {
        "name": "오스 이미지 4.png",
        "type": ItemType.image,
        "visibility": VisibilityType.private,
        "mime_type": "image/png",
        "original_filename": "오스 이미지 4.png",
        "file_size": 2300000,
    },
    {
        "name": "프로젝트 계획서.pdf",
        "type": ItemType.document,
        "visibility": VisibilityType.public,
        "mime_type": "application/pdf",
        "original_filename": "프로젝트 계획서.pdf",
        "file_size": 1200000,
        "preview_text": "프로젝트 범위와 목표를 정리했습니다.\n예산과 일정은 다음 회의에서 확정합니다.",
    },
    {
        "name": "회의록.docx",
        "type": ItemType.document,
        "visibility": VisibilityType.private,
        "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "original_filename": "회의록.docx",
        "file_size": 450000,
        "preview_text": "주요 논의 사항: 일정 조정.\n다음 액션 아이템 확인.",
    },
    {
        "name": "자료.zip",
        "type": ItemType.file,
        "visibility": VisibilityType.private,
        "mime_type": "application/zip",
        "original_filename": "자료.zip",
        "file_size": 45000000,
    },
    {
        "name": "발표 영상.mp4",
        "type": ItemType.video,
        "visibility": VisibilityType.public,
        "mime_type": "video/mp4",
        "original_filename": "발표 영상.mp4",
        "file_size": 250000000,
    },
    {
        "name": "튜토리얼.mov",
        "type": ItemType.video,
        "visibility": VisibilityType.private,
        "mime_type": "video/quicktime",
        "original_filename": "튜토리얼.mov",
        "file_size": 180000000,
    },
]


def build_s3_key(filename: str) -> str:
    safe_name = filename.replace(" ", "_")
    return f"seed/{safe_name}"


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        user = await user_crud.get_by_username(session, username="test_user")
        if not user:
            user = await user_crud.create_user(
                session, user_in=UserCreate(username="test_user", nickname="test_user")
            )

        for item in SEED_ITEMS:
            exists = await session.execute(
                select(LibraryItem).where(
                    LibraryItem.user_profile_id == user.id,
                    LibraryItem.name == item["name"],
                )
            )
            if exists.scalar_one_or_none():
                continue

            db_item = LibraryItem(
                user_profile_id=user.id,
                name=item["name"],
                type=item["type"],
                mime_type=item["mime_type"],
                visibility=item["visibility"],
                s3_key=build_s3_key(item["original_filename"]),
                s3_thumbnail_key=None,
                file_size=item["file_size"],
                original_filename=item["original_filename"],
                preview_text=item.get("preview_text"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(db_item)

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
