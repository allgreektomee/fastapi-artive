# main.py (FastAPI 메인 앱에 프로필 라우터 추가)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 기존 라우터들
from routers import auth, artwork, history, upload
# 새로 추가된 프로필 라우터
from routers import profile

# 데이터베이스 초기화
from models.database import create_tables

app = FastAPI(
    title="Artive API",
    description="아티스트 포트폴리오 플랫폼 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://artive.com"],  # 프론트엔드 도메인
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터베이스 테이블 생성
create_tables()

# 라우터 등록
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(artwork.router, prefix="/artworks", tags=["artworks"])
app.include_router(history.router, prefix="/api/artworks", tags=["history"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(profile.router, prefix="/api", tags=["profile"])  # 새로 추가

@app.get("/")
async def root():
    return {"message": "Artive API Server"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)