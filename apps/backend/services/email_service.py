"""
Email Service (T13)

Renders and sends Jinja2 email templates for onboarding workflow.

Features:
- Template rendering with Jinja2
- HTML + plain text generation
- i18n support (internationalization)
- Email service integration (Postmark/SendGrid)
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp

logger = logging.getLogger(__name__)


class EmailService:
    """Service for rendering and sending emails."""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize email service.

        Args:
            template_dir: Path to email templates directory.
                         Defaults to apps/backend/email_templates/
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "email_templates"

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Email service configuration
        self.email_service = os.getenv('EMAIL_SERVICE', 'postmark')
        self.api_key = os.getenv('EMAIL_API_KEY', '')
        self.from_email = os.getenv('EMAIL_FROM', 'noreply@contexia.online')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Contexia')

    def render(self, template_name: str, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Render email template.

        Args:
            template_name: Name of template file (without .html)
            context: Template variables dictionary

        Returns:
            Dict with 'html' and 'text' keys
        """
        try:
            # Render HTML
            html_template = self.env.get_template(f'{template_name}.html')
            html_content = html_template.render(**context)

            # Generate plain text (simple: strip HTML tags)
            # TODO: Use html2text for better conversion
            text_content = self._html_to_text(html_content)

            logger.info(f"Rendered email template: {template_name}")

            return {
                'html': html_content,
                'text': text_content,
            }

        except Exception as e:
            logger.error(f"Failed to render email template {template_name}: {str(e)}")
            raise

    async def send(
        self,
        to: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any],
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send email using configured service.

        Args:
            to: Recipient email
            subject: Email subject
            template_name: Template name (without .html)
            context: Template context
            reply_to: Reply-to email (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Render template
            content = self.render(template_name, context)

            # Send via configured service
            if self.email_service == 'postmark':
                result = await self._send_postmark(
                    to=to,
                    subject=subject,
                    html=content['html'],
                    text=content['text'],
                    reply_to=reply_to,
                )
            elif self.email_service == 'sendgrid':
                result = await self._send_sendgrid(
                    to=to,
                    subject=subject,
                    html=content['html'],
                    text=content['text'],
                    reply_to=reply_to,
                )
            else:
                # Mock: just log it
                logger.warning(f"Email service '{self.email_service}' not configured, mocking send")
                result = True

            if result:
                logger.info(f"Email sent to {to}: {template_name}")
            else:
                logger.error(f"Failed to send email to {to}")

            return result

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    async def _send_postmark(
        self,
        to: str,
        subject: str,
        html: str,
        text: str,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Send via Postmark API."""
        url = "https://api.postmarkapp.com/email"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.api_key,
        }

        payload = {
            "From": f"{self.from_name} <{self.from_email}>",
            "To": to,
            "Subject": subject,
            "HtmlBody": html,
            "TextBody": text,
            "ReplyTo": reply_to or self.from_email,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                    if resp.status == 200:
                        logger.debug(f"Postmark API returned 200 for {to}")
                        return True
                    else:
                        logger.error(f"Postmark API error: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Postmark request failed: {str(e)}")
            return False

    async def _send_sendgrid(
        self,
        to: str,
        subject: str,
        html: str,
        text: str,
        reply_to: Optional[str] = None,
    ) -> bool:
        """Send via SendGrid API."""
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text},
                {"type": "text/html", "value": html},
            ],
            "reply_to": {"email": reply_to or self.from_email},
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                    if resp.status == 202:
                        logger.debug(f"SendGrid API returned 202 for {to}")
                        return True
                    else:
                        logger.error(f"SendGrid API error: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"SendGrid request failed: {str(e)}")
            return False

    @staticmethod
    def _html_to_text(html: str) -> str:
        """
        Convert HTML to plain text (simple version).

        TODO: Use html2text library for better conversion.

        Args:
            html: HTML content

        Returns:
            Plain text version
        """
        import re

        # Remove script and style tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)

        # Replace <br> and </p> with newlines
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)

        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')

        # Remove extra whitespace
        text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())

        return text.strip()


# Global email service instance
_email_service = None


def get_email_service() -> EmailService:
    """Get or create email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
