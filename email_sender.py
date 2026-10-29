from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import SENDGRID_API_KEY, EMAIL_FROM, EMAIL_TO

def send_email(html_content, subject):
    if not SENDGRID_API_KEY:
        raise RuntimeError("Missing SENDGRID_API_KEY")
    message = Mail(
        from_email=EMAIL_FROM,
        to_emails=[x.strip() for x in EMAIL_TO.split(",") if x.strip()],
        subject=subject,
        html_content=html_content,
    )
    response = SendGridAPIClient(SENDGRID_API_KEY).send(message)
    print(f"SendGrid status: {response.status_code}")
