import time
import logging
from celery import shared_task
from django.conf import settings
from .sendgrid_backend import send_sendgrid_email_with_retry

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_email_task(self, subject, message, recipient_list, fail_silently=False, 
                    html_message=None, from_email=None, attachments=None):
    """
    Celery task to send emails asynchronously via SendGrid
    
    Args:
        subject: Email subject
        message: Plain text message body
        recipient_list: List of recipient email addresses
        fail_silently: Whether to suppress exceptions
        html_message: HTML version of the email
        from_email: Override from email address
        attachments: List of (filename, content, mimetype) tuples
    
    Returns:
        True if successful, False otherwise
    """
    retries = max(1, int(getattr(settings, "EMAIL_SEND_RETRIES", 3)))
    retry_delay = float(getattr(settings, "EMAIL_RETRY_DELAY_SECONDS", 2))
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            success = send_sendgrid_email_with_retry(
                subject=subject,
                message=message,
                recipient_list=recipient_list,
                fail_silently=fail_silently,
                html_message=html_message,
                from_email=from_email,
                attachments=attachments,
                max_retries=1,  # Celery will handle main retries
            )
            
            if success:
                logger.info(
                    f"Async SendGrid email sent successfully for subject '{subject}' "
                    f"(attempt {attempt}/{retries})"
                )
                return True
            else:
                logger.warning(
                    f"Async SendGrid attempt {attempt}/{retries} returned False for subject '{subject}'"
                )
                
        except Exception as exc:
            last_error = exc
            logger.warning(
                f"Async SendGrid attempt {attempt}/{retries} failed for subject '{subject}': {str(exc)}"
            )
            if attempt < retries:
                time.sleep(retry_delay * attempt)
                continue

    if last_error and not fail_silently:
        raise self.retry(exc=last_error)

    logger.error(f"Failed to send async email after {retries} attempts: {subject}")
    return False

