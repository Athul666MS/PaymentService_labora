
import json
import hmac
import hashlib
import logging

import razorpay

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .permissions.internal_service import IsInternalService
from .razorpay_client import razorpay_client

from labora_shared.notification_client import (
    send_notification
)
from .serializers import InternalPaymentListSerializer

logger = logging.getLogger(__name__)


# ==========================================================
# CREATE PAYMENT ORDER
# ==========================================================
@api_view(["POST"])
def create_payment_order(request):

    data = request.data

    amount = int(data["amount"]) * 100

    order = razorpay_client.order.create(
        {
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        }
    )

    payment = Payment.objects.create(
        job_id=data["job_id"],
        application_id=data["application_id"],
        client_id=data["client_id"],
        freelancer_id=data["freelancer_id"],
        amount=data["amount"],
        razorpay_order_id=order["id"],
        status="created"
    )

    return Response(
        {
            "order_id": order["id"],
            "amount": amount,
            "currency": "INR",
            "payment_id": payment.id
        },
        status=status.HTTP_201_CREATED
    )


# ==========================================================
# VERIFY PAYMENT
# ==========================================================
@api_view(["POST"])
def verify_payment(request):

    data = request.data
    params = {
        "razorpay_order_id":
            data["razorpay_order_id"],

        "razorpay_payment_id":
            data["razorpay_payment_id"],

        "razorpay_signature":
            data["razorpay_signature"],
    }

    try:

        razorpay_client.utility.verify_payment_signature(
            params
        )
        with transaction.atomic():

            payment = (
                Payment.objects
                .select_for_update()
                .get(
                    razorpay_order_id=
                    data["razorpay_order_id"]
                )
            )
            # Prevent duplicate processing
            if payment.status == "paid":

                return Response(
                    {
                        "message":
                            "Payment already verified"
                    },
                    status=status.HTTP_200_OK
                )

            payment.razorpay_payment_id = (
                data["razorpay_payment_id"]
            )

            payment.razorpay_signature = (
                data["razorpay_signature"]
            )

            payment.status = "paid"

            payment.save()

        # Notification should not break payment flow
        try:

            send_notification(
                user_id=payment.freelancer_id,
                notification_type="payment_received",
                title="Payment Received",
                message="Payment has been released.",
                payload={
                    "payment_id":
                        payment.id,

                    "job_id":
                        payment.job_id
                }
            )

        except Exception:

            logger.exception(
                "Failed to send payment notification "
                "for payment %s",
                payment.id
            )

        return Response(
            {
                "message":
                    "Payment verified"
            },
            status=status.HTTP_200_OK
        )

    except Payment.DoesNotExist:

        return Response(
            {
                "error":
                    "Payment not found"
            },
            status=status.HTTP_404_NOT_FOUND
        )

    except razorpay.errors.SignatureVerificationError:

        return Response(
            {
                "error":
                    "Invalid signature"
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    except Exception as e:

        logger.exception(str(e))

        return Response(
            {
                "error":
                    "Payment verification failed"
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# ==========================================================
# RAZORPAY WEBHOOK
# ==========================================================
@csrf_exempt
def razorpay_webhook(request):

    payload = request.body

    received_signature = request.headers.get(
        "X-Razorpay-Signature"
    )

    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Verify webhook signature
    if not hmac.compare_digest(
            received_signature,
            expected_signature
    ):

        return HttpResponse(
            status=400
        )

    try:

        data = json.loads(payload)

        event = data.get(
            "event"
        )

        if event == "payment.captured":

            razorpay_order_id = (
                data["payload"]["payment"]["entity"]["order_id"]
            )

            razorpay_payment_id = (
                data["payload"]["payment"]["entity"]["id"]
            )

            with transaction.atomic():

                payment = (
                    Payment.objects
                    .select_for_update()
                    .get(
                        razorpay_order_id=
                        razorpay_order_id
                    )
                )

                # Prevent duplicate webhook processing
                if payment.status != "paid":

                    payment.razorpay_payment_id = (
                        razorpay_payment_id
                    )

                    payment.status = "paid"

                    payment.save()

            try:

                send_notification(
                    user_id=payment.freelancer_id,
                    notification_type="payment_received",
                    title="Payment Received",
                    message="Payment has been released.",
                    payload={
                        "payment_id":
                            payment.id,

                        "job_id":
                            payment.job_id
                    }
                )

            except Exception:

                logger.exception(
                    "Webhook notification failed "
                    "for payment %s",
                    payment.id
                )

        return HttpResponse(
            status=200
        )

    except Payment.DoesNotExist:

        logger.exception(
            "Payment not found"
        )

        return HttpResponse(
            status=404
        )

    except Exception as e:

        logger.exception(
            str(e)
        )

        return HttpResponse(
            status=400
        )
class InternalPaymentListView(APIView):

    permission_classes = [IsInternalService]

    def get(self, request):

        payments = Payment.objects.all().order_by("-created_at")

        paginator = PageNumberPagination()
        paginator.page_size = 20

        page = paginator.paginate_queryset(
            payments,
            request
        )

        serializer = InternalPaymentListSerializer(
            page,
            many=True
        )

        return paginator.get_paginated_response(
            serializer.data
        )


class InternalPaymentStatsView(APIView):

    permission_classes = [IsInternalService]

    def get(self, request):

        total_revenue = (
            Payment.objects.filter(
                status="paid"
            ).aggregate(
                total=Sum("amount")
            )["total"] or 0
        )

        return Response({

            "total_payments": Payment.objects.count(),

            "paid_payments": Payment.objects.filter(
                status="paid"
            ).count(),

            "pending_payments": Payment.objects.filter(
                status="created"
            ).count(),

            "failed_payments": Payment.objects.filter(
                status="failed"
            ).count(),

            "refunded_payments": Payment.objects.filter(
                status="refunded"
            ).count(),

            "total_revenue": total_revenue,

        })


class InternalPaymentDetailView(APIView):

    permission_classes = [IsInternalService]

    def get(self, request, payment_id):

        try:

            payment = Payment.objects.get(
                pk=payment_id
            )

        except Payment.DoesNotExist:

            return Response(
                {
                    "error": "Payment not found"
                },
                status=404
            )

        serializer = InternalPaymentListSerializer(
            payment
        )

        return Response(
            serializer.data
        )