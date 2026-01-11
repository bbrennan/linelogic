"""
Email sender router: picks appropriate sender based on settings.

Order:
1. If EMAIL_PROVIDER is set: use that provider (sendgrid or smtp)
2. Else if SENDGRID_API_KEY present: use SendGrid
3. Else if SMTP config present: use SMTP
4. Else: raise ValueError
"""

from typing import Any

from linelogic.config.settings import settings


def _smtp_config_complete() -> bool:
    return all(
        [
            settings.smtp_host,
            settings.smtp_port,
            settings.smtp_user,
            settings.smtp_pass,
            settings.from_email,
        ]
    )


def get_email_sender() -> Any:
    provider = (
        settings.email_provider.lower().strip() if settings.email_provider else ""
    )

    if provider == "sendgrid":
        from linelogic.email_sender import EmailSender

        return EmailSender()
    if provider == "smtp":
        from linelogic.email_smtp import SMTPEmailSender

        return SMTPEmailSender()

    # Auto: prefer SendGrid if key present, else SMTP
    if getattr(settings, "sendgrid_api_key", ""):
        from linelogic.email_sender import EmailSender

        return EmailSender()

    if _smtp_config_complete():
        from linelogic.email_smtp import SMTPEmailSender

        return SMTPEmailSender()

    raise ValueError(
        "No email provider configured. Set SENDGRID_API_KEY or SMTP_* in .env, or EMAIL_PROVIDER= smtp/sendgrid."
    )
