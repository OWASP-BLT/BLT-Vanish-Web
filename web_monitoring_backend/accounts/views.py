"""
Views for the accounts app - user profiles and account management
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.models import Subscription, Payment, BudgetAllocation
import logging

logger = logging.getLogger(__name__)


@login_required
def account_dashboard(request):
    """User account dashboard"""
    user = request.user
    subscriptions = Subscription.objects.filter(user=user)
    payments = Payment.objects.filter(user=user).order_by('-created_at')[:10]
    budget = BudgetAllocation.objects.order_by('-month').first()
    
    context = {
        'subscriptions': subscriptions,
        'payments': payments,
        'budget': budget,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def payment_history(request):
    """View payment history for current user"""
    user = request.user
    payments = Payment.objects.filter(user=user).order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(payments, 20)  # 20 payments per page
    page = request.GET.get('page')
    payments = paginator.get_page(page)
    
    # Calculate statistics
    total_spent = sum(p.amount for p in Payment.objects.filter(user=user, status='completed'))
    completed_count = Payment.objects.filter(user=user, status='completed').count()
    pending_count = Payment.objects.filter(user=user, status='pending').count()
    failed_count = Payment.objects.filter(user=user, status='failed').count()
    
    context = {
        'payments': payments,
        'total_spent': total_spent,
        'completed_count': completed_count,
        'pending_count': pending_count,
        'failed_count': failed_count,
    }
    return render(request, 'accounts/payment_history.html', context)
