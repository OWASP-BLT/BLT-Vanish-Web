#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

u = User.objects.get(username='admin')
u.set_password('test123456')
u.save()
print('✅ Password set: admin / test123456')
