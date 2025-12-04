"""
URL routing for monitoring app - both API and web views
"""

from django.urls import path
from rest_framework.routers import DefaultRouter
from monitoring import views

# API Router
router = DefaultRouter()
router.register(r'monitors', views.MonitorViewSet, basename='monitor')

# API URLs
app_name = 'monitoring'
api_patterns = router.urls

# Web URLs
web_patterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('monitors/', views.MonitorListView.as_view(), name='monitor_list'),
    path('monitors/create/', views.MonitorCreateView.as_view(), name='monitor_create'),
    path('monitors/<int:pk>/', views.MonitorDetailView.as_view(), name='monitor_detail'),
    path('monitors/<int:pk>/edit/', views.MonitorUpdateView.as_view(), name='monitor_update'),
    path('monitors/<int:pk>/delete/', views.MonitorDeleteView.as_view(), name='monitor_delete'),
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscriptions'),
    path('budget-allocation/', views.BudgetAllocationView.as_view(), name='budget_allocation'),
]

urlpatterns = api_patterns + web_patterns
