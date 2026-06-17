from django.conf import settings
from django.core.checks import Error, Tags, register
from django.core.exceptions import ImproperlyConfigured

from .sendgrid_backend import validate_sendgrid_sender


@register(Tags.security, deploy=True)
def sendgrid_sender_check(app_configs, **kwargs):
    if not getattr(settings, "SENDGRID_API_KEY", ""):
        return []

    try:
        validate_sendgrid_sender()
    except ImproperlyConfigured as exc:
        return [
            Error(
                str(exc),
                hint=(
                    "In Render Environment, set DEFAULT_FROM_EMAIL or "
                    "SENDGRID_FROM_EMAIL to the verified Single Sender or "
                    "authenticated domain address in your SendGrid account."
                ),
                id="cases.E001",
            )
        ]

    return []
