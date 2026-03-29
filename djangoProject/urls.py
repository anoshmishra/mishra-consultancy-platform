"""
URL configuration for djangoProject project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # 1. Django Admin Panel
    path('admin/', admin.site.urls),

    # 2. Built-in Auth (Required for Password Reset Emails)
    # This automatically maps paths like /accounts/password_reset/ 
    # to your templates/registration/password_reset_form.html
    path('accounts/', include('django.contrib.auth.urls')),

    # 3. Your Main App (Mishra Consultancy)
    # The empty string '' means this is the homepage.
    path('', include('cases.urls', namespace='cases')),
]