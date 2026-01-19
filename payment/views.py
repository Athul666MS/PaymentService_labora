from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import hmac
import hashlib
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Payment
from .razorpay_client import razorpay_client

@api_view(["POST"])
def create_payment_order(request):

    data = request.data
    amount = int(data["amount"]) * 100  # Razorpay uses paise

    order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    payment = Payment.objects.create(
        job_id=data["job_id"],
        application_id=data["application_id"],
        client_id=data["client_id"],
        freelancer_id=data["freelancer_id"],
        amount=data["amount"],
        razorpay_order_id=order["id"],
        status="created"
    )

    return Response({
        "order_id": order["id"],
        "amount": amount,
        "currency": "INR",
        "payment_id": payment.id
    }, status=status.HTTP_201_CREATED)

@api_view(["POST"])
def verify_payment(request):
    data = request.data

    params = {
        "razorpay_order_id": data["razorpay_order_id"],
        "razorpay_payment_id": data["razorpay_payment_id"],
        "razorpay_signature": data["razorpay_signature"],
    }

    try:
        razorpay_client.utility.verify_payment_signature(params)

        payment = Payment.objects.get(
            razorpay_order_id=data["razorpay_order_id"]
        )

        payment.razorpay_payment_id = data["razorpay_payment_id"]
        payment.razorpay_signature = data["razorpay_signature"]
        payment.status = "paid"
        payment.save()

        return Response({"message": "Payment verified"}, status=200)

    except Exception:
        return Response({"error": "Payment verification failed"}, status=400)


@csrf_exempt
def razorpay_webhook(request):
    payload = request.body
    received_signature = request.headers.get("X-Razorpay-Signature")

    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Verify webhook signature
    if not hmac.compare_digest(received_signature, expected_signature):
        return HttpResponse(status=400)

    data = json.loads(payload)

    event = data.get("event")

    if event == "payment.captured":
        razorpay_order_id = data["payload"]["payment"]["entity"]["order_id"]
        razorpay_payment_id = data["payload"]["payment"]["entity"]["id"]

        payment = Payment.objects.get(
            razorpay_order_id=razorpay_order_id
        )

        payment.razorpay_payment_id = razorpay_payment_id
        payment.status = "paid"
        payment.save()

    return HttpResponse(status=200)
