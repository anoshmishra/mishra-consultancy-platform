from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Inquiry
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


class InquirySubmissionTests(TestCase):
    def test_homepage_inquiry_is_saved_when_admin_email_fails(self):
        with patch("cases.views.queue_mail_or_fallback", side_effect=RuntimeError("mail down")):
            response = self.client.post(
                reverse("cases:home"),
                {
                    "full_name": "Anosh Mishra",
                    "phone": "8984454339",
                    "client_email": "lead@example.com",
                    "subject": "TAX",
                },
            )

        self.assertRedirects(response, reverse("cases:home"))
        inquiry = Inquiry.objects.get(email="lead@example.com")
        self.assertEqual(inquiry.full_name, "Anosh Mishra")
        self.assertEqual(inquiry.subject, "TAX")
        self.assertEqual(inquiry.status, "NEW")

    def test_homepage_inquiry_rejects_invalid_email(self):
        response = self.client.post(
            reverse("cases:home"),
            {
                "full_name": "Bad Lead",
                "phone": "8984454339",
                "client_email": "not-an-email",
                "subject": "TAX",
            },
        )

        self.assertRedirects(response, reverse("cases:home"))
        self.assertFalse(Inquiry.objects.filter(full_name="Bad Lead").exists())
