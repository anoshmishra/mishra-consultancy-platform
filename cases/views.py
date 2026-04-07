import random
import datetime
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Client, Case, Lawyer, UserProfile, Inquiry, ServiceRequest
from .forms import (
    ClientForm, LawyerForm, CaseForm, 
    DocumentUploadForm, UserUpdateForm, ProfileUpdateForm
)

logger = logging.getLogger(__name__)

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
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        client_email = request.POST.get('client_email')
        service_subject = request.POST.get('subject')

        try:
            Inquiry.objects.create(
                full_name=full_name, phone=phone, 
                email=client_email, subject=service_subject
            )
        except Exception as e:
            logger.error(f"Inquiry Database Error: {e}")

        email_body = f"New Inquiry from {full_name}\nPhone: {phone}\nEmail: {client_email}\nSubject: {service_subject}"

        try:
            send_mail(
                subject=f"NEW INQUIRY: {service_subject}",
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL, 'anoshmishra77@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, f"Thank you {full_name}! Inquiry received.")
        except Exception as e:
            logger.error(f"SMTP Timeout/Error: {e}")
            messages.success(request, f"Thank you {full_name}! Your request is registered.")

        return redirect("cases:home")

def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')

        if User.objects.filter(username=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect("cases:register")

        user = User.objects.create_user(username=email, email=email, password=password, first_name=full_name)
        user.is_active = False 
        user.save()

        profile = UserProfile.objects.create(user=user, phone=phone)
        otp = profile.generate_otp()
        
        try:
            send_mail(
                "Verification Code - Mishra Consultancy",
                f"Your OTP for Mishra Consultancy registration is: {otp}",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            request.session['verification_email'] = email
            messages.info(request, "OTP sent! Please check your email.")
            return redirect("cases:verify_otp")
        except Exception as e:
            logger.error(f"Registration SMTP Error: {e}")
            request.session['verification_email'] = email
            messages.warning(request, "Registration successful, but email service timed out. Please try verifying later.")
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
                send_mail(
                    "Welcome to Mishra Consultancy",
                    welcome_msg,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True,
                )
            except Exception:
                pass

            messages.success(request, "Account verified! Please login.")
            return redirect("cases:login")
        except UserProfile.DoesNotExist:
            messages.error(request, "Invalid OTP.")

    return render(request, "registration/verify.html")

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
                messages.warning(request, "Please verify your email.")
                return redirect("cases:verify_otp")
        else:
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
            send_mail(
                f"Job Request: {request.user.profile.unique_id}",
                admin_msg,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL, 'anoshmishra77@gmail.com'],
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
        send_mail("Profile Change Code", f"Code: {otp}", settings.DEFAULT_FROM_EMAIL, [request.user.email], fail_silently=False)
        messages.info(request, "Code sent to current email.")
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