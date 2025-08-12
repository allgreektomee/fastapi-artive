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
    
    # 관계 설정
    user = relationship("User", back_populates="artist_statement")

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
    
    # 관계 설정
    user = relationship("User", back_populates="artist_videos")

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
    
    # 관계 설정
    user = relationship("User", back_populates="artist_qa")

class Exhibition(Base):
    __tablename__ = "exhibitions"
    
    id = Column(Integer, primary_key=True, index=True)  # 고유 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 사용자 ID
    
    # 전시 정보 (다국어)
    title_ko = Column(String(200), nullable=False)  # 한글 전시명
    title_en = Column(String(200), nullable=False)  # 영문 전시명
    
    # 전시 상세 정보
    venue_ko = Column(String(200))  # 한글 장소명
    venue_en = Column(String(200))  # 영문 장소명
    year = Column(String(10), nullable=False)  # 전시 년도
    exhibition_type = Column(String(50), default="group")  # 전시 타입 (solo, group, fair)
    
    # 전시 설명
    description_ko = Column(Text)  # 한글 설명
    description_en = Column(Text)  # 영문 설명
    
    # 표시 설정
    is_featured = Column(Boolean, default=False)  # 주요 전시 여부
    is_active = Column(Boolean, default=True)  # 활성화 여부
    order_index = Column(Integer, default=0)  # 정렬 순서
    
    # 메타 정보
    created_at = Column(DateTime, default=func.now())  # 생성일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 수정일시
    
    # 관계 설정
    user = relationship("User", back_populates="exhibitions")

class Award(Base):
    __tablename__ = "awards"
    
    id = Column(Integer, primary_key=True, index=True)  # 고유 ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 사용자 ID
    
    # 수상 정보 (다국어)
    title_ko = Column(String(200), nullable=False)  # 한글 수상명
    title_en = Column(String(200), nullable=False)  # 영문 수상명
    
    # 수상 상세 정보
    organization_ko = Column(String(200))  # 한글 주최기관
    organization_en = Column(String(200))  # 영문 주최기관
    year = Column(String(10), nullable=False)  # 수상 년도
    award_type = Column(String(50), default="recognition")  # 수상 타입 (grand, excellence, recognition)
    
    # 수상 설명
    description_ko = Column(Text)  # 한글 설명
    description_en = Column(Text)  # 영문 설명
    
    # 표시 설정
    is_featured = Column(Boolean, default=False)  # 주요 수상 여부
    is_active = Column(Boolean, default=True)  # 활성화 여부
    order_index = Column(Integer, default=0)  # 정렬 순서
    
    # 메타 정보
    created_at = Column(DateTime, default=func.now())  # 생성일시
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())  # 수정일시
    
    # 관계 설정
    user = relationship("User", back_populates="awards")