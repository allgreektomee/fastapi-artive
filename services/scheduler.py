import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.user import User
from routers.upload import cleanup_user_s3_files

async def cleanup_unverified_users():
    """24시간 후 미인증 사용자 삭제"""
    db = SessionLocal()
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        expired_users = db.query(User).filter(
            User.is_verified == False,
            User.created_at <= cutoff_time
        ).all()
        
        for user in expired_users:
            try:
                cleanup_user_s3_files(user.slug)
                db.delete(user)
                print(f"미인증 사용자 삭제: {user.email}")
            except Exception as e:
                print(f"사용자 {user.email} 삭제 실패: {e}")
        
        db.commit()
        print(f"미인증 사용자 {len(expired_users)}명 정리 완료")
        
    except Exception as e:
        print(f"미인증 사용자 정리 오류: {e}")
        db.rollback()
    finally:
        db.close()

def start_scheduler():
    """스케줄러 시작"""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        cleanup_unverified_users,
        'interval', 
        hours=1,  # 1시간마다 체크
        id='cleanup_unverified'
    )
    scheduler.start()
    print("미인증 사용자 정리 스케줄러 시작됨")
    return scheduler