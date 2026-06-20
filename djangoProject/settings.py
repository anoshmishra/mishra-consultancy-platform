import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent


def env_value(name, default=""):
    value = os.getenv(name)
    if value is None:
        for key, env_item in os.environ.items():
            if key.strip() == name:
                value = env_item
                break
    if value is None:
        return default

    value = str(value).strip().strip('"').strip("'")
    if value.startswith("export "):
        value = value.replace("export ", "", 1).strip()
    prefix = f"{name}="
    if value.startswith(prefix):
        value = value.replace(prefix, "", 1).strip().strip('"').strip("'")
    return value


SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-&r^qatb7=!fk#yp88i3y^j_&^w3wee#k9u=hb^ake+^ywu9n0j")
DEBUG = env_value("DEBUG", "True") == "True"

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    "https://mishra-consultancy-platform.onrender.com"
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = env_value("SECURE_SSL_REDIRECT", "False") == "True"

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

STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
WHITENOISE_MANIFEST_STRICT = False

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(env_value("MEDIA_ROOT", str(BASE_DIR / "media")))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'cases:login'
LOGIN_REDIRECT_URL = 'cases:home'
LOGOUT_REDIRECT_URL = 'cases:home'

# --- EMAIL CONFIGURATION ---
# SendGrid is primary. SMTP is a fallback when SENDGRID_API_KEY is not set.
EMAIL_BACKEND = 'cases.sendgrid_backend.SendGridEmailBackend'
SENDGRID_API_KEY = env_value('SENDGRID_API_KEY', '')

EMAIL_HOST = env_value("EMAIL_HOST", "")
EMAIL_PORT = int(env_value("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_value("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = env_value("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_HOST_USER = env_value("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env_value("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = int(env_value("EMAIL_TIMEOUT", "30"))

# Email retry configuration for resilience
EMAIL_SEND_RETRIES = int(env_value("EMAIL_SEND_RETRIES", "3"))
EMAIL_RETRY_DELAY_SECONDS = float(env_value("EMAIL_RETRY_DELAY_SECONDS", "2"))
SENDGRID_MAX_RETRIES = int(env_value("SENDGRID_MAX_RETRIES", "3"))

# Default sender email - must be verified in SendGrid or match SMTP sender.
# Prefer an explicit SendGrid sender alias so Render env vars can stay obvious.
SENDGRID_FROM_EMAIL = env_value("SENDGRID_FROM_EMAIL", "")
SENDGRID_FROM_NAME = env_value("SENDGRID_FROM_NAME", "Mishra Consultancy")
DEFAULT_FROM_EMAIL = env_value("DEFAULT_FROM_EMAIL", SENDGRID_FROM_EMAIL or EMAIL_HOST_USER or "")
SERVER_EMAIL = DEFAULT_FROM_EMAIL or "webmaster@localhost"

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "False") == "True"
EMAIL_USE_CELERY = env_value("EMAIL_USE_CELERY", "False").lower() == "true"

ADMIN_EMAIL_1 = env_value("ADMIN_EMAIL_1", "anoshmishra77@gmail.com")
ADMIN_EMAIL_2 = env_value("ADMIN_EMAIL_2", "mishraconsultancy96@gmail.com")
ADMINS = [
    ('Anosh', ADMIN_EMAIL_1),
    ('Consultancy', ADMIN_EMAIL_2),
]
ADMIN_NOTIFICATION_EMAILS = [email for _, email in ADMINS if email]

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
