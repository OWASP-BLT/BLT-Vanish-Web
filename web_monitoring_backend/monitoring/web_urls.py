"""
Web URLs for monitoring app
"""

from django.urls import path
from monitoring import views

app_name = 'web_monitoring'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('monitors/', views.MonitorListView.as_view(), name='monitor_list'),
    path('monitors/create/', views.MonitorCreateView.as_view(), name='monitor_create'),
    path('monitors/<int:pk>/', views.MonitorDetailView.as_view(), name='monitor_detail'),
    path('monitors/<int:pk>/edit/', views.MonitorUpdateView.as_view(), name='monitor_update'),
    path('monitors/<int:pk>/delete/', views.MonitorDeleteView.as_view(), name='monitor_delete'),
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscriptions'),
    path('subscriptions/plan-selection/<int:monitor_id>/', views.SubscriptionPlanSelectionView.as_view(), name='subscription_plan'),
    path('subscriptions/pricing/', views.PricingPlansView.as_view(), name='pricing_plans'),
    path('subscriptions/create/', views.SubscriptionCreateView.as_view(), name='subscription_create'),
    path('subscriptions/<int:pk>/edit/', views.SubscriptionUpdateView.as_view(), name='subscription_update'),
    path('subscriptions/<int:pk>/delete/', views.SubscriptionDeleteView.as_view(), name='subscription_delete'),
    path('subscriptions/<int:pk>/cancel/', views.SubscriptionCancelView.as_view(), name='subscription_cancel'),
    path('payments/', views.PaymentHistoryView.as_view(), name='payment_history'),
    path('payments/<int:subscription_id>/checkout/', views.StripePaymentView.as_view(), name='stripe_payment'),
    path('payments/<int:payment_id>/success/', views.PaymentSuccessView.as_view(), name='payment_success'),
    path('budget-allocation/', views.BudgetAllocationView.as_view(), name='budget_allocation'),
    
    # Admin URLs
    path('admin/users/', views.AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
]
