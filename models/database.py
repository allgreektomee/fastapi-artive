# models/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# 데이터베이스 설정
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./artive.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 테이블 생성 함수
def create_tables():
    # 실제 존재하는 모델들만 임포트
    try:
        from models.user import User
        print("✓ User model imported")
    except ImportError as e:
        print(f"✗ User model import failed: {e}")
    
    try:
        from models.artwork import Artwork, ArtworkHistory, ArtworkHistoryImage
        print("✓ Artwork models imported")
    except ImportError as e:
        print(f"✗ Artwork models import failed: {e}")
    
    try:
        from models.artist_info import ArtistStatement, ArtistVideo, ArtistQA, Exhibition, Award
        print("✓ Artist info models imported")
    except ImportError as e:
        print(f"✗ Artist info models import failed: {e}")
    
    try:
        from models.blog import BlogPost
        print("✓ Blog model imported")
    except ImportError as e:
        print(f"✗ Blog model import failed: {e}")
    
    try:
        from models.email_verification import EmailVerificationToken
        print("✓ Email verification model imported")
    except ImportError as e:
        print(f"✗ Email verification model import failed: {e}")
    
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")