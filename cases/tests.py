import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .models import Inquiry, UserProfile
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
    def test_homepage_inquiry_saves_and_emails_client_and_admins(self):
        with patch("cases.views.send_immediate_mail", return_value=True) as mocked_mail:
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
        self.assertEqual(mocked_mail.call_count, 2)

        client_call = mocked_mail.call_args_list[0].kwargs
        admin_call = mocked_mail.call_args_list[1].kwargs
        self.assertEqual(client_call["recipient_list"], ["lead@example.com"])
        self.assertEqual(client_call["subject"], "Inquiry Registered - Mishra Consultancy")
        self.assertIn("MC-INQ-", client_call["message"])
        self.assertIn("Taxation (GST / Income Tax)", client_call["message"])
        self.assertIn("anoshmishra77@gmail.com", admin_call["recipient_list"])
        self.assertEqual(admin_call["subject"], "NEW INQUIRY: Taxation (GST / Income Tax)")

    def test_homepage_inquiry_is_saved_when_confirmation_email_fails(self):
        with patch("cases.views.send_immediate_mail", side_effect=[False, True]) as mocked_mail:
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
        self.assertTrue(Inquiry.objects.filter(email="lead@example.com").exists())
        self.assertEqual(mocked_mail.call_count, 2)

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


class ProtectedMediaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="test-password",
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            phone="9999999999",
        )

    def test_profile_photo_is_served_to_its_owner(self):
        with tempfile.TemporaryDirectory() as media_root:
            photo_path = Path(media_root) / "profile_pics" / "avatar.png"
            photo_path.parent.mkdir(parents=True)
            photo_path.write_bytes(b"test-image-content")
            self.profile.profile_pic.name = "profile_pics/avatar.png"
            self.profile.save(update_fields=["profile_pic"])

            self.client.force_login(self.user)
            with override_settings(MEDIA_ROOT=Path(media_root)):
                response = self.client.get("/media/profile_pics/avatar.png")

            self.assertEqual(response.status_code, 200)

    def test_profile_photo_is_not_served_to_another_client(self):
        other_user = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="test-password",
        )
        UserProfile.objects.create(user=other_user, phone="8888888888")
        self.profile.profile_pic.name = "profile_pics/avatar.png"
        self.profile.save(update_fields=["profile_pic"])

        self.client.force_login(other_user)
        response = self.client.get("/media/profile_pics/avatar.png")

        self.assertEqual(response.status_code, 404)
