import os
from pathlib import Path
from django.contrib.auth import get_user_model

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-insecure-key-for-local-only")
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cases',
    'widget_tweaks',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'djangoProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'djangoProject.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'cases:login'
LOGIN_REDIRECT_URL = 'cases:home'
LOGOUT_REDIRECT_URL = 'cases:home'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'anoshmishra77@gmail.com'
EMAIL_HOST_PASSWORD = 'gmbexgmjgdvpmlda'
DEFAULT_FROM_EMAIL = 'anoshmishra77@gmail.com'

ADMINS = [
    ('Anosh', 'anoshmishra77@gmail.com'),
    ('Consultancy', 'mishraconsultancy96@gmail.com'),
]

JAZZMIN_SETTINGS = {
    "site_title": "Mishra Consultancy",
    "site_header": "Mishra Consultancy",
    "site_brand": "MISHRA | COMMAND",
    "welcome_sign": "Mishra Consultancy: Legal & Financial Command Center",
    "copyright": "Mishra Consultancy Ltd",
    "search_model": ["auth.User", "cases.Case"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "auth.User"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user-shield",
        "cases.Case": "fas fa-file-signature",
        "cases.Client": "fas fa-address-book",
        "cases.Lawyer": "fas fa-user-tie",
        "cases.UserProfile": "fas fa-id-card",
        "cases.Inquiry": "fas fa-envelope-open-text",
        "cases.ServiceRequest": "fas fa-concierge-bell",
    },
    "order_with_respect_to": ["cases", "auth"],
    "custom_css": "css/ancient_modern.css",
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": "darkly",
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
}

if os.getenv("RESET_ADMIN") == "True":
    User = get_user_model()
    User.objects.filter(username="admin").delete()
    User.objects.filter(username="abinashmishra").delete()
    User.objects.create_superuser(
        username="admin",
        email="anoshmishraa@gmail.com",
        password="9777233158@Anosh"
    )
    User.objects.create_superuser(
        username="abinashmishra",
        email="mishraconsultancy96@gmail.com",
        password="7008898676@Abinash"
    )