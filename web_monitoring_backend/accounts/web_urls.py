"""
Web URLs for accounts app
"""

from django.urls import path
from accounts import views as account_views
from monitoring import views as monitoring_views

app_name = 'web_accounts'

urlpatterns = [
    path('login/', monitoring_views.CustomLoginView.as_view(), name='login'),
    path('logout/', monitoring_views.CustomLogoutView.as_view(), name='logout'),
    path('register/', monitoring_views.RegisterView.as_view(), name='register'),
    path('profile/', monitoring_views.profile_view, name='profile'),
    path('payments/history/', account_views.payment_history, name='payment_history'),
]
