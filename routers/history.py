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
    HistoryService.delete_history(db, history_id, current_user.id)
    return {"message": "히스토리가 삭제되었습니다"}