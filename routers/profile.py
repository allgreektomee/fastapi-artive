# routers/profile.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from models.database import get_db
from models.user import User
from models.artist_info import ArtistStatement, ArtistVideo, ArtistQA, Exhibition, Award
from routers.auth import get_current_user
from schemas.profile import (
    ProfileResponse, BasicInfoUpdate, ArtistStatementUpdate, 
    ArtistVideoCreate, ArtistQACreate, ExhibitionCreate, AwardCreate
)

router = APIRouter()

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 사용자의 전체 프로필 조회"""
    # 아티스트 소개문 조회
    artist_statement = db.query(ArtistStatement).filter(
        ArtistStatement.user_id == current_user.id
    ).first()
    
    # 아티스트 비디오 조회
    artist_videos = db.query(ArtistVideo).filter(
        ArtistVideo.user_id == current_user.id,
        ArtistVideo.is_active == True
    ).order_by(ArtistVideo.order_index).all()
    
    # Q&A 조회
    qa_list = db.query(ArtistQA).filter(
        ArtistQA.user_id == current_user.id,
        ArtistQA.is_active == True
    ).order_by(ArtistQA.order_index).all()
    
    # 전시회 조회
    exhibitions = db.query(Exhibition).filter(
        Exhibition.user_id == current_user.id,
        Exhibition.is_active == True
    ).order_by(Exhibition.order_index).all()
    
    # 수상 내역 조회
    awards = db.query(Award).filter(
        Award.user_id == current_user.id,
        Award.is_active == True
    ).order_by(Award.order_index).all()
    
    return ProfileResponse(
        basic=current_user,
        artist_statement=artist_statement,
        artist_videos=artist_videos,
        qa_list=qa_list,
        exhibitions=exhibitions,
        awards=awards
    )

@router.put("/profile/basic")
async def update_basic_info(
    data: BasicInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """기본 정보 업데이트"""
    # 슬러그 중복 체크 (다른 사용자가 사용중인지)
    if data.slug and data.slug != current_user.slug:
        existing_user = db.query(User).filter(
            User.slug == data.slug,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용중인 갤러리 주소입니다"
            )
    
    # 업데이트할 필드들
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "기본 정보가 업데이트되었습니다", "user": current_user}

@router.put("/profile/artist-statement")
async def update_artist_statement(
    data: ArtistStatementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """작가 소개문 업데이트"""
    # 기존 소개문 조회
    statement = db.query(ArtistStatement).filter(
        ArtistStatement.user_id == current_user.id
    ).first()
    
    if statement:
        # 기존 소개문 업데이트
        update_data = data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(statement, field):
                setattr(statement, field, value)
    else:
        # 새 소개문 생성
        statement = ArtistStatement(
            user_id=current_user.id,
            **data.dict(exclude_unset=True)
        )
        db.add(statement)
    
    db.commit()
    db.refresh(statement)
    
    return {"message": "작가 소개문이 업데이트되었습니다", "statement": statement}

@router.post("/profile/videos")
async def add_artist_video(
    data: ArtistVideoCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """아티스트 비디오 추가"""
    # 유튜브 비디오 ID 추출
    video_id = extract_youtube_video_id(data.video_url)
    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="올바른 유튜브 URL이 아닙니다"
        )
    
    # 순서 계산
    max_order = db.query(ArtistVideo).filter(
        ArtistVideo.user_id == current_user.id
    ).count()
    
    video = ArtistVideo(
        user_id=current_user.id,
        video_url=data.video_url,
        video_id=video_id,
        title_ko=data.title_ko,
        title_en=data.title_en,
        description_ko=data.description_ko,
        description_en=data.description_en,
        is_featured=data.is_featured,
        order_index=max_order
    )
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    return {"message": "비디오가 추가되었습니다", "video": video}

@router.put("/profile/qa")
async def update_qa_list(
    qa_list: List[ArtistQACreate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Q&A 목록 전체 업데이트"""
    # 기존 Q&A 삭제
    db.query(ArtistQA).filter(ArtistQA.user_id == current_user.id).delete()
    
    # 새 Q&A 추가
    for index, qa_data in enumerate(qa_list):
        qa = ArtistQA(
            user_id=current_user.id,
            question_ko=qa_data.question_ko,
            question_en=qa_data.question_en or qa_data.question_ko,  # 영문이 없으면 한글 사용
            answer_ko=qa_data.answer_ko,
            answer_en=qa_data.answer_en or qa_data.answer_ko,
            order_index=index
        )
        db.add(qa)
    
    db.commit()
    
    return {"message": "Q&A가 업데이트되었습니다"}

@router.post("/profile/exhibitions")
async def add_exhibition(
    data: ExhibitionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """전시회 추가"""
    max_order = db.query(Exhibition).filter(
        Exhibition.user_id == current_user.id
    ).count()
    
    exhibition = Exhibition(
        user_id=current_user.id,
        title_ko=data.title_ko,
        title_en=data.title_en or data.title_ko,
        venue_ko=data.venue_ko,
        venue_en=data.venue_en,
        year=data.year,
        exhibition_type=data.exhibition_type,
        description_ko=data.description_ko,
        description_en=data.description_en,
        is_featured=data.is_featured,
        order_index=max_order
    )
    
    db.add(exhibition)
    db.commit()
    db.refresh(exhibition)
    
    return {"message": "전시회가 추가되었습니다", "exhibition": exhibition}

@router.delete("/profile/exhibitions/{exhibition_id}")
async def delete_exhibition(
    exhibition_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """전시회 삭제"""
    exhibition = db.query(Exhibition).filter(
        Exhibition.id == exhibition_id,
        Exhibition.user_id == current_user.id
    ).first()
    
    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전시회를 찾을 수 없습니다"
        )
    
    db.delete(exhibition)
    db.commit()
    
    return {"message": "전시회가 삭제되었습니다"}

def extract_youtube_video_id(url: str) -> Optional[str]:
    """유튜브 URL에서 비디오 ID 추출"""
    import re
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None