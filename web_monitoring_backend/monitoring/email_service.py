"""
Email notification service for keyword detection
Handles sending alerts when monitored keywords are found on web pages
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from monitoring.models import Notification
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def send_keyword_found_email(monitor, check_result):
    """
    Send email notification when a keyword is found
    
    Args:
        monitor: Monitor instance that detected the keyword
        check_result: CheckResult instance with the detection details
    """
    try:
        user = monitor.user
        
        # Check if user wants email alerts
        if not monitor.alert_email:
            logger.info(f"User {user.username} has email alerts disabled for monitor {monitor.id}")
            return False
        
        # Prepare email content
        subject = f"🔔 Keyword Found: '{monitor.keyword}' on {monitor.url}"
        
        context = {
            'user': user,
            'monitor': monitor,
            'check_result': check_result,
            'keyword': monitor.keyword,
            'url': monitor.url,
            'found_at': check_result.checked_at,
            'page_title': check_result.page_title,
            'page_excerpt': check_result.page_excerpt,
            'http_status': check_result.http_status,
            'response_time_ms': check_result.response_time_ms,
        }
        
        # Render HTML email template
        html_message = render_to_string('monitoring/emails/keyword_found.html', context)
        plain_message = render_to_string('monitoring/emails/keyword_found.txt', context)
        
        # Create notification record
        notification = Notification.objects.create(
            user=user,
            monitor=monitor,
            notification_type='keyword_found',
            delivery_method='email',
            status='pending',
            subject=subject,
            message=plain_message,
            recipient_email=user.email,
        )
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        
        result = email.send()
        
        if result > 0:
            # Update notification status
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            logger.info(f"Keyword found email sent to {user.email} for monitor {monitor.id}")
            return True
        else:
            notification.status = 'failed'
            notification.save()
            logger.error(f"Failed to send keyword found email to {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending keyword found email: {str(e)}")
        return False


def send_check_failed_email(monitor, error_message):
    """
    Send email notification when a check fails
    
    Args:
        monitor: Monitor instance
        error_message: Error message from the failed check
    """
    try:
        user = monitor.user
        
        subject = f"⚠️ Check Failed: '{monitor.keyword}' on {monitor.url}"
        
        context = {
            'user': user,
            'monitor': monitor,
            'error_message': error_message,
            'url': monitor.url,
            'keyword': monitor.keyword,
            'failed_at': timezone.now(),
        }
        
        # Render email templates
        html_message = render_to_string('monitoring/emails/check_failed.html', context)
        plain_message = render_to_string('monitoring/emails/check_failed.txt', context)
        
        # Create notification record
        notification = Notification.objects.create(
            user=user,
            monitor=monitor,
            notification_type='check_failed',
            delivery_method='email',
            status='pending',
            subject=subject,
            message=plain_message,
            recipient_email=user.email,
        )
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        
        result = email.send()
        
        if result > 0:
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            logger.info(f"Check failed email sent to {user.email} for monitor {monitor.id}")
            return True
        else:
            notification.status = 'failed'
            notification.save()
            logger.error(f"Failed to send check failed email to {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending check failed email: {str(e)}")
        return False


def send_subscription_expiring_email(subscription):
    """
    Send email notification when subscription is about to expire (within 7 days)
    
    Args:
        subscription: Subscription instance
    """
    try:
        user = subscription.user
        
        subject = f"⏰ Your SelfErase Subscription Expiring Soon: {subscription.keyword}"
        
        context = {
            'user': user,
            'subscription': subscription,
            'keyword': subscription.keyword,
            'expires_at': subscription.expires_at,
            'days_remaining': (subscription.expires_at - timezone.now()).days,
        }
        
        # Render email templates
        html_message = render_to_string('monitoring/emails/subscription_expiring.html', context)
        plain_message = render_to_string('monitoring/emails/subscription_expiring.txt', context)
        
        # Create notification record
        notification = Notification.objects.create(
            user=user,
            notification_type='subscription_expiring',
            delivery_method='email',
            status='pending',
            subject=subject,
            message=plain_message,
            recipient_email=user.email,
        )
        
        # Send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        
        result = email.send()
        
        if result > 0:
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            logger.info(f"Subscription expiring email sent to {user.email}")
            return True
        else:
            notification.status = 'failed'
            notification.save()
            logger.error(f"Failed to send subscription expiring email to {user.email}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending subscription expiring email: {str(e)}")
        return False
