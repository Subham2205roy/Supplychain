import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.settings import settings

def send_otp_email(to_email: str, otp: str):
    """Sends a real verification email via SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.smtp_user
        msg['To'] = to_email
        msg['Subject'] = "Your GlobalBI Automation OTP"

        body = f"""
        Hello,

        Your verification code for GlobalBI Email Automation is: {otp}

        Enter this code in your dashboard to authorize this email address for automatic CSV uploads.

        --- HOW TO USE ---
        Once authorized, you can upload data to the dashboard simply by sending an email with your CSV attachment to:
        👉 {settings.smtp_user}

        The system will automatically process the attachment and update the relevant charts.

        If you did not request this, please ignore this email.

        Regards,
        GlobalBI Team
        """
        msg.attach(MIMEText(body, 'plain'))

        # Connect and send
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
            
        print(f"✅ Real OTP sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False

def send_success_confirmation(to_email: str):
    """Sends a confirmation email once automation is activated."""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.smtp_user
        msg['To'] = to_email
        msg['Subject'] = "GlobalBI Automation Activated - Instructions"

        body = f"""
        Hello,

        Great news! Your email address has been successfully authorized for GlobalBI Email Automation.

        --- HOW TO SUBMIT DATA ---
        From now on, you can upload CSV reports directly to the dashboard just by sending an email.

        1. Attach your CSV file.
        2. Send the email TO: 👉 {settings.smtp_user}

        Our system will handle the rest!

        Duration: Authorized for the requested period.
        
        Regards,
        GlobalBI Team
        """
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
            
        print(f"✅ Success confirmation sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send confirmation: {e}")
        return False
