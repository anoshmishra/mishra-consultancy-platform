from django.urls import path
from . import views

app_name = 'cases'

urlpatterns = [
    # --- 1. PUBLIC PAGES ---
    path('', views.HomeView.as_view(), name='home'),
    path('services/', views.services_view, name='services'),
    path('about/', views.about_view, name='about'),
    
    # --- 2. AUTHENTICATION & OTP ---
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('verify-otp/resend/', views.resend_otp_view, name='resend_otp'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- 3. CLIENT PROFILE & SECURE EDIT ---
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/request/', views.request_profile_edit, name='request_profile_edit'),
    path('profile/edit/verify/', views.verify_edit_otp, name='verify_edit_otp'),
    path('profile/edit/final/', views.profile_edit_final, name='profile_edit_final'),

    # --- 4. TRANSACTIONAL SERVICES (NEW) ---
    # This is where the client picks a new job and uploads docs
    path('start-filing/', views.start_filing_view, name='start_filing'),
    path('upload-document/<int:case_id>/', views.upload_document_view, name='upload_document'),

    # --- 5. CLIENT MANAGEMENT (Staff Only) ---
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/add/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/update/', views.ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),

    # --- 6. STAFF / LAWYER DIRECTORY (Staff Only) ---
    path('lawyers/', views.LawyerListView.as_view(), name='lawyer_list'),
    path('lawyers/add/', views.LawyerCreateView.as_view(), name='lawyer_create'),
    path('lawyers/<int:pk>/update/', views.LawyerUpdateView.as_view(), name='lawyer_update'),
    path('lawyers/<int:pk>/delete/', views.LawyerDeleteView.as_view(), name='lawyer_delete'),

    # --- 7. CASE & FILING MANAGEMENT (Staff Only) ---
    path('cases/', views.CaseListView.as_view(), name='case_list'),
    path('cases/add/', views.CaseCreateView.as_view(), name='case_create'),
    path('cases/<int:pk>/update/', views.CaseUpdateView.as_view(), name='case_update'),
    path('cases/<int:pk>/delete/', views.CaseDeleteView.as_view(), name='case_delete'),
]
