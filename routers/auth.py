# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from models.database import get_db
from services.auth_service import AuthService
from schemas.user import UserCreate, UserLogin, UserResponse, SlugCheckRequest  # SlugCheckRequest 추가


# 라우터 생성
router = APIRouter()

# JWT Bearer 토큰 스키마
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """현재 로그인한 사용자를 반환하는 의존성 함수"""
    token = credentials.credentials
    payload = AuthService.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에서 사용자 정보를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = AuthService.get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    회원가입 API
    - 새로운 사용자를 생성합니다
    - 이메일 중복 검사를 수행합니다
    - 비밀번호를 안전하게 해싱합니다
    """
    try:
        # 사용자 생성
        user = AuthService.create_user(db, user_create)
        
        # 이메일 인증 토큰 생성 (실제 이메일 발송은 나중에 구현)
        verification_token = AuthService.create_verification_token(db, user.email)
        
        # TODO: 실제 이메일 발송 로직 추가
        print(f"🔐 이메일 인증 토큰: {verification_token}")
        print(f"📧 인증 링크: http://localhost:8000/auth/verify-email?token={verification_token}")
        
        return user
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/login")
async def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    로그인 API
    """
    # 사용자 인증
    user = AuthService.authenticate_user(db, user_login.email, user_login.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이메일 인증이 필요합니다"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다"
        )
    
    # JWT 토큰 생성
    access_token = AuthService.create_access_token(data={"sub": user.email})
    
    # 마지막 로그인 시간 업데이트
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {  # ✅ UserResponse.from_orm 대신 직접 딕셔너리로
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "slug": user.slug
        }
    }

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    이메일 인증 API
    - 이메일 인증 토큰을 검증합니다
    - 사용자의 이메일 인증 상태를 활성화합니다
    """
    success = AuthService.verify_email_token(db, token)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않거나 만료된 인증 토큰입니다"
        )
    
    return {"message": "이메일 인증이 완료되었습니다"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    현재 사용자 정보 조회 API
    - JWT 토큰으로 현재 로그인한 사용자 정보를 반환합니다
    """
    return current_user

@router.post("/resend-verification")
async def resend_verification(email: str, db: Session = Depends(get_db)):
    """
    이메일 인증 재발송 API
    - 이메일 인증 토큰을 재발송합니다
    """
    user = AuthService.get_user_by_email(db, email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 인증된 이메일입니다"
        )
    
    # 새 인증 토큰 생성
    verification_token = AuthService.create_verification_token(db, email)
    
    # TODO: 실제 이메일 발송 로직 추가
    print(f"🔐 이메일 인증 토큰 재발송: {verification_token}")
    print(f"📧 인증 링크: http://localhost:8000/auth/verify-email?token={verification_token}")
    
    return {"message": "인증 이메일이 재발송되었습니다"}

@router.post("/check-slug")
async def check_slug_availability(request: SlugCheckRequest, db: Session = Depends(get_db)):
    """
    슬러그 사용 가능 여부 확인 API
    - 슬러그가 이미 사용중인지 확인합니다
    """
    existing_user = AuthService.get_user_by_slug(db, request.slug)
    
    return {
        "slug": request.slug,
        "available": existing_user is None,
        "message": "사용 가능한 슬러그입니다" if existing_user is None else "이미 사용중인 슬러그입니다"
    }