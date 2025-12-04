"""
Celery configuration for SelfErase Web Monitoring Backend
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'check-monitoring-daily': {
        'task': 'monitoring.tasks.check_all_monitors',
        'schedule': crontab(hour=0, minute=0),  # Run at midnight UTC daily
    },
    'cleanup-old-logs-weekly': {
        'task': 'monitoring.tasks.cleanup_old_logs',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Sunday 2 AM UTC
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
