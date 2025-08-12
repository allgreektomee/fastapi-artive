# models/user.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    # 기본 정보
    id = Column(Integer, primary_key=True, index=True)  # 사용자 고유 ID
    email = Column(String(255), unique=True, nullable=False, index=True)  # 이메일 (로그인용)
    password = Column(String(255), nullable=False)  # 암호화된 비밀번호
    name = Column(String(100), nullable=False)  # 사용자 이름
    
    # 프로필 정보
    thumbnail_url = Column(String(500))  # 프로필 이미지 URL
    bio = Column(Text)  # 자기소개/아티스트 소개
    role = Column(String(50), default="artist")  # 사용자 역할 (artist, admin 등)
    
    # 갤러리 도메인 설정
    slug = Column(String(100), unique=True, nullable=False, index=True)  # 사용자 도메인 경로 (artive.com/{slug})
    custom_domain = Column(String(255), unique=True)  # 커스텀 도메인 ({custom_domain})
    
    # 갤러리 설정
    is_public_gallery = Column(Boolean, default=True)  # 갤러리 공개 여부
    gallery_title = Column(String(200))  # 갤러리 제목 (기본값: name)
    gallery_description = Column(Text)  # 갤러리 소개글
    show_work_in_progress = Column(Boolean, default=True)  # 작업중 작품 표시 여부
    default_artwork_privacy = Column(String(20), default="public")  # 기본 작품 공개 설정 (public/private/unlisted)
    
    # Instagram 연동
    instagram_user_id = Column(String(100))  # Instagram 사용자 ID
    instagram_access_token = Column(Text)  # Instagram API 토큰
    instagram_token_expires = Column(DateTime)  # Instagram 토큰 만료일
    instagram_username = Column(String(100))  # Instagram 사용자명
    
    # 기타 소셜미디어 연동
    youtube_channel_id = Column(String(100))  # YouTube 채널 ID
    facebook_page_id = Column(String(100))  # Facebook 페이지 ID
    
    # 활동 통계
    total_artworks = Column(Integer, default=0)  # 총 작품 수
    total_views = Column(Integer, default=0)  # 총 조회수
    follower_count = Column(Integer, default=0)  # 팔로워 수
    
    # 알림 설정
    email_notifications = Column(Boolean, default=True)  # 이메일 알림 허용
    marketing_emails = Column(Boolean, default=False)  # 마케팅 이메일 수신 허용
    
    # 계정 상태
    is_verified = Column(Boolean, default=False)  # 이메일 인증 여부
    is_active = Column(Boolean, default=True)  # 계정 활성화 여부
    
    # 시스템 정보
    timezone = Column(String(50), default="Asia/Seoul")  # 시간대
    language = Column(String(10), default="ko")  # 언어 설정
    created_at = Column(DateTime, default=func.now())  # 가입일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 수정일시
    last_login = Column(DateTime)  # 마지막 로그인 시간
    
    # 관계 설정
    artworks = relationship("Artwork", back_populates="user")  # 작품들과의 관계
    artist_statement = relationship("ArtistStatement", back_populates="user", uselist=False)  # 작가 소개 (1:1)
    artist_videos = relationship("ArtistVideo", back_populates="user")  # 작가 영상들
    artist_qa = relationship("ArtistQA", back_populates="user")  # Q&A들
    exhibitions = relationship("Exhibition", back_populates="user")  # 전시 경력
    awards = relationship("Award", back_populates="user")  # 수상 경력
    
    # 관계 설정
    artworks = relationship("Artwork", back_populates="user")  # 작품들과의 관계