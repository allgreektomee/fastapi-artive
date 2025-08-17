# create_test_data.py
"""
테스트용 사용자와 블로그 데이터 생성
"""

from sqlalchemy.orm import sessionmaker
from models.database import engine
from models.user import User
from models.blog import BlogPost
from services.auth_service import AuthService
from datetime import datetime

def create_test_data():
    """테스트용 데이터 생성"""
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 1. 테스트 사용자 생성
        print("👤 테스트 사용자 생성 중...")
        
        # park 사용자 생성
        park_user = User(
            email="park@example.com",
            password=AuthService.hash_password("password123"),
            name="박아티스트",
            slug="park",
            bio="안녕하세요! 저는 현대 미술가입니다.",
            gallery_title="박아티스트 갤러리",
            is_verified=True,
            is_active=True
        )
        
        db.add(park_user)
        db.commit()
        db.refresh(park_user)
        
        print(f"✅ 사용자 생성: {park_user.name} (@{park_user.slug})")
        
        # 2. 테스트 블로그 포스트 생성
        print("📝 테스트 블로그 포스트 생성 중...")
        
        test_posts = [
            {
                "title": "갤러리 오픈 공지",
                "content": "# 안녕하세요!\n\n새로운 온라인 갤러리를 오픈했습니다.\n\n## 주요 기능\n- 작품 전시\n- 블로그 기능\n- 공지사항\n\n많은 관심 부탁드립니다!",
                "excerpt": "새로운 온라인 갤러리 오픈 소식을 알려드립니다.",
                "post_type": "NOTICE",
                "is_published": True,
                "is_public": True,
                "is_pinned": True
            },
            {
                "title": "첫 번째 작품 소개",
                "content": "## 새로운 작품\n\n오늘 새로운 작품을 완성했습니다.\n\n> 예술은 마음의 언어입니다.\n\n이번 작품은 현대인의 고독을 표현했습니다.",
                "excerpt": "새로운 작품 완성 소식입니다.",
                "post_type": "BLOG",
                "is_published": True,
                "is_public": True,
                "is_pinned": False
            },
            {
                "title": "전시회 준비 중",
                "content": "다음 달 개인전을 준비하고 있습니다.\n\n- 장소: 서울 갤러리\n- 기간: 2025년 9월\n- 주제: 현대의 고독",
                "excerpt": "개인전 준비 소식을 전해드립니다.",
                "post_type": "EXHIBITION",
                "is_published": True,
                "is_public": True,
                "is_pinned": False
            }
        ]
        
        for post_data in test_posts:
            blog_post = BlogPost(
                title=post_data["title"],
                content=post_data["content"],
                excerpt=post_data["excerpt"],
                post_type=post_data["post_type"],
                is_published=post_data["is_published"],
                is_public=post_data["is_public"],
                is_pinned=post_data["is_pinned"],
                published_at=datetime.now() if post_data["is_published"] else None,
                user_id=park_user.id
            )
            
            db.add(blog_post)
            print(f"✅ 포스트 생성: {post_data['title']}")
        
        db.commit()
        
        print("🎉 테스트 데이터 생성 완료!")
        print("\n📊 생성된 데이터:")
        print(f"- 사용자: {park_user.name} (이메일: {park_user.email})")
        print(f"- 비밀번호: password123")
        print(f"- 블로그 포스트: {len(test_posts)}개")
        print(f"- 접속 URL: http://localhost:3000/{park_user.slug}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()