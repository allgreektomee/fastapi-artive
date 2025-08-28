# services/email_service.py - 환경변수 기반 URL 구분

import os
import resend
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    
    @staticmethod
    def get_backend_url():
        """환경변수 기반으로 프론트엔드 URL 반환"""
        
        # 개발 환경 감지 (여러 조건으로 확인)
        is_development = (
            "localhost" in os.getenv("DATABASE_URL", "").lower() or
            os.getenv("DEBUG", "False").lower() == "true" or
            os.getenv("PORT", "8000") == "8000"
        )
        
        if is_development:
            backend_url = os.getenv("BACKEND_URL_DEV", "http://localhost:8000")
            print(f"🔧 개발 환경 감지 | Frontend: {backend_url}")
        else:
            backend_url = os.getenv("BACKEND_URL", "api.artivefor.me")
            print(f"🚀 운영 환경 감지 | Frontend: {backend_url}")
        
        return backend_url
    
    @staticmethod
    def get_mail_config():
        """이메일 설정 반환"""
        from fastapi_mail import ConnectionConfig
        
        return ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
            MAIL_FROM=os.getenv("MAIL_FROM"),
            MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
            MAIL_SERVER=os.getenv("MAIL_SERVER"),
            MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Artive"),
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
    

    # async def send_verification_email(email: str, token: str, name: str):
    #     """이메일 인증 메일 발송"""
    #     try:
    #         conf = EmailService.get_mail_config()
        
    #         # 백엔드 URL로 수정
    #         backend_url = "http://localhost:8000"  
    #         verification_link = f"{backend_url}/api/auth/verify-email?token={token}"
            
    #         # HTML 이메일 템플릿 - 버튼 스타일 수정
    #         html_content = f"""
    #         <!DOCTYPE html>
    #         <html>
    #         <head>
    #             <meta charset="utf-8">
    #             <title>Artive 이메일 인증</title>
    #         </head>
    #         <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
    #             <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
    #                 <div style="text-align: center; margin-bottom: 30px;">
    #                     <div style="font-size: 32px; font-weight: bold; color: #000; margin-bottom: 10px;">Artive</div>
    #                     <p style="color: #666;">작가를 위한 온라인 갤러리</p>
    #                 </div>
                    
    #                 <div style="background: #f9f9f9; padding: 40px 30px; border-radius: 8px;">
    #                     <h2 style="text-align: center; font-size: 24px; margin-bottom: 20px;">
    #                         안녕하세요, {name}님!
    #                     </h2>
                        
    #                     <p style="text-align: center; font-size: 16px; color: #555; margin-bottom: 10px;">
    #                         Artive에 가입해주셔서 감사합니다.
    #                     </p>
                        
    #                     <p style="text-align: center; font-size: 16px; color: #555; margin-bottom: 40px;">
    #                         아래 버튼을 클릭하여 이메일 인증을 완료해주세요:
    #                     </p>
                        
    #                     <!-- 버튼을 테이블로 변경 (이메일 호환성) -->
    #                     <table width="100%" border="0" cellspacing="0" cellpadding="0">
    #                         <tr>
    #                             <td align="center" style="padding: 20px 0;">
    #                                 <a href="{verification_link}" style="display: inline-block; background-color: #000000; color: #ffffff; font-size: 18px; font-weight: bold; text-decoration: none; padding: 18px 50px; border-radius: 8px;">
    #                                     이메일 인증하기
    #                                 </a>
    #                             </td>
    #                         </tr>
    #                     </table>
                        
    #                     <div style="margin-top: 30px; padding: 20px; background: #fff; border-radius: 5px; word-break: break-all;">
    #                         <p style="font-size: 14px; color: #666; margin: 0 0 10px 0;">
    #                             버튼이 작동하지 않으면 아래 링크를 복사하여 브라우저에 붙여넣으세요:
    #                         </p>
    #                         <p style="font-size: 13px; color: #0066cc; margin: 0;">
    #                             <a href="{verification_link}" style="color: #0066cc; text-decoration: underline;">
    #                                 {verification_link}
    #                             </a>
    #                         </p>
    #                     </div>
                        
    #                     <p style="font-size: 14px; color: #999; text-align: center; margin-top: 30px;">
    #                         이 링크는 24시간 후 만료됩니다.<br>
    #                         본인이 가입하지 않았다면 이 메일을 무시하세요.
    #                     </p>
    #                 </div>
                    
    #                 <div style="text-align: center; margin-top: 30px; font-size: 14px; color: #666;">
    #                     <p>© 2024 Artive. All rights reserved.</p>
    #                     <p>문의: support@artivefor.me</p>
    #                 </div>
    #             </div>
    #         </body>
    #         </html>
    #         """
            
    #         # 메시지 생성 및 발송
    #         from fastapi_mail import MessageSchema, MessageType, FastMail
            
    #         message = MessageSchema(
    #             subject="Artive 이메일 인증",
    #             recipients=[email],
    #             body=html_content,
    #             subtype=MessageType.html
    #         )
            
    #         fm = FastMail(conf)
    #         await fm.send_message(message)
            
    #         print(f"✅ 인증 이메일 발송 성공: {email}")
    #         return True
            
    #     except Exception as e:
    #         print(f"❌ 이메일 발송 실패: {e}")
    #         return False
    @staticmethod
    async def send_verification_email(email: str, token: str, name: str) -> bool:
        """이메일 인증 메일 발송"""
        try:
            # Resend API 키 설정
            resend.api_key = os.getenv("RESEND_API_KEY")
            
            # 인증 링크 생성
            verification_link = f"https://api.artivefor.me/api/auth/verify-email?token={token}"
            
            # 이메일 발송
            response = resend.Emails.send({
                "from": "Artive <onboarding@resend.dev>",
                "to": email,
                "subject": "Artive 이메일 인증",
                "html": f"""
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <div style="font-size: 32px; font-weight: bold; color: #000; margin-bottom: 10px;">Artive</div>
                            <p style="color: #666;">작가를 위한 온라인 갤러리</p>
                        </div>
                        
                        <div style="background: #f9f9f9; padding: 40px 30px; border-radius: 8px;">
                            <h2 style="text-align: center; font-size: 24px; margin-bottom: 20px;">
                                안녕하세요, {name}님!
                            </h2>
                            
                            <p style="text-align: center; font-size: 16px; color: #555; margin-bottom: 10px;">
                                Artive에 가입해주셔서 감사합니다.
                            </p>
                            
                            <p style="text-align: center; font-size: 16px; color: #555; margin-bottom: 40px;">
                                아래 버튼을 클릭하여 이메일 인증을 완료해주세요:
                            </p>
                            
                            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{verification_link}" style="display: inline-block; background-color: #000000; color: #ffffff; font-size: 18px; font-weight: bold; text-decoration: none; padding: 18px 50px; border-radius: 8px;">
                                            이메일 인증하기
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <div style="margin-top: 30px; padding: 20px; background: #fff; border-radius: 5px; word-break: break-all;">
                                <p style="font-size: 14px; color: #666; margin: 0 0 10px 0;">
                                    버튼이 작동하지 않으면 아래 링크를 복사하여 브라우저에 붙여넣으세요:
                                </p>
                                <p style="font-size: 13px; color: #0066cc; margin: 0;">
                                    <a href="{verification_link}" style="color: #0066cc; text-decoration: underline;">
                                        {verification_link}
                                    </a>
                                </p>
                            </div>
                            
                            <p style="font-size: 14px; color: #999; text-align: center; margin-top: 30px;">
                                이 링크는 24시간 후 만료됩니다.<br>
                                본인이 가입하지 않았다면 이 메일을 무시하세요.
                            </p>
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px; font-size: 14px; color: #666;">
                            <p>© 2024 Artive. All rights reserved.</p>
                            <p>문의: support@artivefor.me</p>
                        </div>
                    </div>
                </body>
                """
            })
            print(f"✅ 이메일 발송 성공: {email}")
            return True
            
        except Exception as e:
            print(f"❌ 이메일 발송 실패: {e}")
            print(f"📧 인증 링크: {verification_link}")
            return False
        
    @staticmethod
    async def send_password_reset_email(email: str, token: str, name: str):
        """비밀번호 재설정 메일 발송"""
        try:
            conf = EmailService.get_mail_config()
            
            frontend_url = EmailService.get_frontend_url()
            reset_link = f"{frontend_url}/auth/reset-password?token={token}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Artive 비밀번호 재설정</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .logo {{ font-size: 28px; font-weight: bold; color: #000; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-radius: 8px; }}
                    .button {{ display: inline-block; background: #dc2626; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; font-size: 14px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">Artive</div>
                    </div>
                    
                    <div class="content">
                        <h2>비밀번호 재설정 요청</h2>
                        <p>안녕하세요, {name}님.</p>
                        <p>비밀번호 재설정이 요청되었습니다.</p>
                        
                        <div style="text-align: center;">
                            <a href="{reset_link}" class="button">비밀번호 재설정</a>
                        </div>
                        
                        <p style="font-size: 14px; color: #666;">
                            이 링크는 1시간 후 만료됩니다.<br>
                            본인이 요청하지 않았다면 이 메일을 무시하세요.
                        </p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2024 Artive. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            message = MessageSchema(
                subject="Artive 비밀번호 재설정",
                recipients=[email],
                body=html_content,
                subtype=MessageType.html
            )
            
            fm = FastMail(conf)
            await fm.send_message(message)
            
            print(f"✅ 비밀번호 재설정 이메일 발송 성공: {email}")
            return True
            
        except Exception as e:
            print(f"❌ 비밀번호 재설정 이메일 발송 실패: {e}")
            return False