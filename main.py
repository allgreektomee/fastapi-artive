# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import create_tables

# FastAPI 앱 생성
app = FastAPI(
    title="Artive API",
    description="아티스트 작품 갤러리 플랫폼",
    version="1.0.0"
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js 개발 서버
        "https://artivefor.me",   # 운영 도메인
    ],
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# 애플리케이션 시작시 테이블 생성
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작시 실행되는 함수"""
    create_tables()  # 데이터베이스 테이블 생성
    print("🚀 Artive API 서버가 시작되었습니다!")
    print("📖 API 문서: http://localhost:8000/docs")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Artive API에 오신 것을 환영합니다!", 
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy", "service": "artive-api"}

# 라우터 등록
from routers import auth, artwork
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(artwork.router, prefix="/artworks", tags=["artworks"])