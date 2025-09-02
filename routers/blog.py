# routers/blog.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
import json

from models.database import get_db
from models.blog import BlogPost
from models.user import User
from schemas.blog import BlogPostCreate, BlogPostResponse, BlogPostUpdate
from services.auth_service import AuthService
from routers.auth import get_current_user  # auth.py에서 import

router = APIRouter(prefix="/api/blog", tags=["blog"])

@router.get("/posts")
async def get_blog_posts(
    skip: int = 0,
    limit: int = 10,
    page: Optional[int] = 1,
    post_type: Optional[str] = None,
    user: Optional[str] = None,  
    user_id: Optional[int] = None,  
    search: Optional[str] = None,  
    full_content: Optional[bool] = False,  # 추가: 전체 내용 필요 여부
    db: Session = Depends(get_db)
):
    """블로그 포스트 목록 조회"""
    
    # 페이지네이션 계산
    if page:
        skip = (page - 1) * limit
    
    # 쿼리 시작 - user 관계 포함
    query = db.query(BlogPost).options(joinedload(BlogPost.user)).filter(BlogPost.is_published == True)
    
    # 사용자별 필터링
    if user:
        # slug로 사용자 찾기
        user_obj = db.query(User).filter(User.slug == user).first()
        if user_obj:
            query = query.filter(BlogPost.user_id == user_obj.id)
        else:
            # 사용자가 없으면 빈 결과 반환
            return {
                "posts": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0,
                "has_next": False,
                "has_prev": False
            }
    elif user_id:
        query = query.filter(BlogPost.user_id == user_id)
    
    # 포스트 타입 필터링
    if post_type and post_type != "ALL":
        query = query.filter(BlogPost.post_type == post_type)
    
    # 검색
    if search:
        query = query.filter(
            (BlogPost.title.contains(search)) | 
            (BlogPost.content.contains(search))
        )
    
    # 전체 개수 (페이지네이션용)
    total = query.count()
    
 # 정렬 및 조회
    posts = query.order_by(
        BlogPost.is_pinned.desc(),
        BlogPost.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    if not full_content:
        for post in posts:
            # content를 짧게 자르기 (HTML 태그 제거하고 200자만)
            import re
            plain_text = re.sub('<[^<]+?>', '', post.content)
            if len(plain_text) > 200:
                post.excerpt = plain_text[:200] + "..."
            # content 필드를 비우거나 짧게
            post.content = ""  # 또는 post.content[:500]
            
    # 응답 형식
    return {
        "posts": posts,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "has_next": skip + limit < total,
        "has_prev": page > 1 if page else skip > 0
    }

@router.get("/{slug}/studio")
async def get_studio_post(
    slug: str,
    db: Session = Depends(get_db)
):
    """특정 사용자의 STUDIO 포스트 조회"""
    user = db.query(User).filter(User.slug == slug).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    studio_post = db.query(BlogPost).filter(
        BlogPost.user_id == user.id,
        BlogPost.post_type == "STUDIO",
        BlogPost.is_published == True
    ).first()
    
    if not studio_post:
        return None
    
    return {
        "id": studio_post.id,
        "title": studio_post.title,
        "content": studio_post.content,
        "featured_image": studio_post.featured_image,
        "created_at": studio_post.created_at,
        "updated_at": studio_post.updated_at
    }

@router.post("/posts", response_model=BlogPostResponse)
async def create_blog_post(
    post: BlogPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 블로그 포스트 생성"""
    
    # STUDIO 타입은 1개만 허용
    if post.post_type == "STUDIO":
        existing_studio = db.query(BlogPost).filter(
            BlogPost.user_id == current_user.id,
            BlogPost.post_type == "STUDIO"
        ).first()
        
        if existing_studio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="STUDIO 포스트는 1개만 작성할 수 있습니다. 기존 포스트를 수정해주세요."
            )
    
    # 태그 처리 (리스트를 JSON 문자열로 변환)
    tags_json = None
    if post.tags:
        tags_json = json.dumps(post.tags, ensure_ascii=False)
    
    # 발행 시간 설정
    published_at = None
    if post.is_published:
        if post.scheduled_date:
            published_at = post.scheduled_date
        else:
            published_at = datetime.now()
    
    # 새 포스트 생성
    db_post = BlogPost(
        title=post.title,
        content=post.content,
        excerpt=post.excerpt,
        post_type=post.post_type,
        tags=tags_json,
        featured_image=post.featured_image,
        is_published=post.is_published,
        is_public=post.is_public,
        is_pinned=post.is_pinned,
        published_at=published_at,
        scheduled_date=post.scheduled_date,
        user_id=current_user.id
    )
    
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    return db_post

@router.get("/posts/{post_id}", response_model=BlogPostResponse)
async def get_blog_post(post_id: int, db: Session = Depends(get_db)):
    """특정 블로그 포스트 조회"""
    
    post = db.query(BlogPost).options(joinedload(BlogPost.user)).filter(BlogPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다")
    
    # 조회수 증가
    post.view_count += 1
    db.commit()
    
    return post

@router.put("/posts/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: int,
    post_update: BlogPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """블로그 포스트 수정"""
    
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    # STUDIO 타입 변경 제한
    if post.post_type == "STUDIO" and post_update.post_type and post_update.post_type != "STUDIO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="STUDIO 포스트의 타입은 변경할 수 없습니다"
        )
    
    # 다른 타입을 STUDIO로 변경 시도
    if post.post_type != "STUDIO" and post_update.post_type == "STUDIO":
        existing_studio = db.query(BlogPost).filter(
            BlogPost.user_id == current_user.id,
            BlogPost.post_type == "STUDIO",
            BlogPost.id != post_id
        ).first()
        
        if existing_studio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 STUDIO 포스트가 존재합니다"
            )
    
    # 수정 가능한 필드만 업데이트
    update_data = post_update.dict(exclude_unset=True)
    
    # 태그 처리
    if 'tags' in update_data and update_data['tags'] is not None:
        update_data['tags'] = json.dumps(update_data['tags'], ensure_ascii=False)
    
    for field, value in update_data.items():
        setattr(post, field, value)
    
    db.commit()
    db.refresh(post)
    
    return post

@router.delete("/posts/{post_id}")
async def delete_blog_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """블로그 포스트 삭제"""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다")
    
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="권한이 없습니다")
    
    # STUDIO 포스트는 삭제 불가 (선택사항)
    if post.post_type == "STUDIO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="STUDIO 포스트는 삭제할 수 없습니다. 내용을 수정해주세요."
        )
    
    try:
        # S3 이미지 삭제
        from routers.upload import delete_s3_file
        
        # 대표 이미지 삭제
        if post.featured_image:
            try:
                delete_s3_file(post.featured_image)
            except Exception as e:
                print(f"대표 이미지 삭제 실패: {e}")
        
        # 컨텐츠 내 이미지 추출 및 삭제
        import re
        content_images = re.findall(r'https?://[^"\s]+\.(?:jpg|jpeg|png|gif|webp)', post.content)
        for img_url in content_images:
            if current_user.slug in img_url:  # 사용자의 이미지만 삭제
                try:
                    delete_s3_file(img_url)
                except Exception as e:
                    print(f"컨텐츠 이미지 삭제 실패: {e}")
        
        # 데이터베이스에서 삭제
        db.delete(post)
        db.commit()
        
        return {"message": "포스트가 삭제되었습니다"}
        
    except Exception as e:
        db.rollback()
        print(f"블로그 포스트 삭제 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail="포스트 삭제 중 오류가 발생했습니다"
        )