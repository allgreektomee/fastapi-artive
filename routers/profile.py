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

# ============ 전체 프로필 조회 ============
@router.get("/", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """현재 사용자의 전체 프로필 조회"""
    artist_statement = db.query(ArtistStatement).filter(
        ArtistStatement.user_id == current_user.id
    ).first()
    
    artist_videos = db.query(ArtistVideo).filter(
        ArtistVideo.user_id == current_user.id,
        ArtistVideo.is_active == True
    ).order_by(ArtistVideo.order_index).all()
    
    qa_list = db.query(ArtistQA).filter(
        ArtistQA.user_id == current_user.id,
        ArtistQA.is_active == True
    ).order_by(ArtistQA.order_index).all()
    
    exhibitions = db.query(Exhibition).filter(
        Exhibition.user_id == current_user.id,
        Exhibition.is_active == True
    ).order_by(Exhibition.order_index).all()
    
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

# ============ 메인 프로필 조회 (구체적 경로 먼저!) ============
@router.get("/main")  # 이렇게 하면 /api/profile/main이 됨
async def get_main_profile(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """텍스트 위주 기본 프로필 조회"""
    print("=== /api/profile/main endpoint called ===")
    print(f"current_user type: {type(current_user)}")
    print(f"current_user value: {current_user}")
    
    if not current_user:
        print("current_user is None!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 실패 - 토큰이 유효하지 않거나 사용자를 찾을 수 없습니다"
        )
    
    print(f"User found: {current_user.email}")
    
    # Q&A 조회 - 필드명 변환
    qa_list_raw = db.query(ArtistQA).filter(
        ArtistQA.user_id == current_user.id,
        ArtistQA.is_active == True
    ).order_by(ArtistQA.order_index).all()
    
    qa_list = []
    for qa in qa_list_raw:
        qa_list.append({
            "id": qa.id,
            "question": qa.question_ko,
            "answer": qa.answer_ko,
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
            "about_text": current_user.about_text,
            "about_image": current_user.about_image,
            "about_video": current_user.about_video,
            "studio_description": current_user.studio_description,
            "studio_image": current_user.studio_image,
            "process_video": current_user.process_video,
        },
        "qa_list": qa_list
    }

# ============ 전시회 목록 조회 (구체적 경로) ============
@router.get("/exhibitions")
async def get_exhibitions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """전시회 목록 조회"""
    exhibitions = db.query(Exhibition).filter(
        Exhibition.user_id == current_user.id,
        Exhibition.is_active == True
    ).order_by(Exhibition.start_date.desc().nullslast(), Exhibition.id.desc()).all()
    
    # 날짜 필드를 문자열로 변환
    result = []
    for ex in exhibitions:
        result.append({
            "id": ex.id,
            "title_ko": ex.title_ko,
            "venue_ko": ex.venue_ko,
            "start_date": ex.start_date.isoformat() if ex.start_date else None,
            "end_date": ex.end_date.isoformat() if ex.end_date else None,
            "exhibition_type": ex.exhibition_type,
            "blog_post_url": ex.blog_post_url,
            "is_featured": ex.is_featured
        })
    
    return result

# ============ 수상 목록 조회 (구체적 경로) ============
@router.get("/awards")
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
@router.post("/awards")
async def add_award(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    """수상 추가"""
    try:
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
            award_type=data.get("award_type", ""),
            description_ko=data.get("description_ko", ""),
            description_en=data.get("description_en", ""),
            blog_post_url=data.get("blog_post_url"),
            is_featured=data.get("is_featured", False),
            order_index=max_order,
            is_active=True
        )
        
        db.add(award)
        db.commit()
        db.refresh(award)
        
        award_dict = {
            "id": award.id,
            "title_ko": award.title_ko,
            "organization_ko": award.organization_ko,
            "year": award.year,
            "award_type": award.award_type,
            "blog_post_url": award.blog_post_url,
            "is_featured": award.is_featured
        }
        
        return {"message": "수상이 추가되었습니다", "award": award_dict}
        
    except Exception as e:
        db.rollback()
        print(f"수상 추가 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"수상 추가 실패: {str(e)}"
        )

@router.delete("/awards/{award_id}")
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

# 기존 PUT 엔드포인트는 그대로 유지 (중복 제거)
@router.put("/awards/{award_id}")
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
        update_fields = ["title_ko", "title_en", "organization_ko", "organization_en",
                        "year", "award_type", "description_ko", "description_en",
                        "blog_post_url", "is_featured"]
        
        for field in update_fields:
            if field in data and hasattr(award, field):
                setattr(award, field, data[field])
        
        db.commit()
        db.refresh(award)
        
        award_dict = {
            "id": award.id,
            "title_ko": award.title_ko,
            "organization_ko": award.organization_ko,
            "year": award.year,
            "award_type": award.award_type,
            "blog_post_url": award.blog_post_url,
            "is_featured": award.is_featured
        }
        
        return {"message": "수상이 수정되었습니다", "award": award_dict}
        
    except Exception as e:
        db.rollback()
        print(f"수상 수정 중 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"수상 수정 실패: {str(e)}"
        )
    
  
# ============ 공개 전시 목록 조회 ============
@router.get("/{slug}/exhibitions")
async def get_public_exhibitions(
    slug: str,
    db: Session = Depends(get_db)
):
    """특정 사용자의 공개 전시 목록 조회"""
    user = db.query(User).filter(User.slug == slug).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    exhibitions = db.query(Exhibition).filter(
        Exhibition.user_id == user.id,
        Exhibition.is_active == True
    ).order_by(Exhibition.year.desc()).all()
    
    return exhibitions

# ============ 공개 수상 목록 조회 ============
@router.get("/{slug}/awards")
async def get_public_awards(
    slug: str,
    db: Session = Depends(get_db)
):
    """특정 사용자의 공개 수상 목록 조회"""
    user = db.query(User).filter(User.slug == slug).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    awards = db.query(Award).filter(
        Award.user_id == user.id,
        Award.is_active == True
    ).order_by(Award.year.desc()).all()
    
    return awards
# ============ 공개 프로필 조회 (동적 경로는 마지막에!) ============

@router.get("/{slug}")
async def get_public_profile(
    slug: str,
    db: Session = Depends(get_db)
):
    """슬러그로 특정 사용자의 공개 프로필 조회"""
    user = db.query(User).filter(User.slug == slug).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    return {
        "id": user.id,
        "name": user.name,
        "slug": user.slug,
        "bio": user.bio,
        "gallery_title": user.gallery_title,
        "gallery_description": user.gallery_description,
        "instagram_username": user.instagram_username,
        "youtube_channel_id": user.youtube_channel_id,
        "about_text": user.about_text,
        "about_image": user.about_image,
        "about_video": user.about_video,
        "studio_description": user.studio_description,
        "studio_image": user.studio_image,
        "process_video": user.process_video,
        "artist_statement": user.about_text,
        "artist_interview": user.artist_interview if hasattr(user, 'artist_interview') else "",
        "cv_education": user.cv_education if hasattr(user, 'cv_education') else "",
        "cv_exhibitions": user.cv_exhibitions if hasattr(user, 'cv_exhibitions') else "",
        "cv_awards": user.cv_awards if hasattr(user, 'cv_awards') else "",
    }

# ============ 기본 정보 업데이트 ============
@router.put("/basic")
async def update_basic_info(
    data: BasicInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """기본 정보 업데이트"""
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
    
    update_fields = {
        "name": data.name,
        "slug": data.slug,
        "bio": data.bio,
        "gallery_title": data.gallery_title,
        "gallery_description": data.gallery_description,
        "instagram_username": data.instagram_username,
        "youtube_channel_id": data.youtube_channel_id,
    }
    
    for field, value in update_fields.items():
        if value is not None and hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "기본 정보가 업데이트되었습니다", "user": current_user}

# ============ About 섹션 업데이트 ============
@router.put("/about")
async def update_about_section(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """About 섹션 업데이트"""
    try:
        if "artist_statement" in data:
            current_user.about_text = data["artist_statement"]
        if "about_text" in data:
            current_user.about_text = data["about_text"]
        if "about_image" in data:
            current_user.about_image = data["about_image"]
        if "about_video" in data:
            current_user.about_video = data["about_video"]
        if "artist_interview" in data:
            current_user.artist_interview = data["artist_interview"]
            print(f"artist_interview 데이터 받음: {data['artist_interview'][:100]}...")  # 처음 100자만
            current_user.artist_interview = data["artist_interview"]
            print(f"DB 저장 전 값: {current_user.artist_interview[:100]}...")
            
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

# ============ Studio 섹션 업데이트 ============
@router.put("/studio")
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

# ============ Q&A 업데이트 ============
@router.put("/qa")
async def update_qa_list(
    qa_list: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Q&A 목록 전체 업데이트"""
    try:
        db.query(ArtistQA).filter(ArtistQA.user_id == current_user.id).delete()
        
        for index, qa_data in enumerate(qa_list):
            question = qa_data.get("question") or qa_data.get("question_ko", "")
            answer = qa_data.get("answer") or qa_data.get("answer_ko", "")
            
            if question and answer:
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

# ============ 전시회 CRUD ============
@router.post("/exhibitions")
async def add_exhibition(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """전시회 추가"""
    try:
        max_order = db.query(Exhibition).filter(
            Exhibition.user_id == current_user.id
        ).count()
        
        # 날짜 파싱
        start_date = None
        end_date = None
        year = str(datetime.now().year)  # 기본값 설정
        
        if data.get("start_date"):
            start_date = datetime.strptime(data.get("start_date"), "%Y-%m-%d").date()
            year = str(start_date.year)  # start_date에서 year 추출
        
        if data.get("end_date"):
            end_date = datetime.strptime(data.get("end_date"), "%Y-%m-%d").date()
        
        exhibition = Exhibition(
            user_id=current_user.id,
            title_ko=data.get("title_ko", ""),
            title_en=data.get("title_en", ""),
            venue_ko=data.get("venue_ko", ""),
            venue_en=data.get("venue_en", ""),
            year=year,  # year 필드 추가
            start_date=start_date,
            end_date=end_date,
            exhibition_type=data.get("exhibition_type", "group"),
            blog_post_url=data.get("blog_post_url"),
            is_featured=data.get("is_featured", False),
            order_index=max_order,
            is_active=True
        )
        
        db.add(exhibition)
        db.commit()
        db.refresh(exhibition)
        
        # 응답용 딕셔너리 생성
        exhibition_dict = {
            "id": exhibition.id,
            "title_ko": exhibition.title_ko,
            "venue_ko": exhibition.venue_ko,
            "start_date": exhibition.start_date.isoformat() if exhibition.start_date else None,
            "end_date": exhibition.end_date.isoformat() if exhibition.end_date else None,
            "exhibition_type": exhibition.exhibition_type,
            "blog_post_url": exhibition.blog_post_url,
            "is_featured": exhibition.is_featured
        }
        
        return {"message": "전시회가 추가되었습니다", "exhibition": exhibition_dict}
        
    except Exception as e:
        db.rollback()
        print(f"전시회 추가 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"전시회 추가 실패: {str(e)}"
        )

@router.put("/exhibitions/{exhibition_id}")
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
        # 날짜 필드 처리
        if "start_date" in data:
            exhibition.start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date() if data["start_date"] else None
        if "end_date" in data:
            exhibition.end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date() if data["end_date"] else None
        
        # 나머지 필드 업데이트
        update_fields = ["title_ko", "title_en", "venue_ko", "venue_en", 
                        "exhibition_type", "blog_post_url", "is_featured"]
        
        for field in update_fields:
            if field in data:
                setattr(exhibition, field, data[field])
        
        db.commit()
        db.refresh(exhibition)
        
        # 응답용 딕셔너리 생성
        exhibition_dict = {
            "id": exhibition.id,
            "title_ko": exhibition.title_ko,
            "venue_ko": exhibition.venue_ko,
            "start_date": exhibition.start_date.isoformat() if exhibition.start_date else None,
            "end_date": exhibition.end_date.isoformat() if exhibition.end_date else None,
            "exhibition_type": exhibition.exhibition_type,
            "blog_post_url": exhibition.blog_post_url,
            "is_featured": exhibition.is_featured
        }
        
        return {"message": "전시회가 수정되었습니다", "exhibition": exhibition_dict}
        
    except Exception as e:
        db.rollback()
        print(f"전시회 수정 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"전시회 수정 실패: {str(e)}"
        )

@router.delete("/exhibitions/{exhibition_id}")
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
        from routers.upload import delete_s3_file
        
        files_to_delete = []
        if exhibition.image_url:
            files_to_delete.append(exhibition.image_url)
        if exhibition.video_url and current_user.slug in exhibition.video_url:
            files_to_delete.append(exhibition.video_url)
        
        for file_url in files_to_delete:
            try:
                delete_s3_file(file_url)
                print(f"전시회 파일 삭제 성공: {file_url}")
            except Exception as e:
                print(f"전시회 파일 삭제 실패 (계속 진행): {file_url} - {e}")
        
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

# ============ 헬퍼 함수 ============
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

