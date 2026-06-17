from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from .sendgrid_backend import send_sendgrid_email_with_retry, validate_sendgrid_sender


class SendGridConfigurationTests(SimpleTestCase):
    @override_settings(
        SENDGRID_API_KEY="SG.fake",
        DEFAULT_FROM_EMAIL="noreply@mishra-consultancy.com",
    )
    def test_placeholder_sender_is_rejected_when_sendgrid_enabled(self):
        with self.assertRaises(ImproperlyConfigured):
            validate_sendgrid_sender()

    @override_settings(
        SENDGRID_API_KEY="SG.fake",
        DEFAULT_FROM_EMAIL="verified@example.org",
    )
    def test_non_placeholder_sender_is_allowed(self):
        self.assertEqual(validate_sendgrid_sender(), "verified@example.org")

    @override_settings(EMAIL_SEND_RETRIES=3, EMAIL_RETRY_DELAY_SECONDS=0)
    def test_non_retryable_sendgrid_error_is_not_retried(self):
        class ForbiddenSenderError(Exception):
            status_code = 403
            body = (
                b'{"errors":[{"message":"The from address does not match a '
                b'verified Sender Identity."}]}'
            )

        with patch(
            "cases.sendgrid_backend.send_sendgrid_email",
            side_effect=ForbiddenSenderError("HTTP Error 403: Forbidden"),
        ) as mocked_send:
            with patch("time.sleep") as mocked_sleep:
                sent = send_sendgrid_email_with_retry(
                    subject="Verification Code",
                    message="OTP: 123456",
                    recipient_list=["client@example.org"],
                    fail_silently=True,
                    max_retries=3,
                )

        self.assertFalse(sent)
        self.assertEqual(mocked_send.call_count, 1)
        mocked_sleep.assert_not_called()
