"""
Django admin configuration for monitoring and accounts apps
"""

from django.contrib import admin
from django.utils.html import format_html
from monitoring.models import Monitor, CheckResult, Notification
from accounts.models import Subscription, Payment, BudgetAllocation


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    """Admin interface for Monitor model"""
    
    list_display = ('keyword', 'url_display', 'user', 'status_badge', 'last_checked_time')
    list_filter = ('status', 'created_at', 'alert_email', 'alert_sms')
    search_fields = ('keyword', 'url', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'last_checked_time', 'last_found_time')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'url', 'keyword', 'notes')
        }),
        ('Monitoring Settings', {
            'fields': ('status', 'check_interval_days', 'alert_email', 'alert_sms')
        }),
        ('Timestamps', {
            'fields': ('last_checked_time', 'last_found_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def url_display(self, obj):
        return obj.url[:50] + '...' if len(obj.url) > 50 else obj.url
    url_display.short_description = 'URL'
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'paused': 'orange',
            'stopped': 'gray',
            'error': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    """Admin interface for CheckResult model"""
    
    list_display = ('monitor', 'checked_at', 'keyword_found_badge', 'http_status', 'response_time_ms')
    list_filter = ('keyword_found', 'checked_at', 'http_status')
    search_fields = ('monitor__keyword', 'monitor__url', 'monitor__user__username')
    readonly_fields = ('checked_at', 'monitor')
    
    def keyword_found_badge(self, obj):
        color = 'red' if obj.keyword_found else 'green'
        text = 'FOUND' if obj.keyword_found else 'NOT FOUND'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            text
        )
    keyword_found_badge.short_description = 'Keyword'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model"""
    
    list_display = ('user', 'notification_type', 'delivery_method', 'status_badge', 'created_at')
    list_filter = ('notification_type', 'status', 'created_at')
    search_fields = ('user__username', 'subject')
    readonly_fields = ('created_at', 'sent_at')
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'sent': 'green',
            'failed': 'red',
            'bounced': 'red'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for Subscription model"""
    
    list_display = ('keyword', 'user', 'status_badge', 'cost_per_month', 'expires_at')
    list_filter = ('status', 'check_frequency', 'created_at')
    search_fields = ('keyword', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'keyword', 'check_frequency')
        }),
        ('Pricing', {
            'fields': ('cost_per_month', 'status')
        }),
        ('Expiration', {
            'fields': ('expires_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'paused': 'orange',
            'cancelled': 'red',
            'expired': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model"""
    
    list_display = ('user', 'amount', 'payment_type', 'payment_method', 'status_badge', 'created_at')
    list_filter = ('payment_type', 'payment_method', 'status', 'created_at')
    search_fields = ('user__username', 'transaction_id')
    readonly_fields = ('created_at', 'completed_at', 'transaction_id')
    
    def status_badge(self, obj):
        colors = {
            'pending': 'orange',
            'completed': 'green',
            'failed': 'red',
            'refunded': 'gray'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    """Admin interface for BudgetAllocation model"""
    
    list_display = ('month', 'total_revenue', 'infrastructure_amount', 'development_amount')
    readonly_fields = (
        'infrastructure_amount', 'development_amount',
        'privacy_research_amount', 'legal_amount', 'reserve_amount',
        'created_at', 'updated_at'
    )
    
    fieldsets = (
        ('Month', {
            'fields': ('month', 'total_revenue')
        }),
        ('Allocation Percentages', {
            'fields': (
                'infrastructure_percent', 'development_percent',
                'privacy_research_percent', 'legal_percent', 'reserve_percent'
            )
        }),
        ('Calculated Amounts (Auto)', {
            'fields': (
                'infrastructure_amount', 'development_amount',
                'privacy_research_amount', 'legal_amount', 'reserve_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
