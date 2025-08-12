# models/email_verification.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)  # 토큰 고유 ID
    token = Column(String(255), unique=True, nullable=False)  # 인증 토큰
    email = Column(String(255), nullable=False)  # 인증할 이메일
    expiry_date = Column(DateTime, nullable=False)  # 토큰 만료일시
    created_at = Column(DateTime, default=func.now())  # 토큰 생성일시
    is_used = Column(Boolean, default=False)  # 사용 여부