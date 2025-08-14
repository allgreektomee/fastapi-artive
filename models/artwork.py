# models/artwork.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .database import Base

class ArtworkStatus(str, enum.Enum):
    """작품 상태 열거형"""
    WORK_IN_PROGRESS = "work_in_progress"  # 작업중
    COMPLETED = "completed"  # 완성됨
    ARCHIVED = "archived"  # 보관됨

class ArtworkPrivacy(str, enum.Enum):
    """작품 공개 설정 열거형"""
    PUBLIC = "public"  # 공개
    PRIVATE = "private"  # 비공개
    UNLISTED = "unlisted"  # 링크를 아는 사람만

class Artwork(Base):
    __tablename__ = "artworks"
    
    # 기본 정보
    id = Column(Integer, primary_key=True, index=True)  # 작품 고유 ID
    title = Column(String(200), nullable=False)  # 작품 제목
    description = Column(Text)  # 작품 설명
    
    # 이미지 정보
    thumbnail_url = Column(String(500))  # 대표 이미지 URL (완성작)
    work_in_progress_url = Column(String(500))  # 작업중 표시용 이미지 URL
    
    # 작품 정보
    medium = Column(String(100))  # 매체 (유화, 수채화, 디지털 등)
    size = Column(String(100))  # 크기 (예: "91x117cm (50호)")
    year = Column(String(20))  # 제작년도
    
    # 상태 관리
    status = Column(Enum(ArtworkStatus), default=ArtworkStatus.WORK_IN_PROGRESS)  # 작품 상태
    privacy = Column(Enum(ArtworkPrivacy), default=ArtworkPrivacy.PUBLIC)  # 공개 설정
    
    # 날짜 정보
    started_at = Column(DateTime)  # 작업 시작일
    completed_at = Column(DateTime)  # 완성일
    estimated_completion = Column(DateTime)  # 예상 완성일
    
    # 통계
    view_count = Column(Integer, default=0)  # 조회수
    like_count = Column(Integer, default=0)  # 좋아요 수
    history_count = Column(Integer, default=0)  # 히스토리 개수
    
    # 정렬 순서
    display_order = Column(Integer, default=0)  # 갤러리에서 표시 순서
    
    # 시스템 정보
    created_at = Column(DateTime, default=func.now())  # 생성일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 수정일시
    
    # 외래키
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 작품 소유자
    
    # 관계 설정
    user = relationship("User", back_populates="artworks")  # 사용자와의 관계
    histories = relationship("ArtworkHistory", back_populates="artwork", cascade="all, delete-orphan")  # 히스토리와의 관계


class HistoryType(str, enum.Enum):
    """히스토리 타입 열거형"""
    MANUAL = "manual"  # 직접 작성
    INSTAGRAM = "instagram"  # 인스타그램에서 가져옴
    YOUTUBE = "youtube"  # 유튜브 링크
    FACEBOOK = "facebook"  # 페이스북에서 가져옴

class ArtworkHistory(Base):
    __tablename__ = "artwork_histories"
    
    # 기본 정보
    id = Column(Integer, primary_key=True, index=True)  # 히스토리 고유 ID
    title = Column(String(200))  # 히스토리 제목
    content = Column(Text)  # 설명글/캡션
    
    # 미디어 정보
    media_url = Column(String(500))  # 이미지/동영상 URL
    thumbnail_url = Column(String(500))  # 썸네일 URL (동영상용)
    media_type = Column(String(50))  # 미디어 타입 (image, video)
    
    # 히스토리 타입별 정보
    history_type = Column(Enum(HistoryType), default=HistoryType.MANUAL)  # 히스토리 타입
    external_url = Column(String(500))  # 원본 외부 링크 (인스타/유튜브 등)
    external_id = Column(String(100))  # 외부 플랫폼의 고유 ID
    
    # 유튜브 전용 필드
    youtube_video_id = Column(String(50))  # 유튜브 비디오 ID
    youtube_title = Column(String(200))  # 유튜브 비디오 제목
    youtube_duration = Column(Integer)  # 동영상 길이 (초)
    
    # 인스타그램 전용 필드
    instagram_post_id = Column(String(100))  # 인스타그램 포스트 ID
    instagram_caption = Column(Text)  # 인스타그램 원본 캡션
    
    # 순서 및 날짜
    order_index = Column(Integer, default=0)  # 히스토리 내 순서
    work_date = Column(DateTime)  # 실제 작업한 날짜
    imported_at = Column(DateTime)  # 가져온 날짜 (외부 소스용)
    
    icon_emoji = Column(String(10), default="🎨") 
    
    # 시스템 정보
    created_at = Column(DateTime, default=func.now())  # 생성일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 수정일시
    
    # 외래키
    artwork_id = Column(Integer, ForeignKey("artworks.id"), nullable=False)  # 소속 작품
    
    # 관계 설정
    artwork = relationship("Artwork", back_populates="histories")  # 작품과의 관계
    images = relationship("ArtworkHistoryImage", back_populates="history", cascade="all, delete-orphan")  # 다중 이미지


class ArtworkHistoryImage(Base):
    __tablename__ = "artwork_history_images"
    
    # 기본 정보
    id = Column(Integer, primary_key=True, index=True)  # 이미지 고유 ID
    image_url = Column(String(500), nullable=False)  # 이미지 URL
    alt_text = Column(String(200))  # 대체 텍스트
    caption = Column(Text)  # 이미지 캡션
    
    # 순서
    order_index = Column(Integer, default=0)  # 히스토리 내 이미지 순서
    
    # 시스템 정보
    created_at = Column(DateTime, default=func.now())  # 업로드일시
    
    # 외래키
    history_id = Column(Integer, ForeignKey("artwork_histories.id"), nullable=False)  # 소속 히스토리
    
    # 관계 설정
    history = relationship("ArtworkHistory", back_populates="images")  # 히스토리와의 관계