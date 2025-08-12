# models/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 데이터베이스 URL (개발환경: SQLite, 운영환경: PostgreSQL 등으로 변경)
DATABASE_URL = "sqlite:///./artive.db"

# 데이터베이스 엔진 생성
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # SQLite용 설정
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성 (모든 모델이 상속받을 베이스)
Base = declarative_base()

# 데이터베이스 세션 의존성 함수
def get_db():
    """데이터베이스 세션을 생성하고 반환하는 의존성 함수"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 테이블 생성 함수
def create_tables():
    """모든 테이블을 생성하는 함수"""
    Base.metadata.create_all(bind=engine)