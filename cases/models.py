import random
import datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from .utils import generate_service_pdf

class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='N')
    profile_pic = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.png', blank=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    old_email_verified = models.BooleanField(default=False)
    unique_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.save()
        return self.otp

    def save(self, *args, **kwargs):
        if not self.unique_id:
            year = datetime.date.today().year
            last_profile = UserProfile.objects.filter(
                unique_id__startswith=f"MC-{year}"
            ).order_by('-unique_id').first()
            
            if last_profile and last_profile.unique_id:
                try:
                    last_num = int(last_profile.unique_id.split('-')[-1])
                    new_num = str(last_num + 1).zfill(4)
                except (ValueError, IndexError):
                    new_num = "0001"
            else:
                new_num = "0001"
            
            self.unique_id = f"MC-{year}-{new_num}"
            
        super(UserProfile, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.unique_id} - {self.user.first_name} {self.user.last_name}"

class Lawyer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    specialization = models.CharField(max_length=100, default="General Counsel")

    def __str__(self):
        return f"Adv. {self.first_name} {self.last_name}"

class Client(models.Model):
    profile = models.OneToOneField(UserProfile, on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Inquiry(models.Model):
    STATUS_CHOICES = (
        ('NEW', 'New Inquiry'),
        ('CONTACTED', 'Contacted/Follow-up'),
        ('CONVERTED', 'Converted to Client'),
        ('REJECTED', 'Spam/Rejected'),
    )

    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    subject = models.CharField(max_length=100)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Inquiries"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.pk:
            old_status = Inquiry.objects.get(pk=self.pk).status
            if old_status != self.status and self.status == 'CONTACTED':
                subject = f"Mishra Consultancy: Response to your {self.subject} inquiry"
                message = f"""
Hello {self.full_name},

Our legal team has reviewed your inquiry regarding {self.subject}.
                
A strategist will call you shortly at {self.phone} to discuss the next steps.

Regards,
Admin Command Center
Mishra Consultancy Ltd.
                """
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.email], fail_silently=True)
                except Exception:
                    pass
        super(Inquiry, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.subject}"

class ServiceRequest(models.Model):
    SERVICE_CHOICES = (
        ('GST', 'GST Services'),
        ('TAX', 'Income Tax'),
        ('LEGAL', 'Legal Documentation'),
        ('NOTARY', 'Notary & Affidavit'),
    )
    
    STATUS_CHOICES = (
        ('REQUESTED', 'New Request Received'),
        ('APPROVED', 'Approved by Admin'),
        ('IN_PROGRESS', 'Work Undergoing'),
        ('VERIFICATION', 'Document Verification'),
        ('FULFILLED', 'Service Completed'),
        ('REJECTED', 'Rejected/Cancelled'),
    )
    
    client = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='service_requests')
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    sub_service = models.CharField(max_length=100) 
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='REQUESTED') 
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Enter amount before marking as Fulfilled")
    is_paid = models.BooleanField(default=False)

    def trigger_receipt_automation(self):
        try:
            pdf_io = generate_service_pdf(self, status="COMPLETED")
            subject = f"OFFICIAL RECEIPT: {self.sub_service} - Mishra Consultancy"
            body = (
                f"Dear {self.client.user.first_name},\n\n"
                f"Your service request for '{self.sub_service}' has been successfully fulfilled.\n"
                f"Total recorded charges: ₹{self.amount}\n\n"
                f"Please find your official computer-generated receipt attached to this email.\n\n"
                f"Regards,\nAdmin Command Center\nMishra Consultancy"
            )
            email = EmailMessage(
                subject, 
                body, 
                settings.DEFAULT_FROM_EMAIL, 
                [self.client.user.email]
            )
            email.attach(f"Receipt_{self.id}.pdf", pdf_io.getvalue(), "application/pdf")
            email.send()
            print("SUCCESS: Receipt Email Sent!") 
        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = ServiceRequest.objects.get(pk=self.pk)
            if old_instance.status != 'FULFILLED' and self.status == 'FULFILLED':
                super(ServiceRequest, self).save(*args, **kwargs)
                self.trigger_receipt_automation()
                return 

            elif old_instance.status != self.status:
                subject = f"Mishra Consultancy: Update on {self.sub_service}"
                message = (
                    f"Hello {self.client.user.first_name},\n\n"
                    f"The status of your service request '{self.sub_service}' has been updated to: {self.get_status_display()}.\n\n"
                    f"Please visit your dashboard for further details.\n\n"
                    f"Regards,\nMishra Consultancy Admin"
                )
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.client.user.email], fail_silently=True)
                except Exception:
                    pass
        super(ServiceRequest, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.client.unique_id} - {self.sub_service} ({self.get_status_display()})"

class Case(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Documents Pending'),
        ('RECEIVED', 'Documents Received'),
        ('IN_PROGRESS', 'Filing in Progress'),
        ('REVIEW', 'Under Review'),
        ('COMPLETED', 'Completed/Filed'),
        ('CLOSED', 'Closed/Archived'),
    )
    
    title = models.CharField(max_length=100, help_text="e.g., GST Q1 Filing")
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_status = models.BooleanField(default=False, verbose_name="Is Paid?")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    client_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='cases')
    lawyer = models.ForeignKey(Lawyer, on_delete=models.SET_NULL, null=True)
    document = models.FileField(upload_to='client_docs/%Y/%m/', blank=True, null=True)
    client_notes = models.TextField(blank=True, null=True, help_text="Instructions for the lawyer.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.pk:
            old_case = Case.objects.get(pk=self.pk)
            if old_case.status != self.status:
                subject = f"Legal Filing Update: {self.title}"
                message = (
                    f"Dear {self.client_profile.user.first_name},\n\n"
                    f"Your filing '{self.title}' status has changed to: {self.get_status_display()}.\n\n"
                    f"Regards,\nMishra Consultancy"
                )
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.client_profile.user.email], fail_silently=True)
                except Exception:
                    pass
        super(Case, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.client_profile.unique_id}"

    @property
    def progress_percentage(self):
        progress_map = {
            'PENDING': 10,
            'RECEIVED': 30,
            'IN_PROGRESS': 60,
            'REVIEW': 85,
            'COMPLETED': 100,
            'CLOSED': 100,
        }
        return progress_map.get(self.status, 0)