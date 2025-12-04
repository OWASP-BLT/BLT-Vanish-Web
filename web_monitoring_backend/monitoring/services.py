"""
Notification services for sending emails and SMS
Integrates with Django email and Twilio SMS
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from monitoring.models import Notification
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications"""
    
    @staticmethod
    def send_keyword_found_alert(monitor, check_result):
        """Send email when keyword is found"""
        try:
            context = {
                'keyword': monitor.keyword,
                'url': monitor.url,
                'page_title': check_result.get('page_title', 'N/A'),
                'timestamp': timezone.now(),
                'excerpt': check_result.get('page_excerpt', 'N/A'),
            }
            
            subject = f"Alert: '{monitor.keyword}' found on {monitor.url}"
            html_message = render_to_string('monitoring/email/keyword_found.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [monitor.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Sent keyword found alert to {monitor.user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send keyword found alert: {str(e)}")
            return False
    
    @staticmethod
    def send_subscription_expiring_soon(subscription):
        """Send reminder that subscription is expiring"""
        try:
            context = {
                'keyword': subscription.keyword,
                'expiration_date': subscription.expires_at.date(),
            }
            
            subject = f"Your '{subscription.keyword}' subscription expires soon"
            html_message = render_to_string('monitoring/email/subscription_expiring.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [subscription.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Sent subscription expiring alert to {subscription.user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send subscription expiring alert: {str(e)}")
            return False
    
    @staticmethod
    def send_check_failed_alert(monitor, error_message):
        """Send alert when a check fails"""
        try:
            context = {
                'keyword': monitor.keyword,
                'url': monitor.url,
                'error': error_message,
                'timestamp': timezone.now(),
            }
            
            subject = f"Monitor Error: Could not check {monitor.url}"
            html_message = render_to_string('monitoring/email/check_failed.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [monitor.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            logger.info(f"Sent check failed alert to {monitor.user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send check failed alert: {str(e)}")
            return False


class SMSNotificationService:
    """Service for sending SMS notifications via Twilio"""
    
    @staticmethod
    def send_keyword_found_alert(monitor, phone_number):
        """Send SMS when keyword is found"""
        try:
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            message_body = f"SelfErase: '{monitor.keyword}' found on {monitor.url}"
            
            message = client.messages.create(
                body=message_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"Sent SMS alert to {phone_number}: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {str(e)}")
            return False
    
    @staticmethod
    def send_subscription_expiring_soon(subscription, phone_number):
        """Send SMS reminder that subscription is expiring"""
        try:
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            message_body = f"SelfErase: Your '{subscription.keyword}' subscription expires on {subscription.expires_at.date()}"
            
            message = client.messages.create(
                body=message_body,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"Sent SMS reminder to {phone_number}: {message.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS reminder: {str(e)}")
            return False


class NotificationManager:
    """Unified notification manager"""
    
    @staticmethod
    def notify_keyword_found(monitor, check_result):
        """Send notification when keyword is found"""
        success = False
        
        # Send email if enabled
        if monitor.alert_email:
            success = EmailNotificationService.send_keyword_found_alert(
                monitor,
                check_result
            )
        
        # Send SMS if enabled
        if monitor.alert_sms:
            phone = NotificationManager.get_user_phone(monitor.user)
            if phone:
                success = SMSNotificationService.send_keyword_found_alert(
                    monitor,
                    phone
                )
        
        return success
    
    @staticmethod
    def notify_subscription_expiring(subscription):
        """Send notification that subscription is expiring soon"""
        success = False
        
        # Always send email
        success = EmailNotificationService.send_subscription_expiring_soon(subscription)
        
        # Send SMS if user prefers
        # TODO: Check user notification preferences
        phone = NotificationManager.get_user_phone(subscription.user)
        if phone:
            SMSNotificationService.send_subscription_expiring_soon(subscription, phone)
        
        return success
    
    @staticmethod
    def notify_check_failed(monitor, error_message):
        """Send notification when check fails"""
        return EmailNotificationService.send_check_failed_alert(monitor, error_message)
    
    @staticmethod
    def get_user_phone(user):
        """Get user's phone number from their profile"""
        # TODO: Implement user profile with phone number storage
        return None
