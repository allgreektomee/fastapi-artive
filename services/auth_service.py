# services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
import secrets
import uuid

from models.user import User
from models.email_verification import EmailVerificationToken
from schemas.user import UserCreate

# 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
SECRET_KEY = "your-secret-key-here-change-in-production"  # 운영환경에서는 환경변수로 변경
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class AuthService:
    """인증 관련 비즈니스 로직을 담당하는 서비스 클래스"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """비밀번호를 해싱합니다"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """비밀번호를 검증합니다"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """JWT 액세스 토큰을 생성합니다"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """JWT 토큰을 검증하고 페이로드를 반환합니다"""
        try:
            # "Bearer " 제거 (혹시 포함되어 있다면)
            if token.startswith("Bearer "):
                token = token[7:]
            
            print(f"🔍 정리된 토큰: {token[:50]}...")
            print(f"🔑 SECRET_KEY: {SECRET_KEY}")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print(f"✅ 토큰 검증 성공: {payload}")
            return payload
        except JWTError as e:
            print(f"❌ 토큰 검증 실패: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """이메일로 사용자를 조회합니다"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_slug(db: Session, slug: str) -> Optional[User]:
        """슬러그로 사용자를 조회합니다"""
        return db.query(User).filter(User.slug == slug).first()
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> User:
        """새 사용자를 생성합니다"""
        # 이메일 중복 체크
        if AuthService.get_user_by_email(db, user_create.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 이메일입니다"
            )
        
        # 슬러그 중복 체크
        if AuthService.get_user_by_slug(db, user_create.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용중인 슬러그입니다"
            )
        
        # 비밀번호 해싱
        hashed_password = AuthService.hash_password(user_create.password)
        
        # 사용자 생성
        db_user = User(
            email=user_create.email,
            password=hashed_password,
            name=user_create.name,
            slug=user_create.slug,
            bio=user_create.bio,
            gallery_title=user_create.name  # 기본값으로 이름 사용
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """사용자 인증을 수행합니다"""
        user = AuthService.get_user_by_email(db, email)
        if not user:
            return None
        if not AuthService.verify_password(password, user.password):
            return None
        return user
    
    @staticmethod
    def create_verification_token(db: Session, email: str) -> str:
        """이메일 인증 토큰을 생성합니다"""
        # 기존 토큰이 있다면 삭제
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.email == email
        ).delete()
        
        # 새 토큰 생성
        token = secrets.token_urlsafe(32)
        expiry_date = datetime.utcnow() + timedelta(hours=24)  # 24시간 후 만료
        
        verification_token = EmailVerificationToken(
            token=token,
            email=email,
            expiry_date=expiry_date
        )
        
        db.add(verification_token)
        db.commit()
        
        return token
    
    @staticmethod
    def verify_email_token(db: Session, token: str) -> bool:
        """이메일 인증 토큰을 검증합니다"""
        verification_token = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token,
            EmailVerificationToken.is_used == False,
            EmailVerificationToken.expiry_date > datetime.utcnow()
        ).first()
        
        if not verification_token:
            return False
        
        # 사용자의 이메일 인증 상태 업데이트
        user = AuthService.get_user_by_email(db, verification_token.email)
        if user:
            user.is_verified = True
            verification_token.is_used = True
            db.commit()
            return True
        
        return False
    
    @staticmethod
    def generate_unique_slug(db: Session, base_slug: str) -> str:
        """중복되지 않는 슬러그를 생성합니다"""
        original_slug = base_slug.lower().replace(" ", "-")
        slug = original_slug
        counter = 1
        
        while AuthService.get_user_by_slug(db, slug):
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        return slug