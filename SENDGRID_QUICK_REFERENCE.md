# SENDGRID QUICK REFERENCE
## Mishra Consultancy - Setup & Usage Guide

---

## 🚀 QUICK START (5 Minutes)

### 1. Install Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### 2. Get SendGrid API Key
- Visit: https://sendgrid.com (Sign up if needed)
- Go to: Settings > API Keys
- Click: "Create API Key"
- Name it: `Law Firm Management System`
- Select scope: `mail.send` ✓
- Copy the key: `SG.xxx...`

### 3. Add to Environment
```bash
# Create .env file in project root
echo "SENDGRID_API_KEY=SG.your_key_here" > .env
```

### 4. Verify Sender Email
- Login to SendGrid Dashboard
- Go to: Settings > Sender Authentication
- Verify your domain OR add sender email
- Example: `noreply@mishra-consultancy.com`

### 5. Test It Works
```bash
python manage.py shell
```

```python
from cases.sendgrid_backend import send_sendgrid_email_with_retry

send_sendgrid_email_with_retry(
    subject="Test Email",
    message="Hello from SendGrid!",
    recipient_list=["your-email@example.com"]
)
# Should return: True
```

✅ **Done!** Emails now send via SendGrid

---

## 📧 SENDING EMAILS IN CODE

### Option 1: Simple Sync Send
```python
from cases.sendgrid_backend import send_sendgrid_email_with_retry

send_sendgrid_email_with_retry(
    subject="Hello",
    message="Your message here",
    recipient_list=["recipient@example.com"]
)
```

### Option 2: Async Send (Recommended)
```python
from cases.views import queue_mail_or_fallback

queue_mail_or_fallback(
    subject="Hello",
    message="Your message here",
    recipient_list=["recipient@example.com"]
)
```

### Option 3: With Attachments
```python
# PDF attachment example
pdf_content = b"...pdf content..."
attachment = ("receipt.pdf", pdf_content, "application/pdf")

send_sendgrid_email_with_retry(
    subject="Your Receipt",
    message="See attached",
    recipient_list=["recipient@example.com"],
    attachments=[attachment]
)
```

### Option 4: HTML Email
```python
send_sendgrid_email_with_retry(
    subject="Formatted Email",
    message="Plain text fallback",
    recipient_list=["recipient@example.com"],
    html_message="<h1>HTML Content Here</h1>"
)
```

---

## ⚙️ CONFIGURATION

### Environment Variables (.env)
```bash
# REQUIRED
SENDGRID_API_KEY=SG.your_actual_key_here

# OPTIONAL (defaults shown)
EMAIL_SEND_RETRIES=3
EMAIL_RETRY_DELAY_SECONDS=2
SENDGRID_MAX_RETRIES=3
DEFAULT_FROM_EMAIL=noreply@mishra-consultancy.com
```

### Settings in Django
File: `djangoProject/settings.py`

```python
EMAIL_BACKEND = 'cases.sendgrid_backend.SendGridEmailBackend'
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@...')
```

---

## 🔄 EMAIL FLOW IN YOUR APP

```
User Registration
├─ register_view() → queue_mail_or_fallback()
├─ Celery Task: send_email_task()
└─ SendGrid Backend → Email sent to user

Service Request
├─ ServiceRequest.save()
├─ trigger_receipt_automation()
├─ send_sendgrid_email_with_retry(attachments=[pdf])
└─ SendGrid Backend → Email with PDF receipt

Case Status Update
├─ Case.save() → Status changed
├─ send_sendgrid_email_with_retry()
└─ SendGrid Backend → Status email to client

Admin Action
├─ send_payment_email() action
├─ Loop: send_sendgrid_email_with_retry()
└─ SendGrid Backend → Payment reminder emails
```

---

## 🐛 TROUBLESHOOTING

### Email Not Sending?

**Check 1: API Key**
```python
import os
print(os.getenv('SENDGRID_API_KEY'))  # Should show SG.xxx
```

**Check 2: Django Settings**
```python
from django.conf import settings
print(settings.SENDGRID_API_KEY)  # Should show SG.xxx
print(settings.EMAIL_BACKEND)  # Should show sendgrid_backend
```

**Check 3: Sender Email Verified**
- Go to SendGrid Dashboard
- Settings → Sender Authentication
- Verify your domain/email is listed

**Check 4: Logs**
```python
import logging
logging.getLogger('cases.sendgrid_backend').setLevel(logging.DEBUG)
# Run your email code, check console for debug output
```

### Error: "SENDGRID_API_KEY not configured"
- Make sure `.env` file exists in project root
- Restart Django server after creating `.env`
- Run: `python manage.py shell` to test

### Error: "403 Forbidden"
- Check API key is valid (copy again from SendGrid)
- Check API key has `mail.send` scope
- Regenerate API key if too old

### Email in Spam Folder?
- Add SPF/DKIM records (SendGrid Sender Auth)
- Use verified domain in from email
- Include unsubscribe link in templates

### Celery Not Sending Async?
- Check Redis running: `redis-cli ping`
- Falls back to sync automatically
- Check Celery logs: `celery -A djangoProject worker -l debug`

---

## 📊 MONITORING

### SendGrid Dashboard
- **URL**: https://app.sendgrid.com
- **Monitor**: Email Activity, Bounces, Spam reports
- **Create**: Alerts for delivery issues
- **Export**: Analytics and delivery metrics

### Django Logs
```bash
# View logs in production
tail -f /var/log/django.log | grep sendgrid
```

### Admin Panel
- Cases → Case List → Select cases → "Send Payment Email"
- View delivery status in SendGrid dashboard

---

## 🔐 SECURITY BEST PRACTICES

✅ **DO:**
- Store API key in `.env` (environment variables)
- Regenerate API key after setup
- Use specific key scopes (`mail.send`)
- Monitor SendGrid dashboard
- Check `.gitignore` excludes `.env`

❌ **DON'T:**
- Commit API key to Git
- Share API key in messages/emails
- Use old/unused API keys
- Hardcode API key in Python files
- Use generic sender emails

---

## 📝 FILE REFERENCE

| File | Purpose |
|------|---------|
| `cases/sendgrid_backend.py` | SendGrid backend implementation |
| `cases/tasks.py` | Celery async task |
| `cases/views.py` | Email functions |
| `cases/models.py` | Auto-email notifications |
| `cases/admin.py` | Admin bulk actions |
| `djangoProject/settings.py` | Email config |
| `requirements.txt` | `sendgrid==6.11.0` |
| `.env.example` | Environment template |
| `SENDGRID_SETUP.md` | Full documentation |

---

## 💡 COMMON CODE PATTERNS

### In Views
```python
from cases.views import queue_mail_or_fallback

queue_mail_or_fallback(
    "Subject",
    "Message text",
    ["email@example.com"]
)
```

### In Models
```python
from cases.sendgrid_backend import send_sendgrid_email_with_retry

send_sendgrid_email_with_retry(
    subject="...",
    message="...",
    recipient_list=[self.user.email]
)
```

### In Admin
```python
from cases.sendgrid_backend import send_sendgrid_email_with_retry

for case in queryset:
    send_sendgrid_email_with_retry(
        subject="...",
        message="...",
        recipient_list=[case.client_profile.user.email]
    )
```

---

## 🆘 GET HELP

1. **Documentation**: See `SENDGRID_SETUP.md`
2. **Summary**: See `SENDGRID_MIGRATION_SUMMARY.md`
3. **SendGrid Docs**: https://docs.sendgrid.com/
4. **Django Email**: https://docs.djangoproject.com/en/5.0/topics/email/

---

## ✅ CHECKLIST BEFORE PRODUCTION

- [ ] API key regenerated (old key deleted)
- [ ] `.env` file in `.gitignore`
- [ ] Sender email verified in SendGrid
- [ ] Test email sent successfully
- [ ] Attachments working (PDF tests)
- [ ] Admin bulk email working
- [ ] Model auto-emails working
- [ ] Redis running (for Celery)
- [ ] Celery worker running
- [ ] Logs showing successful sends

---

**Last Updated**: June 13, 2026  
**Status**: Production Ready ✅

Questions? Check SENDGRID_SETUP.md for detailed info.
