# services/history_service.py
import re
from typing import Optional, List
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
        # 작품 소유자 확인
        artwork = db.query(Artwork).filter(
            Artwork.id == artwork_id,
            Artwork.user_id == user_id
        ).first()
        
        if not artwork:
            raise ValueError("작품을 찾을 수 없거나 권한이 없습니다")
        
        # YouTube URL 처리
        youtube_video_id = None
        if history_data.media_url and 'youtube' in history_data.media_url.lower():
            youtube_video_id = HistoryService.extract_youtube_video_id(history_data.media_url)
        
        # 히스토리 생성
        history = ArtworkHistory(
            artwork_id=artwork_id,
            title=history_data.title,
            content=history_data.content,
            media_url=history_data.media_url,
            media_type=history_data.media_type or "text",
            history_type=history_data.history_type,
            work_date=history_data.work_date,
            youtube_video_id=youtube_video_id,  # YouTube ID 저장
            icon_emoji=history_data.icon_emoji or "🎨"
        )
        
        db.add(history)
        db.commit()
        db.refresh(history)
        
        # 작품의 히스토리 카운트 업데이트
        artwork.history_count = db.query(ArtworkHistory).filter(
            ArtworkHistory.artwork_id == artwork_id
        ).count()
        db.commit()
        
        return history

    
    @staticmethod
    def extract_youtube_video_id(url: str) -> Optional[str]:
        """YouTube URL에서 비디오 ID 추출"""
        if not url:
            return None
            
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*?v=([^&\n?#]+)',
            r'youtu\.be\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None  
    
    @staticmethod
    def get_histories_by_artwork(db: Session, artwork_id: int):
        """작품의 히스토리 목록 조회"""
        return db.query(ArtworkHistory).filter(
            ArtworkHistory.artwork_id == artwork_id
        ).order_by(ArtworkHistory.created_at.asc()).all()
    
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