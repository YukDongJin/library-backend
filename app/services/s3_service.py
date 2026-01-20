# 📁 app/services/s3_service.py
# AWS S3 파일 업로드 서비스 (IRSA 사용)

import boto3
from botocore.config import Config
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """
    AWS S3 파일 업로드 서비스
    - IRSA (IAM Role for Service Account) 사용
    - Presigned URL 생성
    - 파일 업로드/다운로드
    """
    
    def __init__(self):
        """S3 클라이언트 초기화 (IRSA 사용)"""
        try:
            # IRSA 사용 - Access Key 없이 IAM Role로 인증
            # signature_version='s3v4' 필수: IRSA Presigned URL 서명 검증을 위해 필요
            self.region = settings.S3_REGION
            self.s3_client = boto3.client(
                "s3",
                region_name=self.region,
                endpoint_url=f"https://s3.{self.region}.amazonaws.com",
                config=Config(
                    signature_version='s3v4',
                    s3={"addressing_style": "virtual"}
                ),
            )
            self.bucket_name = settings.S3_BUCKET_NAME
            logger.info(f"✅ S3 클라이언트 초기화 완료 (버킷: {self.bucket_name}, 리전: {self.region}, signature: s3v4)")
        except NoCredentialsError:
            logger.warning("⚠️ AWS 자격 증명이 설정되지 않음 - 개발 모드로 실행")
            self.s3_client = None
            self.bucket_name = settings.S3_BUCKET_NAME
        except Exception as e:
            logger.error(f"❌ S3 클라이언트 초기화 실패: {e}")
            self.s3_client = None
            self.bucket_name = settings.S3_BUCKET_NAME

    def generate_s3_key(self, filename: str, user_id: str) -> str:
        """
        S3 키 생성 (파일 경로)
        
        형식: {user_id}/library/{년도}/{월}/{uuid}.{확장자}
        예시: 14780408-6031-704d-19af-ab1893f6b8e5/library/2026/01/550e8400-e29b-41d4.jpg
        """
        now = datetime.utcnow()
        file_extension = filename.split('.')[-1] if '.' in filename else ''
        unique_filename = f"{uuid.uuid4()}.{file_extension}" if file_extension else str(uuid.uuid4())
        
        s3_key = f"{user_id}/library/{now.year}/{now.month:02d}/{unique_filename}"
        return s3_key

    def generate_thumbnail_key(self, s3_key: str) -> str:
        """
        썸네일 S3 키 생성
        
        형식: {user_id}/library/{년도}/{월}/thumbs/{uuid}_thumb.{확장자}
        예시: 14780408-6031-704d-19af-ab1893f6b8e5/library/2026/01/thumbs/550e8400_thumb.jpg
        """
        path_parts = s3_key.rsplit('/', 1)
        if len(path_parts) == 2:
            folder, filename = path_parts
        else:
            folder, filename = '', path_parts[0]
        
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        thumbnail_filename = f"{name}_thumb.{ext}" if ext else f"{name}_thumb"
        
        return f"{folder}/thumbs/{thumbnail_filename}"

    async def generate_presigned_upload_url(
        self,
        filename: str,
        content_type: str,
        user_id: str,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        파일 업로드용 Presigned URL 생성
        
        Args:
            filename: 업로드할 파일명
            content_type: 파일 MIME 타입
            user_id: 사용자 ID
            expires_in: URL 만료 시간 (초)
            
        Returns:
            업로드 URL 정보 딕셔너리
        """
        try:
            s3_key = self.generate_s3_key(filename, user_id)
            
            if not self.s3_client:
                # 개발 환경에서 더미 URL 반환
                return {
                    "upload_url": f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}?mock=true",
                    "s3_key": s3_key,
                    "expires_in": expires_in,
                    "fields": {},
                    "is_mock": True
                }
            
            # Presigned POST URL 생성 (더 안전함)
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={
                    "Content-Type": content_type,
                    "x-amz-meta-user-id": user_id,
                    "x-amz-meta-original-filename": filename
                },
                Conditions=[
                    {"Content-Type": content_type},
                    {"x-amz-meta-user-id": user_id},
                    {"x-amz-meta-original-filename": filename},
                    ["content-length-range", 1, 100 * 1024 * 1024]  # 1B ~ 100MB
                ],
                ExpiresIn=expires_in
            )
            
            logger.info(f"Presigned URL 생성: {filename} -> {s3_key}")
            
            return {
                "upload_url": response["url"],
                "s3_key": s3_key,
                "expires_in": expires_in,
                "fields": response["fields"],
                "is_mock": False
            }
            
        except ClientError as e:
            logger.error(f"S3 Presigned URL 생성 실패: {e}")
            raise Exception(f"업로드 URL 생성 실패: {str(e)}")
        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            raise Exception(f"업로드 URL 생성 중 오류: {str(e)}")

    async def generate_presigned_download_url(
        self,
        s3_key: str,
        expires_in: int = 3600
    ) -> str:
        """
        파일 다운로드용 Presigned URL 생성
        
        Args:
            s3_key: S3 파일 키
            expires_in: URL 만료 시간 (초)
            
        Returns:
            다운로드 URL
        """
        try:
            if not self.s3_client:
                # 개발 환경에서 더미 URL 반환
                return f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}?mock=true"
            
            # Presigned URL 생성 (IRSA 세션 토큰 자동 포함)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key,
                    'ResponseCacheControl': 'max-age=3600'
                },
                ExpiresIn=expires_in,
                HttpMethod='GET'
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"S3 다운로드 URL 생성 실패: {e}")
            raise Exception(f"다운로드 URL 생성 실패: {str(e)}")

    async def delete_file(self, s3_key: str) -> bool:
        """
        S3에서 파일 삭제
        
        Args:
            s3_key: 삭제할 파일의 S3 키
            
        Returns:
            삭제 성공 여부
        """
        try:
            if not self.s3_client:
                logger.info(f"개발 모드: 파일 삭제 시뮬레이션 - {s3_key}")
                return True
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"S3 파일 삭제 완료: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 파일 삭제 실패: {e}")
            return False

    async def copy_file(self, source_key: str, dest_key: str) -> bool:
        """
        S3 내에서 파일 복사
        
        Args:
            source_key: 원본 파일 키
            dest_key: 대상 파일 키
            
        Returns:
            복사 성공 여부
        """
        try:
            if not self.s3_client:
                logger.info(f"개발 모드: 파일 복사 시뮬레이션 - {source_key} -> {dest_key}")
                return True
            
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )
            
            logger.info(f"S3 파일 복사 완료: {source_key} -> {dest_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 파일 복사 실패: {e}")
            return False

    def get_file_info(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        S3 파일 정보 조회
        
        Args:
            s3_key: 파일 S3 키
            
        Returns:
            파일 정보 딕셔너리 또는 None
        """
        try:
            if not self.s3_client:
                # 개발 환경에서 더미 정보 반환
                return {
                    "size": 1024000,
                    "last_modified": datetime.utcnow(),
                    "content_type": "application/octet-stream",
                    "is_mock": True
                }
            
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                "size": response.get("ContentLength", 0),
                "last_modified": response.get("LastModified"),
                "content_type": response.get("ContentType", "application/octet-stream"),
                "metadata": response.get("Metadata", {}),
                "is_mock": False
            }
            
        except ClientError as e:
            logger.error(f"S3 파일 정보 조회 실패: {e}")
            return None

    def file_exists(self, s3_key: str) -> bool:
        """
        S3 파일 존재 여부 확인
        
        Args:
            s3_key: 파일 S3 키
            
        Returns:
            파일 존재 여부 (True/False)
        """
        try:
            if not self.s3_client:
                # 개발 환경에서는 항상 존재한다고 가정
                return True
            
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == '404' or error_code == 'NoSuchKey':
                logger.info(f"S3 파일 없음: {s3_key}")
                return False
            logger.error(f"S3 파일 존재 확인 실패: {e}")
            return False

    def is_image_file(self, content_type: str) -> bool:
        """이미지 파일 여부 확인"""
        return content_type.startswith('image/')

    def is_video_file(self, content_type: str) -> bool:
        """비디오 파일 여부 확인"""
        return content_type.startswith('video/')

    async def upload_file_content(
        self,
        s3_key: str,
        file_content: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        파일 내용을 S3에 직접 업로드
        
        Args:
            s3_key: S3 파일 키
            file_content: 업로드할 파일 내용 (bytes)
            content_type: 파일 MIME 타입
            metadata: 추가 메타데이터
            
        Returns:
            업로드 성공 여부
        """
        try:
            if not self.s3_client:
                logger.info(f"개발 모드: S3 업로드 시뮬레이션 - {s3_key}")
                return True
            
            # S3에 파일 업로드
            put_object_kwargs = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': file_content,
                'ContentType': content_type
            }
            
            # 메타데이터 추가 (있는 경우)
            if metadata:
                put_object_kwargs['Metadata'] = metadata
            
            self.s3_client.put_object(**put_object_kwargs)
            logger.info(f"S3 파일 업로드 성공: {s3_key} ({len(file_content)} bytes)")
            return True
            
        except ClientError as e:
            logger.error(f"S3 파일 업로드 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"파일 업로드 중 예상치 못한 오류: {e}")
            return False

    def needs_thumbnail(self, content_type: str) -> bool:
        """썸네일 생성이 필요한 파일 타입인지 확인"""
        return self.is_image_file(content_type) or self.is_video_file(content_type)

    async def trigger_video_preview_generation(
        self,
        s3_key: str,
        item_id: str
    ) -> Optional[str]:
        """
        동영상 프리뷰 생성을 위한 Step Functions 실행
        
        Args:
            s3_key: 원본 동영상 S3 키
            item_id: 라이브러리 아이템 ID (DB 업데이트용)
            
        Returns:
            Step Functions 실행 ARN 또는 None
        """
        try:
            # Step Functions 클라이언트 생성
            sfn_client = boto3.client(
                'stepfunctions',
                region_name=self.region
            )
            
            # Step Functions State Machine ARN
            state_machine_arn = settings.VIDEO_PREVIEW_STATE_MACHINE_ARN
            
            if not state_machine_arn:
                logger.warning("VIDEO_PREVIEW_STATE_MACHINE_ARN이 설정되지 않음")
                return None
            
            # Step Functions 입력 데이터
            input_data = {
                "bucket": self.bucket_name,
                "key": s3_key,
                "item_id": item_id
            }
            
            # Step Functions 실행
            response = sfn_client.start_execution(
                stateMachineArn=state_machine_arn,
                input=json.dumps(input_data)
            )
            
            execution_arn = response.get('executionArn')
            logger.info(f"Step Functions 실행 시작: {execution_arn}")
            
            return execution_arn
            
        except ClientError as e:
            logger.error(f"Step Functions 실행 실패: {e}")
            return None
        except Exception as e:
            logger.error(f"프리뷰 생성 트리거 중 오류: {e}")
            return None

    def generate_preview_key(self, s3_key: str) -> str:
        """
        프리뷰 영상 S3 키 생성
        
        형식: previews/{원본파일명}_preview.mp4
        """
        # 원본 파일명에서 확장자 제거
        filename = s3_key.split('/')[-1]
        name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        return f"previews/{name}_preview.mp4"


# 전역 S3 서비스 인스턴스
s3_service = S3Service()
