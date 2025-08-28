# main.py 수정
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# 환경변수 로드
load_dotenv()

# 라우터 임포트
from routers import auth, artwork, history, upload, profile, blog
from models.database import create_tables

app = FastAPI(
    title="Artive API",
    description="아티스트 포트폴리오 플랫폼 API",
    version="1.0.0"
)

# CORS 설정 - 명시적 도메인 지정
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://artivefor.me",
    "https://www.artivefor.me",
    "https://api.artivefor.me"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 와일드카드 대신 명시적 도메인
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 테이블 생성
create_tables()

# 라우터 등록
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(artwork.router, prefix="/api/artworks", tags=["artworks"])
app.include_router(history.router, prefix="/api/artworks", tags=["history"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(blog.router, tags=["blog"])

# 루트 엔드포인트
@app.get("/")
async def root():
    return {"message": "Artive API Server"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    from services.scheduler import start_scheduler
    
    # 스케줄러 시작
    start_scheduler()
    
    # Railway는 PORT 환경변수 제공
    port = int(os.getenv("PORT", 8000)) 
    uvicorn.run(app, host="0.0.0.0", port=port)