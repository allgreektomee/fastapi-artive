# schemas/user.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    """사용자 생성 요청 스키마"""
    email: EmailStr  # 이메일
    password: str  # 비밀번호
    name: str  # 이름
    slug: str  # 도메인 경로
    bio: Optional[str] = None  # 자기소개
    
class UserUpdate(BaseModel):
    """사용자 정보 수정 스키마"""
    name: Optional[str] = None  # 이름 수정
    bio: Optional[str] = None  # 자기소개 수정
    thumbnail_url: Optional[str] = None  # 프로필 이미지 URL
    gallery_title: Optional[str] = None  # 갤러리 제목
    gallery_description: Optional[str] = None  # 갤러리 소개
    is_public_gallery: Optional[bool] = None  # 갤러리 공개 여부
    show_work_in_progress: Optional[bool] = None  # 작업중 작품 표시 여부
    custom_domain: Optional[str] = None  # 커스텀 도메인
    
class UserResponse(BaseModel):
    """사용자 응답 스키마"""
    id: int  # 사용자 ID
    email: str  # 이메일
    name: str  # 이름
    slug: str  # 도메인 경로
    custom_domain: Optional[str] = None  # 커스텀 도메인
    thumbnail_url: Optional[str] = None  # 프로필 이미지
    bio: Optional[str] = None  # 자기소개
    gallery_title: Optional[str] = None  # 갤러리 제목
    is_public_gallery: bool  # 갤러리 공개 여부
    total_artworks: int  # 총 작품 수
    total_views: int  # 총 조회수
    created_at: datetime  # 가입일시
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr  # 이메일
    password: str  # 비밀번호

class UserGalleryPublic(BaseModel):
    """공개 갤러리용 사용자 정보 스키마"""
    name: str  # 아티스트 이름
    slug: str  # 도메인 경로
    bio: Optional[str] = None  # 자기소개
    thumbnail_url: Optional[str] = None  # 프로필 이미지
    gallery_title: Optional[str] = None  # 갤러리 제목
    gallery_description: Optional[str] = None  # 갤러리 소개
    total_artworks: int  # 총 작품 수
    total_views: int  # 총 조회수
    
    class Config:
        from_attributes = True

class InstagramConnect(BaseModel):
    """Instagram 계정 연결 스키마"""
    access_token: str  # Instagram 액세스 토큰
    user_id: str  # Instagram 사용자 ID
    username: str  # Instagram 사용자명
    
class SlugCheckRequest(BaseModel):
    """슬러그 중복 확인 요청 스키마"""
    slug: str