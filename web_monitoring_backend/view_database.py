#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from monitoring.models import Monitor, CheckResult, Notification
from accounts.models import Subscription, Payment, BudgetAllocation

print("\n" + "="*80)
print("DATABASE CONTENTS - SelfErase Web Monitoring")
print("="*80)

# USERS
print("\n" + "█"*80)
print("👤 REGISTERED USERS")
print("█"*80)
users = User.objects.all()
print(f"\nTotal Users: {users.count()}\n")

if users.count() == 0:
    print("❌ No users registered yet\n")
else:
    for user in users:
        print(f"┌─ ID: {user.id}")
        print(f"├─ Username: {user.username}")
        print(f"├─ Email: {user.email}")
        print(f"├─ Full Name: {user.first_name} {user.last_name}".strip())
        print(f"├─ Active: {'✓' if user.is_active else '✗'}")
        print(f"├─ Staff: {'✓' if user.is_staff else '✗'}")
        print(f"├─ Superuser: {'✓' if user.is_superuser else '✗'}")
        print(f"├─ Joined: {user.date_joined}")
        print(f"├─ Last Login: {user.last_login}")
        print(f"└─ Password Hash: {user.password[:40]}...\n")

# MONITORS
print("\n" + "█"*80)
print("📊 MONITORS")
print("█"*80)
monitors = Monitor.objects.all()
print(f"\nTotal Monitors: {monitors.count()}\n")

if monitors.count() == 0:
    print("❌ No monitors created yet\n")
else:
    for monitor in monitors:
        print(f"┌─ ID: {monitor.id}")
        print(f"├─ User: {monitor.user.username if monitor.user else 'N/A'}")
        print(f"├─ Keyword: {monitor.keyword}")
        print(f"├─ Status: {monitor.status}")
        print(f"├─ URL: {monitor.url}")
        print(f"├─ Created: {monitor.created_at}")
        print(f"└─ Updated: {monitor.updated_at}\n")

# CHECK RESULTS
print("\n" + "█"*80)
print("✅ CHECK RESULTS")
print("█"*80)
results = CheckResult.objects.all()
print(f"\nTotal Results: {results.count()}\n")

if results.count() == 0:
    print("❌ No check results yet\n")
else:
    for result in results[:5]:  # Show first 5
        print(f"┌─ ID: {result.id}")
        print(f"├─ Monitor: {result.monitor.keyword if result.monitor else 'N/A'}")
        print(f"├─ Status: {result.status}")
        print(f"├─ Found: {'✓' if result.keyword_found else '✗'}")
        print(f"├─ Timestamp: {result.timestamp}")
        print(f"└─ Result: {result.result_text[:50]}...\n")
    if results.count() > 5:
        print(f"... and {results.count() - 5} more results\n")

# SUBSCRIPTIONS
print("\n" + "█"*80)
print("💳 SUBSCRIPTIONS")
print("█"*80)
subscriptions = Subscription.objects.all()
print(f"\nTotal Subscriptions: {subscriptions.count()}\n")

if subscriptions.count() == 0:
    print("❌ No subscriptions yet\n")
else:
    for sub in subscriptions:
        print(f"┌─ ID: {sub.id}")
        print(f"├─ User: {sub.user.username if sub.user else 'N/A'}")
        print(f"├─ Keyword: {sub.keyword}")
        print(f"├─ Cost: ${sub.cost_per_month}/month")
        print(f"├─ Status: {sub.status}")
        print(f"├─ Created: {sub.created_at}")
        print(f"└─ Updated: {sub.updated_at}\n")

# PAYMENTS
print("\n" + "█"*80)
print("💰 PAYMENTS")
print("█"*80)
payments = Payment.objects.all()
print(f"\nTotal Payments: {payments.count()}\n")

if payments.count() == 0:
    print("❌ No payments yet\n")
else:
    for payment in payments:
        print(f"┌─ ID: {payment.id}")
        print(f"├─ User: {payment.user.username if payment.user else 'N/A'}")
        print(f"├─ Amount: ${payment.amount}")
        print(f"├─ Status: {payment.status}")
        print(f"├─ Transaction ID: {payment.transaction_id}")
        print(f"├─ Created: {payment.created_at}")
        print(f"└─ Updated: {payment.updated_at}\n")

# BUDGET ALLOCATIONS
print("\n" + "█"*80)
print("💵 BUDGET ALLOCATIONS")
print("█"*80)
budgets = BudgetAllocation.objects.all()
print(f"\nTotal Budget Allocations: {budgets.count()}\n")

if budgets.count() == 0:
    print("❌ No budget allocations yet\n")
else:
    for budget in budgets:
        print(f"┌─ ID: {budget.id}")
        print(f"├─ User: {budget.user.username if budget.user else 'N/A'}")
        print(f"├─ Monthly Limit: ${budget.monthly_budget_limit}")
        print(f"├─ Remaining: ${budget.remaining_budget}")
        print(f"├─ Created: {budget.created_at}")
        print(f"└─ Updated: {budget.updated_at}\n")

# SUMMARY
print("\n" + "="*80)
print("📈 DATABASE SUMMARY")
print("="*80)
print(f"✓ Users: {users.count()}")
print(f"✓ Monitors: {monitors.count()}")
print(f"✓ Check Results: {results.count()}")
print(f"✓ Subscriptions: {subscriptions.count()}")
print(f"✓ Payments: {payments.count()}")
print(f"✓ Budget Allocations: {budgets.count()}")
print("="*80 + "\n")
