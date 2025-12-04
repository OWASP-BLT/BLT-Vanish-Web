"""
Django REST Framework serializers for API endpoints
"""

from rest_framework import serializers
from monitoring.models import Monitor, CheckResult, Notification
from accounts.models import Subscription, Payment


class MonitorSerializer(serializers.ModelSerializer):
    """Serializer for Monitor model"""
    
    class Meta:
        model = Monitor
        fields = [
            'id', 'url', 'keyword', 'status', 'last_checked_time',
            'last_found_time', 'check_interval_days', 'alert_email',
            'alert_sms', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_checked_time', 'last_found_time']


class CheckResultSerializer(serializers.ModelSerializer):
    """Serializer for CheckResult model"""
    
    class Meta:
        model = CheckResult
        fields = [
            'id', 'monitor', 'checked_at', 'keyword_found', 'page_title',
            'page_excerpt', 'http_status', 'error_message', 'response_time_ms'
        ]
        read_only_fields = ['id', 'checked_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'monitor', 'notification_type', 'delivery_method',
            'status', 'subject', 'message', 'created_at', 'sent_at'
        ]
        read_only_fields = ['id', 'created_at', 'sent_at']


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model"""
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'keyword', 'check_frequency', 'status',
            'cost_per_month', 'created_at', 'expires_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    class Meta:
        model = Payment
        fields = [
            'id', 'amount', 'payment_type', 'payment_method',
            'status', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at']
