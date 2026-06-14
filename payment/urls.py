from django.urls import path
from .views import create_payment_order, verify_payment, razorpay_webhook


urlpatterns = [
    path("payments/orders/", create_payment_order),
    path("payments/verify/", verify_payment),
    path("payments/webhooks/razorpay/", razorpay_webhook),
]