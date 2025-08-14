# schemas/profile.py (수정된 버전)
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List

# === 기본 정보 스키마 ===
class BasicInfoUpdate(BaseModel):
    """기본 정보 업데이트 스키마"""
    name: Optional[str] = None
    slug: Optional[str] = None
    bio: Optional[str] = None
    thumbnail_url: Optional[str] = None
    gallery_title: Optional[str] = None
    gallery_description: Optional[str] = None
    is_public_gallery: Optional[bool] = None
    instagram_username: Optional[str] = None
    youtube_channel_id: Optional[str] = None
    custom_domain: Optional[str] = None

# === 작가 소개문 스키마 ===
class ArtistStatementUpdate(BaseModel):
    """작가 소개문 업데이트 스키마"""
    statement_ko: Optional[str] = None
    statement_en: Optional[str] = None

class ArtistStatementResponse(BaseModel):
    """작가 소개문 응답 스키마"""
    id: int
    statement_ko: Optional[str] = None
    statement_en: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === 아티스트 비디오 스키마 ===
class ArtistVideoCreate(BaseModel):
    """아티스트 비디오 생성 스키마"""
    video_url: str
    title_ko: Optional[str] = None
    title_en: Optional[str] = None
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    is_featured: bool = False

class ArtistVideoUpdate(BaseModel):
    """아티스트 비디오 수정 스키마"""
    title_ko: Optional[str] = None
    title_en: Optional[str] = None
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    order_index: Optional[int] = None

class ArtistVideoResponse(BaseModel):
    """아티스트 비디오 응답 스키마"""
    id: int
    video_url: str
    video_id: Optional[str] = None
    title_ko: Optional[str] = None
    title_en: Optional[str] = None
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    is_featured: bool
    is_active: bool
    order_index: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# === Q&A 스키마 ===
class ArtistQACreate(BaseModel):
    """Q&A 생성 스키마"""
    question_ko: str
    question_en: Optional[str] = None
    answer_ko: str
    answer_en: Optional[str] = None

class ArtistQAResponse(BaseModel):
    """Q&A 응답 스키마"""
    id: int
    question_ko: str
    question_en: str
    answer_ko: str
    answer_en: str
    is_active: bool
    order_index: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# === 전시회 스키마 ===
class ExhibitionCreate(BaseModel):
    """전시회 생성 스키마"""
    title_ko: str
    title_en: Optional[str] = None
    venue_ko: Optional[str] = None
    venue_en: Optional[str] = None
    year: str
    exhibition_type: str = "group"  # solo, group, fair
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    is_featured: bool = False

class ExhibitionUpdate(BaseModel):
    """전시회 수정 스키마"""
    title_ko: Optional[str] = None
    title_en: Optional[str] = None
    venue_ko: Optional[str] = None
    venue_en: Optional[str] = None
    year: Optional[str] = None
    exhibition_type: Optional[str] = None
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    order_index: Optional[int] = None

class ExhibitionResponse(BaseModel):
    """전시회 응답 스키마"""
    id: int
    title_ko: str
    title_en: str
    venue_ko: Optional[str] = None
    venue_en: Optional[str] = None
    year: str
    exhibition_type: str
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    is_featured: bool
    is_active: bool
    order_index: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# === 수상 스키마 ===
class AwardCreate(BaseModel):
    """수상 생성 스키마"""
    title_ko: str
    title_en: Optional[str] = None
    organization_ko: Optional[str] = None
    organization_en: Optional[str] = None
    year: str
    award_type: str = "recognition"  # grand, excellence, recognition
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    is_featured: bool = False

class AwardResponse(BaseModel):
    """수상 응답 스키마"""
    id: int
    title_ko: str
    title_en: str
    organization_ko: Optional[str] = None
    organization_en: Optional[str] = None
    year: str
    award_type: str
    description_ko: Optional[str] = None
    description_en: Optional[str] = None
    is_featured: bool
    is_active: bool
    order_index: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# === 프론트엔드 호환 스키마 ===
class StudioProcessUpdate(BaseModel):
    """스튜디오 프로세스 업데이트 (프론트엔드 호환)"""
    studio_description: Optional[str] = None
    process_video_1: Optional[str] = None  # ✅ 수정: None1 -> None
    process_video_2: Optional[str] = None

class AboutArtistUpdate(BaseModel):
    """About Artist 업데이트 (프론트엔드 호환)"""
    bio: Optional[str] = None
    youtube_url_1: Optional[str] = None
    youtube_url_2: Optional[str] = None

class InterviewUpdate(BaseModel):
    """인터뷰 업데이트 (프론트엔드 호환)"""
    qa_list: List[dict] = []  # [{"id": 1, "question": "...", "answer": "..."}]

# === 통합 프로필 응답 스키마 ===
class ProfileResponse(BaseModel):
    """전체 프로필 응답 스키마"""
    basic: dict  # 임시로 dict 사용, 나중에 UserResponse로 변경
    artist_statement: Optional[ArtistStatementResponse] = None
    artist_videos: List[ArtistVideoResponse] = []
    qa_list: List[ArtistQAResponse] = []
    exhibitions: List[ExhibitionResponse] = []
    awards: List[AwardResponse] = []