# routers/history.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models.user import User
from models.artwork import ArtworkHistory
from schemas.artwork import ArtworkHistoryCreate, ArtworkHistoryResponse
from routers.auth import get_current_user
from services.history_service import HistoryService

router = APIRouter()

@router.post("/{artwork_id}/histories", response_model=ArtworkHistoryResponse)
async def add_history(
    artwork_id: int,
    history_data: ArtworkHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    작품에 새 히스토리 추가
    """
    history = HistoryService.create_history(db, artwork_id, history_data, current_user.id)
    return ArtworkHistoryResponse.from_orm(history)

@router.get("/{artwork_id}/histories", response_model=List[ArtworkHistoryResponse])
async def get_histories(
    artwork_id: int,
    db: Session = Depends(get_db)
):
    """
    작품의 히스토리 목록 조회
    """
    histories = HistoryService.get_histories_by_artwork(db, artwork_id)
    return [ArtworkHistoryResponse.from_orm(history) for history in histories]

@router.delete("/{artwork_id}/histories/{history_id}")
async def delete_history(
    artwork_id: int,
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """히스토리 삭제"""
    history = db.query(ArtworkHistory).filter(
        ArtworkHistory.id == history_id,
        ArtworkHistory.artwork_id == artwork_id
    ).first()
    
    if not history:
        raise HTTPException(
            status_code=404,
            detail="히스토리를 찾을 수 없습니다"
        )
    
    # 권한 확인
    artwork = db.query(Artwork).filter(Artwork.id == artwork_id).first()
    if not artwork or artwork.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="권한이 없습니다"
        )
    
    try:
        # S3 이미지 삭제
        from routers.upload import delete_s3_file
        
        images_to_delete = []
        if history.media_url:
            images_to_delete.append(history.media_url)
        if history.thumbnail_url:
            images_to_delete.append(history.thumbnail_url)
        
        # 히스토리의 추가 이미지들
        for img in history.images:
            if img.image_url:
                images_to_delete.append(img.image_url)
        
        # S3 파일 삭제
        for img_url in images_to_delete:
            try:
                delete_s3_file(img_url)
            except Exception as e:
                print(f"히스토리 이미지 삭제 실패: {e}")
        
        # 데이터베이스에서 삭제
        db.delete(history)
        db.commit()
        
        return {"message": "히스토리가 삭제되었습니다"}
        
    except Exception as e:
        db.rollback()
        print(f"히스토리 삭제 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="히스토리 삭제 중 오류가 발생했습니다"
        )