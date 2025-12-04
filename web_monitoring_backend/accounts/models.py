"""
Models for user accounts, subscriptions, and payment tracking
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator

class Subscription(models.Model):
    """
    User subscription for keyword monitoring.
    Each subscription covers monitoring of one keyword with specified check frequency.
    """
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    keyword = models.CharField(max_length=255, help_text="Keyword to monitor")
    check_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='daily',
        help_text="How often to check for this keyword"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    cost_per_month = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1.00,
        validators=[MinValueValidator(0)],
        help_text="Cost in USD per month"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When subscription expires (null = never)"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.keyword}"
    
    def is_expired(self):
        """Check if subscription has expired"""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
    
    def renew(self, days=30):
        """Renew subscription for specified days"""
        self.expires_at = timezone.now() + timezone.timedelta(days=days)
        self.status = 'active'
        self.save()


class Payment(models.Model):
    """
    Track payments for subscriptions and keyword discovery
    """
    
    PAYMENT_TYPE_CHOICES = [
        ('subscription', 'Subscription'),
        ('discovery', 'Keyword Discovery'),
        ('credit', 'Credit'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
        ('manual', 'Manual'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='stripe'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="External payment processor transaction ID"
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    description = models.TextField(blank=True, help_text="Payment description")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - ${self.amount} - {self.status}"
    
    def mark_completed(self):
        """Mark payment as completed"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()


class BudgetAllocation(models.Model):
    """
    Tracks how subscription revenue is allocated to platform fund
    Provides transparency on where user money goes
    """
    
    ALLOCATION_TYPE_CHOICES = [
        ('infrastructure', 'Infrastructure & Hosting'),
        ('development', 'Development & Operations'),
        ('privacy_research', 'Privacy Research'),
        ('legal', 'Legal & Compliance'),
        ('reserve', 'Reserve Fund'),
    ]
    
    month = models.DateField(
        help_text="Month for which this allocation applies (always 1st of month)"
    )
    total_revenue = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    infrastructure_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    infrastructure_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=40,
        validators=[MinValueValidator(0)]
    )
    development_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    development_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=30,
        validators=[MinValueValidator(0)]
    )
    privacy_research_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    privacy_research_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15,
        validators=[MinValueValidator(0)]
    )
    legal_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    legal_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        validators=[MinValueValidator(0)]
    )
    reserve_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    reserve_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5,
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-month']
        unique_together = ['month']
        verbose_name_plural = "Budget Allocations"
    
    def __str__(self):
        return f"Budget Allocation - {self.month.strftime('%Y-%m')}"
    
    def calculate_allocations(self):
        """Calculate dollar amounts based on percentages and total revenue"""
        self.infrastructure_amount = (self.total_revenue * self.infrastructure_percent / 100)
        self.development_amount = (self.total_revenue * self.development_percent / 100)
        self.privacy_research_amount = (self.total_revenue * self.privacy_research_percent / 100)
        self.legal_amount = (self.total_revenue * self.legal_percent / 100)
        self.reserve_amount = (self.total_revenue * self.reserve_percent / 100)
    
    def save(self, *args, **kwargs):
        """Auto-calculate allocations before saving"""
        self.calculate_allocations()
        super().save(*args, **kwargs)
