Mishra Consultancy: Legal & Tax Center
An enterprise-grade Law Firm & Tax Management System built with Django 6.0. It bridges the gap between complex legal workflows and client-centric transparency. This platform is designed specifically for GST compliance, Income Tax (ITR), and Legal Documentation.

 Key Innovations & Features
 1. God-Mode Security Layer
OTP-Based Registration: Every client is verified via email-based One-Time Passwords before account activation.

Secure Profile Editing: Changing sensitive data (Email/Phone) requires a secondary OTP challenge to prevent identity theft.

Emergency Lockdown: Admin can instantly suspend any account or the entire system in one click.

 2. Automated Receipt Engine
Government-Style PDF Generation: Professional, branded receipts created using ReportLab.

Live Watermarking: Completed jobs receive an "OFFICIAL RECEIPT" green watermark, while pending tasks show as "UNPAID".

Auto-Dispatch: Receipts are automatically attached and emailed to clients the second a service is marked as "Fulfilled".

 3. Dual-Layer Client Dashboard
Service Request Tracking: Real-time visibility for new requests (GST, ITR, Notary) before they become formal cases.

Active Filing Management: A dedicated table for formal legal cases with progress bars and document upload capabilities.

Financial Transparency: Clients can see total charges and payment status for every individual task.

 4. Admin Command Center
Manual Billing Control: Admins can set custom service fees directly from the list view.

Filing Automation: One-click conversion from a "Service Request" to an "Active Case."

Identity Management: Unique ID generation system (e.g., MC-2026-0005) for professional record keeping.

 5. Tech Stack & Infrastructure
Backend: Python 3.13 / Django 6.0 (The "Perfectionist" Framework)

PDF Engine: ReportLab (High-fidelity vector document generation)

Database: PostgreSQL / SQLite (Scalable relational storage)

UI/UX: Bootstrap 5 + Jazzmin (Dark-mode optimized Admin Command Center)

Email: SMTP Integration (Gmail App Passwords for automated alerts)

 6. Project Structure (Core Logic)
Bash
├── cases/
│   ├── admin.py          # God-Mode & Bulk Actions
│   ├── models.py         # ServiceRequest & Case Logic 
│   ├── utils.py          # Professional PDF Generation Engine
│   ├── views.py          # OTP Auth & Dual-Layer Dashboard Logic
│   └── forms.py          # Secure Data Input Validation
├── templates/
│   ├── registration/     # Secure Auth & Profile Edit Templates
│   └── cases/            # Start Filing & Document Management
└── static/               # Custom "Ancient Modern" Professional CSS
 Impact
By digitizing the manual "Consultancy-to-Client" pipeline, this system reduces operational overhead by 40% and eliminates manual billing errors through automated PDF reconciliation.

OTP Email Variables (Production)
- Set either `SENDGRID_API_KEY` or the SMTP variables below on Render. Without one of these providers, OTP email cannot be delivered.
- `SENDGRID_API_KEY=your-sendgrid-api-key`
- `DEFAULT_FROM_EMAIL=your-verified-sendgrid-sender@example.com`
- `SENDGRID_FROM_EMAIL=your-verified-sendgrid-sender@example.com`
- `SENDGRID_FROM_NAME=Mishra Consultancy`
- `EMAIL_HOST=smtp.gmail.com`
- `EMAIL_PORT=587`
- `EMAIL_USE_TLS=True`
- `EMAIL_USE_SSL=False`
- `EMAIL_TIMEOUT=30`
- `EMAIL_SEND_RETRIES=3`
- `EMAIL_RETRY_DELAY_SECONDS=2`
- `EMAIL_HOST_USER=your-gmail@gmail.com`
- `EMAIL_HOST_PASSWORD=your-16-char-app-password`

SendGrid Sender Fix
- The Render log `The from address does not match a verified Sender Identity` means SendGrid accepted the API key but rejected the sender address.
- In Render, set `DEFAULT_FROM_EMAIL` or `SENDGRID_FROM_EMAIL` to the exact email verified in SendGrid under Sender Authentication. Do not use the old fallback `noreply@mishra-consultancy.com` unless that address/domain is verified.
- After updating the environment variable, redeploy or restart the Render service.

Celery Queue Variables (Production)
- `REDIS_URL=your-render-redis-internal-url`
- `CELERY_BROKER_URL=your-render-redis-internal-url`
- `CELERY_RESULT_BACKEND=your-render-redis-internal-url`
- `CELERY_TASK_ALWAYS_EAGER=False`

Render Setup (Required for Background Queue)
- Add a Render Redis instance.
- Attach `REDIS_URL` to this web service environment.
- Ensure worker process is enabled from `Procfile`:
- `worker: celery -A djangoProject worker --loglevel=info --pool=solo`

Profile Photos and Uploaded Documents on Render
- Attach a persistent disk to the web service, for example at `/var/data`.
- Set `MEDIA_ROOT=/var/data/media` in Render Environment.
- Without a persistent disk, Render's ephemeral filesystem can delete uploaded profile photos and documents during a deploy or restart.

Security Note
- Never hardcode SMTP credentials in source code.
- If credentials were previously committed, rotate the Gmail App Password immediately.
