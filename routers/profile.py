# routers/profile.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime 

from models.database import get_db
from models.user import User
from models.artist_info import ArtistStatement, ArtistVideo, ArtistQA, Exhibition, Award
from routers.auth import get_current_user
from schemas.profile import (
    ProfileResponse, BasicInfoUpdate, ArtistStatementUpdate, 
    ArtistVideoCreate, ArtistQACreate, ExhibitionCreate, AwardCreate
)


from sqlalchemy.sql import func  

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

# routers/profile.py - Q&A 엔드포인트 수정
@router.put("/profile/qa")
async def update_qa_list(
    qa_list: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Q&A 목록 전체 업데이트"""
    try:
        # 기존 Q&A 삭제
        db.query(ArtistQA).filter(ArtistQA.user_id == current_user.id).delete()
        
        # 새 Q&A 추가
        for index, qa_data in enumerate(qa_list):
            # 프론트엔드에서 question/answer로 보내는 경우 처리
            question = qa_data.get("question") or qa_data.get("question_ko", "")
            answer = qa_data.get("answer") or qa_data.get("answer_ko", "")
            
            if question and answer:  # 유효성 검사
                qa = ArtistQA(
                    user_id=current_user.id,
                    question_ko=question,
                    question_en=qa_data.get("question_en", ""),
                    answer_ko=answer,
                    answer_en=qa_data.get("answer_en", ""),
                    order_index=qa_data.get("order_index", index),
                    is_active=True
                )
                db.add(qa)
        
        db.commit()
        
        # 저장된 Q&A 목록 반환
        saved_qa = db.query(ArtistQA).filter(
            ArtistQA.user_id == current_user.id,
            ArtistQA.is_active == True
        ).order_by(ArtistQA.order_index).all()
        
        return {"message": "Q&A가 업데이트되었습니다", "qa_list": saved_qa}
        
    except Exception as e:
        db.rollback()
        print(f"Q&A 업데이트 에러: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Q&A 업데이트 실패: {str(e)}"
        )

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

# 전시회 삭제시 S3 정리
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
    
    try:
        # S3 이미지/영상 삭제
        from routers.upload import delete_s3_file
        
        files_to_delete = []
        if exhibition.image_url:
            files_to_delete.append(exhibition.image_url)
        if exhibition.video_url and current_user.slug in exhibition.video_url:
            # 유튜브 링크가 아닌 S3 업로드 영상인 경우만 삭제
            files_to_delete.append(exhibition.video_url)
        
        # S3 파일 삭제 (실패해도 계속 진행)
        for file_url in files_to_delete:
            try:
                delete_s3_file(file_url)
                print(f"전시회 파일 삭제 성공: {file_url}")
            except Exception as e:
                print(f"전시회 파일 삭제 실패 (계속 진행): {file_url} - {e}")
        
        # 데이터베이스에서 삭제 (soft delete)
        exhibition.is_active = False
        db.commit()
        
        return {"message": "전시회가 삭제되었습니다"}
        
    except Exception as e:
        db.rollback()
        print(f"전시회 삭제 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전시회 삭제 중 오류가 발생했습니다"
        )

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


@router.get("/profile/main")
async def get_main_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """텍스트 위주 기본 프로필 조회"""
    
    # Q&A 조회 - 필드명 변환
    qa_list_raw = db.query(ArtistQA).filter(
        ArtistQA.user_id == current_user.id,
        ArtistQA.is_active == True
    ).order_by(ArtistQA.order_index).all()
    
    # 프론트엔드 형식으로 변환
    qa_list = []
    for qa in qa_list_raw:
        qa_list.append({
            "id": qa.id,
            "question": qa.question_ko,  # question_ko -> question
            "answer": qa.answer_ko,      # answer_ko -> answer
            "order_index": qa.order_index
        })
    
    return {
        "basic": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "slug": current_user.slug,
            "bio": current_user.bio,
            "gallery_title": current_user.gallery_title,
            "gallery_description": current_user.gallery_description,
            "instagram_username": current_user.instagram_username,
            "youtube_channel_id": current_user.youtube_channel_id,
            
            # About 섹션
            "about_text": current_user.about_text,
            "about_image": current_user.about_image,
            "about_video": current_user.about_video,
            
            # Studio 섹션
            "studio_description": current_user.studio_description,
            "studio_image": current_user.studio_image,
            "process_video": current_user.process_video,
        },
        "qa_list": qa_list  # 변환된 Q&A 리스트
    }

@router.get("/profile/exhibitions")
async def get_exhibitions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """전시회 목록 조회"""
    exhibitions = db.query(Exhibition).filter(
        Exhibition.user_id == current_user.id,
        Exhibition.is_active == True
    ).order_by(Exhibition.year.desc(), Exhibition.order_index).all()
    
    return exhibitions

@router.get("/profile/awards")
async def get_awards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """수상/공모전 목록 조회"""
    awards = db.query(Award).filter(
        Award.user_id == current_user.id,
        Award.is_active == True
    ).order_by(Award.year.desc(), Award.order_index).all()
    
    return awards

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
    update_fields = {
        "name": data.name,
        "slug": data.slug,
        "bio": data.bio,
        "gallery_title": data.gallery_title,
        "gallery_description": data.gallery_description,
        "instagram_username": data.instagram_username,
        "youtube_channel_id": data.youtube_channel_id,
    }
    
    # None이 아닌 값만 업데이트
    for field, value in update_fields.items():
        if value is not None and hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "기본 정보가 업데이트되었습니다", "user": current_user}


@router.put("/profile/about")
async def update_about_section(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """About 섹션 업데이트"""
    try:
        if "about_text" in data:
            current_user.about_text = data["about_text"]
        if "about_image" in data:
            current_user.about_image = data["about_image"]
        if "about_video" in data:
            current_user.about_video = data["about_video"]
            
        current_user.updated_at = func.now()
        
        db.commit()
        db.refresh(current_user)
        
        return {"message": "소개 정보가 업데이트되었습니다"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
        
@router.put("/profile/studio")
async def update_studio_section(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Studio Process 섹션 업데이트"""
    try:
        if "studio_description" in data:
            current_user.studio_description = data["studio_description"]
        if "studio_image" in data:
            current_user.studio_image = data["studio_image"]
        if "process_video" in data:
            current_user.process_video = data["process_video"]
            
        current_user.updated_at = func.now()
        
        db.commit()
        db.refresh(current_user)
        
        return {"message": "작업공간 정보가 업데이트되었습니다"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
        
# ============ 전시회 CRUD ============
@router.get("/profile/exhibitions")
async def get_exhibitions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """전시회 목록 조회"""
    exhibitions = db.query(Exhibition).filter(
        Exhibition.user_id == current_user.id,
        Exhibition.is_active == True
    ).order_by(Exhibition.year.desc(), Exhibition.order_index).all()
    
    return exhibitions

@router.post("/profile/exhibitions")
async def add_exhibition(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """전시회 추가"""
    max_order = db.query(Exhibition).filter(
        Exhibition.user_id == current_user.id
    ).count()
    
    exhibition = Exhibition(
        user_id=current_user.id,
        title_ko=data.get("title_ko", ""),
        title_en=data.get("title_en", ""),
        venue_ko=data.get("venue_ko", ""),
        venue_en=data.get("venue_en", ""),
        year=data.get("year", str(datetime.now().year)),
        exhibition_type=data.get("exhibition_type", "group"),
        description_ko=data.get("description_ko", ""),
        description_en=data.get("description_en", ""),
        is_featured=data.get("is_featured", False),
        order_index=max_order,
        is_active=True
    )
    
    db.add(exhibition)
    db.commit()
    db.refresh(exhibition)
    
    return {"message": "전시회가 추가되었습니다", "exhibition": exhibition}
# 전시회 수정시 이전 이미지 정리 (선택사항)
@router.put("/profile/exhibitions/{exhibition_id}")
async def update_exhibition(
    exhibition_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """전시회 수정"""
    exhibition = db.query(Exhibition).filter(
        Exhibition.id == exhibition_id,
        Exhibition.user_id == current_user.id
    ).first()
    
    if not exhibition:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="전시회를 찾을 수 없습니다"
        )
    
    try:
        # 이미지/영상이 변경되는 경우 이전 파일 삭제
        from routers.upload import delete_s3_file
        
        # 새로운 이미지로 교체하는 경우 이전 이미지 삭제
        if "image_url" in data and data["image_url"] != exhibition.image_url:
            if exhibition.image_url:
                try:
                    delete_s3_file(exhibition.image_url)
                    print(f"이전 전시회 이미지 삭제: {exhibition.image_url}")
                except Exception as e:
                    print(f"이전 전시회 이미지 삭제 실패: {e}")
        
        # 새로운 영상으로 교체하는 경우 이전 영상 삭제
        if "video_url" in data and data["video_url"] != exhibition.video_url:
            if exhibition.video_url and current_user.slug in exhibition.video_url:
                try:
                    delete_s3_file(exhibition.video_url)
                    print(f"이전 전시회 영상 삭제: {exhibition.video_url}")
                except Exception as e:
                    print(f"이전 전시회 영상 삭제 실패: {e}")
        
        # 데이터 업데이트
        for field, value in data.items():
            if hasattr(exhibition, field):
                setattr(exhibition, field, value)
        
        db.commit()
        db.refresh(exhibition)
        
        return {"message": "전시회가 수정되었습니다", "exhibition": exhibition}
        
    except Exception as e:
        db.rollback()
        print(f"전시회 수정 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전시회 수정 중 오류가 발생했습니다"
        )

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
    
    try:
        # S3 이미지/영상 삭제
        from routers.upload import delete_s3_file
        
        files_to_delete = []
        if exhibition.image_url:
            files_to_delete.append(exhibition.image_url)
        if exhibition.video_url and current_user.slug in exhibition.video_url:
            # 유튜브 링크가 아닌 S3 업로드 영상인 경우만 삭제
            files_to_delete.append(exhibition.video_url)
        
        # S3 파일 삭제 (실패해도 계속 진행)
        for file_url in files_to_delete:
            try:
                delete_s3_file(file_url)
                print(f"전시회 파일 삭제 성공: {file_url}")
            except Exception as e:
                print(f"전시회 파일 삭제 실패 (계속 진행): {file_url} - {e}")
        
        # 데이터베이스에서 삭제 (soft delete)
        exhibition.is_active = False
        db.commit()
        
        return {"message": "전시회가 삭제되었습니다"}
        
    except Exception as e:
        db.rollback()
        print(f"전시회 삭제 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전시회 삭제 중 오류가 발생했습니다"
        )

# ============ 수상 CRUD ============
@router.get("/profile/awards")
async def get_awards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """수상/공모전 목록 조회"""
    awards = db.query(Award).filter(
        Award.user_id == current_user.id,
        Award.is_active == True
    ).order_by(Award.year.desc(), Award.order_index).all()
    
    return awards

@router.post("/profile/awards")
async def add_award(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """수상 추가"""
    max_order = db.query(Award).filter(
        Award.user_id == current_user.id
    ).count()
    
    award = Award(
        user_id=current_user.id,
        title_ko=data.get("title_ko", ""),
        title_en=data.get("title_en", ""),
        organization_ko=data.get("organization_ko", ""),
        organization_en=data.get("organization_en", ""),
        year=data.get("year", str(datetime.now().year)),
        award_type=data.get("award_type", "award"),
        description_ko=data.get("description_ko", ""),
        description_en=data.get("description_en", ""),
        is_featured=data.get("is_featured", False),
        order_index=max_order,
        is_active=True
    )
    
    db.add(award)
    db.commit()
    db.refresh(award)
    
    return {"message": "수상이 추가되었습니다", "award": award}

# 수상 수정시 이전 이미지 정리 (선택사항)
@router.put("/profile/awards/{award_id}")
async def update_award(
    award_id: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """수상 수정"""
    award = db.query(Award).filter(
        Award.id == award_id,
        Award.user_id == current_user.id
    ).first()
    
    if not award:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="수상을 찾을 수 없습니다"
        )
    
    try:
        # 이미지/영상이 변경되는 경우 이전 파일 삭제
        from routers.upload import delete_s3_file
        
        # 새로운 이미지로 교체하는 경우 이전 이미지 삭제
        if "image_url" in data and data["image_url"] != award.image_url:
            if award.image_url:
                try:
                    delete_s3_file(award.image_url)
                    print(f"이전 수상 이미지 삭제: {award.image_url}")
                except Exception as e:
                    print(f"이전 수상 이미지 삭제 실패: {e}")
        
        # 새로운 영상으로 교체하는 경우 이전 영상 삭제
        if "video_url" in data and data["video_url"] != award.video_url:
            if award.video_url and current_user.slug in award.video_url:
                try:
                    delete_s3_file(award.video_url)
                    print(f"이전 수상 영상 삭제: {award.video_url}")
                except Exception as e:
                    print(f"이전 수상 영상 삭제 실패: {e}")
        
        # 데이터 업데이트
        for field, value in data.items():
            if hasattr(award, field):
                setattr(award, field, value)
        
        db.commit()
        db.refresh(award)
        
        return {"message": "수상이 수정되었습니다", "award": award}
        
    except Exception as e:
        db.rollback()
        print(f"수상 수정 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수상 수정 중 오류가 발생했습니다"
        )
        
# 수상 삭제시 S3 정리
@router.delete("/profile/awards/{award_id}")
async def delete_award(
    award_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """수상 삭제"""
    award = db.query(Award).filter(
        Award.id == award_id,
        Award.user_id == current_user.id
    ).first()
    
    if not award:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="수상을 찾을 수 없습니다"
        )
    
    try:
        # S3 이미지/영상 삭제
        from routers.upload import delete_s3_file
        
        files_to_delete = []
        if award.image_url:
            files_to_delete.append(award.image_url)
        if award.video_url and current_user.slug in award.video_url:
            # 유튜브 링크가 아닌 S3 업로드 영상인 경우만 삭제
            files_to_delete.append(award.video_url)
        
        # S3 파일 삭제 (실패해도 계속 진행)
        for file_url in files_to_delete:
            try:
                delete_s3_file(file_url)
                print(f"수상 파일 삭제 성공: {file_url}")
            except Exception as e:
                print(f"수상 파일 삭제 실패 (계속 진행): {file_url} - {e}")
        
        # 데이터베이스에서 삭제 (soft delete)
        award.is_active = False
        db.commit()
        
        return {"message": "수상이 삭제되었습니다"}
        
    except Exception as e:
        db.rollback()
        print(f"수상 삭제 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="수상 삭제 중 오류가 발생했습니다"
        )