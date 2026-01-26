""" Email Service """
from pathlib import Path
import logging
from emails import Message
from emails.template import JinjaTemplate
from app.core.config import settings

logger = logging.getLogger(__name__)

# Templates folder
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"


def send_reset_password_email(
    email_to: str,
    token: str,
    subject: str = "Password Reset Request",
    template_name: str = "reset_password.html"
):
    """
    Send password reset email with reset link
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return
    project_name = settings.PROJECT_NAME
    frontend_url = settings.FRONTEND_URL or "http://localhost:5173"
    reset_link = f"{frontend_url}/reset-password"

    if subject is None:
        subject = f"{project_name} - Password Reset Request"

    # Template ကို ဖတ်ပါ
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template {template_name} not found")

    with open(template_path, "r", encoding="utf-8") as f:
        template_str = f.read()

    html_template = JinjaTemplate(template_str)

    message = Message(
        subject=subject,
        html=html_template,
        mail_from=(settings.EMAIL_FROM_NAME,
                   settings.EMAIL_FROM),
    )

    smtp_options = {
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "user": settings.SMTP_USER,
        "password": settings.SMTP_PASSWORD,
        "tls": True,
    }

    try:
        response = message.send(
            to=email_to,
            render={
                "project_name": project_name,
                "token": token,
                "reset_link": reset_link,
                "expiry_hours": 1,
            },
            smtp=smtp_options
        )

        if response.status_code not in (250, 235):
            return Exception(
                f"Failed to send email. Status: {response.status_code}")

        logger.info("Password reset email sent to %s", email_to)
    except Exception as e:
        logger.error("Email sending failed: %s", str(e))
        raise
