# models/user.py (순환 import 문제 해결)
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    # 기본 정보
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    
    # 프로필 정보
    thumbnail_url = Column(String(500))
    bio = Column(Text)
    role = Column(String, default="artist", nullable=False)
    
    # 갤러리 도메인 설정
    slug = Column(String(100), unique=True, nullable=False, index=True)
    custom_domain = Column(String(255), unique=True)
    
    # 갤러리 설정
    is_public_gallery = Column(Boolean, default=True)
    gallery_title = Column(String(200))
    gallery_description = Column(Text)
    show_work_in_progress = Column(Boolean, default=True)
    default_artwork_privacy = Column(String(20), default="public")
    
    # Instagram 연동
    instagram_user_id = Column(String(100))
    instagram_access_token = Column(Text)
    instagram_token_expires = Column(DateTime)
    instagram_username = Column(String(100))
    
    # About 섹션 (범용적)
    about_text = Column(Text)           # 소개 텍스트
    about_image = Column(String(500))   # 소개 이미지
    about_video = Column(String(500))   # 소개 영상
    
    # 작업공간 
    studio_description = Column(Text)
    studio_image = Column(String(500))
    process_video = Column(String(500))
    
    # 기타 소셜미디어 연동
    youtube_channel_id = Column(String(100))
    facebook_page_id = Column(String(100))
    
    # 활동 통계
    total_artworks = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    follower_count = Column(Integer, default=0)
    
    # 알림 설정
    email_notifications = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    
    # 계정 상태
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # 시스템 정보
    timezone = Column(String(50), default="Asia/Seoul")
    language = Column(String(10), default="ko")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # === 관계 설정 ===
    # 작품 관계 (순환 import 방지를 위해 string으로 설정)
    artworks = relationship("Artwork", back_populates="user")
    blog_posts = relationship("BlogPost", back_populates="user") 
    
    # 아티스트 정보 관계 (string으로 설정)
    artist_statement = relationship("ArtistStatement", back_populates="user", uselist=False)
    artist_videos = relationship("ArtistVideo", back_populates="user")
    artist_qa = relationship("ArtistQA", back_populates="user")
    exhibitions = relationship("Exhibition", back_populates="user")
    awards = relationship("Award", back_populates="user")