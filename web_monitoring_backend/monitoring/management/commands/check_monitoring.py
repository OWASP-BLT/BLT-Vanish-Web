"""
Management command for checking all active monitors
Step 2: Develop management command for web content monitoring

This command:
1. Fetches all active monitors
2. Uses BeautifulSoup to extract page content
3. Checks for keyword presence
4. Creates CheckResult records
5. Sends notifications when keywords are found
6. Handles errors gracefully
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from monitoring.models import Monitor, CheckResult, Notification
from accounts.models import Subscription
from monitoring.email_service import send_subscription_expiring_email
from datetime import timedelta
import requests
from bs4 import BeautifulSoup
import logging
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check all active monitors for keyword presence'

    def add_arguments(self, parser):
        parser.add_argument(
            '--monitor-id',
            type=int,
            help='Check specific monitor by ID',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Check all monitors for specific user',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output',
        )

    def handle(self, *args, **options):
        self.verbose = options.get('verbose', False)
        start_time = timezone.now()
        
        # Get monitors to check
        monitors = self.get_monitors_to_check(options)
        
        if not monitors:
            self.stdout.write(self.style.WARNING('No monitors to check'))
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Checking {monitors.count()} monitors...')
        )
        
        checked_count = 0
        keyword_found_count = 0
        error_count = 0
        skipped_expired = 0
        warned_expiring = 0
        
        for monitor in monitors:
            # CHECK 1: Verify subscription exists and is active for this user
            subscription = Subscription.objects.filter(
                user=monitor.user,
                status='active'
            ).first()
            
            if not subscription:
                logger.warning(f"Monitor {monitor.id} has no active subscription. Skipping.")
                self.stdout.write(self.style.WARNING(f"  Monitor {monitor.id}: No active subscription found"))
                skipped_expired += 1
                continue
            
            # CHECK 2: Check if subscription has expired
            now = timezone.now()
            if subscription.expires_at and subscription.expires_at < now:
                logger.info(f"Monitor {monitor.id} subscription expired on {subscription.expires_at}. Stopping monitoring.")
                self.stdout.write(self.style.ERROR(f"  Monitor {monitor.id}: Subscription EXPIRED on {subscription.expires_at}. Stopping checks."))
                
                # Pause the monitor
                monitor.status = 'paused'
                monitor.save()
                
                # Update subscription status to expired
                subscription.status = 'expired'
                subscription.save()
                
                # Create notification
                Notification.objects.create(
                    user=monitor.user,
                    notification_type='subscription_expired',
                    status='sent',
                    recipient_email=monitor.user.email,
                    subject=f'Subscription Expired: {monitor.url}',
                    message=f'Your subscription for monitoring {monitor.url} has expired. Please renew to continue monitoring.'
                )
                
                skipped_expired += 1
                continue
            
            # CHECK 3: Send warning email if subscription expires in 7 days
            days_until_expiry = (subscription.expires_at - now).days if subscription.expires_at else -1
            if days_until_expiry == 7:
                logger.info(f"Subscription {subscription.id} expires in 7 days. Sending warning.")
                self.stdout.write(self.style.WARNING(f"  Monitor {monitor.id}: Subscription expires in 7 days. Sending warning email."))
                
                try:
                    send_subscription_expiring_email(subscription)
                    warned_expiring += 1
                except Exception as e:
                    logger.error(f"Error sending expiration warning for subscription {subscription.id}: {str(e)}")
            
            # NOW RUN THE CHECK (only if subscription is active and not expired)
            try:
                result = self.check_monitor(monitor)
                checked_count += 1
                
                if result['keyword_found']:
                    keyword_found_count += 1
                    self.send_alert_notification(monitor, result)
                
                if self.verbose:
                    status = "FOUND" if result['keyword_found'] else "NOT FOUND"
                    self.stdout.write(
                        f"  {monitor.keyword} on {monitor.url}: {status}"
                    )
            
            except Exception as e:
                error_count += 1
                logger.error(f"Error checking monitor {monitor.id}: {str(e)}")
                if self.verbose:
                    self.stdout.write(
                        self.style.ERROR(f"  Error: {str(e)}")
                    )
                # Store error in CheckResult
                CheckResult.objects.create(
                    monitor=monitor,
                    keyword_found=False,
                    http_status=None,
                    error_message=str(e)
                )
            
            # Add small delay to avoid rate limiting
            time.sleep(0.5)
        
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        
        # Summary output
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Checked: {checked_count} monitors'
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f'⚠ Found: {keyword_found_count} alerts'
            )
        )
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'✗ Errors: {error_count}'
                )
            )
        if skipped_expired > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'⏸ Skipped (expired/inactive): {skipped_expired}'
                )
            )
        if warned_expiring > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⏰ Expiration warnings sent: {warned_expiring}'
                )
            )
        self.stdout.write(
            self.style.SUCCESS(
                f'⏱ Duration: {duration:.2f} seconds'
            )
        )

    def get_monitors_to_check(self, options):
        """Get monitors to check based on command options"""
        if options.get('monitor_id'):
            monitors = Monitor.objects.filter(
                id=options['monitor_id'],
                status='active'
            )
        elif options.get('user_id'):
            monitors = Monitor.objects.filter(
                user_id=options['user_id'],
                status='active'
            )
        else:
            # Get all active monitors that need checking
            monitors = Monitor.objects.filter(status='active')
            monitors = [m for m in monitors if m.needs_check()]
            monitors = Monitor.objects.filter(
                id__in=[m.id for m in monitors]
            )
        
        return monitors

    def check_monitor(self, monitor):
        """
        Check a single monitor for keyword presence
        Returns dict with: keyword_found, page_title, page_excerpt, http_status, response_time_ms
        """
        start_time = time.time()
        
        try:
            # Fetch the URL
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(
                monitor.url,
                headers=headers,
                timeout=10,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract page title
            page_title = soup.title.string if soup.title else ''
            
            # Get full text content
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Check if keyword exists (case-insensitive)
            keyword_found = monitor.keyword.lower() in text_content.lower()
            
            # Extract excerpt (context around keyword if found)
            excerpt = ''
            if keyword_found:
                # Find context window around keyword
                lower_text = text_content.lower()
                keyword_pos = lower_text.find(monitor.keyword.lower())
                start = max(0, keyword_pos - 100)
                end = min(len(text_content), keyword_pos + len(monitor.keyword) + 100)
                excerpt = text_content[start:end]
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Create CheckResult record
            CheckResult.objects.create(
                monitor=monitor,
                keyword_found=keyword_found,
                page_title=page_title[:255],
                page_excerpt=excerpt[:1000],
                http_status=response.status_code,
                response_time_ms=int(response_time)
            )
            
            # Update monitor's last_checked_time
            monitor.mark_checked(found=keyword_found)
            
            return {
                'keyword_found': keyword_found,
                'page_title': page_title,
                'page_excerpt': excerpt,
                'http_status': response.status_code,
                'response_time_ms': int(response_time)
            }
        
        except requests.RequestException as e:
            response_time = (time.time() - start_time) * 1000
            CheckResult.objects.create(
                monitor=monitor,
                keyword_found=False,
                http_status=None,
                error_message=str(e),
                response_time_ms=int(response_time)
            )
            monitor.status = 'error'
            monitor.last_checked_time = timezone.now()
            monitor.save()
            raise

    def send_alert_notification(self, monitor, check_result):
        """Send notification when keyword is found"""
        try:
            # Create notification record
            subject = f"Alert: '{monitor.keyword}' found on {monitor.url}"
            message = f"""
Keyword Alert
=============

Your monitored keyword '{monitor.keyword}' has been found on:
{monitor.url}

Title: {check_result.get('page_title', 'N/A')}
Found: {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Excerpt:
{check_result.get('page_excerpt', 'N/A')}

---
SelfErase Web Monitoring System
"""
            
            notification = Notification.objects.create(
                monitor=monitor,
                user=monitor.user,
                notification_type='keyword_found',
                delivery_method='email' if monitor.alert_email else 'sms' if monitor.alert_sms else 'email',
                subject=subject,
                message=message,
                recipient_email=monitor.user.email if monitor.alert_email else '',
                recipient_phone=self.get_user_phone(monitor.user) if monitor.alert_sms else '',
                status='pending'
            )
            
            # Send email if enabled
            if monitor.alert_email and monitor.user.email:
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [monitor.user.email],
                        fail_silently=False,
                    )
                    notification.status = 'sent'
                    notification.sent_at = timezone.now()
                except Exception as e:
                    logger.error(f"Failed to send email notification: {str(e)}")
                    notification.status = 'failed'
                    notification.error_message = str(e)
            
            # Send SMS if enabled (would integrate with Twilio)
            if monitor.alert_sms:
                # TODO: Implement Twilio SMS sending
                pass
            
            notification.save()
        
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")

    def get_user_phone(self, user):
        """Get user's phone number for SMS notifications"""
        # TODO: Implement user phone storage and retrieval
        return None
