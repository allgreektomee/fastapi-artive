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
from routers.auth import get_current_user_required
from models.user import User

import re
from urllib.parse import urlparse

from PIL import Image, ImageOps
import io

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
    print("S3 클라이언트 초기화 성공")
except Exception as e:
    print(f"S3 클라이언트 초기화 실패: {e}")

def resize_image(file_content: bytes, max_width: int, quality: int = 85) -> bytes:
    """이미지 리사이징 함수"""
    # 이미지 열기
    img = Image.open(io.BytesIO(file_content))
    
    # EXIF 회전 처리
    try:
        img = ImageOps.exif_transpose(img)
    except:
        pass
    
    # RGB 변환 (PNG 투명도 제거)
    if img.mode in ('RGBA', 'LA', 'P'):
        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = rgb_img
    
    # 비율 유지하며 리사이징
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
    
    # 바이트로 변환
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=quality, optimize=True)
    return output.getvalue()

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
    current_user: User = Depends(get_current_user_required),
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
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """
    작품 이미지 전용 업로드 (리사이징 적용)
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
        # 파일 내용 읽기
        file_content = await file.read()
        
        # 타임스탬프와 고유 ID 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        base_name = f"{timestamp}_{unique_id}"
        
        # 1. 디스플레이용 이미지 (1920px)
        display_content = resize_image(file_content, 1920, quality=90)
        display_key = f"artworks/{current_user.slug}/display/{base_name}.jpg"
        
        # 2. 썸네일 이미지 (400px)
        thumb_content = resize_image(file_content, 400, quality=85)
        thumb_key = f"artworks/{current_user.slug}/thumb/{base_name}.jpg"
        
        # S3에 각각 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=display_key,
            Body=display_content,
            ContentType='image/jpeg',
            ContentDisposition=f'inline; filename="{file.filename}"',
            CacheControl='max-age=31536000'
        )
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=thumb_key,
            Body=thumb_content,
            ContentType='image/jpeg',
            ContentDisposition=f'inline; filename="{file.filename}"',
            CacheControl='max-age=31536000'
        )
        
        # URL 생성
        cdn_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        if cdn_domain:
            display_url = f"https://{cdn_domain}/{display_key}"
            thumb_url = f"https://{cdn_domain}/{thumb_key}"
        else:
            display_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{display_key}"
            thumb_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{thumb_key}"
        
        return {
            "file_url": display_url,  # 기존 호환성 유지
            "display_url": display_url,
            "thumbnail_url": thumb_url,
            "file_name": file.filename,
            "file_size": len(display_content),  # 리사이징된 크기
            "content_type": "image/jpeg"
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
    current_user: User = Depends(get_current_user_required),
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
        if not validate_image_file(file):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="지원하지 않는 파일 형식입니다"
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
        s3_key = generate_unique_filename(file.filename, current_user.slug)
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type or 'image/jpeg',
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

@router.post("/upload/temp")
async def upload_temp_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """임시 이미지 업로드 (24시간 후 자동 삭제)"""
    
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
        # temp 폴더에 업로드
        file_extension = os.path.splitext(file.filename)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        s3_key = f"temp/{current_user.slug}/{timestamp}_{unique_id}{file_extension}"
        
        file_content = await file.read()
        
        # S3에 24시간 만료 정책으로 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type or f'image/{file_extension[1:]}',
            ContentDisposition=f'inline; filename="{file.filename}"',
            CacheControl='max-age=86400',  # 24시간
            # 임시 파일 태그 추가
            Tagging='Type=temp&AutoDelete=true'
        )
        
        # URL 생성
        cdn_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        if cdn_domain:
            file_url = f"https://{cdn_domain}/{s3_key}"
        else:
            file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        return {
            "url": file_url,
            "file_url": file_url,
            "is_temp": True,  # 임시 파일임을 표시
            "expires_in": 24,  # 24시간 후 만료
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

# S3 이미지 삭제 함수들
def extract_s3_key_from_url(url: str) -> str:
    """URL에서 S3 키 추출"""
    try:
        # CloudFront URL인 경우
        cdn_domain = os.getenv("CLOUDFRONT_DOMAIN", "")
        if cdn_domain and cdn_domain in url:
            return url.split(f"https://{cdn_domain}/")[1]
        
        # S3 직접 URL인 경우
        bucket_name = os.getenv("S3_BUCKET", "artive-uploads")
        region = os.getenv("AWS_REGION", "ap-southeast-2")
        s3_pattern = f"https://{bucket_name}.s3.{region}.amazonaws.com/"
        
        if s3_pattern in url:
            return url.split(s3_pattern)[1]
        
        # 다른 S3 URL 패턴들
        parsed = urlparse(url)
        if parsed.netloc.endswith('.amazonaws.com'):
            return parsed.path.lstrip('/')
        
        return ""
    except:
        return ""

def delete_s3_file(file_url: str) -> bool:
    """S3에서 파일 삭제"""
    if not file_url:
        return True
    
    try:
        s3_key = extract_s3_key_from_url(file_url)
        if not s3_key:
            print(f"S3 키를 추출할 수 없습니다: {file_url}")
            return False
        
        s3_client.delete_object(
            Bucket=S3_BUCKET,
            Key=s3_key
        )
        print(f"S3 파일 삭제 성공: {s3_key}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code'] if e.response else 'Unknown'
        if error_code == 'NoSuchKey':
            print(f"파일이 이미 존재하지 않습니다: {file_url}")
            return True  # 이미 없는 파일은 성공으로 처리
        else:
            print(f"S3 파일 삭제 실패: {error_code} - {file_url}")
            return False
    except Exception as e:
        print(f"파일 삭제 중 오류: {e}")
        return False

@router.delete("/delete-file")
async def delete_uploaded_file(
    file_url: str,
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """업로드된 파일 삭제 API"""
    
    # 파일 URL이 현재 사용자의 것인지 확인
    if not file_url or current_user.slug not in file_url:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 파일을 삭제할 권한이 없습니다"
        )
    
    success = delete_s3_file(file_url)
    
    if success:
        return {"message": "파일이 삭제되었습니다", "file_url": file_url}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 삭제 중 오류가 발생했습니다"
        )

@router.post("/move-temp-to-permanent")
async def move_temp_to_permanent(
    temp_url: str,
    target_folder: str = "blog",  # blog, artworks, history 등
    current_user: User = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """임시 파일을 정식 폴더로 이동"""
    
    if not temp_url or "temp/" not in temp_url:
        raise HTTPException(
            status_code=400,
            detail="유효하지 않은 임시 파일 URL입니다"
        )
    
    try:
        # 기존 S3 키 추출
        old_key = extract_s3_key_from_url(temp_url)
        
        # 새 키 생성 (temp 제거)
        new_key = old_key.replace("temp/", f"{target_folder}/")
        
        # S3에서 파일 복사
        s3_client.copy_object(
            Bucket=S3_BUCKET,
            CopySource={'Bucket': S3_BUCKET, 'Key': old_key},
            Key=new_key,
            TaggingDirective='REPLACE',  # 임시 태그 제거
            Tagging='Type=permanent'
        )
        
        # 원본 임시 파일 삭제
        s3_client.delete_object(Bucket=S3_BUCKET, Key=old_key)
        
        # 새 URL 반환
        new_url = temp_url.replace("temp/", f"{target_folder}/")
        
        return {
            "old_url": temp_url,
            "new_url": new_url,
            "message": "파일이 정식으로 이동되었습니다"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"파일 이동 중 오류: {str(e)}"
        )

@router.delete("/cleanup-temp-files")
async def cleanup_temp_files():
    """24시간 지난 temp 폴더 파일들 정리"""
    try:
        # temp 폴더의 모든 파일 조회
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix="temp/"
        )
        
        if 'Contents' not in response:
            return {"message": "정리할 임시 파일이 없습니다"}
        
        deleted_count = 0
        now = datetime.now()
        
        for obj in response['Contents']:
            # 24시간 지난 파일들만 삭제
            if (now - obj['LastModified'].replace(tzinfo=None)).total_seconds() > 86400:
                try:
                    s3_client.delete_object(
                        Bucket=S3_BUCKET,
                        Key=obj['Key']
                    )
                    deleted_count += 1
                    print(f"삭제된 임시 파일: {obj['Key']}")
                except Exception as e:
                    print(f"파일 삭제 실패: {obj['Key']} - {e}")
        
        return {
            "message": f"{deleted_count}개의 임시 파일이 정리되었습니다",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"임시 파일 정리 중 오류: {str(e)}"
        )

def cleanup_user_s3_files(user_slug: str) -> dict:
    """특정 사용자의 모든 S3 파일 삭제 (회원 탈퇴용)"""
    try:
        # 사용자 폴더들
        prefixes = [
            f"blog/{user_slug}/",
            f"artworks/{user_slug}/", 
            f"history/{user_slug}/",
            f"temp/{user_slug}/"
        ]
        
        deleted_files = []
        failed_files = []
        
        for prefix in prefixes:
            try:
                # 폴더 내 모든 객체 조회
                response = s3_client.list_objects_v2(
                    Bucket=S3_BUCKET,
                    Prefix=prefix
                )
                
                if 'Contents' in response:
                    # 객체들을 일괄 삭제
                    objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                    
                    if objects_to_delete:
                        delete_response = s3_client.delete_objects(
                            Bucket=S3_BUCKET,
                            Delete={
                                'Objects': objects_to_delete,
                                'Quiet': False
                            }
                        )
                        
                        # 삭제된 파일들 기록
                        if 'Deleted' in delete_response:
                            deleted_files.extend([obj['Key'] for obj in delete_response['Deleted']])
                        
                        # 실패한 파일들 기록
                        if 'Errors' in delete_response:
                            failed_files.extend([obj['Key'] for obj in delete_response['Errors']])
                            
            except ClientError as e:
                print(f"폴더 {prefix} 정리 중 오류: {e}")
                
        return {
            "success": True,
            "deleted_count": len(deleted_files),
            "failed_count": len(failed_files),
            "deleted_files": deleted_files,
            "failed_files": failed_files
        }
        
    except Exception as e:
        print(f"사용자 파일 정리 중 오류: {e}")
        return {
            "success": False,
            "error": str(e)
        }