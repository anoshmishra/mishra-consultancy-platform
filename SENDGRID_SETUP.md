# SENDGRID EMAIL CONFIGURATION GUIDE
# Mishra Consultancy - Law Firm Management System

## Overview
This project has been converted from Google SMTP to SendGrid for reliable, scalable email delivery. SendGrid provides enterprise-grade email infrastructure with high deliverability rates, comprehensive analytics, and advanced features.

---

## SETUP INSTRUCTIONS

### Step 1: Install Dependencies
```bash
pip install --upgrade -r requirements.txt
```

The `sendgrid==6.11.0` package will be installed automatically.

---

### Step 2: Configure SendGrid API Key

#### Option A: Using Environment Variables (Recommended)

Create a `.env` file in the project root directory with the following content:

```bash
# SendGrid Configuration
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx

# Optional: Override email retry settings (defaults shown)
EMAIL_SEND_RETRIES=3
EMAIL_RETRY_DELAY_SECONDS=2
SENDGRID_MAX_RETRIES=3

# Optional: Override sender email (must be verified in SendGrid)
DEFAULT_FROM_EMAIL=noreply@mishra-consultancy.com

# Other Django settings
SECRET_KEY=your-secret-key-here
DEBUG=False
```

#### Option B: Using Render/Heroku Environment Variables

For production deployment on Render or Heroku:

1. Go to your deployment dashboard
2. Navigate to "Environment Variables" or "Config Vars"
3. Add: `SENDGRID_API_KEY` = `SG.your_actual_api_key_here`

---

### Step 3: Verify SendGrid Sender Email

Before sending emails, you must verify your sender email address in SendGrid:

1. Go to [SendGrid Dashboard](https://app.sendgrid.com)
2. Navigate to **Settings > Sender Authentication**
3. Add and verify your sender domain (e.g., `mishra-consultancy.com`)
4. Or add specific sender emails

**Important:** The `DEFAULT_FROM_EMAIL` in your settings must be a verified sender.

---

### Step 4: Update Your Application

The following files have been automatically updated to use SendGrid:

- `djangoProject/settings.py` - Email backend configuration
- `cases/sendgrid_backend.py` - Custom SendGrid backend (NEW)
- `cases/tasks.py` - Celery async email sending
- `cases/views.py` - All email sending functions
- `cases/models.py` - Model email notifications
- `cases/admin.py` - Admin panel email actions
- `requirements.txt` - Added sendgrid package

---

## SENDGRID API KEY MANAGEMENT

### ⚠️ SECURITY ALERT
The API key provided in your message MUST be regenerated immediately after setup for security:

1. Log in to [SendGrid Dashboard](https://app.sendgrid.com)
2. Go to **Settings > API Keys**
3. Find the old key and delete it
4. Create a new API key with:
   - **Name**: `Law Firm Management System`
   - **Scopes**: 
     - `mail.send` ✓ (Required)
     - `mail.template_engine.read` (Optional)
     - `stats.read` (Optional)
5. Copy the new key and update your `.env` file or deployment variables

### Best Practices:
- ✅ Store API keys in environment variables only
- ✅ Never commit API keys to version control
- ✅ Rotate keys regularly (every 3-6 months)
- ✅ Use specific key scopes (principle of least privilege)
- ✅ Monitor API key usage in SendGrid dashboard

---

## EMAIL SENDING ARCHITECTURE

### Three-Tier Email System:

#### 1. **Synchronous (Fallback)**
```python
from cases.sendgrid_backend import send_sendgrid_email_with_retry

send_sendgrid_email_with_retry(
    subject="Your Subject",
    message="Your message",
    recipient_list=["user@example.com"],
    fail_silently=False
)
```

#### 2. **Asynchronous (Celery - Recommended)**
```python
from cases.views import queue_mail_or_fallback

queue_mail_or_fallback(
    subject="Your Subject",
    message="Your message",
    recipient_list=["user@example.com"],
    fail_silently=False
)
```
- Queues email in Celery (if Redis is available)
- Falls back to sync SendGrid if queue fails

#### 3. **With Attachments (PDFs, Documents)**
```python
from cases.sendgrid_backend import send_sendgrid_email_with_retry

pdf_content = generate_pdf()  # Your PDF generation
attachment = ("filename.pdf", pdf_content, "application/pdf")

send_sendgrid_email_with_retry(
    subject="Your Subject",
    message="Your message",
    recipient_list=["user@example.com"],
    attachments=[attachment]
)
```

---

## EMAIL SENDING LOCATIONS IN YOUR APP

### Registration & Verification
- **File**: `cases/views.py`
- **Functions**: 
  - `register_view()` - Send OTP
  - `verify_otp_view()` - Send welcome email
  - `resend_otp_view()` - Resend verification code

### Inquiry Management
- **File**: `cases/views.py`
- **Function**: `HomeView.post()` - Send inquiry acknowledgment
- **File**: `cases/models.py`
- **Model**: `Inquiry.save()` - Send response when status changes to CONTACTED

### Client Communications
- **File**: `cases/models.py`
- **Model**: `ServiceRequest.save()` - Status update notifications
- **Model**: `ServiceRequest.trigger_receipt_automation()` - PDF receipt with attachment
- **Model**: `Case.save()` - Filing status updates

### Admin Actions
- **File**: `cases/admin.py`
- **Action**: `send_payment_email()` - Bulk payment reminders

### Profile Management
- **File**: `cases/views.py`
- **Functions**:
  - `request_profile_edit()` - Send edit verification code
  - `start_filing_view()` - Send job request notification

---

## RETRY LOGIC & ERROR HANDLING

### Automatic Retries
Each email attempt includes:
- **Retries**: 3 attempts by default (configurable)
- **Delay**: Exponential backoff (2, 4, 6 seconds)
- **Logging**: Detailed error logs for debugging

### Configuration
```python
# In .env or settings.py
EMAIL_SEND_RETRIES=3                # Number of retry attempts
EMAIL_RETRY_DELAY_SECONDS=2         # Base delay between retries
SENDGRID_MAX_RETRIES=3              # Max retries for SendGrid backend
```

### Error Scenarios Handled:
- ✅ Network timeouts
- ✅ SendGrid API rate limiting
- ✅ Invalid recipient emails
- ✅ Attachment encoding errors
- ✅ Celery queue unavailability

---

## MONITORING & ANALYTICS

### SendGrid Dashboard Features:
1. **Email Activity** - Real-time email tracking
2. **Bounce Management** - Track soft/hard bounces
3. **Spam Reports** - Monitor complaint rate
4. **Unsubscribe Management** - Compliance tracking
5. **Analytics** - Open rates, click rates, delivery metrics

### Access Dashboard:
- URL: https://app.sendgrid.com
- Monitor email performance regularly
- Set up alerts for delivery issues

---

## TROUBLESHOOTING

### Issue: "SENDGRID_API_KEY not configured"
**Solution**: 
- Check `.env` file exists in project root
- Ensure `SENDGRID_API_KEY` is set
- Reload Django server: `python manage.py runserver`

### Issue: "Email sending fails with 403 error"
**Solution**:
- Verify API key is valid and not expired
- Check API key has `mail.send` scope
- Ensure sender email is verified in SendGrid

### Issue: "Email marked as spam"
**Solution**:
- Set up SPF/DKIM authentication in SendGrid
- Use verified domain sender instead of generic email
- Include unsubscribe link in email templates

### Issue: "Celery queue not picking up emails"
**Solution**:
- Check Redis is running: `redis-cli ping` (should return PONG)
- Verify Celery worker is running
- Check Celery logs for errors
- Falls back to sync SendGrid automatically if Celery fails

### Issue: "Attachment not sending"
**Solution**:
- Verify file content is binary or bytes
- Check file size < 25MB (SendGrid limit)
- Ensure MIME type is correct
- Check logs for encoding errors

---

## TESTING YOUR SETUP

### Quick Test Script
Create `test_sendgrid.py`:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from cases.sendgrid_backend import send_sendgrid_email_with_retry

# Test basic email
result = send_sendgrid_email_with_retry(
    subject="SendGrid Test Email",
    message="This is a test email from Mishra Consultancy.",
    recipient_list=["your-test-email@example.com"],
    fail_silently=False
)

print(f"Email sent successfully: {result}")
```

Run test:
```bash
python test_sendgrid.py
```

---

## PRODUCTION DEPLOYMENT CHECKLIST

- [ ] API key regenerated and old key deleted
- [ ] `.env` file NOT committed to Git (check `.gitignore`)
- [ ] Sender domain verified in SendGrid
- [ ] SPF/DKIM records configured
- [ ] Environment variables set on deployment platform
- [ ] Redis running for Celery (if using async emails)
- [ ] Email templates reviewed for branding
- [ ] Test email sent successfully
- [ ] Admin email notifications enabled
- [ ] Monitor SendGrid dashboard for bounces/complaints

---

## SUPPORT & RESOURCES

- **SendGrid Documentation**: https://docs.sendgrid.com/
- **SendGrid API Reference**: https://docs.sendgrid.com/api-reference/
- **Python SendGrid Library**: https://github.com/sendgrid/sendgrid-python
- **Django Email Documentation**: https://docs.djangoproject.com/en/5.0/topics/email/

---

## MIGRATION NOTES

### What Changed:
- ❌ Removed Google SMTP configuration (no longer needed)
- ❌ Removed `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
- ✅ Added SendGrid backend
- ✅ Enhanced retry logic with exponential backoff
- ✅ Better attachment handling with base64 encoding
- ✅ Comprehensive error logging
- ✅ Improved reliability with async/sync fallback

### Backward Compatibility:
- All existing email-sending code continues to work
- New features available without code changes
- Graceful fallback from Celery to sync if needed

---

**Last Updated**: June 13, 2026
**Migration Status**: Complete ✅
**Email Backend**: SendGrid 6.11.0
**Python Version**: 3.10+
**Django Version**: 5.0.4
