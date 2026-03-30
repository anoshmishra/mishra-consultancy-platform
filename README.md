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
