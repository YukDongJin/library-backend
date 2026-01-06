# 📁 app/api/deps.py
# API 의존성 함수들 - Cognito JWT 검증

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt, jwk
from jose.utils import base64url_decode
from app.database.base import get_async_session
from app.core.config import settings
from app.crud.user import user_crud
from app.models.user import User
import httpx
import logging
import json

logger = logging.getLogger(__name__)

# JWT 토큰 스키마 (토큰 없을 때 403 대신 None 반환)
security = HTTPBearer(auto_error=False)

# Cognito JWKS 캐시
_jwks_cache = None


async def get_cognito_jwks():
    """Cognito 공개키(JWKS) 가져오기"""
    global _jwks_cache
    
    if _jwks_cache:
        return _jwks_cache
    
    jwks_url = f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            _jwks_cache = response.json()
            logger.info("✅ Cognito JWKS 로드 완료")
            return _jwks_cache
    except Exception as e:
        logger.error(f"❌ Cognito JWKS 로드 실패: {e}")
        return None


def get_cognito_public_key(token: str, jwks: dict):
    """토큰 헤더에서 kid를 추출하고 해당 공개키 반환"""
    try:
        headers = jwt.get_unverified_headers(token)
        kid = headers.get("kid")
        
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return jwk.construct(key)
        
        logger.warning(f"일치하는 kid를 찾을 수 없음: {kid}")
        return None
    except Exception as e:
        logger.error(f"공개키 추출 실패: {e}")
        return None


async def verify_cognito_token(token: str) -> Optional[dict]:
    """Cognito JWT 토큰 검증"""
    try:
        logger.info(f"🔍 토큰 검증 시작 (길이: {len(token)}, 시작: {token[:20]}...)")
        
        # JWKS 가져오기
        jwks = await get_cognito_jwks()
        if not jwks:
            logger.error("❌ JWKS를 가져올 수 없음")
            return None
        
        # 공개키 가져오기
        public_key = get_cognito_public_key(token, jwks)
        if not public_key:
            logger.error("❌ 공개키를 찾을 수 없음")
            return None
        
        # 토큰 디코딩 및 검증
        # options에서 at_hash 검증 스킵 (access_token 없이 idToken만 사용)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=settings.COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{settings.AWS_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}",
            options={"verify_at_hash": False}
        )
        
        logger.info(f"✅ 토큰 검증 성공: sub={payload.get('sub')}")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("⚠️ 토큰 만료됨")
        return None
    except jwt.JWTClaimsError as e:
        logger.warning(f"⚠️ 토큰 클레임 오류: {e}")
        return None
    except JWTError as e:
        logger.error(f"❌ JWT 검증 실패: {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"❌ 토큰 검증 중 오류: {e}", exc_info=True)
        return None


async def get_db() -> AsyncSession:
    """데이터베이스 세션 의존성"""
    async for session in get_async_session():
        yield session


async def get_current_user_optional(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    현재 사용자 조회 (선택적)
    - 토큰이 없어도 None 반환 (에러 발생 안함)
    - DEBUG 모드에서는 test_user 사용
    """
    # 개발 환경에서는 test_user 사용
    if settings.DEBUG and not credentials:
        test_user = await user_crud.get_by_user_id(db, user_id="test_user")
        if test_user:
            return test_user
        logger.warning("DEBUG 모드: test_user가 DB에 없습니다")
        return None
    
    if not credentials:
        logger.info("🔍 인증 정보 없음")
        return None
    
    try:
        logger.info(f"🔍 인증 시도: 토큰 길이={len(credentials.credentials)}")
        
        # Cognito 토큰 검증
        payload = await verify_cognito_token(credentials.credentials)
        if not payload:
            logger.warning("⚠️ 토큰 검증 실패")
            return None
        
        # Cognito sub (사용자 고유 ID) 추출
        cognito_sub = payload.get("sub")
        if not cognito_sub:
            logger.warning("⚠️ 토큰에 sub 없음")
            return None
        
        logger.info(f"🔍 사용자 조회: user_id={cognito_sub}")
        
        # 사용자 조회 (회원가입은 팀원 서비스에서 처리)
        user = await user_crud.get_by_user_id(db, user_id=cognito_sub)
        if not user:
            logger.warning(f"⚠️ 사용자를 찾을 수 없음: {cognito_sub} (회원가입 필요)")
        else:
            logger.info(f"✅ 사용자 인증 성공: {user.user_id}")
        
        return user
        
    except Exception as e:
        logger.error(f"❌ 사용자 인증 중 오류: {e}", exc_info=True)
        return None


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    현재 사용자 조회 (필수)
    - 토큰이 없거나 유효하지 않으면 401 에러 발생
    - DEBUG 모드에서는 test_user 사용
    """
    # 개발 환경에서는 test_user 사용
    if settings.DEBUG:
        test_user = await user_crud.get_by_user_id(db, user_id="test_user")
        if test_user:
            return test_user
        # test_user가 없으면 에러 (수동으로 DB에 추가 필요)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="DEBUG 모드: test_user가 DB에 없습니다. users 테이블에 test_user를 추가하세요.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    try:
        # Cognito 토큰 검증
        payload = await verify_cognito_token(credentials.credentials)
        if not payload:
            raise credentials_exception
        
        # Cognito sub 추출
        cognito_sub = payload.get("sub")
        if not cognito_sub:
            raise credentials_exception
        
        # 사용자 조회 (회원가입은 팀원 서비스에서 처리)
        user = await user_crud.get_by_user_id(db, user_id=cognito_sub)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="회원가입이 필요합니다",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"사용자 인증 중 오류: {e}")
        raise credentials_exception


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """현재 활성 사용자 조회"""
    if current_user.status and current_user.status != "active":
        raise HTTPException(status_code=400, detail="비활성 사용자입니다")
    return current_user


class CommonQueryParams:
    """공통 쿼리 파라미터 클래스"""
    def __init__(
        self,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.skip = skip
        self.limit = min(limit, 100)
        self.sort_by = sort_by
        self.sort_order = sort_order


def common_parameters(
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> CommonQueryParams:
    """공통 쿼리 파라미터 의존성"""
    return CommonQueryParams(skip, limit, sort_by, sort_order)
