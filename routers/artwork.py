# routers/artwork.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from models.database import get_db
from models.user import User
from schemas.artwork import (
    ArtworkCreate, ArtworkUpdate, ArtworkCardResponse, ArtworkDetailResponse,
    ArtworkFilter, PaginatedArtworksResponse, UserArtworkStats,
    ArtworkStatusEnum, ArtworkPrivacyEnum
)
from services.artwork_service import ArtworkService
from routers.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=ArtworkDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_artwork(
    artwork_data: ArtworkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    새 작품을 생성합니다
    - 로그인한 사용자만 생성 가능
    - 대표 이미지와 작업중 이미지를 별도로 설정 가능
    """
    artwork = ArtworkService.create_artwork(db, artwork_data, current_user.id)
    return ArtworkDetailResponse.from_orm(artwork)

@router.get("/my", response_model=PaginatedArtworksResponse)
async def get_my_artworks(
    status: Optional[ArtworkStatusEnum] = Query(None, description="작품 상태 필터"),
    year: Optional[str] = Query(None, description="제작 년도 필터"),
    medium: Optional[str] = Query(None, description="매체 필터"),
    privacy: Optional[ArtworkPrivacyEnum] = Query(None, description="공개 설정 필터"),
    search: Optional[str] = Query(None, description="제목/설명 검색"),
    sort_by: str = Query("created_at", description="정렬 기준"),
    sort_order: str = Query("desc", description="정렬 순서"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 작품 목록을 조회합니다
    - 로그인한 사용자의 모든 작품 조회 (비공개 포함)
    - 필터링, 검색, 정렬, 페이지네이션 지원
    """
    filters = ArtworkFilter(
        status=status,
        year=year,
        medium=medium,
        privacy=privacy,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size
    )
    
    return ArtworkService.get_user_artworks(db, current_user.id, filters, current_user.id)

@router.get("/stats", response_model=UserArtworkStats)
async def get_my_artwork_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    내 작품 통계를 조회합니다
    - 총 작품 수, 완성/작업중 개수
    - 조회수, 좋아요 통계
    - 가장 인기 있는 작품 정보
    """
    return ArtworkService.get_user_artwork_stats(db, current_user.id)

@router.get("/{artwork_id}", response_model=ArtworkDetailResponse)
async def get_artwork(
    artwork_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    작품 상세 정보를 조회합니다
    - 공개 작품은 누구나 조회 가능
    - 비공개 작품은 소유자만 조회 가능
    - 조회수 자동 증가
    """
    user_id = current_user.id if current_user else None
    artwork = ArtworkService.get_artwork_by_id(db, artwork_id, user_id)
    
    if not artwork:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작품을 찾을 수 없거나 접근 권한이 없습니다"
        )
    
    # 조회수 증가 (소유자가 아닌 경우만)
    if not current_user or current_user.id != artwork.user_id:
        ArtworkService.increment_view_count(db, artwork_id)
    
    return ArtworkDetailResponse.from_orm(artwork)

@router.put("/{artwork_id}", response_model=ArtworkDetailResponse)
async def update_artwork(
    artwork_id: int,
    artwork_data: ArtworkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    작품 정보를 수정합니다
    - 작품 소유자만 수정 가능
    - 상태를 '완성됨'으로 변경하면 완성일이 자동 설정됨
    """
    artwork = ArtworkService.update_artwork(db, artwork_id, artwork_data, current_user.id)
    return ArtworkDetailResponse.from_orm(artwork)

@router.delete("/{artwork_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_artwork(
    artwork_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    작품을 삭제합니다
    - 작품 소유자만 삭제 가능
    - 연관된 모든 히스토리도 함께 삭제됨
    """
    ArtworkService.delete_artwork(db, artwork_id, current_user.id)

@router.post("/{artwork_id}/like")
async def toggle_artwork_like(
    artwork_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    작품 좋아요를 토글합니다
    - 로그인한 사용자만 좋아요 가능
    """
    success = ArtworkService.toggle_like(db, artwork_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작품을 찾을 수 없습니다"
        )
    
    return {"message": "좋아요가 반영되었습니다"}

# === 공개 갤러리 조회 API ===
@router.get("/user/{user_slug}", response_model=PaginatedArtworksResponse)
async def get_user_gallery_artworks(
    user_slug: str,
    status: Optional[ArtworkStatusEnum] = Query(None, description="작품 상태 필터"),
    year: Optional[str] = Query(None, description="제작 년도 필터"),
    medium: Optional[str] = Query(None, description="매체 필터"),
    search: Optional[str] = Query(None, description="제목/설명 검색"),
    sort_by: str = Query("created_at", description="정렬 기준"),
    sort_order: str = Query("desc", description="정렬 순서"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 공개 갤러리를 조회합니다
    - slug로 사용자 식별 (예: artive.com/johndoe)
    - 공개 작품만 조회 (로그인 없이도 접근 가능)
    """
    from services.auth_service import AuthService
    
    user = AuthService.get_user_by_slug(db, user_slug)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    if not user.is_public_gallery:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비공개 갤러리입니다"
        )
    
    filters = ArtworkFilter(
        status=status,
        year=year,
        medium=medium,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size
    )
    
    # 로그인하지 않은 사용자는 viewer_id를 None으로 처리
    return ArtworkService.get_user_artworks(db, user.id, filters, None)

@router.get("/user/{user_slug}/stats", response_model=UserArtworkStats)
async def get_user_gallery_stats(
    user_slug: str,
    db: Session = Depends(get_db)
):
    """
    특정 사용자의 공개 갤러리 통계를 조회합니다
    """
    from services.auth_service import AuthService
    
    user = AuthService.get_user_by_slug(db, user_slug)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    if not user.is_public_gallery:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비공개 갤러리입니다"
        )
    
    return ArtworkService.get_user_artwork_stats(db, user.id)