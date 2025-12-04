"""
Payment service integrations for Stripe and PayPal
"""

import logging
import stripe
from django.conf import settings
from django.utils import timezone
from accounts.models import Payment

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    """Service for handling Stripe payments"""
    
    @staticmethod
    def create_payment_intent(user, amount, subscription=None):
        """Create a Stripe PaymentIntent"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency='usd',
                metadata={
                    'user_id': user.id,
                    'user_email': user.email,
                    'subscription_id': subscription.id if subscription else None,
                }
            )
            
            # Create Payment record
            payment = Payment.objects.create(
                user=user,
                amount=amount,
                payment_type='subscription' if subscription else 'credit',
                payment_method='stripe',
                transaction_id=intent.id,
                subscription=subscription,
                status='pending'
            )
            
            logger.info(f"Created Stripe PaymentIntent {intent.id} for user {user.id}")
            return {
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'amount': amount,
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating PaymentIntent: {str(e)}")
            raise
    
    @staticmethod
    def verify_payment(payment_intent_id):
        """Verify that a Stripe payment succeeded"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == 'succeeded':
                # Update Payment record
                payment = Payment.objects.get(transaction_id=payment_intent_id)
                payment.mark_completed()
                
                logger.info(f"Verified Stripe payment {payment_intent_id}")
                return True
            else:
                logger.warning(f"Stripe payment {payment_intent_id} status: {intent.status}")
                return False
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error verifying payment: {str(e)}")
            return False
    
    @staticmethod
    def create_subscription(user, price_id):
        """Create recurring subscription with Stripe"""
        try:
            # Get or create customer
            customer = stripe.Customer.create(
                email=user.email,
                name=f"{user.first_name} {user.last_name}".strip(),
                metadata={'user_id': user.id}
            )
            
            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
            )
            
            logger.info(f"Created Stripe subscription {subscription.id} for user {user.id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {str(e)}")
            raise
    
    @staticmethod
    def cancel_subscription(stripe_subscription_id):
        """Cancel a Stripe subscription"""
        try:
            stripe.Subscription.delete(stripe_subscription_id)
            logger.info(f"Cancelled Stripe subscription {stripe_subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {str(e)}")
            return False


class PayPalPaymentService:
    """Service for handling PayPal payments"""
    
    @staticmethod
    def create_order(user, amount, subscription=None):
        """Create a PayPal order"""
        # TODO: Implement PayPal integration
        # This would use the PayPal API to create orders
        pass
    
    @staticmethod
    def verify_payment(order_id):
        """Verify that a PayPal payment succeeded"""
        # TODO: Implement PayPal payment verification
        pass
    
    @staticmethod
    def create_subscription(user, plan_id):
        """Create recurring subscription with PayPal"""
        # TODO: Implement PayPal subscription creation
        pass


class PaymentManager:
    """Unified payment manager for handling both Stripe and PayPal"""
    
    @staticmethod
    def process_payment(user, amount, payment_method='stripe', subscription=None):
        """Process a payment using specified method"""
        if payment_method == 'stripe':
            return StripePaymentService.create_payment_intent(user, amount, subscription)
        elif payment_method == 'paypal':
            return PayPalPaymentService.create_order(user, amount, subscription)
        else:
            raise ValueError(f"Unknown payment method: {payment_method}")
    
    @staticmethod
    def verify_payment(transaction_id, payment_method='stripe'):
        """Verify payment completion"""
        if payment_method == 'stripe':
            return StripePaymentService.verify_payment(transaction_id)
        elif payment_method == 'paypal':
            return PayPalPaymentService.verify_payment(transaction_id)
        else:
            raise ValueError(f"Unknown payment method: {payment_method}")
