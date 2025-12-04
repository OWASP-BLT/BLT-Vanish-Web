"""
URL routing for accounts app - authentication and profiles
"""

from django.urls import path
from accounts import views as account_views
from monitoring import views as monitoring_views

# API URLs
app_name = 'accounts'
api_patterns = [
    # Add API endpoints here later
]

# Web URLs
web_patterns = [
    path('login/', monitoring_views.CustomLoginView.as_view(), name='login'),
    path('logout/', monitoring_views.CustomLogoutView.as_view(), name='logout'),
    path('register/', monitoring_views.RegisterView.as_view(), name='register'),
    path('profile/', monitoring_views.profile_view, name='profile'),
    path('payments/history/', account_views.payment_history, name='payment_history'),
]

urlpatterns = api_patterns + web_patterns
