from django.urls import path
from .views import create_payment_order, verify_payment, razorpay_webhook, InternalPaymentStatsView, \
    InternalPaymentListView, InternalPaymentDetailView

urlpatterns = [
    path("payments/orders/", create_payment_order),
    path("payments/verify/", verify_payment),
    path("payments/webhooks/razorpay/", razorpay_webhook),
    path(
        "internal/payments/",
        InternalPaymentListView.as_view()
    ),

    path(
        "internal/payments/stats/",
        InternalPaymentStatsView.as_view()
    ),

    path(
        "internal/payments/<int:payment_id>/",
        InternalPaymentDetailView.as_view()
    ),
]