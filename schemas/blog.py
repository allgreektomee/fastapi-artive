# schemas/blog.py
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import json

class BlogPostBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    post_type: str = "BLOG"
    tags: Optional[List[str]] = None
    featured_image: Optional[str] = None
    is_public: bool = True
    is_pinned: bool = False

class BlogPostCreate(BlogPostBase):
    is_published: bool = False
    scheduled_date: Optional[datetime] = None

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    post_type: Optional[str] = None
    tags: Optional[List[str]] = None
    featured_image: Optional[str] = None
    is_published: Optional[bool] = None
    is_public: Optional[bool] = None
    is_pinned: Optional[bool] = None
    scheduled_date: Optional[datetime] = None

class UserBasicInfo(BaseModel):
    id: int
    name: str
    slug: str
    thumbnail_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class BlogPostResponse(BlogPostBase):
    id: int
    user_id: int
    view_count: int
    like_count: int
    is_published: bool
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    scheduled_date: Optional[datetime] = None
    user: Optional[UserBasicInfo] = None
    tags: Optional[List[str]] = None
    
    @validator('tags', pre=True, always=True)
    def parse_tags(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                # ensure_ascii=False로 한글 제대로 처리
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else []
            except:
                return []
        return v
    
    class Config:
        from_attributes = True