# 📁 새로 생성된 파일: app/services/file_service.py
# 파일 처리 서비스

import mimetypes
from typing import Optional, Dict, Any, Tuple
from app.models.library_item import ItemType
import logging

logger = logging.getLogger(__name__)


class FileService:
    """
    파일 처리 서비스
    - MIME 타입 감지
    - 파일 타입 분류
    - 파일 크기 검증
    """

    def __init__(self):
        """파일 서비스 초기화"""
        # MIME 타입별 아이템 타입 매핑
        self.mime_type_mapping = {
            # 이미지
            'image/jpeg': ItemType.image,
            'image/jpg': ItemType.image,
            'image/png': ItemType.image,
            'image/gif': ItemType.image,
            'image/webp': ItemType.image,
            'image/svg+xml': ItemType.image,
            'image/bmp': ItemType.image,
            'image/tiff': ItemType.image,
            
            # 비디오
            'video/mp4': ItemType.video,
            'video/mpeg': ItemType.video,
            'video/quicktime': ItemType.video,
            'video/x-msvideo': ItemType.video,  # .avi
            'video/webm': ItemType.video,
            'video/x-flv': ItemType.video,
            'video/3gpp': ItemType.video,
            
            # 문서
            'application/pdf': ItemType.document,
            'application/msword': ItemType.document,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ItemType.document,  # .docx
            'application/vnd.ms-excel': ItemType.document,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ItemType.document,  # .xlsx
            'application/vnd.ms-powerpoint': ItemType.document,
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ItemType.document,  # .pptx
            'text/plain': ItemType.document,
            'text/html': ItemType.document,
            'text/css': ItemType.document,
            'text/javascript': ItemType.document,
            'application/json': ItemType.document,
            'application/xml': ItemType.document,
            'text/xml': ItemType.document,
            'text/csv': ItemType.document,
            'application/rtf': ItemType.document,
        }
        
        # 파일 크기 제한 (바이트)
        self.size_limits = {
            ItemType.image: 50 * 1024 * 1024,      # 50MB
            ItemType.video: 500 * 1024 * 1024,     # 500MB
            ItemType.document: 100 * 1024 * 1024,  # 100MB
            ItemType.file: 1024 * 1024 * 1024,     # 1GB
        }

    def detect_mime_type(self, filename: str) -> str:
        """
        파일명으로부터 MIME 타입 감지
        
        Args:
            filename: 파일명
            
        Returns:
            MIME 타입
        """
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'

    def get_item_type_from_mime(self, mime_type: str) -> ItemType:
        """
        MIME 타입으로부터 아이템 타입 결정
        
        Args:
            mime_type: MIME 타입
            
        Returns:
            아이템 타입
        """
        return self.mime_type_mapping.get(mime_type, ItemType.file)

    def get_item_type_from_filename(self, filename: str) -> ItemType:
        """
        파일명으로부터 아이템 타입 결정
        
        Args:
            filename: 파일명
            
        Returns:
            아이템 타입
        """
        mime_type = self.detect_mime_type(filename)
        return self.get_item_type_from_mime(mime_type)

    def validate_file_size(self, file_size: int, item_type: ItemType) -> Tuple[bool, Optional[str]]:
        """
        파일 크기 검증
        
        Args:
            file_size: 파일 크기 (바이트)
            item_type: 아이템 타입
            
        Returns:
            (검증 성공 여부, 에러 메시지)
        """
        max_size = self.size_limits.get(item_type, self.size_limits[ItemType.file])
        
        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            return False, f"{item_type.value} 파일은 최대 {max_size_mb:.0f}MB까지 업로드 가능합니다"
        
        if file_size <= 0:
            return False, "파일 크기가 유효하지 않습니다"
        
        return True, None

    def validate_filename(self, filename: str) -> Tuple[bool, Optional[str]]:
        """
        파일명 검증
        
        Args:
            filename: 파일명
            
        Returns:
            (검증 성공 여부, 에러 메시지)
        """
        if not filename or not filename.strip():
            return False, "파일명이 비어있습니다"
        
        # 파일명 길이 제한
        if len(filename) > 255:
            return False, "파일명이 너무 깁니다 (최대 255자)"
        
        # 금지된 문자 확인
        forbidden_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in forbidden_chars:
            if char in filename:
                return False, f"파일명에 사용할 수 없는 문자가 포함되어 있습니다: {char}"
        
        return True, None

    def validate_mime_type(self, mime_type: str, expected_type: Optional[ItemType] = None) -> Tuple[bool, Optional[str]]:
        """
        MIME 타입 검증
        
        Args:
            mime_type: MIME 타입
            expected_type: 예상되는 아이템 타입 (선택사항)
            
        Returns:
            (검증 성공 여부, 에러 메시지)
        """
        if not mime_type:
            return False, "MIME 타입이 지정되지 않았습니다"
        
        # 지원되지 않는 MIME 타입 확인
        detected_type = self.get_item_type_from_mime(mime_type)
        
        if expected_type and detected_type != expected_type:
            return False, f"파일 타입이 일치하지 않습니다. 예상: {expected_type.value}, 실제: {detected_type.value}"
        
        return True, None

    def format_file_size(self, size_bytes: int) -> str:
        """
        파일 크기를 읽기 쉬운 형태로 포맷
        
        Args:
            size_bytes: 파일 크기 (바이트)
            
        Returns:
            포맷된 파일 크기 문자열
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def get_file_extension(self, filename: str) -> str:
        """
        파일 확장자 추출
        
        Args:
            filename: 파일명
            
        Returns:
            파일 확장자 (점 포함)
        """
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return ''

    def is_supported_file_type(self, mime_type: str) -> bool:
        """
        지원되는 파일 타입인지 확인
        
        Args:
            mime_type: MIME 타입
            
        Returns:
            지원 여부
        """
        # 모든 파일 타입을 지원하지만, 특정 타입은 제외
        blocked_types = [
            'application/x-executable',
            'application/x-msdownload',
            'application/x-msdos-program',
        ]
        
        return mime_type not in blocked_types

    def validate_upload_request(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        expected_type: Optional[ItemType] = None
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        업로드 요청 전체 검증
        
        Args:
            filename: 파일명
            content_type: MIME 타입
            file_size: 파일 크기
            expected_type: 예상되는 아이템 타입
            
        Returns:
            (검증 성공 여부, 에러 메시지, 파일 정보)
        """
        # 파일명 검증
        valid, error = self.validate_filename(filename)
        if not valid:
            return False, error, {}
        
        # MIME 타입 검증
        valid, error = self.validate_mime_type(content_type, expected_type)
        if not valid:
            return False, error, {}
        
        # 지원되는 파일 타입인지 확인
        if not self.is_supported_file_type(content_type):
            return False, "지원되지 않는 파일 타입입니다", {}
        
        # 아이템 타입 결정
        item_type = self.get_item_type_from_mime(content_type)
        
        # 파일 크기 검증
        valid, error = self.validate_file_size(file_size, item_type)
        if not valid:
            return False, error, {}
        
        # 파일 정보 생성
        file_info = {
            "item_type": item_type,
            "mime_type": content_type,
            "file_size": file_size,
            "formatted_size": self.format_file_size(file_size),
            "file_extension": self.get_file_extension(filename),
            "needs_thumbnail": item_type in [ItemType.image, ItemType.video]
        }
        
        return True, None, file_info


# 전역 파일 서비스 인스턴스
file_service = FileService()