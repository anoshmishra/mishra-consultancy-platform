"""
Simplified SendGrid Email Backend for Django
"""
import logging
import base64
from typing import List, Optional
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Attachment, FileContent, FileName, FileType, Disposition

logger = logging.getLogger(__name__)


class SendGridBackend(BaseEmailBackend):
    """Simple SendGrid backend for Django"""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        
        if not self.api_key:
            msg = "SENDGRID_API_KEY not configured"
            logger.error(msg)
            if not fail_silently:
                raise ValueError(msg)

    def send_messages(self, email_messages):
        """Send email messages via SendGrid"""
        if not self.api_key:
            return 0
        
        msg_count = 0
        sg = SendGridAPIClient(self.api_key)
        
        for message in email_messages:
            try:
                # Build mail
                mail = Mail(
                    from_email=(message.from_email, "Mishra Consultancy"),
                    to_emails=[Email(to_email) for to_email in message.to],
                    subject=message.subject,
                    plain_text_content=message.body,
                )
                
                # Add HTML if available
                if message.content_subtype == 'html':
                    mail.plain_text_content = None
                    mail.html_content = message.body
                
                # Add attachments
                if message.attachments:
                    for filename, content, mimetype in message.attachments:
                        if isinstance(content, str):
                            content = content.encode('utf-8')
                        
                        attachment = Attachment(
                            FileContent(base64.b64encode(content).decode()),
                            FileName(filename),
                            FileType(mimetype),
                            Disposition('attachment')
                        )
                        mail.add_attachment(attachment)
                
                # Send
                response = sg.send(mail)
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Email sent to {message.to}: {response.status_code}")
                    msg_count += 1
                else:
                    logger.error(f"SendGrid error for {message.to}: {response.status_code}")
                    if not self.fail_silently:
                        logger.error(f"Response body: {response.body}")
                        
            except Exception as e:
                logger.error(f"Failed to send email: {str(e)}")
                if not self.fail_silently:
                    raise
        
        return msg_count
