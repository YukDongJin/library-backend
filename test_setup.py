# 📁 새로 생성된 파일: test_setup.py
# 백엔드 설정 테스트 스크립트

"""
백엔드 설정 및 기본 기능 테스트 스크립트
- 모듈 import 테스트
- 설정 로드 테스트
- 데이터베이스 연결 테스트 (선택사항)
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """모듈 import 테스트"""
    print("🔍 모듈 import 테스트...")
    
    try:
        # 핵심 모듈들 import 테스트
        from app.core.config import settings
        print("✅ 설정 모듈 import 성공")
        
        from app.models.user import User
        from app.models.library_item import LibraryItem
        print("✅ 모델 모듈 import 성공")
        
        from app.schemas.user import UserCreate, UserResponse
        from app.schemas.library_item import LibraryItemCreate, LibraryItemResponse
        print("✅ 스키마 모듈 import 성공")
        
        from app.crud.user import user_crud
        from app.crud.library_item import library_item_crud
        print("✅ CRUD 모듈 import 성공")
        
        from app.api.v1.users import router as users_router
        from app.api.v1.library_items import router as items_router
        print("✅ API 라우터 import 성공")
        
        from app.main import app
        print("✅ FastAPI 앱 import 성공")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False


def test_config():
    """설정 테스트"""
    print("\n🔧 설정 테스트...")
    
    try:
        from app.core.config import settings
        
        print(f"📊 프로젝트명: {settings.PROJECT_NAME}")
        print(f"🔢 버전: {settings.VERSION}")
        print(f"🌐 호스트: {settings.HOST}:{settings.PORT}")
        print(f"🔐 디버그 모드: {settings.DEBUG}")
        print(f"🗄️ 데이터베이스 호스트: {settings.DB_HOST}:{settings.DB_PORT}")
        print(f"📝 데이터베이스명: {settings.DB_NAME}")
        print(f"🔑 JWT 알고리즘: {settings.JWT_ALGORITHM}")
        print(f"☁️ AWS 리전: {settings.AWS_REGION}")
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 로드 오류: {e}")
        return False


def test_database_connection():
    """데이터베이스 연결 테스트 (선택사항)"""
    print("\n🗄️ 데이터베이스 연결 테스트...")
    
    try:
        import asyncio
        from app.database.base import test_connection
        
        # 비동기 함수 실행
        async def run_test():
            return await test_connection()
        
        result = asyncio.run(run_test())
        
        if result:
            print("✅ 데이터베이스 연결 성공")
            return True
        else:
            print("❌ 데이터베이스 연결 실패")
            return False
            
    except Exception as e:
        print(f"⚠️ 데이터베이스 연결 테스트 건너뜀: {e}")
        print("💡 .env 파일 설정 후 다시 시도하세요")
        return None


def test_models():
    """모델 생성 테스트"""
    print("\n🏗️ 모델 생성 테스트...")
    
    try:
        from app.models.user import User
        from app.models.library_item import LibraryItem, ItemType, VisibilityType
        import uuid
        
        # 사용자 모델 테스트
        user_data = {
            "id": uuid.uuid4(),
            "username": "test-cognito-id",
            "nickname": "테스트사용자"
        }
        
        # 모델 인스턴스 생성 (DB 저장 없이)
        user = User(**user_data)
        print(f"✅ 사용자 모델 생성: {user}")
        
        # 라이브러리 아이템 모델 테스트
        item_data = {
            "id": uuid.uuid4(),
            "user_profile_id": user.id,
            "name": "테스트 아이템",
            "type": ItemType.image,
            "mime_type": "image/jpeg",
            "visibility": VisibilityType.private,
            "s3_key": "uploads/2024/12/test.jpg",
            "file_size": 1024000,
            "original_filename": "test.jpg"
        }
        
        item = LibraryItem(**item_data)
        print(f"✅ 라이브러리 아이템 모델 생성: {item}")
        
        return True
        
    except Exception as e:
        print(f"❌ 모델 생성 오류: {e}")
        return False


def test_schemas():
    """스키마 검증 테스트"""
    print("\n📋 스키마 검증 테스트...")
    
    try:
        from app.schemas.user import UserCreate, UserResponse
        from app.schemas.library_item import LibraryItemCreate, ItemType, VisibilityType
        
        # 사용자 생성 스키마 테스트
        user_create_data = {
            "username": "test-cognito-id",
            "nickname": "테스트사용자"
        }
        
        user_create = UserCreate(**user_create_data)
        print(f"✅ 사용자 생성 스키마: {user_create}")
        
        # 라이브러리 아이템 생성 스키마 테스트
        item_create_data = {
            "name": "테스트 이미지",
            "type": ItemType.image,
            "visibility": VisibilityType.private,
            "mime_type": "image/jpeg",
            "s3_key": "uploads/2024/12/test.jpg",
            "file_size": 1024000,
            "original_filename": "test.jpg"
        }
        
        item_create = LibraryItemCreate(**item_create_data)
        print(f"✅ 라이브러리 아이템 생성 스키마: {item_create}")
        
        return True
        
    except Exception as e:
        print(f"❌ 스키마 검증 오류: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("🚀 FastAPI 백엔드 설정 테스트 시작\n")
    
    tests = [
        ("모듈 Import", test_imports),
        ("설정 로드", test_config),
        ("모델 생성", test_models),
        ("스키마 검증", test_schemas),
        ("데이터베이스 연결", test_database_connection)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    # 결과 요약
    print("\n" + "="*50)
    print("📊 테스트 결과 요약")
    print("="*50)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}: 통과")
            passed += 1
        elif result is False:
            print(f"❌ {test_name}: 실패")
            failed += 1
        else:
            print(f"⚠️ {test_name}: 건너뜀")
            skipped += 1
    
    print(f"\n📈 총 {len(results)}개 테스트 중:")
    print(f"   ✅ 통과: {passed}개")
    print(f"   ❌ 실패: {failed}개")
    print(f"   ⚠️ 건너뜀: {skipped}개")
    
    if failed == 0:
        print("\n🎉 모든 필수 테스트가 통과했습니다!")
        print("💡 다음 단계:")
        print("   1. .env 파일 설정")
        print("   2. PostgreSQL 데이터베이스 생성")
        print("   3. python run_server.py 실행")
    else:
        print(f"\n⚠️ {failed}개의 테스트가 실패했습니다.")
        print("💡 requirements.txt의 패키지들을 설치했는지 확인하세요:")
        print("   pip install -r requirements.txt")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)