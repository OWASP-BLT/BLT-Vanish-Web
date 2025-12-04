"""
Models for the monitoring app - Core Step 1
Defines Monitor, CheckResult, and Notification models
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Monitor(models.Model):
    """
    Monitor: Tracks web content monitoring for specific URLs and keywords
    Core entity for the SelfErase web monitoring system
    
    Fields:
    - url: Target webpage URL to monitor
    - keyword: Keyword/phrase to search for in the page content
    - last_checked_time: Timestamp of most recent check
    - status: Current monitoring status (active/paused/stopped)
    - user: ForeignKey relation to the User model who owns this monitor
    """
    
    STATUS_CHOICES = [
        ('active', 'Active - Actively monitoring'),
        ('paused', 'Paused - Monitoring paused'),
        ('stopped', 'Stopped - No longer monitoring'),
        ('error', 'Error - Last check failed'),
    ]
    
    # Core fields
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='monitors',
        help_text="User who owns this monitor"
    )
    url = models.URLField(
        max_length=2048,
        help_text="URL of webpage to monitor"
    )
    keyword = models.CharField(
        max_length=255,
        help_text="Keyword or phrase to search for"
    )
    
    # Monitoring state
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current monitoring status"
    )
    last_checked_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the URL was last checked"
    )
    last_found_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When keyword was last found"
    )
    
    # Configuration
    check_interval_days = models.PositiveIntegerField(
        default=1,
        help_text="How often to check (in days)"
    )
    alert_email = models.BooleanField(
        default=True,
        help_text="Send email alert when keyword found"
    )
    alert_sms = models.BooleanField(
        default=False,
        help_text="Send SMS alert when keyword found"
    )
    
    # Metadata
    notes = models.TextField(
        blank=True,
        help_text="User notes about this monitor"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Monitor'
        verbose_name_plural = 'Monitors'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['last_checked_time']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.keyword} on {self.url}"
    
    def needs_check(self):
        """Determine if this monitor needs to be checked based on check_interval"""
        if self.status != 'active':
            return False
        if self.last_checked_time is None:
            return True
        time_since_check = timezone.now() - self.last_checked_time
        return time_since_check.days >= self.check_interval_days
    
    def mark_checked(self, found=False):
        """Update monitor after a check is performed"""
        self.last_checked_time = timezone.now()
        if found:
            self.last_found_time = timezone.now()
        self.save()


class CheckResult(models.Model):
    """
    Stores results of each keyword check
    Provides audit trail and historical data for analysis
    """
    
    monitor = models.ForeignKey(
        Monitor,
        on_delete=models.CASCADE,
        related_name='check_results',
        help_text="Monitor this check belongs to"
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    keyword_found = models.BooleanField(
        help_text="Whether keyword was found in page content"
    )
    page_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Title of the webpage"
    )
    page_excerpt = models.TextField(
        blank=True,
        help_text="Excerpt of page content where keyword was found"
    )
    http_status = models.IntegerField(
        null=True,
        blank=True,
        help_text="HTTP response status code"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if check failed"
    )
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time taken to fetch and process page (milliseconds)"
    )
    
    class Meta:
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['monitor', 'checked_at']),
            models.Index(fields=['keyword_found']),
        ]
    
    def __str__(self):
        status = "Found" if self.keyword_found else "Not found"
        return f"{self.monitor.keyword} - {status} - {self.checked_at}"


class Notification(models.Model):
    """
    Notification record - tracks alerts sent to users
    Integrates with email and SMS services
    """
    
    TYPE_CHOICES = [
        ('keyword_found', 'Keyword Found Alert'),
        ('check_failed', 'Check Failed Alert'),
        ('subscription_expiring', 'Subscription Expiring'),
        ('payment_failed', 'Payment Failed'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('both', 'Both Email and SMS'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    monitor = models.ForeignKey(
        Monitor,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    delivery_method = models.CharField(
        max_length=10,
        choices=DELIVERY_METHOD_CHOICES,
        default='email'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    subject = models.CharField(max_length=255)
    message = models.TextField()
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    external_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="External service ID (Twilio SID, SendGrid message ID, etc.)"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.notification_type} - {self.status}"
