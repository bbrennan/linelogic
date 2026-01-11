"""
SMTP email sender for LineLogic using Python's smtplib.

Supports common SMTP providers (iCloud, Gmail app password, Mailjet, Brevo).
"""

import smtplib
from email.message import EmailMessage
from typing import Optional

from linelogic.config.settings import settings


class SMTPEmailSender:
    """Send HTML emails via SMTP."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: Optional[bool] = None,
        from_email: Optional[str] = None,
    ):
        self.host = host or settings.smtp_host
        self.port = port or settings.smtp_port
        self.user = user or settings.smtp_user
        self.password = password or settings.smtp_pass
        self.use_tls = use_tls if use_tls is not None else settings.smtp_tls
        self.from_email = from_email or settings.from_email

        if not (
            self.host and self.port and self.user and self.password and self.from_email
        ):
            raise ValueError(
                "SMTP settings incomplete. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL in .env"
            )

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg.set_content("This email requires an HTML-capable client.")
        msg.add_alternative(html_content, subtype="html")

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"SMTP send failed: {e}")
            return False
