# routers/upload.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import boto3
from botocore.exceptions import ClientError
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

from models.database import get_db
from routers.auth import get_current_user
from models.user import User

router = APIRouter()

# AWS S3 설정 - 환경변수에서 가져오기
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
S3_BUCKET = os.getenv("S3_BUCKET", "artive-uploads")

if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
    raise ValueError("AWS 자격 증명이 설정되지 않았습니다. 환경변수를 확인하세요.")

# S3 클라이언트 초기화
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

def generate_unique_filename(original_filename: str, user_id: int) -> str:
    """고유한 파일명 생성"""
    # 파일 확장자 추출
    file_extension = os.path.splitext(original_filename)[1].lower()
    
    # 현재 시간과 UUID를 조합한 고유 파일명 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    return f"artworks/{user_id}/{timestamp}_{unique_id}{file_extension}"

def validate_image_file(file: UploadFile) -> bool:
    """이미지 파일 유효성 검사"""
    # 허용된 이미지 확장자
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    # 파일 확장자 확인
    file_extension = os.path.splitext(file.filename or "")[1].lower()
    if file_extension not in allowed_extensions:
        return False
    
    # Content-Type 확인
    if not file.content_type or not file.content_type.startswith('image/'):
        return False
    
    return True

@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    이미지를 S3에 업로드하고 URL을 반환합니다
    - 로그인한 사용자만 업로드 가능
    - JPG, PNG, GIF, WebP 형식만 지원
    - 최대 10MB까지 업로드 가능
    """
    
    # 파일 유효성 검사
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없습니다"
        )
    
    if not validate_image_file(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="지원하지 않는 파일 형식입니다. JPG, PNG, GIF, WebP만 업로드 가능합니다."
        )
    
    # 파일 크기 확인 (10MB 제한)
    file.file.seek(0, 2)  # 파일 끝으로 이동
    file_size = file.file.tell()  # 현재 위치(파일 크기) 확인
    file.file.seek(0)  # 파일 시작으로 복원
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일 크기는 10MB 이하여야 합니다"
        )
    
    try:
        # 고유한 파일명 생성
        s3_key = generate_unique_filename(file.filename, current_user.id)
        
        # 파일 내용 읽기
        file_content = await file.read()
        
        # S3에 업로드
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=file.content_type,
            ContentDisposition=f'inline; filename="{file.filename}"',
            # 캐시 설정 (1년)
            CacheControl='max-age=31536000'
        )
        
        # 업로드된 파일의 공개 URL 생성
        file_url = f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"
        
        return {
            "message": "파일 업로드 성공",
            "url": file_url,
            "filename": file.filename,
            "size": file_size,
            "content_type": file.content_type
        }
        
    except ClientError as e:
        print(f"S3 업로드 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 업로드 중 오류가 발생했습니다"
        )
    except Exception as e:
        print(f"업로드 처리 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 처리 중 오류가 발생했습니다"
        )

@router.delete("/upload/image")
async def delete_image(
    image_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    S3에서 이미지를 삭제합니다
    - 로그인한 사용자만 삭제 가능
    - 본인이 업로드한 이미지만 삭제 가능 (URL에 user_id 포함)
    """
    
    try:
        # URL에서 S3 키 추출
        if not image_url.startswith(f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="올바르지 않은 이미지 URL입니다"
            )
        
        s3_key = image_url.replace(f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/", "")
        
        # 사용자 권한 확인 (URL에 user_id가 포함되어 있는지 확인)
        if not s3_key.startswith(f"artworks/{current_user.id}/"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 이미지를 삭제할 권한이 없습니다"
            )
        
        # S3에서 파일 삭제
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        
        return {"message": "이미지가 삭제되었습니다"}
        
    except ClientError as e:
        print(f"S3 삭제 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이미지 삭제 중 오류가 발생했습니다"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"삭제 처리 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이미지 삭제 처리 중 오류가 발생했습니다"
        )