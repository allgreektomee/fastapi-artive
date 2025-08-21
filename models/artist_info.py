# models/artist_info.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class ArtistStatement(Base):
    __tablename__ = "artist_statements"
    
    id = Column(Integer, primary_key=True, index=True)  # 고유 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)  # 사용자 ID (1:1 관계)
    
    # 작가 소개문 (다국어)
    statement_ko = Column(Text)  # 한글 작가 소개
    statement_en = Column(Text)  # 영문 작가 소개
    
    # 메타 정보
    created_at = Column(DateTime, default=func.now())  # 생성일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 수정일시
    
    # 관계 설정 - back_populates 제거
    user = relationship("User")

class ArtistVideo(Base):
    __tablename__ = "artist_videos"
    
    id = Column(Integer, primary_key=True, index=True)  # 고유 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 사용자 ID
    
    # 유튜브 영상 정보
    video_url = Column(String(500), nullable=False)  # 유튜브 URL
    video_id = Column(String(50))  # 유튜브 비디오 ID (자동 추출)
    
    # 영상 제목 (다국어)
    title_ko = Column(String(200))  # 한글 제목
    title_en = Column(String(200))  # 영문 제목
    
    # 영상 설명 (다국어)
    description_ko = Column(Text)  # 한글 설명
    description_en = Column(Text)  # 영문 설명
    
    # 영상 메타데이터
    thumbnail_url = Column(String(500))  # 썸네일 URL
    duration = Column(Integer)  # 영상 길이 (초)
    
    # 표시 설정
    is_featured = Column(Boolean, default=False)  # 대표 영상 여부
    is_active = Column(Boolean, default=True)  # 활성화 여부
    order_index = Column(Integer, default=0)  # 정렬 순서
    
    # 메타 정보
    created_at = Column(DateTime, default=func.now())  # 생성일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 수정일시
    
    # 관계 설정 - back_populates 제거
    user = relationship("User")

class ArtistQA(Base):
    __tablename__ = "artist_qa"
    
    id = Column(Integer, primary_key=True, index=True)  # 고유 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 사용자 ID
    
    # 질문 (다국어)
    question_ko = Column(Text, nullable=False)  # 한글 질문
    question_en = Column(Text, nullable=False)  # 영문 질문
    
    # 답변 (다국어)
    answer_ko = Column(Text, nullable=False)  # 한글 답변
    answer_en = Column(Text, nullable=False)  # 영문 답변
    
    # 표시 설정
    is_active = Column(Boolean, default=True)  # 활성화 여부
    order_index = Column(Integer, default=0)  # 정렬 순서
    
    # 메타 정보
    created_at = Column(DateTime, default=func.now())  # 생성일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 수정일시
    
    # 관계 설정 - back_populates 제거
    user = relationship("User")
    
    
class Exhibition(Base):
    __tablename__ = "exhibitions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 기존 필드들
    title_ko = Column(String(200), nullable=False)
    title_en = Column(String(200), nullable=False)
    venue_ko = Column(String(200))
    venue_en = Column(String(200))
    year = Column(String(10), nullable=False)
    exhibition_type = Column(String(50), default="group")
    description_ko = Column(Text)
    description_en = Column(Text)
    
    # 추가 필드
    image_url = Column(String(500))  # 전시 포스터/사진
    video_url = Column(String(500))  # 전시 영상 링크
    
    # 표시 설정
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    
    # 메타 정보
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User")

class Award(Base):
    __tablename__ = "awards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 기존 필드들
    title_ko = Column(String(200), nullable=False)
    title_en = Column(String(200), nullable=False)
    organization_ko = Column(String(200))
    organization_en = Column(String(200))
    year = Column(String(10), nullable=False)
    award_type = Column(String(50), default="recognition")
    description_ko = Column(Text)
    description_en = Column(Text)
    
    # 추가 필드
    image_url = Column(String(500))  # 수상 증서/사진
    video_url = Column(String(500))  # 수상 관련 영상
    
    # 표시 설정
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    order_index = Column(Integer, default=0)
    
    # 메타 정보
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User")