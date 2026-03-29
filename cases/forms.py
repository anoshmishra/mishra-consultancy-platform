from django import forms
from django.contrib.auth.models import User
from .models import Case, Client, Lawyer, UserProfile

# --- 1. STAFF / ADMIN FORMS ---

class CaseForm(forms.ModelForm):
    """Admin/Staff form to manage client cases and filings."""
    class Meta:
        model = Case
        fields = ['title', 'description', 'status', 'client_profile', 'lawyer', 'amount_due', 'payment_status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. GST Filing Q1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'client_profile': forms.Select(attrs={'class': 'form-select'}),
            'lawyer': forms.Select(attrs={'class': 'form-select'}),
            'amount_due': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ClientForm(forms.ModelForm):
    """Staff form to manually register a new client."""
    class Meta:
        model = Client
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile Number'}),
        }

class LawyerForm(forms.ModelForm):
    """Form to manage staff/lawyer directory entries."""
    class Meta:
        model = Lawyer
        fields = ['first_name', 'last_name', 'email', 'phone', 'specialization']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Criminal Defense'}),
        }

# --- 2. PUBLIC / CLIENT FORMS ---

class ContactForm(forms.Form):
    """Lead capture form on the home page (Consult an Expert)."""
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Your Full Name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Email Address'
    }))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Phone Number'
    }))
    subject = forms.ChoiceField(choices=[
        ('GST', 'GST Registration/Filing'),
        ('NOTARY', 'Notary Services'),
        ('CIVIL', 'Civil Law'),
        ('CRIMINAL', 'Criminal Defense'),
        ('OTHER', 'Other Inquiry')
    ], widget=forms.Select(attrs={'class': 'form-select'}))
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control', 'placeholder': 'Tell us about your requirements...', 'rows': 4
    }))

class DocumentUploadForm(forms.ModelForm):
    """Form for clients to upload identity/legal docs to their cases."""
    class Meta:
        model = Case
        fields = ['document', 'client_notes']
        widgets = {
            'document': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf, .jpg, .jpeg, .png'
            }),
            'client_notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Explain what you are uploading (e.g., Aadhaar Card for verification.)'
            }),
        }

# --- 3. PROFILE MANAGEMENT FORMS ---

class UserUpdateForm(forms.ModelForm):
    """Allows users to update their core account details (First/Last name, Email)."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    """Allows users to update their Mishra Consultancy specific profile details."""
    class Meta:
        model = UserProfile
        fields = ['phone', 'gender', 'address', 'profile_pic']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'profile_pic': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }