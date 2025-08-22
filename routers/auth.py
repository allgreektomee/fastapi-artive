# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from passlib.context import CryptContext  # 이 줄 추가!
from datetime import datetime, timedelta

# models import
from models.database import get_db
from models.user import User
from services.auth_service import AuthService
from schemas.user import UserCreate, UserLogin, UserResponse, SlugCheckRequest


# 설정값들 (AuthService에서 가져오거나 환경변수에서)
SECRET_KEY = "your-secret-key-here"  # 실제로는 환경변수에서 가져와야 함
ALGORITHM = "HS256"

# 라우터 생성
router = APIRouter()

# JWT Bearer 토큰 스키마 (토큰 선택적)
oauth2_scheme = HTTPBearer(auto_error=False)

# 기존 방식 (토큰 필수)
security = HTTPBearer()



pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_current_user_required(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db)
) -> User:
    """현재 로그인한 사용자를 반환하는 의존성 함수 (토큰 필수)"""
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

def get_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme)
) -> Optional[User]:
    """현재 로그인한 사용자 조회 (토큰 선택적)"""
    print(f"credentials: {credentials}")  # 디버깅용
    
    if not credentials:
        print("No credentials provided")  # 디버깅용
        return None
    
    try:
        # AuthService 사용
        payload = AuthService.verify_token(credentials.credentials)
        print(f"payload: {payload}")  # 디버깅용
        
        if payload is None:
            print("Token verification failed")  # 디버깅용
            return None
        
        email: str = payload.get("sub")
        print(f"email from token: {email}")  # 디버깅용
        
        if email is None:
            return None
        
        user = AuthService.get_user_by_email(db, email=email)
        print(f"user found: {user.email if user else 'None'}")  # 디버깅용
        return user
    except Exception as e:
        print(f"Exception in get_current_user: {e}")  # 디버깅용
        return None
        

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """
    회원가입 API
    """
    try:
        # 사용자 생성
        user = AuthService.create_user(db, user_create)
        
        # 이메일 인증 토큰 생성
        verification_token = AuthService.create_verification_token(db, user.email)
        
        # 이메일 발송 추가
        from services.email_service import EmailService
        email_sent = await EmailService.send_verification_email(
            email=user.email,
            token=verification_token,
            name=user.name
        )
        
        if not email_sent:
            print(f"⚠️ 이메일 발송 실패 - 터미널 링크 사용")
            print(f"📧 인증 링크: http://localhost:8000/api/auth/verify-email?token={verification_token}")
        
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
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
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
    
# 더 간단한 버전 (통계 없이)
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_required)
):
    """
    현재 로그인한 사용자 정보 조회 (간단 버전)
    - JWT 토큰 필요
    - 기본 사용자 정보만 반환
    """
    return current_user

# 비밀번호 변경

@router.put("/password")
async def change_password(
    data: dict,
    current_user: User = Depends(get_current_user_required),  # 이미 있는 함수 사용
    db: Session = Depends(get_db)
):
    """비밀번호 변경"""
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="필수 정보가 누락되었습니다"
        )
    
    # 현재 비밀번호 확인 (AuthService 사용)
    if not AuthService.verify_password(current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 일치하지 않습니다"
        )
    
    # 비밀번호 유효성 검사
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 8자 이상이어야 합니다"
        )
    
    # 새 비밀번호 해시화 및 저장
    current_user.password = AuthService.hash_password(new_password)
    db.commit()
    
    return {"message": "비밀번호가 변경되었습니다"}


# 회원 탈퇴

@router.delete("/account")
async def delete_account(
    data: dict,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """회원 탈퇴"""
    password = data.get("password")
    
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호를 입력해주세요"
        )
    
    # 비밀번호 확인
    if not AuthService.verify_password(password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 일치하지 않습니다"
        )
    
    # 관련 데이터 먼저 삭제 (순서 중요!)
    try:
        # 1. 개별 S3 파일들 정리 (DB 삭제 전에)
        try:
            from routers.upload import delete_s3_file
            from models.artwork import Artwork, ArtworkHistory
            from models.artist_info import Exhibition, Award
            
            # 전시회 이미지들 삭제
            exhibitions = db.query(Exhibition).filter(Exhibition.user_id == current_user.id).all()
            for exhibition in exhibitions:
                if exhibition.image_url:
                    try:
                        delete_s3_file(exhibition.image_url)
                    except Exception as e:
                        print(f"전시회 이미지 삭제 실패: {e}")
                if exhibition.video_url and current_user.slug in exhibition.video_url:
                    try:
                        delete_s3_file(exhibition.video_url)
                    except Exception as e:
                        print(f"전시회 영상 삭제 실패: {e}")
            
            # 수상 이미지들 삭제
            awards = db.query(Award).filter(Award.user_id == current_user.id).all()
            for award in awards:
                if award.image_url:
                    try:
                        delete_s3_file(award.image_url)
                    except Exception as e:
                        print(f"수상 이미지 삭제 실패: {e}")
                if award.video_url and current_user.slug in award.video_url:
                    try:
                        delete_s3_file(award.video_url)
                    except Exception as e:
                        print(f"수상 영상 삭제 실패: {e}")
            
            # 작품 이미지들 삭제
            artworks = db.query(Artwork).filter(Artwork.user_id == current_user.id).all()
            for artwork in artworks:
                if artwork.thumbnail_url:
                    try:
                        delete_s3_file(artwork.thumbnail_url)
                    except Exception as e:
                        print(f"작품 썸네일 삭제 실패: {e}")
                if artwork.work_in_progress_url:
                    try:
                        delete_s3_file(artwork.work_in_progress_url)
                    except Exception as e:
                        print(f"작품 WIP 이미지 삭제 실패: {e}")
                
                # 작품 히스토리 이미지들 삭제
                histories = db.query(ArtworkHistory).filter(ArtworkHistory.artwork_id == artwork.id).all()
                for history in histories:
                    if history.media_url:
                        try:
                            delete_s3_file(history.media_url)
                        except Exception as e:
                            print(f"히스토리 미디어 삭제 실패: {e}")
                    if history.thumbnail_url:
                        try:
                            delete_s3_file(history.thumbnail_url)
                        except Exception as e:
                            print(f"히스토리 썸네일 삭제 실패: {e}")
                    
                    # 히스토리 추가 이미지들
                    for img in history.images:
                        if img.image_url:
                            try:
                                delete_s3_file(img.image_url)
                            except Exception as e:
                                print(f"히스토리 이미지 삭제 실패: {e}")
            
        except Exception as e:
            print(f"개별 S3 파일 정리 중 오류 (계속 진행): {e}")
        
        # 2. S3 폴더 전체 정리 (추가 보험)
        try:
            from routers.upload import cleanup_user_s3_files
            s3_cleanup_result = cleanup_user_s3_files(current_user.slug)
            print(f"S3 폴더 정리 결과: {s3_cleanup_result}")
        except Exception as e:
            print(f"S3 폴더 정리 중 오류 (계속 진행): {e}")
        
        # 3. 데이터베이스 정리
        from models.artwork import Artwork, ArtworkHistory, ArtworkHistoryImage
        from models.artist_info import ArtistQA, Exhibition, Award, ArtistVideo, ArtistStatement
        
        # 작품 관련 데이터 삭제
        artwork_ids = db.query(Artwork.id).filter(Artwork.user_id == current_user.id).subquery()
        history_ids = db.query(ArtworkHistory.id).filter(
            ArtworkHistory.artwork_id.in_(artwork_ids)
        ).subquery()
        
        # 히스토리 이미지 삭제
        db.query(ArtworkHistoryImage).filter(
            ArtworkHistoryImage.history_id.in_(history_ids)
        ).delete(synchronize_session=False)
        
        # 작품 히스토리 삭제
        db.query(ArtworkHistory).filter(
            ArtworkHistory.artwork_id.in_(artwork_ids)
        ).delete(synchronize_session=False)
        
        # 작품 삭제
        db.query(Artwork).filter(Artwork.user_id == current_user.id).delete(synchronize_session=False)
        
        # 아티스트 정보 삭제
        db.query(ArtistQA).filter(ArtistQA.user_id == current_user.id).delete(synchronize_session=False)
        db.query(Exhibition).filter(Exhibition.user_id == current_user.id).delete(synchronize_session=False)
        db.query(Award).filter(Award.user_id == current_user.id).delete(synchronize_session=False)
        db.query(ArtistVideo).filter(ArtistVideo.user_id == current_user.id).delete(synchronize_session=False)
        db.query(ArtistStatement).filter(ArtistStatement.user_id == current_user.id).delete(synchronize_session=False)
        
        # 블로그 포스트 삭제
        try:
            from models.blog import BlogPost
            db.query(BlogPost).filter(BlogPost.user_id == current_user.id).delete(synchronize_session=False)
        except ImportError:
            pass
        
        # 이메일 인증 토큰 삭제
        try:
            from models.email_verification import EmailVerificationToken
            db.query(EmailVerificationToken).filter(
                EmailVerificationToken.email == current_user.email
            ).delete(synchronize_session=False)
        except ImportError:
            pass
        
        # 사용자 삭제
        db.delete(current_user)
        
        # 모든 변경사항 커밋
        db.commit()
        
        return {"message": "회원 탈퇴가 완료되었습니다"}
        
    except Exception as e:
        db.rollback()
        print(f"회원 탈퇴 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원 탈퇴 처리 중 오류가 발생했습니다: {str(e)}"
        )