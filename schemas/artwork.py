# schemas/artwork.py
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ArtworkStatusEnum(str, Enum):
    """작품 상태"""
    WORK_IN_PROGRESS = "work_in_progress"  # 작업중
    COMPLETED = "completed"  # 완성됨
    ARCHIVED = "archived"  # 보관됨

class ArtworkPrivacyEnum(str, Enum):
    """작품 공개 설정"""
    PUBLIC = "public"  # 공개
    PRIVATE = "private"  # 비공개
    UNLISTED = "unlisted"  # 링크를 아는 사람만

class HistoryTypeEnum(str, Enum):
    """히스토리 타입"""
    MANUAL = "manual"  # 직접 작성
    INSTAGRAM = "instagram"  # 인스타그램
    YOUTUBE = "youtube"  # 유튜브
    FACEBOOK = "facebook"  # 페이스북

# === 작품 스키마 ===
class ArtworkCreate(BaseModel):
    """작품 생성 스키마"""
    title: str  # 작품 제목
    description: Optional[str] = None  # 작품 설명
    medium: Optional[str] = None  # 매체
    size: Optional[str] = None  # 크기
    year: Optional[str] = None  # 제작년도
    thumbnail_url: Optional[str] = None  # 대표 이미지
    work_in_progress_url: Optional[str] = None  # 작업중 이미지
    privacy: ArtworkPrivacyEnum = ArtworkPrivacyEnum.PUBLIC  # 공개 설정
    started_at: Optional[datetime] = None  # 작업 시작일
    estimated_completion: Optional[datetime] = None  # 예상 완성일

class ArtworkUpdate(BaseModel):
    """작품 수정 스키마"""
    title: Optional[str] = None  # 제목 수정
    description: Optional[str] = None  # 설명 수정
    medium: Optional[str] = None  # 매체 수정
    size: Optional[str] = None  # 크기 수정
    year: Optional[str] = None  # 제작년도 수정
    thumbnail_url: Optional[str] = None  # 대표 이미지 수정
    work_in_progress_url: Optional[str] = None  # 작업중 이미지 수정
    status: Optional[ArtworkStatusEnum] = None  # 상태 수정
    privacy: Optional[ArtworkPrivacyEnum] = None  # 공개 설정 수정
    completed_at: Optional[datetime] = None  # 완성일 설정
    estimated_completion: Optional[datetime] = None  # 예상 완성일 수정

class ArtworkCardResponse(BaseModel):
    """갤러리 카드용 작품 정보 (목록용)"""
    id: int  # 작품 ID
    title: str  # 제목
    thumbnail_url: Optional[str] = None  # 썸네일
    work_in_progress_url: Optional[str] = None  # 작업중 이미지
    status: ArtworkStatusEnum  # 상태
    medium: Optional[str] = None  # 매체
    size: Optional[str] = None  # 크기
    year: Optional[str] = None  # 제작년도
    view_count: int  # 조회수
    like_count: int  # 좋아요
    history_count: int  # 히스토리 개수
    created_at: datetime  # 생성일
    
    class Config:
        from_attributes = True

class ArtworkDetailResponse(BaseModel):
    """작품 상세 정보"""
    id: int  # 작품 ID
    title: str  # 제목
    description: Optional[str] = None  # 설명
    thumbnail_url: Optional[str] = None  # 대표 이미지
    work_in_progress_url: Optional[str] = None  # 작업중 이미지
    medium: Optional[str] = None  # 매체
    size: Optional[str] = None  # 크기
    year: Optional[str] = None  # 제작년도
    status: ArtworkStatusEnum  # 상태
    privacy: ArtworkPrivacyEnum  # 공개 설정
    started_at: Optional[datetime] = None  # 시작일
    completed_at: Optional[datetime] = None  # 완성일
    estimated_completion: Optional[datetime] = None  # 예상 완성일
    view_count: int  # 조회수
    like_count: int  # 좋아요
    history_count: int  # 히스토리 개수
    created_at: datetime  # 생성일
    updated_at: datetime  # 수정일
    user_id: int  # 소유자 ID
    
    class Config:
        from_attributes = True

# === 히스토리 스키마 ===
class HistoryImageCreate(BaseModel):
    """히스토리 이미지 생성 스키마"""
    image_url: str  # 이미지 URL
    alt_text: Optional[str] = None  # 대체 텍스트
    caption: Optional[str] = None  # 캡션
    order_index: int = 0  # 순서

class HistoryImageResponse(BaseModel):
    """히스토리 이미지 응답 스키마"""
    id: int  # 이미지 ID
    image_url: str  # 이미지 URL
    alt_text: Optional[str] = None  # 대체 텍스트
    caption: Optional[str] = None  # 캡션
    order_index: int  # 순서
    
    class Config:
        from_attributes = True

class ArtworkHistoryCreate(BaseModel):
    """히스토리 생성 스키마"""
    title: Optional[str] = None  # 제목
    content: Optional[str] = None  # 내용
    media_url: Optional[str] = None  # 미디어 URL
    thumbnail_url: Optional[str] = None  # 썸네일
    media_type: Optional[str] = "image"  # 미디어 타입
    history_type: HistoryTypeEnum = HistoryTypeEnum.MANUAL  # 히스토리 타입
    external_url: Optional[str] = None  # 외부 링크
    youtube_video_id: Optional[str] = None  # 유튜브 비디오 ID
    work_date: Optional[datetime] = None  # 작업 날짜
    images: List[HistoryImageCreate] = []  # 다중 이미지

class ArtworkHistoryUpdate(BaseModel):
    """히스토리 수정 스키마"""
    title: Optional[str] = None  # 제목 수정
    content: Optional[str] = None  # 내용 수정
    media_url: Optional[str] = None  # 미디어 URL 수정
    thumbnail_url: Optional[str] = None  # 썸네일 수정
    work_date: Optional[datetime] = None  # 작업 날짜 수정
    order_index: Optional[int] = None  # 순서 수정

class ArtworkHistoryResponse(BaseModel):
    """히스토리 응답 스키마"""
    id: int  # 히스토리 ID
    title: Optional[str] = None  # 제목
    content: Optional[str] = None  # 내용
    media_url: Optional[str] = None  # 미디어 URL
    thumbnail_url: Optional[str] = None  # 썸네일
    media_type: Optional[str] = None  # 미디어 타입
    history_type: HistoryTypeEnum  # 히스토리 타입
    external_url: Optional[str] = None  # 외부 링크
    youtube_video_id: Optional[str] = None  # 유튜브 비디오 ID
    youtube_title: Optional[str] = None  # 유튜브 제목
    instagram_post_id: Optional[str] = None  # 인스타그램 포스트 ID
    order_index: int  # 순서
    work_date: Optional[datetime] = None  # 작업 날짜
    created_at: datetime  # 생성일
    images: List[HistoryImageResponse] = []  # 다중 이미지
    
    class Config:
        from_attributes = True

# === 유튜브 링크 관련 ===
class YoutubeVideoInfo(BaseModel):
    """유튜브 비디오 정보"""
    video_id: str  # 비디오 ID
    title: str  # 제목
    thumbnail_url: str  # 썸네일
    duration: Optional[int] = None  # 길이(초)

class AddYoutubeHistory(BaseModel):
    """유튜브 히스토리 추가 스키마"""
    youtube_url: str  # 유튜브 URL
    title: Optional[str] = None  # 커스텀 제목
    content: Optional[str] = None  # 설명
    work_date: Optional[datetime] = None  # 작업 날짜

# === 인스타그램 관련 ===
class AddInstagramHistory(BaseModel):
    """인스타그램 히스토리 추가 스키마"""
    instagram_url: str  # 인스타그램 URL
    title: Optional[str] = None  # 커스텀 제목
    content: Optional[str] = None  # 추가 설명

# === 갤러리 통합 응답 스키마 ===
class UserGalleryResponse(BaseModel):
    """사용자 갤러리 전체 응답"""
    user_info: 'UserGalleryPublic'  # 사용자 정보 (forward reference)
    artworks: List[ArtworkCardResponse]  # 작품 목록
    total_count: int  # 전체 작품 수
    work_in_progress_count: int  # 작업중 작품 수
    completed_count: int  # 완성 작품 수
    archived_count: int  # 보관된 작품 수

class ArtworkWithHistoriesResponse(BaseModel):
    """작품 상세 + 히스토리 목록 통합 응답"""
    artwork: ArtworkDetailResponse  # 작품 상세 정보
    histories: List[ArtworkHistoryResponse]  # 히스토리 목록 (시간순 정렬)
    next_artwork_id: Optional[int] = None  # 다음 작품 ID (갤러리 네비게이션용)
    prev_artwork_id: Optional[int] = None  # 이전 작품 ID (갤러리 네비게이션용)
    total_histories: int  # 총 히스토리 개수

# === 검색/필터링 스키마 ===
class ArtworkFilter(BaseModel):
    """작품 필터링/검색 파라미터"""
    status: Optional[ArtworkStatusEnum] = None  # 상태별 필터 (작업중/완성/보관)
    year: Optional[str] = None  # 년도별 필터
    medium: Optional[str] = None  # 매체별 필터 (유화/수채화/디지털 등)
    search: Optional[str] = None  # 제목/설명 텍스트 검색
    privacy: Optional[ArtworkPrivacyEnum] = None  # 공개 설정별 필터
    sort_by: Optional[str] = "created_at"  # 정렬 기준 (created_at/updated_at/view_count/like_count)
    sort_order: Optional[str] = "desc"  # 정렬 순서 (asc/desc)
    page: int = 1  # 페이지 번호
    size: int = 20  # 페이지 크기

class PaginatedArtworksResponse(BaseModel):
    """페이지네이션된 작품 목록 응답"""
    artworks: List[ArtworkCardResponse]  # 작품 목록
    total: int  # 전체 작품 수
    page: int  # 현재 페이지
    size: int  # 페이지 크기
    pages: int  # 총 페이지 수
    has_next: bool  # 다음 페이지 존재 여부
    has_prev: bool  # 이전 페이지 존재 여부

# === 통계 스키마 ===
class UserArtworkStats(BaseModel):
    """사용자 작품 통계"""
    total_artworks: int  # 총 작품 수
    completed_artworks: int  # 완성 작품 수
    work_in_progress: int  # 작업중 작품 수
    archived_artworks: int  # 보관된 작품 수
    total_views: int  # 총 조회수
    total_likes: int  # 총 좋아요
    total_histories: int  # 총 히스토리 수
    most_viewed_artwork: Optional[ArtworkCardResponse] = None  # 가장 인기 작품
    recent_artwork: Optional[ArtworkCardResponse] = None  # 최근 작품
    years_active: List[str] = []  # 활동 연도 목록
    mediums_used: List[str] = []  # 사용한 매체 목록

# === 벌크 작업 스키마 ===
class BulkUpdateArtworks(BaseModel):
    """여러 작품 일괄 수정"""
    artwork_ids: List[int]  # 수정할 작품 ID 목록
    privacy: Optional[ArtworkPrivacyEnum] = None  # 일괄 공개 설정 변경
    status: Optional[ArtworkStatusEnum] = None  # 일괄 상태 변경
    display_order_start: Optional[int] = None  # 표시 순서 일괄 변경 시작 번호

class BulkDeleteArtworks(BaseModel):
    """여러 작품 일괄 삭제"""
    artwork_ids: List[int]  # 삭제할 작품 ID 목록
    confirm: bool  # 삭제 확인 (안전장치)

# === 히스토리 순서 변경 스키마 ===
class ReorderHistories(BaseModel):
    """히스토리 순서 재정렬"""
    history_orders: List[tuple[int, int]]  # [(history_id, new_order_index), ...]

class HistoryOrderUpdate(BaseModel):
    """개별 히스토리 순서 변경"""
    history_id: int  # 히스토리 ID
    new_order_index: int  # 새로운 순서

# === 외부 플랫폼 연동 응답 스키마 ===
class InstagramImportResult(BaseModel):
    """인스타그램 가져오기 결과"""
    success: bool  # 성공 여부
    imported_histories: List[ArtworkHistoryResponse] = []  # 가져온 히스토리들
    failed_urls: List[str] = []  # 실패한 URL들
    message: str  # 결과 메시지

class YoutubeImportResult(BaseModel):
    """유튜브 가져오기 결과"""
    success: bool  # 성공 여부
    imported_history: Optional[ArtworkHistoryResponse] = None  # 가져온 히스토리
    video_info: Optional[YoutubeVideoInfo] = None  # 비디오 정보
    message: str  # 결과 메시지