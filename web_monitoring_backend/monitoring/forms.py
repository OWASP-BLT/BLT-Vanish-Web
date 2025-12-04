"""
Django forms for the monitoring and accounts apps
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from monitoring.models import Monitor, Notification
from accounts.models import Subscription


class MonitorForm(forms.ModelForm):
    """Form for creating/editing monitors"""
    
    class Meta:
        model = Monitor
        fields = ['url', 'keyword', 'check_interval_days', 'alert_email', 'alert_sms', 'notes']
        widgets = {
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'keyword': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Keyword or phrase to monitor'
            }),
            'check_interval_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '365'
            }),
            'alert_email': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'alert_sms': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this monitor'
            }),
        }


class SubscriptionForm(forms.ModelForm):
    """Form for managing subscriptions"""
    
    class Meta:
        model = Subscription
        fields = ['keyword', 'check_frequency', 'cost_per_month', 'status']
        widgets = {
            'keyword': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Keyword to monitor'
            }),
            'check_frequency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'cost_per_month': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Cost per month (USD)'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
        }


class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with email"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
        }
