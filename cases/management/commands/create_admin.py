from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = "Create admin users"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        admin_username = os.getenv("ADMIN_USERNAME")
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_password = os.getenv("ADMIN_PASSWORD")

        admin2_username = os.getenv("ADMIN2_USERNAME")
        admin2_email = os.getenv("ADMIN2_EMAIL")
        admin2_password = os.getenv("ADMIN2_PASSWORD")

        if admin_username and not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password
            )

        if admin2_username and not User.objects.filter(username=admin2_username).exists():
            User.objects.create_superuser(
                username=admin2_username,
                email=admin2_email,
                password=admin2_password
            )

        self.stdout.write(self.style.SUCCESS("Admins created successfully"))