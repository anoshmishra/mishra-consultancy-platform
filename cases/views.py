import random
import datetime
import logging
import time
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import Client, Case, Lawyer, UserProfile, Inquiry, ServiceRequest
from .forms import (
    ClientForm, LawyerForm, CaseForm, 
    DocumentUploadForm, UserUpdateForm, ProfileUpdateForm
)
from .sendgrid_backend import send_sendgrid_email_with_retry

logger = logging.getLogger(__name__)


def build_registration_otp_message(otp):
    return (
        "Dear User,\n\n"
        "Welcome to Mishra Consultancy.\n"
        "Use the One-Time Password (OTP) below to verify your account:\n\n"
        f"OTP: {otp}\n\n"
        "This OTP is confidential. Please do not share it with anyone.\n\n"
        "If you did not initiate this request, you can safely ignore this email.\n\n"
        "Regards,\n"
        "Mishra Consultancy Team"
    )


def send_registration_otp(profile, email):
    otp = profile.generate_otp()
    return send_mail_with_retry(
        "Verification Code - Mishra Consultancy",
        build_registration_otp_message(otp),
        [email],
        fail_silently=False,
    )


def send_mail_with_retry(subject, message, recipient_list, fail_silently=False):
    """
    Send email via SendGrid with built-in retry logic
    Returns True on success, False otherwise
    """
    return send_sendgrid_email_with_retry(
        subject=subject,
        message=message,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
        max_retries=int(getattr(settings, "EMAIL_SEND_RETRIES", 3))
    )


def admin_notification_recipients():
    return getattr(settings, "ADMIN_NOTIFICATION_EMAILS", ["anoshmishra77@gmail.com"])


def queue_mail_or_fallback(subject, message, recipient_list, fail_silently=False,
                          html_message=None, from_email=None, attachments=None):
    """
    Queue email via Celery, with sync fallback if queue fails
    SendGrid handles all delivery
    """
    try:
        from .tasks import send_email_task
        send_email_task.delay(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
            fail_silently=fail_silently,
            html_message=html_message,
            from_email=from_email,
            attachments=attachments
        )
        logger.info(f"Email queued via Celery: {subject}")
        return True
    except Exception as e:
        logger.warning(f"Celery enqueue failed for '{subject}'. Falling back to sync SendGrid: {e}")
        return send_sendgrid_email_with_retry(
            subject=subject,
            message=message,
            recipient_list=recipient_list,
            fail_silently=fail_silently,
            html_message=html_message,
            from_email=from_email,
            attachments=attachments
        )

def services_view(request):
    return render(request, 'services.html')

def about_view(request):
    return render(request, 'about.html')

class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status_id = self.request.GET.get('status_search')
        if status_id:
            context['tracked_case'] = Case.objects.filter(
                Q(client_profile__unique_id__iexact=status_id) | 
                Q(client_profile__phone__icontains=status_id)
            ).first()
        
        context['clients_count'] = Client.objects.count()
        context['lawyers_count'] = Lawyer.objects.count()
        context['cases_count'] = Case.objects.count()
        return context

    def post(self, request, *args, **kwargs):
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        client_email = request.POST.get('client_email', '').strip().lower()
        service_subject = request.POST.get('subject', '').strip()

        service_labels = dict(Inquiry.SERVICE_CHOICES)
        if not service_subject:
            service_subject = "GENERAL"

        if not full_name or not phone or not client_email:
            messages.error(request, "Please fill all inquiry fields before submitting.")
            return redirect("cases:home")

        try:
            validate_email(client_email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return redirect("cases:home")

        try:
            inquiry = Inquiry.objects.create(
                full_name=full_name, phone=phone, 
                email=client_email, subject=service_subject
            )
        except Exception as e:
            logger.error(f"Inquiry Database Error: {e}")
            messages.error(request, "We could not register your inquiry right now. Please try again.")
            return redirect("cases:home")

        service_name = service_labels.get(service_subject, service_subject)
        email_body = (
            f"New Inquiry #{inquiry.id}\n"
            f"Name: {full_name}\n"
            f"Phone: {phone}\n"
            f"Email: {client_email}\n"
            f"Service: {service_name}\n"
            f"Admin: /admin/cases/inquiry/{inquiry.id}/change/"
        )

        try:
            queue_mail_or_fallback(
                subject=f"NEW INQUIRY: {service_name}",
                message=email_body,
                recipient_list=admin_notification_recipients(),
                fail_silently=True,
            )
        except Exception as e:
            logger.error("Inquiry saved but admin notification failed: %s", e)

        messages.success(request, f"Thank you {full_name}! Your inquiry has been registered.")
        return redirect("cases:home")

def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        phone = request.POST.get('phone')

        existing_user = User.objects.filter(username=email).first()
        if existing_user and not existing_user.is_active:
            request.session['verification_email'] = existing_user.email or existing_user.username
            try:
                sent = send_registration_otp(existing_user.profile, request.session['verification_email'])
                if sent:
                    messages.info(request, "A fresh OTP has been sent. Please check your inbox, spam, junk, promotions, or updates folder.")
                else:
                    messages.warning(request, "Your account is pending verification, but we could not send a fresh OTP right now. Please use Resend OTP after a minute.")
            except Exception as e:
                logger.error("Registration OTP resend failed: %s", e)
                messages.warning(request, "Your account is pending verification, but we could not send a fresh OTP right now. Please use Resend OTP after a minute.")
            return redirect("cases:verify_otp")

        if existing_user:
            messages.error(request, "This email is already registered.")
            return redirect("cases:register")

        user = User.objects.create_user(username=email, email=email, password=password, first_name=full_name)
        user.is_active = False 
        user.save()

        profile = UserProfile.objects.create(user=user, phone=phone)
        
        try:
            sent = send_registration_otp(profile, email)
            request.session['verification_email'] = email
            if sent:
                messages.info(request, "OTP sent. Please check your inbox, spam, junk, promotions, or updates folder.")
            else:
                messages.warning(request, "Registration is saved, but the OTP email could not be sent right now. Please use Resend OTP after a minute.")
            return redirect("cases:verify_otp")
        except Exception as e:
            logger.error(f"Registration OTP SMTP Error: {e}")
            request.session['verification_email'] = email
            messages.warning(request, "Registration is saved, but the OTP email service is busy. Please use Resend OTP after a minute and check spam or junk folders.")
            return redirect("cases:verify_otp")
            
    return render(request, "registration/register.html")

def verify_otp_view(request):
    email = request.session.get('verification_email')
    if not email:
        return redirect("cases:register")

    if request.method == "POST":
        otp_entered = request.POST.get('otp')
        try:
            profile = UserProfile.objects.get(user__username=email, otp=otp_entered)
            profile.is_verified = True
            profile.save() 
            
            user = profile.user
            user.is_active = True
            user.save()
            
            welcome_msg = f"Hello {user.first_name},\n\nWelcome! Your Private Client ID is: {profile.unique_id}"
            try:
                queue_mail_or_fallback(
                    "Welcome to Mishra Consultancy",
                    welcome_msg,
                    [email],
                    fail_silently=True,
                )
            except Exception:
                pass

            messages.success(request, "Account verified! Please login.")
            request.session.pop('verification_email', None)
            return redirect("cases:login")
        except UserProfile.DoesNotExist:
            messages.error(request, "Invalid OTP.")

    return render(request, "registration/verify.html")


def resend_otp_view(request):
    email = request.session.get("verification_email")
    if not email:
        messages.error(request, "Verification session expired. Please register again.")
        return redirect("cases:register")

    try:
        profile = UserProfile.objects.get(user__username=email)
    except UserProfile.DoesNotExist:
        messages.error(request, "Account not found. Please register again.")
        return redirect("cases:register")

    try:
        sent = send_registration_otp(profile, email)
        if sent:
            messages.info(request, "A new OTP has been sent. Please check your inbox, spam, junk, promotions, or updates folder.")
        else:
            messages.warning(request, "We could not send a new OTP right now. Please try again after a minute.")
    except Exception as e:
        logger.error("Resend OTP SMTP Error: %s", e)
        messages.warning(request, "Email service is busy. Please try Resend OTP after a minute.")

    return redirect("cases:verify_otp")

def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return redirect("cases:home")
            else:
                request.session['verification_email'] = user.email or user.username
                messages.warning(request, "Please verify your email.")
                return redirect("cases:verify_otp")
        else:
            inactive_user = User.objects.filter(username=email, is_active=False).first()
            if inactive_user and inactive_user.check_password(password):
                request.session['verification_email'] = inactive_user.email or inactive_user.username
                messages.warning(request, "Please verify your email.")
                return redirect("cases:verify_otp")
            messages.error(request, "Invalid email or password.")
    return render(request, "registration/login.html")

def logout_view(request):
    auth_logout(request)
    return redirect("cases:home")

@login_required
def profile_view(request):
    user_cases = Case.objects.filter(client_profile=request.user.profile).order_by('-created_at')
    service_requests = ServiceRequest.objects.filter(client=request.user.profile).order_by('-created_at')
    context = {
        'user_cases': user_cases,
        'service_requests': service_requests,
    }
    return render(request, 'registration/profile.html', context)

@login_required
def upload_document_view(request, case_id):
    case = get_object_or_404(Case, id=case_id, client_profile=request.user.profile)
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES, instance=case)
        if form.is_valid():
            case.status = 'RECEIVED'
            form.save()
            messages.success(request, "Document uploaded!")
            return redirect('cases:profile')
    else:
        form = DocumentUploadForm(instance=case)
    return render(request, 'cases/upload_document.html', {'form': form, 'case': case})

@login_required
def start_filing_view(request):
    if request.method == "POST":
        service_type = request.POST.get('service_type')
        sub_service = request.POST.get('sub_service')
        
        ServiceRequest.objects.create(
            client=request.user.profile,
            service_type=service_type,
            sub_service=sub_service,
            status='REQUESTED'
        )

        admin_msg = f"New Request\nClient: {request.user.get_full_name()}\nID: {request.user.profile.unique_id}\nService: {service_type}\nSub: {sub_service}"
        try:
            queue_mail_or_fallback(
                f"Job Request: {request.user.profile.unique_id}",
                admin_msg,
                admin_notification_recipients(),
                fail_silently=False,
            )
            messages.success(request, "Request submitted!")
        except Exception:
            messages.success(request, "Request submitted!")
        return redirect('cases:profile')
    return render(request, 'cases/start_filing.html')

@login_required
def request_profile_edit(request):
    profile = request.user.profile
    otp = profile.generate_otp()
    try:
        sent = send_mail_with_retry("Profile Change Code", f"Code: {otp}", [request.user.email], fail_silently=False)
        if sent:
            messages.info(request, "Security code sent. Please check your inbox, spam, junk, promotions, or updates folder.")
        else:
            messages.warning(request, "We could not send the security code right now. Please try again after a minute.")
        return redirect('cases:verify_edit_otp')
    except Exception as e:
        logger.error(f"Edit OTP SMTP Error: {e}")
        messages.error(request, "Mail server is busy. Could not send code.")
        return redirect('cases:profile')

@login_required
def verify_edit_otp(request):
    if request.method == "POST":
        if request.POST.get('otp') == request.user.profile.otp:
            request.user.profile.old_email_verified = True
            request.user.profile.save()
            return redirect('cases:profile_edit_final')
        messages.error(request, "Invalid code.")
    return render(request, 'registration/verify_edit.html')

@login_required
def profile_edit_final(request):
    if not request.user.profile.old_email_verified:
        return redirect('cases:profile')
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            request.user.profile.old_email_verified = False
            request.user.profile.save()
            messages.success(request, "Profile updated!")
            return redirect('cases:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    return render(request, 'registration/profile_edit_form.html', {'u_form': u_form, 'p_form': p_form})

class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "clients/client_list.html"
    context_object_name = "clients"

class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("cases:client_list")

class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "clients/client_form.html"
    success_url = reverse_lazy("cases:client_list")

class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = "clients/client_confirm_delete.html"
    success_url = reverse_lazy("cases:client_list")

class LawyerListView(LoginRequiredMixin, ListView):
    model = Lawyer
    template_name = "lawyers/lawyer_list.html"
    context_object_name = "lawyers"

class LawyerCreateView(LoginRequiredMixin, CreateView):
    model = Lawyer
    form_class = LawyerForm
    template_name = "lawyers/lawyer_form.html"
    success_url = reverse_lazy("cases:lawyer_list")

class LawyerUpdateView(LoginRequiredMixin, UpdateView):
    model = Lawyer
    form_class = LawyerForm
    template_name = "lawyers/lawyer_form.html"
    success_url = reverse_lazy("cases:lawyer_list")

class LawyerDeleteView(LoginRequiredMixin, DeleteView):
    model = Lawyer
    template_name = "lawyers/lawyer_confirm_delete.html"
    success_url = reverse_lazy("cases:lawyer_list")

class CaseListView(LoginRequiredMixin, ListView):
    model = Case
    template_name = "cases/case_list.html"
    context_object_name = "cases"

class CaseCreateView(LoginRequiredMixin, CreateView):
    model = Case
    form_class = CaseForm
    template_name = "cases/case_form.html"
    success_url = reverse_lazy("cases:case_list")

class CaseUpdateView(LoginRequiredMixin, UpdateView):
    model = Case
    form_class = CaseForm
    template_name = "cases/case_form.html"
    success_url = reverse_lazy("cases:case_list")

class CaseDeleteView(LoginRequiredMixin, DeleteView):
    model = Case
    template_name = "cases/case_confirm_delete.html"
    success_url = reverse_lazy("cases:case_list")
