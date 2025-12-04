"""
Celery tasks for the monitoring app
Handles background job execution for monitoring checks
"""

from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from monitoring.models import Monitor, CheckResult
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_all_monitors(self):
    """
    Celery task to check all active monitors
    Scheduled to run daily via Celery Beat
    """
    try:
        logger.info("Starting check_all_monitors task")
        call_command('check_monitoring', verbose=True)
        logger.info("Completed check_all_monitors task")
        return "Success"
    except Exception as exc:
        logger.error(f"Error in check_all_monitors: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def check_monitor_task(monitor_id):
    """
    Check a specific monitor
    """
    try:
        monitor = Monitor.objects.get(id=monitor_id)
        call_command('check_monitoring', '--monitor-id', str(monitor_id))
        logger.info(f"Checked monitor {monitor_id}")
        return f"Checked monitor {monitor_id}"
    except Monitor.DoesNotExist:
        logger.error(f"Monitor {monitor_id} not found")
        return f"Monitor {monitor_id} not found"
    except Exception as e:
        logger.error(f"Error checking monitor {monitor_id}: {str(e)}")
        raise


@shared_task
def cleanup_old_logs():
    """
    Clean up old check results (older than 90 days)
    Reduces database size and improves performance
    """
    from datetime import timedelta
    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count, _ = CheckResult.objects.filter(checked_at__lt=cutoff_date).delete()
    logger.info(f"Cleaned up {deleted_count} old check results")
    return f"Deleted {deleted_count} old check results"


@shared_task
def send_expiry_notifications():
    """
    Send notifications for subscriptions expiring soon
    """
    from datetime import timedelta
    from accounts.models import Subscription
    from monitoring.models import Notification
    
    # Get subscriptions expiring in 7 days
    soon = timezone.now() + timedelta(days=7)
    expiring = Subscription.objects.filter(
        expires_at__lt=soon,
        expires_at__gte=timezone.now(),
        status='active'
    )
    
    notification_count = 0
    for sub in expiring:
        # Create notification
        Notification.objects.get_or_create(
            user=sub.user,
            notification_type='subscription_expiring',
            defaults={
                'subject': f'Subscription expiring soon: {sub.keyword}',
                'message': f'Your subscription for "{sub.keyword}" monitoring expires on {sub.expires_at.date()}',
                'recipient_email': sub.user.email,
            }
        )
        notification_count += 1
    
    logger.info(f"Created {notification_count} expiry notifications")
    return f"Created {notification_count} expiry notifications"
