import time
import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_email_task(self, subject, message, recipient_list, fail_silently=False):
    retries = max(1, int(getattr(settings, "EMAIL_SEND_RETRIES", 3)))
    retry_delay = float(getattr(settings, "EMAIL_RETRY_DELAY_SECONDS", 2))
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=fail_silently,
            )
            return True
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Async SMTP attempt %s/%s failed for subject '%s': %s",
                attempt,
                retries,
                subject,
                exc,
            )
            if attempt < retries:
                time.sleep(retry_delay * attempt)

    if last_error and not fail_silently:
        raise self.retry(exc=last_error)

    return False
