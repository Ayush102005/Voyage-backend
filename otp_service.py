"""
OTP Verification Service for Voyage
Handles OTP generation, storage, and verification
"""

import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# In-memory OTP storage (in production, use Redis or database)
otp_storage: Dict[str, Dict] = {}

# OTP Configuration
OTP_LENGTH = 6
OTP_VALIDITY_MINUTES = 10
MAX_ATTEMPTS = 3


class OTPService:
    """Service for handling OTP operations"""
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a random 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=OTP_LENGTH))
    
    @staticmethod
    def send_otp_email(email: str, otp: str) -> bool:
        """Send OTP via email"""
        try:
            # Email configuration
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            sender_email = os.getenv('SENDER_EMAIL')
            sender_password = os.getenv('SENDER_PASSWORD')
            
            if not sender_email or not sender_password:
                print("⚠️ Email credentials not configured. OTP will be logged to console.")
                print(f"🔐 OTP for {email}: {otp}")
                return True  # Return True for development
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "Your Voyage OTP Code"
            message["From"] = sender_email
            message["To"] = email
            
            # HTML email template
            html_content = f"""
            <html>
              <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f8fafc;">
                <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 16px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                  <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #1e3a8a; font-size: 32px; margin: 0;">✈️ Voyage</h1>
                    <p style="color: #64748b; font-size: 14px; margin-top: 5px;">Your AI Travel Companion</p>
                  </div>
                  
                  <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); padding: 30px; border-radius: 12px; text-align: center; margin-bottom: 30px;">
                    <h2 style="color: #1e3a8a; margin: 0 0 10px 0;">Your Verification Code</h2>
                    <div style="font-size: 48px; font-weight: bold; color: #2563eb; letter-spacing: 8px; margin: 20px 0;">
                      {otp}
                    </div>
                    <p style="color: #64748b; font-size: 14px; margin: 10px 0 0 0;">
                      Valid for {OTP_VALIDITY_MINUTES} minutes
                    </p>
                  </div>
                  
                  <div style="background: #fef3c7; padding: 20px; border-radius: 12px; border-left: 4px solid #f59e0b; margin-bottom: 30px;">
                    <p style="margin: 0; color: #92400e; font-size: 14px;">
                      <strong>🔒 Security Notice:</strong><br/>
                      Never share this OTP with anyone. Voyage team will never ask for your OTP.
                    </p>
                  </div>
                  
                  <div style="text-align: center; color: #94a3b8; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                    <p>If you didn't request this OTP, please ignore this email.</p>
                    <p style="margin-top: 10px;">© 2025 Voyage. All rights reserved.</p>
                  </div>
                </div>
              </body>
            </html>
            """
            
            # Plain text version
            text_content = f"""
            Voyage - Your Verification Code
            
            Your OTP: {otp}
            
            This code is valid for {OTP_VALIDITY_MINUTES} minutes.
            
            Never share this OTP with anyone.
            
            If you didn't request this, please ignore this email.
            
            © 2025 Voyage
            """
            
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, message.as_string())
            
            print(f"✅ OTP sent to {email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send OTP email: {e}")
            # For development, still log the OTP
            print(f"🔐 OTP for {email}: {otp}")
            return True  # Return True for development
    
    @staticmethod
    def send_otp_sms(phone_number: str, otp: str) -> bool:
        """Send OTP via SMS (placeholder for SMS gateway integration)"""
        try:
            # TODO: Integrate with SMS gateway (Twilio, AWS SNS, etc.)
            # For now, just log to console
            print(f"📱 SMS OTP for {phone_number}: {otp}")
            
            # In production, use Twilio or similar:
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(
            #     body=f"Your Voyage OTP is: {otp}. Valid for {OTP_VALIDITY_MINUTES} minutes.",
            #     from_=twilio_phone,
            #     to=phone_number
            # )
            
            return True
        except Exception as e:
            print(f"❌ Failed to send OTP SMS: {e}")
            return False
    
    @staticmethod
    def store_otp(identifier: str, otp: str, method: str = 'email'):
        """Store OTP with expiry time"""
        otp_storage[identifier] = {
            'otp': otp,
            'method': method,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=OTP_VALIDITY_MINUTES),
            'attempts': 0,
            'verified': False
        }
        print(f"💾 OTP stored for {identifier} (expires in {OTP_VALIDITY_MINUTES} min)")
    
    @staticmethod
    def verify_otp(identifier: str, otp: str) -> Dict[str, any]:
        """
        Verify OTP for given identifier
        Returns: {success: bool, message: str}
        """
        if identifier not in otp_storage:
            return {
                'success': False,
                'message': 'No OTP found. Please request a new one.'
            }
        
        stored_data = otp_storage[identifier]
        
        # Check if already verified
        if stored_data['verified']:
            return {
                'success': False,
                'message': 'OTP already used. Please request a new one.'
            }
        
        # Check expiry
        if datetime.now() > stored_data['expires_at']:
            del otp_storage[identifier]
            return {
                'success': False,
                'message': 'OTP expired. Please request a new one.'
            }
        
        # Check max attempts
        if stored_data['attempts'] >= MAX_ATTEMPTS:
            del otp_storage[identifier]
            return {
                'success': False,
                'message': f'Maximum attempts ({MAX_ATTEMPTS}) exceeded. Please request a new OTP.'
            }
        
        # Verify OTP
        stored_data['attempts'] += 1
        
        if stored_data['otp'] == otp:
            stored_data['verified'] = True
            return {
                'success': True,
                'message': 'OTP verified successfully!'
            }
        else:
            attempts_left = MAX_ATTEMPTS - stored_data['attempts']
            return {
                'success': False,
                'message': f'Invalid OTP. {attempts_left} attempts remaining.'
            }
    
    @staticmethod
    def send_otp(phone_number: str) -> tuple[bool, str]:
        """
        Send OTP to phone number (wrapper for server.py compatibility)
        Returns: (success: bool, message: str)
        """
        # Generate OTP
        otp = OTPService.generate_otp()
        
        # Try to send via SMS
        success = OTPService.send_otp_sms(phone_number, otp)
        
        if success:
            # Store OTP
            OTPService.store_otp(phone_number, otp, 'sms')
            return (True, f'OTP sent successfully to {phone_number}')
        else:
            return (False, 'Failed to send OTP. Please try again.')
    
    @staticmethod
    def verify_otp_simple(phone_number: str, otp: str) -> tuple[bool, str]:
        """
        Verify OTP (wrapper for server.py compatibility)
        Returns: (success: bool, message: str)
        """
        result = OTPService.verify_otp(phone_number, otp)
        return (result['success'], result['message'])
    
    @staticmethod
    def resend_otp(identifier: str, method: str = 'email') -> Dict[str, any]:
        """Resend OTP to identifier"""
        # Generate new OTP
        new_otp = OTPService.generate_otp()
        
        # Send based on method
        success = False
        if method == 'email':
            success = OTPService.send_otp_email(identifier, new_otp)
        elif method == 'sms':
            success = OTPService.send_otp_sms(identifier, new_otp)
        
        if success:
            OTPService.store_otp(identifier, new_otp, method)
            return {
                'success': True,
                'message': f'OTP resent successfully via {method}!'
            }
        else:
            return {
                'success': False,
                'message': f'Failed to send OTP via {method}.'
            }
    
    @staticmethod
    def cleanup_expired_otps():
        """Remove expired OTPs from storage"""
        now = datetime.now()
        expired_keys = [
            key for key, data in otp_storage.items()
            if now > data['expires_at']
        ]
        for key in expired_keys:
            del otp_storage[key]
        
        if expired_keys:
            print(f"🧹 Cleaned up {len(expired_keys)} expired OTPs")
    
    @staticmethod
    def get_otp_status(identifier: str) -> Optional[Dict]:
        """Get OTP status for debugging"""
        if identifier in otp_storage:
            data = otp_storage[identifier]
            return {
                'exists': True,
                'method': data['method'],
                'attempts': data['attempts'],
                'verified': data['verified'],
                'expires_at': data['expires_at'].isoformat(),
                'time_remaining': str(data['expires_at'] - datetime.now())
            }
        return {'exists': False}


# Periodic cleanup task (call this from background scheduler)
def cleanup_task():
    """Background task to clean expired OTPs"""
    OTPService.cleanup_expired_otps()


# Singleton instance
_otp_service_instance = None

def get_otp_service() -> OTPService:
    """
    Get or create the OTP service singleton instance
    
    Returns:
        OTPService instance
    """
    global _otp_service_instance
    if _otp_service_instance is None:
        _otp_service_instance = OTPService()
    return _otp_service_instance
