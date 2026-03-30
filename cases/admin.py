import random
import datetime
from django.contrib import admin, messages
from django.utils.html import format_html, mark_safe
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import Client, Lawyer, Case, UserProfile, Inquiry, ServiceRequest

# --- 1. GLOBAL EMERGENCY & BULK ACTIONS ---

@admin.action(description="🛑 SECURITY: Emergency Account Lockdown")
def suspend_accounts(modeladmin, request, queryset):
    """Instantly disables accounts and kicks users out of the session."""
    count = queryset.update(is_active=False)
    messages.warning(request, f"GOD-MODE: {count} accounts have been locked out of the system.")

@admin.action(description="✅ SECURITY: Restore System Access")
def activate_accounts(modeladmin, request, queryset):
    """Restores login access for selected users."""
    count = queryset.update(is_active=True)
    messages.success(request, f"GOD-MODE: {count} accounts restored.")

@admin.action(description="📧 Send Payment Request & Invoice Alert")
def send_payment_email(modeladmin, request, queryset):
    """
    Loops through selected cases and sends an automated email regarding pending payments.
    """
    count = 0
    for case in queryset:
        if hasattr(case, 'client_profile') and case.client_profile.user:
            recipient_email = case.client_profile.user.email
            recipient_name = case.client_profile.user.first_name
            if recipient_email:
                subject = f"Invoice Alert: {case.title} - Mishra Consultancy"
                message = (
                    f"Dear {recipient_name},\n\n"
                    f"Action Required for Case: {case.title}\n"
                    f"Consultancy ID: {case.client_profile.unique_id}\n"
                    f"Total Amount Due: ₹{case.amount_due}\n\n"
                    f"Please settle the payment to proceed with the filing.\n\n"
                    f"Regards,\nAdmin Command Center\nMishra Consultancy"
                )
                try:
                    send_mail(
                        subject, 
                        message, 
                        settings.DEFAULT_FROM_EMAIL, 
                        [recipient_email], 
                        fail_silently=False
                    )
                    count += 1
                except Exception as e:
                    messages.error(request, f"Failed to send to {recipient_name}: {str(e)}")
            else:
                messages.warning(request, f"Skipped {recipient_name} - No email found.")
        else:
            messages.warning(request, f"Skipped case '{case.title}' - No linked profile.")
    messages.success(request, f"System successfully sent {count} automated payment alerts.")

# --- 2. ADVANCED IDENTITY CONTROL (USER & PROFILE GOD-MODE) ---

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = '🔐 Identity & Security Layer'
    readonly_fields = ('unique_id', 'otp')
    fieldsets = (
        (None, {
            'fields': ('unique_id', 'phone', 'gender', 'profile_pic', 'address')
        }),
        ('Security Flags', {
            'fields': ('otp', 'is_verified', 'old_email_verified')
        }),
    )

class AdvancedUserAdmin(BaseUserAdmin):
    """
    God-Mode User Management: Controls Authentication, Profiles, and System Access.
    """
    inlines = (UserProfileInline,)
    list_display = (
        'id', 
        'username', 
        'email', 
        'get_id', 
        'access_level', 
        'status_icon', 
        'last_login_formatted'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    actions = [suspend_accounts, activate_accounts]
    ordering = ('-date_joined',)

    def get_id(self, obj):
        return obj.profile.unique_id if hasattr(obj, 'profile') else "No Profile"
    get_id.short_description = "Consultancy ID"

    def access_level(self, obj):
        if obj.is_superuser: 
            return mark_safe('<b style="color:purple;">ROOT</b>')
        if obj.is_staff: 
            return mark_safe('<b style="color:blue;">STAFF</b>')
        return "CLIENT"
    access_level.short_description = "Access Rank"

    def status_icon(self, obj):
        color = "green" if obj.is_active else "red"
        return mark_safe(f'<span style="color:{color}; font-size:18px; line-height:1;">●</span>')
    status_icon.short_description = "Status"

    def last_login_formatted(self, obj):
        if obj.last_login:
            return obj.last_login.strftime("%d/%m/%y %H:%M")
        return mark_safe('<span style="color:#ccc;">Never Logged In</span>')
    last_login_formatted.short_description = "Session Activity"

# Re-register User with Advanced Admin
admin.site.unregister(User)
admin.site.register(User, AdvancedUserAdmin)

# --- 3. SERVICE INTAKE CONTROL (REQUESTS & FINANCE) ---

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    """
    Transactional Control Room: Full lifecycle management of service requests.
    Includes manual amount entry for automated billing without external payment gateways.
    """
    list_display = (
        'id', 
        'client_control_link', 
        'service_type', 
        'sub_service', 
        'status', 
        'amount',           # Manual Entry Field
        'finance_status',    # Payment tracking
        'request_badge', 
        'created_at'
    )
    list_editable = ('status', 'amount') 
    list_filter = ('status', 'service_type', 'is_paid', 'created_at')
    search_fields = ('client__unique_id', 'sub_service', 'client__user__first_name')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def client_control_link(self, obj):
        try:
            url = reverse('admin:auth_user_change', args=[obj.client.user.id])
            return format_html('<a href="{}" style="font-weight:bold; color:#002d5b;">{}</a>', url, obj.client.unique_id)
        except:
            return obj.client.unique_id if obj.client else "N/A"
    client_control_link.short_description = "Client Profile"

    def finance_status(self, obj):
        if obj.is_paid:
            return mark_safe('<b style="color:#28a745;">● PAID</b>')
        return mark_safe('<b style="color:#dc3545;">● PENDING</b>')
    finance_status.short_description = "Payment Status"

    def request_badge(self, obj):
        bg_colors = {
            'REQUESTED': '#ffc107',    
            'APPROVED': '#17a2b8',     
            'IN_PROGRESS': '#007bff',  
            'VERIFICATION': '#6610f2', 
            'FULFILLED': '#28a745',    
            'REJECTED': '#dc3545',     
        }
        return mark_safe(f'<span style="background:{bg_colors.get(obj.status, "#666")}; color:white; padding:3px 8px; border-radius:4px; font-size:10px; font-weight:bold;">Visual Status</span>')
    request_badge.short_description = "Label"

# --- 4. CORE FILING CONTROL (CASES) ---

@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    """
    Case Management Engine: Full control over legal filings, progress, and financials.
    """
    list_display = (
        'title', 
        'client_profile', 
        'status', 
        'lawyer', 
        'payment_status', 
        'amount_due', 
        'status_visual', 
        'finance_visual', 
        'file_vault'
    )
    list_editable = ('status', 'lawyer', 'payment_status', 'amount_due')
    list_filter = ('status', 'payment_status', 'lawyer', 'created_at')
    search_fields = (
        'title', 
        'client_profile__unique_id', 
        'client_profile__user__first_name',
        'client_profile__user__last_name'
    )
    actions = [send_payment_email]
    readonly_fields = ('created_at', 'updated_at')

    def status_visual(self, obj):
        return mark_safe(f'<div style="width:80px; background:#eee; border-radius:10px; border:1px solid #ddd;"><div style="width:{obj.progress_percentage}%; background:#002d5b; height:8px; border-radius:10px;"></div></div>')
    status_visual.short_description = "Progress Bar"

    def finance_visual(self, obj):
        color = "#28a745" if obj.payment_status else "#dc3545"
        label = "CLEARED" if obj.payment_status else "PENDING"
        return mark_safe(f'<span style="color:{color}; font-size:11px; font-weight:bold;">● {label}</span>')
    finance_visual.short_description = "Finance Alert"

    def file_vault(self, obj):
        if obj.document:
            return format_html('<a href="{}" target="_blank" style="background:#007bff; color:white; padding:2px 8px; border-radius:4px; text-decoration:none; font-size:10px;">📥 VIEW DOC</a>', obj.document.url)
        return mark_safe('<span style="color:#ccc; font-style:italic;">Empty</span>')
    file_vault.short_description = "Documents"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client_profile', 'lawyer')

# --- 5. STAFF & LEAD MANAGEMENT ---

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """Lead Management Dashboard for Home Page Consultation requests."""
    list_display = ('full_name', 'email', 'phone', 'subject', 'status', 'status_color_indicator', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'subject', 'created_at')
    search_fields = ('full_name', 'phone', 'subject', 'email')
    ordering = ('-created_at',)
    actions = ['convert_to_client']

    def status_color_indicator(self, obj):
        color = {"NEW": "blue", "CONTACTED": "orange", "CONVERTED": "green", "REJECTED": "red"}
        return mark_safe(f'<b style="color:{color.get(obj.status, "black")}; font-size:18px;">●</b>')
    status_color_indicator.short_description = "Visual Status"

    def save_model(self, request, obj, form, change):
        """Triggers emails when the Admin changes the status of an Inquiry."""
        if change:
            if obj.status == 'CONTACTED':
                subject = f"Response from Mishra Consultancy: {obj.subject}"
                message = f"""
                Hello {obj.full_name},

                Thank you for reaching out to Mishra Consultancy regarding {obj.subject}.

                Our legal strategists have reviewed your inquiry. One of our team members will call you 
                shortly at {obj.phone} to discuss the next steps.

                Regards,
                Admin Command Center
                Mishra Consultancy Ltd.
                """
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [obj.email])
                    self.message_user(request, f"Response email successfully sent to {obj.full_name}.", messages.SUCCESS)
                except Exception as e:
                    self.message_user(request, f"Email failed to send: {str(e)}", messages.ERROR)
        super().save_model(request, obj, form, change)

    @admin.action(description="Convert selected inquiries into Clients")
    def convert_to_client(self, request, queryset):
        for inquiry in queryset:
            if inquiry.status == 'CONVERTED' or User.objects.filter(email=inquiry.email).exists():
                self.message_user(request, f"{inquiry.email} is already a user.", messages.WARNING)
                continue

            user = User.objects.create_user(
                username=inquiry.email,
                email=inquiry.email,
                password=inquiry.phone, 
                first_name=inquiry.full_name
            )

            UserProfile.objects.create(
                user=user,
                phone=inquiry.phone
            )

            inquiry.status = 'CONVERTED'
            inquiry.save()

            subject = "Account Created - Mishra Consultancy"
            body = f"""
            Hello {inquiry.full_name},

            Welcome to Mishra Consultancy! We have converted your inquiry into a formal client account.

            Your Credentials:
            Username: {inquiry.email}
            Temporary Password: {inquiry.phone}

            Please login to your dashboard to track your filings.
            """
            try:
                send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [inquiry.email])
            except Exception:
                pass

        self.message_user(request, "Selected inquiries converted successfully!", messages.SUCCESS)

@admin.register(Lawyer)
class LawyerAdmin(admin.ModelAdmin):
    """Directory for the Consultants / Staff Members."""
    list_display = ('id', 'full_name_display', 'specialization', 'email', 'phone')
    search_fields = ('first_name', 'last_name', 'email')
    
    def full_name_display(self, obj):
        return f"Adv. {obj.first_name} {obj.last_name}"
    full_name_display.short_description = "Legal Professional"

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Manual Record Keeping for Legacy Clients."""
    list_display = ('id', 'first_name', 'last_name', 'email', 'phone', 'linked_profile_id')
    search_fields = ('first_name', 'last_name', 'email', 'phone')

    def linked_profile_id(self, obj):
        if obj.profile:
            return obj.profile.unique_id
        return mark_safe('<span style="color:#999;">No Web Profile</span>')
    linked_profile_id.short_description = "Sync Status"

# --- 6. GLOBAL ADMIN BRANDING ---

admin.site.site_header = "MISHRA CONSULTANCY CENTER"
admin.site.site_title =  "ADMIN"
admin.site.index_title = "SYSTEM INFRASTRUCTURE CONTROL PANEL"