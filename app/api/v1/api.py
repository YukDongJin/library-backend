# 📁 새로 생성된 파일: app/api/v1/api.py
# API v1 라우터 통합

from fastapi import APIRouter
from app.api.v1 import users, library_items, test_endpoints, upload

# API v1 메인 라우터
api_router = APIRouter()

# 각 모듈의 라우터를 메인 라우터에 포함
api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["users"],
    responses={
        404: {"description": "사용자를 찾을 수 없습니다"},
        401: {"description": "인증이 필요합니다"},
        403: {"description": "권한이 없습니다"}
    }
)

api_router.include_router(
    library_items.router, 
    prefix="/library-items", 
    tags=["library-items"],
    responses={
        404: {"description": "라이브러리 아이템을 찾을 수 없습니다"},
        401: {"description": "인증이 필요합니다"},
        403: {"description": "권한이 없습니다"}
    }
)

# 실제 S3 업로드 엔드포인트
api_router.include_router(
    upload.router,
    prefix="/upload",
    tags=["upload"],
    responses={
        401: {"description": "인증이 필요합니다"},
        403: {"description": "권한이 없습니다"}
    }
)

# 테스트용 엔드포인트 (Cognito 없이 테스트 가능)
api_router.include_router(
    test_endpoints.router,
    prefix="/test",
    tags=["test"],
    responses={
        404: {"description": "리소스를 찾을 수 없습니다"}
    }
)