# routers/upload.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import boto3
from botocore.exceptions import ClientError
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

from models.database import get_db
from routers.auth import get_current_user_required  # get_current_user 대신 get_current_user_required 임포트
from models.user import User

# .env 파일 로드
load_dotenv()

router = APIRouter()

# AWS S3 설정 (환경변수에서 가져오기) - 표준 AWS 환경변수 이름 사용
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
S3_BUCKET = os.getenv("S3_BUCKET", "artive-uploads")

# 디버깅용 출력
print("=== AWS 환경변수 확인 ===")
print(f"AWS_ACCESS_KEY_ID: {AWS_ACCESS_KEY[:10] if AWS_ACCESS_KEY else 'NOT_SET'}...")
print(f"AWS_SECRET_ACCESS_KEY 설정됨: {bool(AWS_SECRET_KEY)}")
print(f"AWS_REGION: {AWS_REGION}")
print(f"S3_BUCKET: {S3_BUCKET}")
print("========================")

# S3 클라이언트 초기화
try:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION
    )
    # S3 연결 테스트 (선택적)
    # s3_client.head_bucket(Bucket=S3_BUCKET)
    print("S3 클라이언트 초기화 성공")
except Exception as e:
    print(f"S3 클라이언트 초기화 실패: {e}")

def generate_unique_filename(original_filename: str, user_slug: str, folder: str = "blog") -> str:
    """고유한 파일명 생성 - user slug 사용"""
    file_extension = os.path.splitext(original_filename)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    return f"{folder}/{user_slug}/{timestamp}_{unique_id}{file_extension}"

def validate_image_file(file: UploadFile) -> bool:
    """이미지 파일 유효성 검사"""
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
    
    file_extension = os.path.splitext(file.filename or "")[1].lower()
    if file_extension not in allowed_extensions:
        return False
    
    if not file.content_type or not file.content_type.startswith('image/'):
        return False
    
    return True

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_required),  # get_current_user_required 사용
    db: Session = Depends(get_db)
):
    """
    파일을 S3에 업로드하고 URL을 반환합니다.
    블로그 에디터와 다른 용도로 모두 사용 가능.
    """
    
    # AWS 자격 증명 확인
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS 자격 증명이 구성되지 않았습니다"
        )
    
    # 파일 유효성 검사
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없습니다"
        )
    
    if not validate_image_file(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 파일 형식입니다. JPG, PNG, GIF, WebP, SVG만 업로드 가능합니다."
        )
    
    # 파일 크기 확인 (10MB 제한)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일 크기는 10MB 이하여야 합니다"
        )
    
    try:
        # 고유한 파일명 생성 - slug 사용
        s3_key = generate_unique_filename(file.filename, current_user.slug)
        
        # 파일 내용 읽기
        file_content = await file.read()
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type,
            ContentDisposition=f'inline; filename="{file.filename}"',
            CacheControl='max-age=31536000'
        )
        
        # CloudFront CDN URL 생성 (있다면)
        cdn_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        if cdn_domain:
            file_url = f"https://{cdn_domain}/{s3_key}"
        else:
            # S3 직접 URL
            file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        return {
            "file_url": file_url,
            "file_name": file.filename,
            "file_size": file_size,
            "content_type": file.content_type
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code'] if e.response else 'Unknown'
        print(f"S3 업로드 오류 - Code: {error_code}, Message: {e}")
        
        if error_code == 'InvalidAccessKeyId':
            detail = "잘못된 AWS Access Key입니다"
        elif error_code == 'SignatureDoesNotMatch':
            detail = "잘못된 AWS Secret Key입니다"
        elif error_code == 'NoSuchBucket':
            detail = f"S3 버킷 '{S3_BUCKET}'을 찾을 수 없습니다"
        elif error_code == 'AccessDenied':
            detail = "S3 버킷에 대한 접근 권한이 없습니다"
        else:
            detail = f"파일 업로드 중 오류가 발생했습니다: {error_code}"
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
    except Exception as e:
        print(f"업로드 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/upload/artwork")
async def upload_artwork_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_required),  # get_current_user_required 사용
    db: Session = Depends(get_db)
):
    """
    작품 이미지 전용 업로드 (더 큰 파일 크기 허용)
    """
    
    # AWS 자격 증명 확인
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS 자격 증명이 구성되지 않았습니다"
        )
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없습니다"
        )
    
    if not validate_image_file(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 파일 형식입니다"
        )
    
    # 작품은 20MB까지 허용
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일 크기는 20MB 이하여야 합니다"
        )
    
    try:
        # artwork 폴더에 저장 - slug 사용
        s3_key = generate_unique_filename(file.filename, current_user.slug, "artworks")
        
        file_content = await file.read()
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type,
            ContentDisposition=f'inline; filename="{file.filename}"',
            CacheControl='max-age=31536000'
        )
        
        cdn_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        if cdn_domain:
            file_url = f"https://{cdn_domain}/{s3_key}"
        else:
            file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        return {
            "file_url": file_url,
            "file_name": file.filename,
            "file_size": file_size,
            "content_type": file.content_type
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code'] if e.response else 'Unknown'
        print(f"S3 업로드 오류 - Code: {error_code}, Message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 업로드 중 오류가 발생했습니다: {error_code}"
        )
    except Exception as e:
        print(f"업로드 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 업로드 중 오류가 발생했습니다"
        )
        
@router.post("/upload/image")
async def upload_blog_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_required),  # get_current_user_required 사용
    db: Session = Depends(get_db)
):
    """
    블로그 에디터용 이미지 업로드 (간단한 버전)
    """
    
    # AWS 자격 증명 확인
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS 자격 증명이 구성되지 않았습니다"
        )
    
    try:
        # 파일 유효성 검사
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="파일명이 없습니다"
            )
        
        # 이미지 파일인지 확인
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(allowed_extensions)}"
            )
        
        # 파일 크기 확인 (10MB 제한)
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="파일 크기는 10MB 이하여야 합니다"
            )
        
        # 고유한 파일명 생성 - slug 사용
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        s3_key = f"blog/{current_user.slug}/{timestamp}_{unique_id}{file_extension}"
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type or f'image/{file_extension[1:]}',
            ContentDisposition=f'inline; filename="{file.filename}"',
            CacheControl='max-age=31536000'
        )
        
        # URL 생성
        cdn_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        if cdn_domain:
            file_url = f"https://{cdn_domain}/{s3_key}"
        else:
            file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        # 프론트엔드가 기대하는 형식으로 반환
        return {
            "url": file_url,  # 프론트엔드에서 url 필드를 사용하는 경우
            "file_url": file_url,  # 또는 file_url 필드를 사용하는 경우
            "success": True
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code'] if e.response else 'Unknown'
        print(f"S3 업로드 오류 - Code: {error_code}, Message: {e}")
        
        if error_code == 'InvalidAccessKeyId':
            detail = "잘못된 AWS Access Key입니다"
        elif error_code == 'SignatureDoesNotMatch':
            detail = "잘못된 AWS Secret Key입니다"
        else:
            detail = f"S3 업로드 실패: {error_code}"
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
    except Exception as e:
        print(f"업로드 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 처리 중 오류: {str(e)}"
        )

@router.post("/upload/history")
async def upload_history_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    연혁(히스토리) 이미지 업로드
    """
    
    # AWS 자격 증명 확인
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS 자격 증명이 구성되지 않았습니다"
        )
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없습니다"
        )
    
    if not validate_image_file(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 파일 형식입니다"
        )
    
    # 히스토리 이미지는 5MB까지 허용
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일 크기는 5MB 이하여야 합니다"
        )
    
    try:
        # history 폴더에 저장 - slug 사용
        s3_key = generate_unique_filename(file.filename, current_user.slug, "history")
        
        file_content = await file.read()
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type,
            ContentDisposition=f'inline; filename="{file.filename}"',
            CacheControl='max-age=31536000'
        )
        
        cdn_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        if cdn_domain:
            file_url = f"https://{cdn_domain}/{s3_key}"
        else:
            file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        return {
            "url": file_url,
            "file_url": file_url,
            "file_name": file.filename,
            "file_size": file_size,
            "content_type": file.content_type,
            "success": True
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code'] if e.response else 'Unknown'
        print(f"S3 업로드 오류 - Code: {error_code}, Message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 업로드 중 오류가 발생했습니다: {error_code}"
        )
    except Exception as e:
        print(f"업로드 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 업로드 중 오류가 발생했습니다"
        )