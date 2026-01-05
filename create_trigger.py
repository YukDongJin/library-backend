#!/usr/bin/env python3
"""
PostgreSQL 트리거 생성 스크립트
library_items 삭제 시 history 테이블의 s3_key를 NULL로 만드는 트리거
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.models_config import sync_engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_trigger():
    """PostgreSQL 트리거 생성"""
    try:
        with sync_engine.connect() as conn:
            logger.info("🔄 PostgreSQL 트리거 생성 중...")
            
            # 1. 트리거 함수 생성 (친구가 성공한 코드 그대로 사용)
            function_sql = """
            CREATE OR REPLACE FUNCTION update_history_s3_key_on_library_delete()
            RETURNS TRIGGER AS $$
            BEGIN
                IF OLD.s3_key IS NOT NULL THEN
                    UPDATE history
                    SET s3_key = NULL
                    WHERE s3_key = OLD.s3_key;
                END IF;
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            conn.execute(text(function_sql))
            logger.info("✅ 트리거 함수 생성 완료")
            
            # 2. 기존 트리거 삭제 (있다면)
            drop_trigger_sql = """
            DROP TRIGGER IF EXISTS trigger_update_history_on_library_delete ON library_items;
            """
            
            conn.execute(text(drop_trigger_sql))
            logger.info("🗑️ 기존 트리거 삭제 완료")
            
            # 3. 새 트리거 생성 (친구가 성공한 코드 그대로 사용)
            trigger_sql = """
            CREATE TRIGGER trigger_update_history_on_library_delete
                AFTER DELETE ON library_items
                FOR EACH ROW
                EXECUTE FUNCTION update_history_s3_key_on_library_delete();
            """
            
            conn.execute(text(trigger_sql))
            logger.info("✅ 트리거 생성 완료")
            
            # 4. 변경사항 커밋
            conn.commit()
            logger.info("💾 변경사항 저장 완료")
            
            print("\n🎉 트리거 생성 성공!")
            print("📋 생성된 트리거:")
            print("  - 함수명: update_history_s3_key_on_library_delete()")
            print("  - 트리거명: trigger_update_history_on_library_delete")
            print("  - 동작: library_items 삭제 시 history 테이블의 s3_key를 NULL로 설정")
            
    except Exception as e:
        logger.error(f"❌ 트리거 생성 실패: {e}")
        raise

if __name__ == "__main__":
    print("🚀 PostgreSQL 트리거 생성 스크립트 시작")
    print("📊 데이터베이스: testdb (192.168.0.163:5432)")
    print()
    
    try:
        create_trigger()
        print("\n✨ 트리거 생성 완료!")
        print("이제 라이브러리에서 파일을 삭제하면 history 테이블의 s3_key가 자동으로 NULL이 됩니다.")
        
    except Exception as e:
        print(f"\n💥 오류 발생: {e}")
        sys.exit(1)