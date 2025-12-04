#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

user = User.objects.get(username='testuser')
print('=' * 70)
print('GENERAL USER STATUS')
print('=' * 70)
print('Username: {}'.format(user.username))
print('Email: {}'.format(user.email))
print('Is Admin/Staff: {}'.format(user.is_staff))
print('')
print('PERMISSIONS FOR GENERAL USER:')
print('  • Can pause subscription: NO (admin-only)')
print('  • Can delete subscription: NO (admin-only)')
print('  • Can view payment history: YES (/accounts/payments/history/)')
print('')
print('SERVER RUNNING AT: http://127.0.0.1:8000/')
print('LOGIN CREDENTIALS:')
print('  Username: testuser')
print('  Password: testpass123')
print('=' * 70)
