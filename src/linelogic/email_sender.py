"""
Email sender for LineLogic summaries using SendGrid.

SendGrid free tier: 100 emails/day - perfect for daily reports.
Get free API key at: https://sendgrid.com/
"""

import base64
import json
from typing import Optional

import requests

from linelogic.config.settings import settings


class EmailSender:
    """Send emails via SendGrid API."""

    SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SendGrid email sender.

        Args:
            api_key: SendGrid API key (defaults to settings.sendgrid_api_key)
        """
        self.api_key = api_key or getattr(settings, "sendgrid_api_key", "")
        if not self.api_key:
            raise ValueError(
                "SendGrid API key not found. Set SENDGRID_API_KEY environment variable or in .env"
            )

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str = "linelogic@example.com",
    ) -> bool:
        """
        Send HTML email via SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            from_email: Sender email (must be verified in SendGrid)

        Returns:
            True if successful, False otherwise
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": subject,
                }
            ],
            "from": {"email": from_email, "name": "LineLogic"},
            "content": [
                {
                    "type": "text/html",
                    "value": html_content,
                }
            ],
        }

        try:
            response = requests.post(
                self.SENDGRID_API_URL, headers=headers, json=payload, timeout=10
            )

            if response.status_code in (200, 201, 202):
                return True
            else:
                print(f"SendGrid error: {response.status_code} {response.text}")
                return False

        except requests.RequestException as e:
            print(f"Email send failed: {e}")
            return False
