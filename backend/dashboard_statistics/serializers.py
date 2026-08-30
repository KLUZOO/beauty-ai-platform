from rest_framework import serializers


class StatisticsSerializer(serializers.Serializer):
    total_appointments = serializers.IntegerField(read_only=True)
    upcoming_appointments = serializers.IntegerField(read_only=True)
    completed_appointments = serializers.IntegerField(read_only=True)
    cancelled_appointments = serializers.IntegerField(read_only=True)
    today_appointments = serializers.IntegerField(read_only=True)
    total_earnings = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    monthly_earnings = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    average_rating = serializers.FloatField(read_only=True)
    total_reviews = serializers.IntegerField(read_only=True)
    number_of_active_services = serializers.IntegerField(read_only=True)
    total_clients = serializers.IntegerField(read_only=True)
