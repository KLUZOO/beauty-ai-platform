from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    payment_method_display = serializers.CharField(
        source="get_payment_method_display",
        read_only=True,
    )
    payment_status_display = serializers.CharField(
        source="get_payment_status_display",
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = (
            "id",
            "appointment",
            "amount",
            "currency",
            "payment_method",
            "payment_method_display",
            "payment_status",
            "payment_status_display",
            "payment_date",
        )
        read_only_fields = (
            "id",
            "payment_method_display",
            "payment_status_display",
            "payment_date",
        )
