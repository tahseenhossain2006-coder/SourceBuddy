# sourceai/outreach/provider.py
import aiosmtplib
import logging
from email.message import EmailMessage
from typing import Optional
from sourceai.config.settings import settings

logger = logging.getLogger(__name__)

class EmailProvider:
    async def send(self, to: str, subject: str, body: str,
                   from_addr: Optional[str] = None) -> str:
        raise NotImplementedError

class SMTPProvider(EmailProvider):
    async def send(self, to: str, subject: str, body: str,
                   from_addr: Optional[str] = None) -> str:
        msg = EmailMessage()
        msg["From"] = from_addr or settings.SMTP_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        try:
            result = await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=settings.SMTP_TLS,
            )
            return str(result)  # message id
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            raise

def get_email_provider() -> EmailProvider:
    if settings.SMTP_HOST:
        return SMTPProvider()
    raise RuntimeError("SMTP not configured")