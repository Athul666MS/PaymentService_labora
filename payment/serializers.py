from rest_framework import serializers

from .models import Payment


class InternalPaymentListSerializer(serializers.ModelSerializer):

    class Meta:

        model = Payment

        fields = [

            "id",

            "job_id",

            "application_id",

            "client_id",

            "freelancer_id",

            "amount",

            "currency",

            "status",

            "created_at",

        ]