# SelfErase Web Monitoring Backend - Complete Workflow Documentation

## Table of Contents

1. [Overview](#overview)
2. [Visual Workflow Diagrams](#visual-workflow-diagrams)
3. [Monitor Creation Workflow](#monitor-creation-workflow)
4. [Subscription Management](#subscription-management)
5. [Payment Processing](#payment-processing)
6. [User Features](#user-features)
7. [Admin Features](#admin-features)
8. [Email Notification System](#email-notification-system)
9. [Setup and Installation](#setup-and-installation)
10. [Running Tests](#running-tests)
11. [Example Workflows](#example-workflows)

---

## Overview

SelfErase is a web monitoring platform that allows users to:
- Create monitors to track specific URLs for keyword changes
- Subscribe to monitoring plans (Standard: $1/month, Discovery: $5/month)
- Receive email notifications when keywords are found, checks fail, or subscriptions expire
- Manage their monitors, subscriptions, and payment history

The platform integrates with:
- **Django** for the backend API
- **Stripe** for payment processing
- **Gmail SMTP** for email delivery
- **BeautifulSoup4** for web scraping and keyword detection

---

## Visual Workflow Diagrams

### Complete User Flow - Monitor Creation to Active Monitoring

```
┌─────────────────────────────────────────────────────────────────┐
│                         START: LOGIN                            │
│                    testuser / testpass123                       │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │   STEP 1: CREATE   │
        │     MONITOR        │
        └────────────────────┘
        
    ┌───────────────────────────────┐
    │  Form Fields:                 │
    │  • URL to monitor             │
    │  • Keyword to search for      │
    │  • Check interval (days)      │
    │  • Email alerts (optional)    │
    │  • SMS alerts (optional)      │
    │  • Notes (optional)           │
    └───────────────────────────────┘
    
    [Button: "Next: Select Plan" (creates monitor, saves to DB)]
                 │
                 ▼
        ┌────────────────────────────┐
        │ STEP 2: SELECT PLAN        │
        │ (Plan Selection Page)      │
        └────────────────────────────┘
        
    ┌──────────────────────────┬──────────────────────────┐
    │    STANDARD PLAN         │    DISCOVERY PLAN        │
    │    ✓ $1/month            │    ✓ $5/month            │
    │    ✓ Monitor 1 keyword   │    ✓ AI-powered          │
    │    ✓ Daily checks        │    ✓ Unlimited checks    │
    │    ✓ Email alerts        │    ✓ Advanced analytics  │
    │    ✓ Basic support       │    ✓ Priority support    │
    │                          │    (RECOMMENDED)         │
    └──────────────────────────┴──────────────────────────┘
    
    ❗ KEYWORD: Auto-filled from monitor (no manual entry needed!)
    ❗ COST: Automatically set based on plan selection
    
    [Button: "Continue to Payment"]
                 │
                 ▼
        ┌────────────────────────────┐
        │ STEP 3: PAYMENT            │
        │ (Stripe Payment Form)      │
        └────────────────────────────┘
        
    ┌──────────────────────────────────────────┐
    │ Order Summary:                           │
    │ ┌──────────────────────────────────────┐ │
    │ │ Subscription: test (from monitor)    │ │
    │ │ Amount: 🔒 $1.00 or $5.00 (LOCKED)  │ │
    │ │         ^ Cannot be changed!        │ │
    │ └──────────────────────────────────────┘ │
    │                                          │
    │ Form Fields:                             │
    │ • Cardholder Name                        │
    │ • Email (pre-filled)                     │
    │ • Card Details (Stripe element)          │
    │ • Billing Address                        │
    └──────────────────────────────────────────┘
    
    💳 Test Card: 4242 4242 4242 4242
    📅 Expiry: Any future date
    🔐 CVC: Any 3 digits
    
    [Button: "Pay Now"]
                 │
                 ▼
        ┌────────────────────────────┐
        │ Stripe Payment Processing  │
        └────────────────────────────┘
                 │
          ┌──────┴──────┐
          │             │
        SUCCESS       FAILED
          │             │
          ▼             ▼
    ┌─────────────┐  Error message
    │ Payment OK  │  stays on page
    └──────┬──────┘
           │
           ▼
    ┌──────────────────────────────┐
    │ STEP 4: SUCCESS              │
    │ (Payment Success Page)       │
    └──────────────────────────────┘
    
    ✅ Success Message
    📊 Payment Details:
       • Amount: $1.00 or $5.00
       • Transaction ID: pi_xxxxx
       • Keyword: test
       • Date: 04/Dec/2025 11:50:30
    
    ✉️ Confirmation email sent
    
    [Buttons:]
    1️⃣ "Back to Monitor Details"
       └─→ Returns to the monitor created in Step 1
    
    2️⃣ "View Payment History"
       └─→ Shows all past payments
                 │
                 ▼ (if clicked button 1)
    ┌────────────────────────────┐
    │ Monitor Detail Page        │
    │ (Back to where you started)│
    │                            │
    │ ✅ Subscription ACTIVE     │
    │ ✅ Payment COMPLETED       │
    │ ✅ Ready to monitor!       │
    └────────────────────────────┘
```

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       STEP 1: CREATE MONITOR                    │
├─────────────────────────────────────────────────────────────────┤
│ Input: user_id, url, keyword, check_interval, alert_email, etc.│
│ Action: Monitor.objects.create(user=request.user, ...)         │
│ Output: monitor_id = 42                                        │
│ Redirect: /subscriptions/plan-selection/42/                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  STEP 2: SELECT SUBSCRIPTION PLAN               │
├─────────────────────────────────────────────────────────────────┤
│ Input: monitor_id=42, selected_plan='standard' or 'discovery'   │
│ Data: keyword from monitor (auto-filled, not user input!)      │
│ Cost: $1.00 (standard) or $5.00 (discovery)                    │
│                                                                 │
│ Action: Subscription.objects.create(                           │
│   user=request.user,                                           │
│   keyword='test',        # From monitor, not user input        │
│   cost_per_month=1.00,   # From plan selection                 │
│   status='pending_payment'                                     │
│ )                                                               │
│                                                                 │
│ Session: Store monitor_id and subscription_id                  │
│ Output: subscription_id = 99                                   │
│ Redirect: /payments/99/checkout/                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        STEP 3: PAYMENT                          │
├─────────────────────────────────────────────────────────────────┤
│ Input: subscription_id=99, payment details from form           │
│                                                                 │
│ Security: Amount is READ-ONLY (cannot be changed via form)     │
│          Cost is locked to: $1.00 or $5.00 (from subscription) │
│                                                                 │
│ Action: stripe.PaymentIntent.create(                           │
│   amount=100 (in cents),   # $1.00 locked                      │
│   currency='usd'                                               │
│ )                                                               │
│                                                                 │
│ IF Stripe returns status='succeeded':                          │
│   Payment.objects.create(...)                                  │
│   subscription.status = 'active'                               │
│   Output: payment_id = 777                                     │
│   Redirect: /payments/777/success/                             │
│                                                                 │
│ ELSE:                                                          │
│   Error message on same page                                   │
│   Stay on /payments/99/checkout/ for retry                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   STEP 4: SUCCESS & RETURN                      │
├─────────────────────────────────────────────────────────────────┤
│ Display: payment_id=777, subscription details, confirmation    │
│                                                                 │
│ Session: Retrieved monitor_id = 42                             │
│                                                                 │
│ Button 1 - "Back to Monitor Details":                          │
│   Action: POST request → Clear session → Redirect to monitor   │
│   Redirect: /monitors/42/                                      │
│   Display: Monitor detail page (subscription now active!)      │
│                                                                 │
│ Button 2 - "View Payment History":                             │
│   Redirect: /payments/                                         │
│   Display: All payments for this user                          │
└─────────────────────────────────────────────────────────────────┘
```

### Session Management Flow

```
REQUEST 1 (Step 1: Create Monitor)
  ↓
  Monitor created: id=42
  ↓
  REDIRECT → /subscriptions/plan-selection/42/

REQUEST 2 (Step 2: Select Plan)
  ↓
  Receive: monitor_id=42
  Get monitor, display plans
  User selects plan
  ↓
  Create Subscription: id=99
  ↓
  session['monitor_id'] = 42
  session['subscription_id'] = 99
  ↓
  REDIRECT → /payments/99/checkout/

REQUEST 3 (Step 3: Payment)
  ↓
  Receive: subscription_id=99
  Payment form displayed
  User fills form and submits
  ↓
  Stripe payment → SUCCESS
  ↓
  Create Payment: id=777
  Update subscription status
  ↓
  REDIRECT → /payments/777/success/

REQUEST 4 (Step 4: Success)
  ↓
  Receive: payment_id=777
  ↓
  Retrieve from session:
  monitor_id = 42 (from session)
  ↓
  Display success page with "Back to Monitor Details" button
  
REQUEST 5 (Step 4: Return to Monitor)
  ↓
  User POSTs from success page
  ↓
  Clear session:
  del session['monitor_id']
  del session['subscription_id']
  ↓
  REDIRECT → /monitors/42/
  ↓
  Display monitor detail page
  Monitor now shows: ✅ Subscription ACTIVE
```

### Status Indicators

```
┌─────────────────────────────────────────┐
│  Step 1: CREATE MONITOR                 │
│  ⭕ IN PROGRESS                         │
│  ↓                                      │
│  ✅ COMPLETED (monitor created)         │
│  ↓                                      │
│  Step 2: SELECT PLAN                    │
│  ⭕ IN PROGRESS                         │
│  ↓                                      │
│  ✅ COMPLETED (subscription created)    │
│  ↓                                      │
│  Step 3: PAYMENT                        │
│  ⭕ IN PROGRESS                         │
│  ↓                                      │
│  ✅ COMPLETED (payment created)         │
│  ↓                                      │
│  Step 4: SUCCESS                        │
│  ✅ COMPLETED (ready to monitor!)       │
└─────────────────────────────────────────┘
```

---

## Monitor Creation Workflow

### Step 1: Create Monitor

Users navigate to the monitor creation page and fill out the form with:

**Required Fields:**
- **URL to monitor** - The website URL to check for keyword changes
- **Keyword to search for** - The specific text to look for on the page
- **Check interval** - How often to check (in days, e.g., 1 day = daily checks)

**Optional Fields:**
- **Email alerts** - Email address to send notifications to
- **SMS alerts** - Phone number for SMS notifications
- **Notes** - Additional notes about what to monitor

**Backend Process:**
```python
# monitoring/views.py - MonitorCreateView
monitor = Monitor.objects.create(
    user=request.user,
    url=form.cleaned_data['url'],
    keyword=form.cleaned_data['keyword'],
    check_interval=form.cleaned_data['check_interval'],
    alert_email=form.cleaned_data['alert_email'],
    alert_sms=form.cleaned_data['alert_sms'],
    notes=form.cleaned_data['notes'],
    status='pending_payment'  # Not active until paid
)
# Redirect to plan selection
```

**After Step 1:**
- Monitor is created with `status='pending_payment'`
- Monitor ID is stored in session
- User is redirected to plan selection page

---

## Subscription Management

### Subscription Lifecycle

1. **Created (pending_payment)** - After user selects a plan, before payment
2. **Active** - After successful payment, monitoring is running
3. **Expiring Soon** - 7 days before expiration (warning email sent)
4. **Expired** - Subscription past expiration date, monitoring paused
5. **Cancelled** - User manually cancelled

### Auto-Renewal System

- All subscriptions are **30-day auto-renewing**
- Expiration date = creation_date + 30 days
- 7 days before expiration: warning email sent automatically
- On expiration date: monitoring automatically paused
- User can view subscription status in monitor details

### Subscription Expiration Check

The `check_monitoring.py` management command runs periodically to:

1. **Verify subscription exists** - Skip if no subscription
2. **Check if subscription is active** - Skip if paused/cancelled
3. **Check expiration date** - Compare against current time
4. **Send 7-day warning** - If exactly 7 days until expiration
5. **Auto-pause monitoring** - If subscription has expired

```python
# monitoring/management/commands/check_monitoring.py

# Check subscription status
subscription = Subscription.objects.filter(monitor=monitor).first()
if not subscription:
    continue  # Skip - no subscription

if subscription.status != 'active':
    continue  # Skip - not active

# Calculate days until expiration
now = timezone.now()
if subscription.expires_at < now:
    # Subscription has expired
    monitor.status = 'paused'
    monitor.save()
    skipped_expired += 1
    continue

# Calculate days remaining
days_until_expiry = (subscription.expires_at - now).days

# Send warning email if 7 days left
if days_until_expiry == 7:
    send_subscription_expiring_email(subscription)
    warned_expiring += 1
```

---

## Payment Processing

### Stripe Integration

**Test Credentials:**
- Test Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., 12/25)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any value (e.g., 12345)

**Payment Flow:**

1. User arrives at checkout page with subscription_id
2. Order summary shows:
   - Keyword (from monitor)
   - Amount (locked, cannot be changed)
   - Plan selected
3. User fills payment form:
   - Card details via Stripe element
   - Billing address
   - Email confirmation
4. Form submission triggers Stripe Payment Intent
5. Response handling:
   - **Success**: Create Payment record, set subscription to active
   - **Failure**: Show error message, allow retry

**Security Measures:**
- Amount is READ-ONLY in form (cannot be changed via form manipulation)
- Cost is locked to selected plan ($1 or $5)
- Stripe handles PCI compliance
- No card data stored in database

---

## User Features

### 1. Monitor Management

**View Monitors:**
- List all monitors created by user
- Shows status: pending_payment, active, paused, expired
- Shows subscription info if active
- Shows next check date

**Create Monitor:**
- Form with URL, keyword, check interval
- Optional email/SMS fields
- Creates monitor in pending_payment status

**View Monitor Details:**
- Complete monitor information
- Subscription details (plan, cost, expiration date)
- Payment history
- Recent check results
- Edit/delete options

**Edit Monitor:**
- Update URL, keyword, check interval
- Update alert preferences
- Changes take effect on next check

**Delete Monitor:**
- Removes monitor from system
- Removes associated subscription (if present)
- Stops all monitoring and notifications

### 2. Subscription Management

**View Subscriptions:**
- List all active and expired subscriptions
- Shows plan type, cost, expiration date
- Days remaining until expiration
- Renewal options

**Renew Subscription:**
- Extend expiration by another 30 days
- Same plan and cost as original
- Seamless transition

**Cancel Subscription:**
- Mark subscription as cancelled
- Stop monitoring immediately
- Cannot be undone (must create new monitor)

### 3. Payment History

**View All Payments:**
- List of all transactions
- Shows amount, date, subscription, transaction ID
- Filter by date range
- Export options (CSV)

**Payment Details:**
- Full payment information
- Receipt available
- Subscription details at time of payment

### 4. Profile Management

**User Settings:**
- Update email address
- Change password
- Set default alert preferences
- Enable/disable features

**Alert Preferences:**
- Email notifications enabled/disabled
- SMS notifications enabled/disabled
- Notification frequency settings

### 5. Search & Filter

**Find Monitors:**
- Search by URL
- Search by keyword
- Filter by status
- Sort by date created

**Find Payments:**
- Search by transaction ID
- Filter by date range
- Filter by amount

### 6. Dashboard

**Quick Stats:**
- Total monitors
- Active subscriptions
- Recent checks
- Upcoming expirations
- Quick actions

---

## Admin Features

### 1. User Management

**View All Users:**
- Paginated list of users
- Username, email, registration date
- Subscription count
- Payment count

**User Details:**
- Complete user information
- All monitors created
- All subscriptions
- All payments
- Recent check activity
- Can suspend/unsuspend account

### 2. Monitor Monitoring

**View All Monitors:**
- All monitors across all users
- Status overview
- Filter by status
- Search functionality

**Monitor Activity:**
- View recent checks
- Check results (found/not found)
- Error logs
- Performance metrics

### 3. Subscription Analytics

**Overview:**
- Active subscriptions
- Plan distribution
- Expiring soon (next 30 days)
- Expired subscriptions
- Renewal rates

**Plan Performance:**
- $1 plan adoption
- $5 plan adoption
- Churn rate
- Revenue metrics

### 4. Payment Management

**View All Payments:**
- All transactions across system
- Filter by date range
- Filter by amount
- Filter by status

**Payment Details:**
- Transaction information
- Stripe payment intent details
- User information
- Subscription details

### 5. System Health

**Error Logs:**
- All system errors
- Failed payments
- Failed email sends
- Failed checks

**Performance Metrics:**
- Check execution time
- Email send success rate
- API response times
- Database query performance

---

## Email Notification System

The system automatically sends three types of email notifications:

### 1. Keyword Found Email

**Trigger:** When a keyword is found during a web check

**Content:**
- Monitor details (URL, keyword)
- Check result (found, timestamp)
- Original page excerpt (if available)
- Action links (view monitor, view full result)

**Recipients:** 
- User's alert_email (if configured)
- Falls back to account email

**Template:** `monitoring/templates/emails/keyword_found.html` and `.txt`

**Example:**
```
Subject: ⚠️ Keyword Found: "test" on https://example.com

Hello User,

Your keyword has been found!

Monitor: https://example.com
Keyword: test
Found at: 2025-12-04 11:50:30 UTC

View the full result: [link to monitor details]

---
SelfErase Monitoring System
```

### 2. Check Failed Email

**Trigger:** When a web check fails (network error, timeout, etc.)

**Content:**
- Monitor details (URL, keyword)
- Error message (detailed technical error)
- Error timestamp
- Next check scheduled time

**Recipients:**
- User's alert_email (if configured)
- Falls back to account email

**Template:** `monitoring/templates/emails/check_failed.html` and `.txt`

**Example:**
```
Subject: ❌ Check Failed: https://example.com

Hello User,

Your monitoring check failed to complete.

Monitor: https://example.com
Error: Connection timeout after 30 seconds
Time: 2025-12-04 11:50:30 UTC

Next check will run: 2025-12-05 11:50:30 UTC

---
SelfErase Monitoring System
```

### 3. Subscription Expiring Email

**Trigger:** Automatically sent 7 days before subscription expiration

**Content:**
- Subscription details (plan, cost)
- Expiration date countdown
- Auto-renewal information
- Renewal link
- FAQ about expiration

**Recipients:**
- User's alert_email (if configured)
- Falls back to account email

**Template:** `monitoring/templates/emails/subscription_expiring.html` and `.txt`

**Example:**
```
Subject: ⏰ Your Subscription Expires in 7 Days

Hello User,

Your subscription will expire in 7 days!

Plan: Standard ($1/month)
Expires: 2025-12-11 11:50:30 UTC

Your monitoring will automatically pause when the subscription expires.

To continue monitoring, renew your subscription: [renewal link]

---
SelfErase Monitoring System
```

### Notification Tracking

All notifications are tracked in the `Notification` model:

```python
# monitoring/models.py

class Notification(models.Model):
    TYPES = [
        ('keyword_found', 'Keyword Found'),
        ('check_failed', 'Check Failed'),
        ('subscription_expiring', 'Subscription Expiring'),
    ]
    STATUS = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('bounced', 'Bounced'),
    ]
    
    notification_type = models.CharField(max_length=20, choices=TYPES)
    status = models.CharField(max_length=10, choices=STATUS)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    sent_at = models.DateTimeField(null=True)
    error_message = models.TextField(blank=True)
```

**Tracking Includes:**
- Type of notification sent
- Recipient email
- Subject line
- Sent timestamp
- Status (pending/sent/failed)
- Error messages if failed
- Bounce tracking

---

## Setup and Installation

### Prerequisites

- Python 3.11+
- PostgreSQL (for production)
- Redis (for Celery background tasks)
- Stripe account (test keys)
- Gmail account (for email sending)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/SelfErase.git
cd SelfErase
```

### Step 2: Create Virtual Environment

```bash
# Windows PowerShell
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
cd web_monitoring_backend
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy example to actual .env file
cp .env.example .env

# Edit .env with your settings:
# - Django secret key
# - Database URL
# - Stripe test keys
# - Gmail SMTP credentials
```

### Step 5: Run Database Migrations

```bash
python manage.py migrate
```

### Step 6: Create Superuser (Admin)

```bash
python manage.py createsuperuser
# Follow prompts to create admin account
```

### Step 7: Start Django Server

```bash
python manage.py runserver
```

Server will be available at: `http://127.0.0.1:8000/`

---

## Running Tests

### Test Credentials (Development)

**User Login:**
```
Username: testuser
Password: testpass123
Email: testuser@example.com
```

**Test Card (Stripe):**
```
Card Number: 4242 4242 4242 4242
Expiry: 12/25 (or any future date)
CVC: 123 (or any 3 digits)
ZIP: 12345 (or any value)
```

### Quick 5-Minute Test

1. **Start Server**
   ```bash
   python manage.py runserver
   ```

2. **Login**
   - Navigate to http://127.0.0.1:8000/
   - Login with testuser/testpass123

3. **Create Monitor**
   - Click "Create Monitor"
   - URL: https://example.com
   - Keyword: example
   - Check interval: 1 day
   - Click "Next: Select Plan"

4. **Select Plan**
   - Choose "Standard ($1/month)"
   - Click "Continue to Payment"

5. **Complete Payment**
   - Fill form with test card details
   - Click "Pay Now"
   - Should see success page

6. **Verify Monitor**
   - Click "Back to Monitor Details"
   - Should show subscription as ACTIVE

### Unit Test Procedures

**Test Email Sending:**
```python
# Run from Django shell
python manage.py shell

from monitoring.models import Monitor, Subscription
from monitoring.email_service import send_keyword_found_email

# Get a monitor
monitor = Monitor.objects.first()

# Simulate check result
check_result = {
    'found': True,
    'timestamp': timezone.now(),
    'excerpt': 'This is where keyword was found'
}

# Send email
send_keyword_found_email(monitor, check_result)

# Check console/email log for success
```

**Test Subscription Expiration:**
```python
# Run from Django shell
python manage.py shell

from monitoring.models import Subscription
from datetime import timedelta
from django.utils import timezone

# Get a subscription
sub = Subscription.objects.first()

# Set expiration to 7 days from now
sub.expires_at = timezone.now() + timedelta(days=7)
sub.save()

# Run check_monitoring command
# It should detect the 7-day threshold and send warning email
```

**Test Payment Processing:**
```python
# Run from Django shell
python manage.py shell

from payments.models import Payment
from accounts.models import Subscription

# Get a pending payment
payment = Payment.objects.filter(status='pending').first()

# Manually mark as completed (simulating Stripe webhook)
payment.status = 'completed'
payment.save()

# Verify subscription is now active
subscription = payment.subscription
print(f"Subscription status: {subscription.status}")  # Should be 'active'
```

### End-to-End Test Scenario

1. Create a new user account
2. Create a monitor with a keyword
3. Select and pay for a subscription
4. Run check_monitoring command manually
5. Verify keyword found email is sent
6. Modify monitor and run checks again
7. Verify new emails are sent
8. Wait/simulate 7 days before expiration
9. Verify expiration warning email is sent
10. Verify monitoring stops after expiration

---

## Example Workflows

### Workflow 1: Basic User - Set and Forget

**Scenario:** User wants to monitor a website for competitor activity

**Steps:**
1. User logs in
2. Creates monitor for competitor website
3. Sets keyword: "new product launch"
4. Sets check interval: 1 day
5. Selects Standard plan ($1/month)
6. Makes payment
7. Receives keyword alerts via email
8. Monitors automatically stop after 30 days

**Timeline:**
- Day 1: Monitor created, payment successful, monitoring starts
- Day 15: Keyword found, email notification sent
- Day 24: Subscription expiration warning email sent
- Day 30: Monitoring pauses automatically

### Workflow 2: Power User - Multiple Monitors with Discovery Plan

**Scenario:** SEO professional monitoring multiple client websites

**Steps:**
1. User logs in
2. Creates 5 different monitors for 5 clients
3. Each monitor has different keywords (SEO terms, brand mentions, etc.)
4. Selects Discovery plan ($5/month) for premium features
5. Receives multiple email alerts throughout the month
6. Reviews analytics in admin dashboard
7. Renews subscription monthly

**Timeline:**
- Week 1: 5 monitors created, all subscriptions active
- Week 2-3: Multiple keyword alerts, emails sent daily
- Week 4: Receives renewal reminder email
- Month 1 ends: Renews subscription, continues monitoring

### Workflow 3: Admin - Managing Multiple Users

**Scenario:** Company IT team monitoring corporate website

**Steps:**
1. Admin logs in to admin dashboard
2. Views all monitors across organization
3. Checks recent activity and check results
4. Reviews email notification logs
5. Identifies failed checks and investigates
6. Manages user accounts and permissions
7. Reviews payment history and subscription status

**Timeline:**
- Daily: Reviews overnight check results
- Weekly: Checks subscription renewals
- Monthly: Reviews analytics and generates reports
- Quarterly: Analyzes churn and ROI

### Workflow 4: Troubleshooting - Monitor Not Working

**Scenario:** User reports monitor not finding expected keywords

**Steps:**
1. User reports issue
2. Admin pulls monitor details
3. Checks subscription status (active/expired)
4. Views recent check results
5. Reviews check_monitoring logs
6. Tests keyword matching manually
7. Finds: URL changed, keyword no longer present
8. Advises user to update monitor
9. User updates keyword and receives notification immediately

**Resolution:**
- User updates monitor with correct keyword
- Next check finds keyword
- Email notification confirms working

---

## Key Design Decisions

### Design Decision 1: Keyword Auto-Fill

**Bad Approach:** ❌ Ask user to type keyword again in subscription form
**Good Approach:** ✅ Get keyword from monitor automatically

**Why:** Prevents data entry errors and improves user experience

### Design Decision 2: Cost Lock

**Bad Approach:** ❌ Allow user to change cost on payment page
**Good Approach:** ✅ Amount is immutable, displayed with lock icon

**Why:** Prevents fraud and ensures payment matches plan selected

### Design Decision 3: Linear Flow

**Bad Approach:** ❌ Multiple redirects with backtracking possible
**Good Approach:** ✅ 1→2→3→4 linear progression, no loops

**Why:** Clear path reduces user confusion

### Design Decision 4: Session Data

**Bad Approach:** ❌ Store monitor_id in URL
**Good Approach:** ✅ Store in session for security & cleanliness

**Why:** Prevents URL manipulation and cleaner URLs

### Design Decision 5: Return Navigation

**Bad Approach:** ❌ Always go to list page after payment
**Good Approach:** ✅ Return to specific monitor that was created

**Why:** User sees their newly created monitor immediately

### Design Decision 6: Form Validation

**Bad Approach:** ❌ Show errors but start from step 1
**Good Approach:** ✅ Show errors, stay on current step, allow retry

**Why:** Better UX, user doesn't lose previous data

---

**This workflow is optimized for user experience while maintaining security and data integrity.**
