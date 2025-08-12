# models/__init__.py
from .database import Base, engine, get_db, create_tables
from .user import User
from .email_verification import EmailVerificationToken
from .artwork import Artwork, ArtworkHistory, ArtworkHistoryImage
from .artist_info import ArtistStatement, ArtistVideo, ArtistQA, Exhibition, Award

# 모든 모델을 임포트해서 테이블 생성시 인식되도록 함
__all__ = [
    "Base",
    "engine", 
    "get_db",
    "create_tables",
    "User",
    "EmailVerificationToken",
    "Artwork",
    "ArtworkHistory", 
    "ArtworkHistoryImage",
    "ArtistStatement",
    "ArtistVideo",
    "ArtistQA",
    "Exhibition",
    "Award"
]