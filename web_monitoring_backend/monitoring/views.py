"""
Views for the monitoring app - frontend and API endpoints
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db import models
from monitoring.models import Monitor, CheckResult, Notification
from accounts.models import Subscription, Payment, BudgetAllocation
from monitoring.forms import MonitorForm, SubscriptionForm, CustomUserCreationForm, UserProfileForm
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from monitoring.serializers import MonitorSerializer, CheckResultSerializer, NotificationSerializer
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Web Views (HTML Templates)
# ============================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard with statistics and recent alerts"""
    template_name = 'monitoring/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['active_monitors_count'] = Monitor.objects.filter(
            user=user, status='active'
        ).count()
        context['active_subscriptions_count'] = Subscription.objects.filter(
            user=user, status='active'
        ).count()
        context['recent_alerts_count'] = Notification.objects.filter(
            user=user, notification_type='keyword_found',
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        context['total_checks_count'] = CheckResult.objects.filter(
            monitor__user=user
        ).count()
        
        context['recent_alerts'] = CheckResult.objects.filter(
            monitor__user=user, keyword_found=True
        ).select_related('monitor').order_by('-checked_at')[:10]
        
        context['total_monthly_cost'] = sum(
            sub.cost_per_month for sub in Subscription.objects.filter(
                user=user, status='active'
            )
        )
        
        return context


class MonitorListView(LoginRequiredMixin, ListView):
    """List all monitors for current user"""
    model = Monitor
    template_name = 'monitoring/monitor_list.html'
    context_object_name = 'monitors'
    paginate_by = 10
    
    def get_queryset(self):
        return Monitor.objects.filter(user=self.request.user).order_by('-created_at')


class MonitorDetailView(LoginRequiredMixin, DetailView):
    """View details of a single monitor with check history"""
    model = Monitor
    template_name = 'monitoring/monitor_detail.html'
    context_object_name = 'monitor'
    
    def get_queryset(self):
        return Monitor.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all check results for this monitor
        all_check_results = CheckResult.objects.filter(
            monitor=self.object
        ).order_by('-checked_at')
        
        # Calculate statistics
        total_checks = all_check_results.count()
        keyword_found_count = all_check_results.filter(keyword_found=True).count()
        keyword_not_found_count = all_check_results.filter(keyword_found=False).count()
        
        # Success rate
        success_rate = 0
        if total_checks > 0:
            success_rate = round((keyword_found_count / total_checks) * 100, 1)
        
        # Get recent check results (last 50)
        recent_check_results = all_check_results[:50]
        
        # Get subscription for this monitor
        subscription = Subscription.objects.filter(
            user=self.object.user,
            status='active'
        ).first()
        
        # Add to context
        context['check_results'] = recent_check_results
        context['total_checks'] = total_checks
        context['keyword_found_count'] = keyword_found_count
        context['keyword_not_found_count'] = keyword_not_found_count
        context['success_rate'] = success_rate
        context['subscription'] = subscription
        
        # Get found instances (for detailed view)
        context['found_instances'] = all_check_results.filter(
            keyword_found=True
        ).order_by('-checked_at')[:100]
        
        return context


class MonitorCreateView(LoginRequiredMixin, CreateView):
    """Create a new monitor"""
    model = Monitor
    form_class = MonitorForm
    template_name = 'monitoring/monitor_form.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        self.object = form.save()
        # Redirect to subscription plan selection instead of monitor list
        return redirect('web_monitoring:subscription_plan', monitor_id=self.object.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Create New Monitor'
        context['submit_button'] = 'Next: Select Plan'
        return context


class MonitorUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing monitor"""
    model = Monitor
    form_class = MonitorForm
    template_name = 'monitoring/monitor_form.html'
    success_url = reverse_lazy('web_monitoring:monitor_list')
    
    def get_queryset(self):
        return Monitor.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Monitor updated successfully!')
        return response


class MonitorDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a monitor"""
    model = Monitor
    template_name = 'monitoring/monitor_confirm_delete.html'
    success_url = reverse_lazy('web_monitoring:monitor_list')
    
    def get_queryset(self):
        return Monitor.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Monitor deleted successfully!')
        return super().delete(request, *args, **kwargs)


class SubscriptionListView(LoginRequiredMixin, TemplateView):
    """List all subscriptions for current user"""
    template_name = 'monitoring/subscription_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['active_subscriptions'] = Subscription.objects.filter(
            user=user, status='active'
        ).order_by('-created_at')
        context['inactive_subscriptions'] = Subscription.objects.filter(
            user=user
        ).exclude(status='active').order_by('-created_at')
        
        context['total_monthly_cost'] = sum(
            sub.cost_per_month for sub in context['active_subscriptions']
        )
        
        return context


class SubscriptionPlanSelectionView(LoginRequiredMixin, TemplateView):
    """Select subscription plan ($1 or $5) - Step 2 in workflow"""
    template_name = 'monitoring/subscription_plan_selection.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        monitor_id = self.kwargs.get('monitor_id')
        
        # Get the monitor being subscribed to
        try:
            monitor = Monitor.objects.get(id=monitor_id, user=self.request.user)
            context['monitor'] = monitor
        except Monitor.DoesNotExist:
            context['error'] = 'Monitor not found'
            return context
        
        # Define pricing plans
        context['plans'] = [
            {
                'name': 'Standard',
                'price': 1.00,
                'currency': 'USD',
                'billing_period': 'per month',
                'description': 'Essential keyword monitoring',
                'features': [
                    'Monitor 1 keyword',
                    'Daily checks',
                    'Email alerts',
                    'Basic support'
                ],
                'plan_id': 'standard',
                'icon': 'fa-star'
            },
            {
                'name': 'Discovery',
                'price': 5.00,
                'currency': 'USD',
                'billing_period': 'per month',
                'description': 'Advanced discovery features',
                'features': [
                    'AI-powered suggestions',
                    'Unlimited keyword checks',
                    'Advanced analytics',
                    'Priority support',
                    'Custom alerts'
                ],
                'plan_id': 'discovery',
                'icon': 'fa-rocket',
                'recommended': True
            }
        ]
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle plan selection"""
        monitor_id = kwargs.get('monitor_id')
        selected_plan = request.POST.get('plan')
        
        try:
            monitor = Monitor.objects.get(id=monitor_id, user=request.user)
        except Monitor.DoesNotExist:
            messages.error(request, 'Monitor not found')
            return redirect('web_monitoring:monitor_list')
        
        # Map plan to cost
        plan_costs = {
            'standard': 1.00,
            'discovery': 5.00
        }
        
        if selected_plan not in plan_costs:
            messages.error(request, 'Invalid plan selected')
            return redirect('web_monitoring:subscription_plan', monitor_id=monitor_id)
        
        # Create subscription with pre-filled cost and keyword from monitor
        subscription = Subscription.objects.create(
            user=request.user,
            keyword=monitor.keyword,  # Use monitor's keyword
            check_frequency='daily',
            cost_per_month=plan_costs[selected_plan],
            status='pending_payment'  # Mark as pending until payment
        )
        
        # Store monitor_id in session for later reference
        request.session['monitor_id'] = monitor_id
        request.session['subscription_id'] = subscription.id
        
        # Redirect to payment with subscription ID
        return redirect('web_monitoring:stripe_payment', subscription_id=subscription.id)


class SubscriptionCreateView(LoginRequiredMixin, CreateView):
    """Create a new subscription (standard flow, not used in new workflow)"""
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'monitoring/subscription_form.html'
    success_url = reverse_lazy('web_monitoring:subscriptions')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Subscription created successfully!')
        return response


class SubscriptionUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing subscription"""
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'monitoring/subscription_form.html'
    success_url = reverse_lazy('web_monitoring:subscriptions')
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Subscription updated successfully!')
        return response


class SubscriptionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a subscription - only admin can delete"""
    model = Subscription
    template_name = 'monitoring/subscription_confirm_delete.html'
    success_url = reverse_lazy('web_monitoring:subscriptions')
    
    def get_queryset(self):
        # Only admin can delete any subscription
        if self.request.user.is_staff:
            return Subscription.objects.all()
        # Regular users cannot delete subscriptions
        return Subscription.objects.none()
    
    def dispatch(self, request, *args, **kwargs):
        """Only allow admin users to access this view"""
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to delete subscriptions. Contact administrator.')
            return redirect('web_monitoring:subscriptions')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        subscription_user = self.get_object().user.username
        messages.success(self.request, f'Subscription for {subscription_user} deleted successfully!')
        return super().delete(request, *args, **kwargs)


class SubscriptionCancelView(LoginRequiredMixin, UpdateView):
    """Cancel (pause) a subscription - only admin can cancel"""
    model = Subscription
    fields = []
    template_name = 'monitoring/subscription_cancel.html'
    success_url = reverse_lazy('web_monitoring:subscriptions')
    
    def get_queryset(self):
        # Only admin can cancel any subscription
        if self.request.user.is_staff:
            return Subscription.objects.all()
        # Regular users cannot cancel subscriptions
        return Subscription.objects.none()
    
    def dispatch(self, request, *args, **kwargs):
        """Only allow admin users to access this view"""
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to cancel subscriptions. Contact administrator.')
            return redirect('web_monitoring:subscriptions')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.status = 'paused'
        response = super().form_valid(form)
        messages.success(self.request, f'Subscription for {form.instance.user.username} paused successfully!')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'pause'
        context['is_admin'] = self.request.user.is_staff
        return context





class PricingPlansView(LoginRequiredMixin, TemplateView):
    """Display pricing plans for subscriptions"""
    template_name = 'monitoring/pricing_plans.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = [
            {
                'name': 'Standard',
                'price': 1,
                'currency': 'USD',
                'billing_period': 'month per keyword',
                'description': 'Monitor one keyword',
                'features': [
                    'Monitor 1 keyword',
                    'Daily checks',
                    'Email alerts',
                    'Check history',
                    'Standard support'
                ],
                'plan_type': 'standard',
                'stripe_price_id': 'price_1AXDPaJf2aLiTGE4EwXAuIJl'
            },
            {
                'name': 'Discovery',
                'price': 5,
                'currency': 'USD',
                'billing_period': 'month',
                'description': 'Discover new keywords automatically',
                'features': [
                    'Keyword discovery',
                    'AI-powered suggestions',
                    'Unlimited checks',
                    'Advanced analytics',
                    'Priority support',
                    'Custom alerts'
                ],
                'plan_type': 'discovery',
                'stripe_price_id': 'price_1AXDPbJf2aLiTGE4EwXAuIJm'
            }
        ]
        return context


class BudgetAllocationView(LoginRequiredMixin, TemplateView):
    """Display fund allocation transparency"""
    template_name = 'monitoring/budget_allocation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the most recent allocation
        context['budget_allocation'] = BudgetAllocation.objects.order_by('-month').first()
        
        # Calculate user's contribution
        user_payments = Payment.objects.filter(
            user=self.request.user,
            status='completed'
        ).aggregate(total=models.Sum('amount'))
        
        context['user_total_paid'] = user_payments.get('total') or 0
        
        return context


# ============================================================================
# Payment Views (Stripe Integration)
# ============================================================================

class StripePaymentView(LoginRequiredMixin, TemplateView):
    """Handle Stripe payment with card details using Payment Intent - Step 3 in workflow"""
    template_name = 'monitoring/payment_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        import stripe
        from django.conf import settings
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        context['stripe_public_key'] = settings.STRIPE_PUBLIC_KEY
        context['subscription_id'] = self.kwargs.get('subscription_id')
        
        # Get subscription details
        try:
            subscription = Subscription.objects.get(
                id=context['subscription_id'],
                user=self.request.user
            )
            context['subscription'] = subscription
            context['amount_display'] = f"${subscription.cost_per_month:.2f}"
            context['amount_readonly'] = True  # Cost cannot be changed
            
            # Create a Payment Intent
            if stripe.api_key and stripe.api_key.startswith('sk_'):
                try:
                    intent = stripe.PaymentIntent.create(
                        amount=int(subscription.cost_per_month * 100),  # Convert to cents
                        currency='usd',
                        metadata={
                            'user_id': self.request.user.id,
                            'subscription_id': subscription.id,
                            'username': self.request.user.username
                        }
                    )
                    context['client_secret'] = intent.client_secret
                    context['payment_intent_id'] = intent.id
                except stripe.error.StripeError as e:
                    context['error'] = f'Stripe Error: {str(e)}'
            
        except Subscription.DoesNotExist:
            context['error'] = 'Subscription not found'
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle payment confirmation after Stripe processes the payment"""
        import stripe
        from django.conf import settings
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        subscription_id = self.kwargs.get('subscription_id')
        payment_intent_id = request.POST.get('payment_intent_id')
        
        if not payment_intent_id:
            messages.error(request, 'Payment intent ID is required')
            return redirect('web_monitoring:stripe_payment', subscription_id=subscription_id)
        
        try:
            subscription = Subscription.objects.get(
                id=subscription_id,
                user=request.user
            )
            
            # Verify the payment intent with Stripe
            try:
                intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                
                if intent.status == 'succeeded':
                    # Create payment record
                    payment = Payment.objects.create(
                        user=request.user,
                        amount=subscription.cost_per_month,
                        payment_type='subscription',
                        payment_method='stripe',
                        status='completed',
                        transaction_id=intent.id,
                        subscription=subscription,
                        description=f'Payment for {subscription.keyword} subscription'
                    )
                    
                    # Update subscription status to active and set expiration date (1 month from now)
                    subscription.status = 'active'
                    subscription.expires_at = timezone.now() + timezone.timedelta(days=30)
                    subscription.save()
                    
                    messages.success(request, f'Payment of ${subscription.cost_per_month} successful!')
                    return redirect('web_monitoring:payment_success', payment_id=payment.id)
                else:
                    messages.error(request, f'Payment status: {intent.status}')
                    return redirect('web_monitoring:stripe_payment', subscription_id=subscription_id)
                    
            except stripe.error.StripeError as e:
                messages.error(request, f'Payment Error: {str(e)}')
                return redirect('web_monitoring:stripe_payment', subscription_id=subscription_id)
        
        except Subscription.DoesNotExist:
            messages.error(request, 'Subscription not found')
            return redirect('web_monitoring:subscriptions')





class PaymentHistoryView(LoginRequiredMixin, ListView):
    """View payment history for user"""
    model = Payment
    template_name = 'monitoring/payment_history.html'
    context_object_name = 'payments'
    paginate_by = 20
    
    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        completed_payments = Payment.objects.filter(
            user=self.request.user,
            status='completed'
        ).aggregate(total=models.Sum('amount'))
        context['total_paid'] = completed_payments.get('total') or 0
        return context


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    """Payment success confirmation page - redirect back to create monitor"""
    template_name = 'monitoring/payment_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = self.kwargs.get('payment_id')
        
        try:
            payment = Payment.objects.get(id=payment_id, user=self.request.user)
            context['payment'] = payment
            
            # Get monitor ID from session if available
            monitor_id = self.request.session.get('monitor_id')
            if monitor_id:
                try:
                    context['monitor'] = Monitor.objects.get(id=monitor_id, user=self.request.user)
                except Monitor.DoesNotExist:
                    pass
        except Payment.DoesNotExist:
            context['error'] = 'Payment not found'
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle redirect back to monitor after payment success"""
        monitor_id = request.session.get('monitor_id')
        
        # Clear session
        if 'monitor_id' in request.session:
            del request.session['monitor_id']
        if 'subscription_id' in request.session:
            del request.session['subscription_id']
        
        if monitor_id:
            try:
                monitor = Monitor.objects.get(id=monitor_id, user=request.user)
                return redirect('web_monitoring:monitor_detail', pk=monitor_id)
            except Monitor.DoesNotExist:
                pass
        
        return redirect('web_monitoring:monitor_list')


# ============================================================================
# API ViewSets (REST Framework)
# ============================================================================

class MonitorViewSet(viewsets.ModelViewSet):
    """API endpoint for monitors"""
    serializer_class = MonitorSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Monitor.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def check_now(self, request, pk=None):
        """Trigger immediate check of a monitor"""
        monitor = self.get_object()
        from monitoring.tasks import check_monitor_task
        check_monitor_task.delay(monitor.id)
        return Response({'status': 'check scheduled'})
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get check results for a monitor"""
        monitor = self.get_object()
        results = CheckResult.objects.filter(monitor=monitor).order_by('-checked_at')[:100]
        serializer = CheckResultSerializer(results, many=True)
        return Response(serializer.data)


# Web Authentication Views
class CustomLoginView(LoginView):
    """Login view"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('web_monitoring:dashboard')


class CustomLogoutView(LoginRequiredMixin, LogoutView):
    """Logout view"""
    template_name = 'accounts/logged_out.html'
    next_page = 'web_accounts:login'


class RegisterView(CreateView):
    """User registration view"""
    form_class = CustomUserCreationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('web_accounts:login')


@login_required
def profile_view(request):
    """User profile view"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('web_accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form})


# Admin Views for User Management
class AdminUserListView(LoginRequiredMixin, ListView):
    """Display all users (admin only)"""
    template_name = 'monitoring/admin_user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    model = User
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('web_monitoring:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return User.objects.all().order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['total_active_monitors'] = Monitor.objects.filter(status='active').count()
        context['total_subscriptions'] = Subscription.objects.count()
        context['total_payments'] = Payment.objects.filter(status='completed').count()
        return context


class AdminUserDetailView(LoginRequiredMixin, DetailView):
    """Display detailed activities of a specific user (admin only)"""
    template_name = 'monitoring/admin_user_detail.html'
    context_object_name = 'target_user'
    model = User
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('web_monitoring:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # User's monitors
        context['monitors'] = Monitor.objects.filter(user=user).order_by('-created_at')
        context['monitor_count'] = context['monitors'].count()
        context['active_monitors'] = context['monitors'].filter(status='active').count()
        
        # User's subscriptions
        context['subscriptions'] = Subscription.objects.filter(user=user).order_by('-created_at')
        context['subscription_count'] = context['subscriptions'].count()
        context['active_subscriptions'] = context['subscriptions'].filter(status='active').count()
        
        # User's payments
        context['payments'] = Payment.objects.filter(user=user).order_by('-created_at')[:10]
        context['payment_count'] = Payment.objects.filter(user=user).count()
        context['total_spent'] = Payment.objects.filter(user=user, status='completed').aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # User's check results (recent)
        context['recent_checks'] = CheckResult.objects.filter(
            monitor__user=user
        ).order_by('-checked_at')[:20]
        
        # User's notifications (recent)
        context['recent_notifications'] = Notification.objects.filter(
            user=user
        ).order_by('-created_at')[:10]
        
        # Account info
        context['user_joined'] = user.date_joined
        context['last_login'] = user.last_login
        
        return context
