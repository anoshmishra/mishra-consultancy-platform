"""
SendGrid Email Backend for Django
Provides a robust email sending solution with retry logic and comprehensive error handling.
"""
import logging
import json
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.core.mail.backends.base import BaseEmailBackend
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Email, To, Content, Attachment, FileContent, 
    FileName, FileType, Disposition, ContentId, Header
)
import base64

logger = logging.getLogger(__name__)


def smtp_is_configured() -> bool:
    return all([
        getattr(settings, 'EMAIL_HOST', ''),
        getattr(settings, 'EMAIL_HOST_USER', ''),
        getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
    ])


class SendGridEmailBackend(BaseEmailBackend):
    """
    SendGrid Email Backend for Django
    Efficiently sends emails via SendGrid API with comprehensive error handling and retry logic.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.max_retries = getattr(settings, 'SENDGRID_MAX_RETRIES', 3)
        self.client = None
        
        if not self.api_key:
            logger.error("SENDGRID_API_KEY not configured in settings")
            if not fail_silently:
                raise ValueError("SENDGRID_API_KEY is not configured")

    def _get_client(self):
        """Lazy initialization of SendGrid client"""
        if self.client is None and self.api_key:
            self.client = SendGridAPIClient(self.api_key)
        return self.client

    def send_messages(self, email_messages: List) -> int:
        """
        Send one or more EmailMessage objects and return the number of email
        messages sent.
        """
        if not email_messages:
            return 0

        sent_count = 0
        for message in email_messages:
            try:
                if self._send(message):
                    sent_count += 1
            except Exception as e:
                if not self.fail_silently:
                    raise
                logger.error(f"Failed to send email: {str(e)}")

        return sent_count

    def _send(self, message) -> bool:
        """
        Send a single email message via SendGrid
        Returns True if successful, False otherwise
        """
        if not self._get_client():
            return False

        try:
            # Build the Mail object
            mail = self._build_mail(message)
            
            # Send with retry logic
            for attempt in range(1, self.max_retries + 1):
                try:
                    response = self.client.send(mail)
                    
                    if response.status_code in [200, 201, 202]:
                        logger.info(
                            f"Email sent successfully to {message.to} "
                            f"(attempt {attempt}/{self.max_retries})"
                        )
                        return True
                    else:
                        logger.warning(
                            f"SendGrid returned status {response.status_code} "
                            f"for recipient {message.to}"
                        )
                        if attempt < self.max_retries:
                            continue
                        return False
                        
                except Exception as retry_error:
                    logger.warning(
                        f"Attempt {attempt}/{self.max_retries} failed for {message.to}: "
                        f"{str(retry_error)}"
                    )
                    if attempt < self.max_retries:
                        continue
                    raise retry_error

            return False

        except Exception as e:
            logger.error(f"Failed to send email to {message.to}: {str(e)}")
            if not self.fail_silently:
                raise
            return False

    def _build_mail(self, message) -> Mail:
        """
        Convert Django EmailMessage to SendGrid Mail object
        """
        # Parse from email
        from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
        from_name = getattr(message, 'from_name', None)
        
        # Create Mail object with proper initialization
        mail = Mail(
            from_email=Email(from_email, from_name),
            to_emails=[To(email=recipient) for recipient in message.to if isinstance(recipient, str) and recipient.strip()],
            subject=message.subject,
            plain_text_content=message.body if message.content_subtype == 'text' else None,
            html_content=message.body if message.content_subtype == 'html' else None
        )
        
        # Add CC recipients
        for cc in getattr(message, 'cc', []):
            if isinstance(cc, str) and cc.strip():
                mail.add_cc(cc)
        
        # Add BCC recipients
        for bcc in getattr(message, 'bcc', []):
            if isinstance(bcc, str) and bcc.strip():
                mail.add_bcc(bcc)
        
        # Add attachments
        if message.attachments:
            for attachment in message.attachments:
                if isinstance(attachment, tuple):
                    # attachment is (filename, content, mimetype)
                    filename, content, mimetype = attachment
                    self._add_attachment(mail, filename, content, mimetype)
        
        # Add reply-to if present
        if getattr(message, 'reply_to', None) and message.reply_to:
            mail.reply_to = Email(message.reply_to[0])
        
        # Add custom headers if present
        if getattr(message, 'extra_headers', None):
            for header_name, header_value in message.extra_headers.items():
                mail.add_header(Header(header_name, header_value))
        
        return mail

    def _add_attachment(self, mail: Mail, filename: str, content: Any, 
                       mimetype: str = 'application/octet-stream'):
        """
        Add attachment to SendGrid Mail object
        """
        try:
            # Handle file-like objects (e.g., BytesIO)
            if hasattr(content, 'read'):
                file_content = content.read()
                if isinstance(file_content, str):
                    file_content = file_content.encode('utf-8')
            else:
                file_content = content
                if isinstance(file_content, str):
                    file_content = file_content.encode('utf-8')
            
            # Encode content to base64
            encoded_content = base64.b64encode(file_content).decode()
            
            # Determine file type from mimetype
            file_type = FileType(mimetype)
            
            # Create and add attachment
            attachment = Attachment(
                FileContent(encoded_content),
                FileName(filename),
                file_type,
                Disposition('attachment')
            )
            mail.add_attachment(attachment)
            
            logger.info(f"Attachment {filename} added successfully")
            
        except Exception as e:
            logger.error(f"Failed to add attachment {filename}: {str(e)}")
            if not self.fail_silently:
                raise


def send_sendgrid_email(subject: str, message: str, recipient_list: List[str],
                        fail_silently: bool = False, html_message: Optional[str] = None,
                        from_email: Optional[str] = None, attachments: Optional[List] = None,
                        cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None,
                        reply_to: Optional[str] = None, extra_headers: Optional[Dict] = None,
                        max_retries: int = 3) -> bool:
    """
    Simplified function to send emails via SendGrid with retry logic
    
    Args:
        subject: Email subject
        message: Email body (plain text or HTML based on html_message)
        recipient_list: List of recipient email addresses
        fail_silently: Whether to suppress exceptions
        html_message: HTML version of the email body
        from_email: Override the from email address
        attachments: List of attachments as (filename, content, mimetype) tuples
        cc: List of CC recipients
        bcc: List of BCC recipients
        reply_to: Reply-to email address
        extra_headers: Dictionary of extra headers
        max_retries: Number of retry attempts
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    from django.core.mail import EmailMessage
    
    try:
        # Create EmailMessage object
        email_msg = EmailMessage(
            subject=subject,
            body=html_message or message,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=recipient_list,
            cc=cc or [],
            bcc=bcc or [],
            reply_to=[reply_to] if reply_to else [],
        )
        
        # Set content subtype to HTML if html_message is provided
        if html_message:
            email_msg.content_subtype = 'html'
            email_msg.alternatives = [(message, 'text/plain')]
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                email_msg.attach(*attachment)
        
        # Add extra headers if provided
        if extra_headers:
            email_msg.extra_headers = extra_headers
        
        if getattr(settings, 'SENDGRID_API_KEY', ''):
            backend = SendGridEmailBackend(fail_silently=fail_silently)
        elif smtp_is_configured():
            logger.warning("SENDGRID_API_KEY not configured. Sending email via SMTP fallback.")
            backend = SMTPEmailBackend(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
                use_ssl=settings.EMAIL_USE_SSL,
                timeout=settings.EMAIL_TIMEOUT,
                fail_silently=fail_silently,
            )
        else:
            raise ValueError("No email provider configured. Set SENDGRID_API_KEY or SMTP EMAIL_HOST/EMAIL_HOST_USER/EMAIL_HOST_PASSWORD.")

        result = backend.send_messages([email_msg])
        
        return result > 0
        
    except Exception as e:
        logger.error(f"SendGrid email sending failed: {str(e)}")
        if not fail_silently:
            raise
        return False


def send_sendgrid_email_with_retry(subject: str, message: str, recipient_list: List[str],
                                   fail_silently: bool = False, html_message: Optional[str] = None,
                                   from_email: Optional[str] = None, attachments: Optional[List] = None,
                                   max_retries: Optional[int] = None) -> bool:
    """
    Send email via SendGrid with automatic retry logic
    
    Args:
        subject: Email subject
        message: Email body
        recipient_list: List of recipients
        fail_silently: Whether to suppress exceptions
        html_message: HTML version of body
        from_email: Override from address
        attachments: List of (filename, content, mimetype) tuples
        max_retries: Override default retry count
    
    Returns:
        True if successful, False otherwise
    """
    import time
    
    retries = max_retries or getattr(settings, 'EMAIL_SEND_RETRIES', 3)
    retry_delay = float(getattr(settings, 'EMAIL_RETRY_DELAY_SECONDS', 2))
    last_error = None
    
    for attempt in range(1, retries + 1):
        try:
            success = send_sendgrid_email(
                subject=subject,
                message=message,
                recipient_list=recipient_list,
                fail_silently=False,
                html_message=html_message,
                from_email=from_email,
                attachments=attachments,
            )
            
            if success:
                logger.info(f"Email sent successfully on attempt {attempt}/{retries}")
                return True
                
        except Exception as e:
            last_error = e
            logger.warning(
                f"Attempt {attempt}/{retries} to send email failed: {str(e)}"
            )
            
            if attempt < retries:
                time.sleep(retry_delay * attempt)
                continue
    
    if last_error and not fail_silently:
        raise last_error
    
    logger.error(f"Failed to send email after {retries} attempts")
    return False
