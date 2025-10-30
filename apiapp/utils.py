from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import CreateDistributor

def send_sms(mobile, otp):
    # Placeholder function to simulate sending an SMS
     # In a real-world scenario, integrate with an SMS gateway API here
    print(f"📱 Sending OTP {otp} to {mobile}")


def send_otp_email(to_email, otp,shop_name=None):
    subject = 'Your OTP for Verification '
    message=f'Your OTP is {otp}. for {shop_name}. It is valid for 10 minutes.'
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(
        subject,
        message,
        from_email,
        [to_email],
        fail_silently=False,

    )