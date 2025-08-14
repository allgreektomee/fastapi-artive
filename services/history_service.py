# services/history_service.py
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from datetime import datetime

from models.artwork import Artwork, ArtworkHistory
from schemas.artwork import ArtworkHistoryCreate

class HistoryService:
    
    # services/history_service.py
    @staticmethod
    def create_history(db: Session, artwork_id: int, history_data: ArtworkHistoryCreate, user_id: int):
        """히스토리 생성"""
        # 작품 소유자 확인
        artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
        if not artwork:
            raise HTTPException(status_code=404, detail="작품을 찾을 수 없습니다")
        
        if artwork.user_id != user_id:
            raise HTTPException(status_code=403, detail="권한이 없습니다")
        
        # 순서 계산
        max_order = db.query(ArtworkHistory).filter(
            ArtworkHistory.artwork_id == artwork_id
        ).count()
        
        # 유튜브 비디오 ID 추출 (URL에서)
        youtube_video_id = None
        if history_data.media_type == "youtube" and history_data.media_url:
            youtube_video_id = extract_youtube_video_id(history_data.media_url)
        
        history = ArtworkHistory(
            title=history_data.title,
            content=history_data.content,
            media_url=history_data.media_url,
            thumbnail_url=history_data.thumbnail_url,
            media_type=history_data.media_type,
            history_type=history_data.history_type,
            external_url=history_data.external_url,
            youtube_video_id=youtube_video_id,
            work_date=history_data.work_date or datetime.utcnow(),
            order_index=max_order,
            artwork_id=artwork_id
        )
        
        db.add(history)
        db.commit()
        db.refresh(history)
        
        # 다중 이미지 처리
        if history_data.images:
            for img_data in history_data.images:
                history_image = ArtworkHistoryImage(
                    image_url=img_data.image_url,
                    alt_text=img_data.alt_text,
                    caption=img_data.caption,
                    order_index=img_data.order_index,
                    history_id=history.id
                )
                db.add(history_image)
        
        # 작품의 히스토리 개수 업데이트
        artwork.history_count = db.query(ArtworkHistory).filter(
            ArtworkHistory.artwork_id == artwork_id
        ).count()
        
        db.commit()
        db.refresh(history)
        
        return history

    
    def extract_youtube_video_id(url: str) -> str:
        """유튜브 URL에서 비디오 ID 추출"""
        import re
        pattern = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        match = re.search(pattern, url)
        return match.group(1) if match else None    
    
    @staticmethod
    def get_histories_by_artwork(db: Session, artwork_id: int):
        """작품의 히스토리 목록 조회"""
        return db.query(ArtworkHistory).filter(
            ArtworkHistory.artwork_id == artwork_id
        ).order_by(ArtworkHistory.order_index.asc()).all()
    
    @staticmethod
    def delete_history(db: Session, history_id: int, user_id: int):
        """히스토리 삭제"""
        history = db.query(ArtworkHistory).filter(ArtworkHistory.id == history_id).first()
        if not history:
            raise HTTPException(status_code=404, detail="히스토리를 찾을 수 없습니다")
        
        # 작품 소유자 확인
        artwork = db.query(Artwork).filter(Artwork.id == history.artwork_id).first()
        if artwork.user_id != user_id:
            raise HTTPException(status_code=403, detail="권한이 없습니다")
        
        db.delete(history)
        db.commit()
        
        # 작품의 히스토리 개수 업데이트
        artwork.history_count = db.query(ArtworkHistory).filter(
            ArtworkHistory.artwork_id == artwork.id
        ).count()
        db.commit()