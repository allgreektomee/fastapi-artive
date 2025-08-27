# models/blog.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class BlogPost(Base):
    __tablename__ = "blog_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)  # 요약
    post_type = Column(String(50), default="BLOG")  # BLOG, NOTICE, NEWS, EXHIBITION, AWARD
    tags = Column(Text, nullable=True)  # JSON 문자열로 저장
    featured_image = Column(String(500), nullable=True)  # 대표 이미지 URL
    
    # 발행 관련
    is_published = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    is_pinned = Column(Boolean, default=False)
    
    # 통계
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    # 시간
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_date = Column(DateTime(timezone=True), nullable=True)  # 예약 발행
    
    # 외래키
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 관계 설정 (기존 User 모델과 맞춤)
    user = relationship("User", back_populates="blog_posts")