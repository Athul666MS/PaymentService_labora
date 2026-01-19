from django.db import models

class Payment(models.Model):
    job_id = models.IntegerField()
    application_id = models.IntegerField()

    client_id = models.IntegerField()
    freelancer_id = models.IntegerField()

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="INR")

    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("created", "Created"),
            ("paid", "Paid"),
            ("failed", "Failed"),
            ("refunded", "Refunded"),
        ],
        default="created"
    )

    created_at = models.DateTimeField(auto_now_add=True)

