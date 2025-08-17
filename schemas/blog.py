# schemas/blog.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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
    user: Optional[UserBasicInfo] = None  # user 관계 (blog.py와 일치)
    
    class Config:
        from_attributes = True