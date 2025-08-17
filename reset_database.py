# reset_database.py
"""
데이터베이스를 완전히 리셋하는 스크립트
주의: 모든 데이터가 삭제됩니다!
"""

import os
from models.database import engine, Base

def reset_database():
    """데이터베이스 파일 삭제 후 재생성"""
    
    # SQLite 데이터베이스 파일 경로
    db_file = "artive.db"  # 또는 실제 DB 파일명
    
    try:
        # 1. 기존 DB 파일 삭제
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"✅ 기존 데이터베이스 파일 삭제: {db_file}")
        
        # 2. 모든 테이블 재생성
        print("🔨 새 테이블 생성 중...")
        
        # 모든 모델 import (테이블 생성을 위해)
        from models.user import User
        from models.blog import BlogPost
        try:
            from models.artwork import Artwork
        except ImportError:
            print("⚠️ Artwork 모델 없음 - 건너뛰기")
        
        try:
            from models.email_verification import EmailVerificationToken
        except ImportError:
            print("⚠️ EmailVerificationToken 모델 없음 - 건너뛰기")
        
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        print("✅ 새 테이블 생성 완료!")
        
        # 테이블 확인
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"📋 생성된 테이블: {tables}")
        
        # blog_posts 테이블 컬럼 확인
        if 'blog_posts' in tables:
            columns = inspector.get_columns('blog_posts')
            print("📝 blog_posts 테이블 컬럼:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
        
        print("🎉 데이터베이스 리셋 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("⚠️  모든 데이터가 삭제됩니다!")
    response = input("계속하시겠습니까? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        reset_database()
    else:
        print("❌ 취소되었습니다.")