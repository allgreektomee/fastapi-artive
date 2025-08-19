# services/artwork_service.py
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc
from fastapi import HTTPException, status
from datetime import datetime
import math

from models.artwork import Artwork, ArtworkHistory, ArtworkHistoryImage, ArtworkStatus, ArtworkPrivacy
from models.user import User
from schemas.artwork import (
    ArtworkCreate, ArtworkUpdate, ArtworkFilter, 
    PaginatedArtworksResponse, UserArtworkStats,
    ArtworkCardResponse, ArtworkDetailResponse
)

class ArtworkService:
    """작품 관련 비즈니스 로직을 담당하는 서비스"""
    
    @staticmethod
    def create_artwork(db: Session, artwork_data: ArtworkCreate, user_id: int) -> Artwork:
        """새 작품을 생성합니다"""
        # 표시 순서 계산 (가장 마지막에 추가)
        max_order = db.query(Artwork).filter(Artwork.user_id == user_id).count()
        # 사용자 정보 가져오기
        user = db.query(User).filter(User.id == user_id).first()
    
        artwork = Artwork(
            title=artwork_data.title,
            description=artwork_data.description,
            artist_name=user.name  if user else "Unknown Artist", 
            medium=artwork_data.medium,
            size=artwork_data.size,
            year=artwork_data.year,
            thumbnail_url=artwork_data.thumbnail_url,
            work_in_progress_url=artwork_data.work_in_progress_url,
            privacy=artwork_data.privacy,
            started_at=artwork_data.started_at,
            estimated_completion=artwork_data.estimated_completion,
            display_order=max_order,
            user_id=user_id
        )
        
        db.add(artwork)
        db.commit()
        db.refresh(artwork)
        
        # 사용자의 총 작품 수 업데이트
        ArtworkService._update_user_artwork_count(db, user_id)
        
        return artwork
    
    @staticmethod
    def get_artwork_by_id(db: Session, artwork_id: int, user_id: Optional[int] = None) -> Optional[Artwork]:
        """ID로 작품을 조회합니다 (아티스트 정보 포함)"""
        # User 정보도 함께 로드하도록 수정
        query = db.query(Artwork).options(
            joinedload(Artwork.user)  # User 관계 함께 로드
        ).filter(Artwork.id == artwork_id)
        
        # 소유자가 아닌 경우 공개된 작품만 조회
        if user_id:
            artwork = query.first()
            if artwork and (artwork.user_id == user_id or artwork.privacy == ArtworkPrivacy.PUBLIC):
                return artwork
        else:
            # 로그인하지 않은 경우 공개 작품만
            return query.filter(Artwork.privacy == ArtworkPrivacy.PUBLIC).first()
        
        return None
    
    @staticmethod
    def update_artwork(db: Session, artwork_id: int, artwork_data: ArtworkUpdate, user_id: int) -> Optional[Artwork]:
        """작품 정보를 수정합니다"""
        artwork = db.query(Artwork).filter(
            and_(Artwork.id == artwork_id, Artwork.user_id == user_id)
        ).first()
        
        if not artwork:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="작품을 찾을 수 없습니다"
            )
        
        # 수정 가능한 필드들 업데이트
        update_data = artwork_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(artwork, field):
                setattr(artwork, field, value)
        
        # 상태가 완성됨으로 변경되면 완성일 설정
        if artwork_data.status == ArtworkStatus.COMPLETED and not artwork.completed_at:
            artwork.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(artwork)
        
        return artwork
    
    @staticmethod
    def delete_artwork(db: Session, artwork_id: int, user_id: int) -> bool:
        """작품을 삭제합니다"""
        artwork = db.query(Artwork).filter(
            and_(Artwork.id == artwork_id, Artwork.user_id == user_id)
        ).first()
        
        if not artwork:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="작품을 찾을 수 없습니다"
            )
        
        db.delete(artwork)
        db.commit()
        
        # 사용자의 총 작품 수 업데이트
        ArtworkService._update_user_artwork_count(db, user_id)
        
        return True
    
    @staticmethod
    def get_user_artworks(
        db: Session, 
        user_id: int, 
        filters: ArtworkFilter, 
        viewer_id: Optional[int] = None
    ) -> PaginatedArtworksResponse:
        """사용자의 작품 목록을 조회합니다 (필터링/페이지네이션 포함)"""
        
        query = db.query(Artwork).filter(Artwork.user_id == user_id)
        
        # 권한 체크 (소유자가 아닌 경우 공개 작품만)
        if viewer_id != user_id:
            query = query.filter(Artwork.privacy == ArtworkPrivacy.PUBLIC)
        
        # 필터 적용
        if filters.status:
            query = query.filter(Artwork.status == filters.status)
        
        if filters.year:
            query = query.filter(Artwork.year == filters.year)
        
        if filters.medium:
            query = query.filter(Artwork.medium.ilike(f"%{filters.medium}%"))
        
        if filters.privacy and viewer_id == user_id:  # 소유자만 프라이버시 필터 가능
            query = query.filter(Artwork.privacy == filters.privacy)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Artwork.title.ilike(search_term),
                    Artwork.description.ilike(search_term)
                )
            )
        
        # 정렬
        if filters.sort_by == "title":
            order_by = Artwork.title
        elif filters.sort_by == "updated_at":
            order_by = Artwork.updated_at
        elif filters.sort_by == "view_count":
            order_by = Artwork.view_count
        elif filters.sort_by == "like_count":
            order_by = Artwork.like_count
        else:
            order_by = Artwork.created_at
        
        if filters.sort_order == "asc":
            query = query.order_by(asc(order_by))
        else:
            query = query.order_by(desc(order_by))
        
        # 총 개수 계산
        total = query.count()
        
        # 페이지네이션
        offset = (filters.page - 1) * filters.size
        artworks = query.offset(offset).limit(filters.size).all()
        
        # 페이지 정보 계산
        pages = math.ceil(total / filters.size) if total > 0 else 1
        has_next = filters.page < pages
        has_prev = filters.page > 1
        
        return PaginatedArtworksResponse(
            artworks=[ArtworkCardResponse.from_orm(artwork) for artwork in artworks],
            total=total,
            page=filters.page,
            size=filters.size,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    
    @staticmethod
    def get_user_artwork_stats(db: Session, user_id: int) -> UserArtworkStats:
        """사용자의 작품 통계를 조회합니다"""
        artworks = db.query(Artwork).filter(Artwork.user_id == user_id).all()
        
        total_artworks = len(artworks)
        completed_artworks = len([a for a in artworks if a.status == ArtworkStatus.COMPLETED])
        work_in_progress = len([a for a in artworks if a.status == ArtworkStatus.WORK_IN_PROGRESS])
        archived_artworks = len([a for a in artworks if a.status == ArtworkStatus.ARCHIVED])
        
        total_views = sum(artwork.view_count for artwork in artworks)
        total_likes = sum(artwork.like_count for artwork in artworks)
        
        # 총 히스토리 수
        total_histories = db.query(ArtworkHistory).join(Artwork).filter(
            Artwork.user_id == user_id
        ).count()
        
        # 가장 인기 있는 작품 (조회수 기준)
        most_viewed_artwork = None
        if artworks:
            most_viewed = max(artworks, key=lambda x: x.view_count)
            if most_viewed.view_count > 0:
                most_viewed_artwork = ArtworkCardResponse.from_orm(most_viewed)
        
        # 최근 작품
        recent_artwork = None
        if artworks:
            recent = max(artworks, key=lambda x: x.created_at)
            recent_artwork = ArtworkCardResponse.from_orm(recent)
        
        # 활동 연도
        years_active = sorted(list(set(artwork.year for artwork in artworks if artwork.year)))
        
        # 사용한 매체
        mediums_used = sorted(list(set(artwork.medium for artwork in artworks if artwork.medium)))
        
        return UserArtworkStats(
            total_artworks=total_artworks,
            completed_artworks=completed_artworks,
            work_in_progress=work_in_progress,
            archived_artworks=archived_artworks,
            total_views=total_views,
            total_likes=total_likes,
            total_histories=total_histories,
            most_viewed_artwork=most_viewed_artwork,
            recent_artwork=recent_artwork,
            years_active=years_active,
            mediums_used=mediums_used
        )
    
    @staticmethod
    def increment_view_count(db: Session, artwork_id: int) -> bool:
        """작품 조회수를 증가시킵니다"""
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if artwork:
            artwork.view_count += 1
            db.commit()
            return True
        return False
    
    @staticmethod
    def toggle_like(db: Session, artwork_id: int, user_id: int) -> bool:
        """작품 좋아요를 토글합니다 (실제로는 단순히 카운트만 증가)"""
        # TODO: 실제로는 Like 테이블을 만들어서 중복 방지해야 함
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if artwork:
            artwork.like_count += 1
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_next_prev_artwork(
        db: Session, 
        current_artwork_id: int, 
        user_id: int, 
        viewer_id: Optional[int] = None
    ) -> tuple[Optional[int], Optional[int]]:
        """현재 작품의 이전/다음 작품 ID를 반환합니다"""
        query = db.query(Artwork).filter(Artwork.user_id == user_id)
        
        # 권한 체크
        if viewer_id != user_id:
            query = query.filter(Artwork.privacy == ArtworkPrivacy.PUBLIC)
        
        # 생성일 기준으로 정렬
        artworks = query.order_by(desc(Artwork.created_at)).all()
        
        current_index = None
        for i, artwork in enumerate(artworks):
            if artwork.id == current_artwork_id:
                current_index = i
                break
        
        if current_index is None:
            return None, None
        
        # 이전 작품 (더 최근)
        prev_artwork_id = artworks[current_index - 1].id if current_index > 0 else None
        
        # 다음 작품 (더 오래됨)
        next_artwork_id = artworks[current_index + 1].id if current_index < len(artworks) - 1 else None
        
        return prev_artwork_id, next_artwork_id
    
    @staticmethod
    def _update_user_artwork_count(db: Session, user_id: int):
        """사용자의 총 작품 수를 업데이트합니다"""
        count = db.query(Artwork).filter(Artwork.user_id == user_id).count()
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.total_artworks = count
            db.commit()