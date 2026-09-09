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


class ScheduleSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    client = serializers.CharField(read_only=True)
    master = serializers.CharField(read_only=True)
    service = serializers.CharField(read_only=True)
    date_time = serializers.DateTimeField(read_only=True)
    status = serializers.CharField(read_only=True)
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )


class AdminStatisticsSerializer(serializers.Serializer):
    revenue_current = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    revenue_previous = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    bookings_current = serializers.IntegerField(read_only=True)
    bookings_previous = serializers.IntegerField(read_only=True)
    clients_current = serializers.IntegerField(read_only=True)
    clients_previous = serializers.IntegerField(read_only=True)
    masters_current = serializers.IntegerField(read_only=True)
    masters_previous = serializers.IntegerField(read_only=True)
    bookings_today = serializers.IntegerField(read_only=True)
    completed_today = serializers.IntegerField(read_only=True)
    cancelled_today = serializers.IntegerField(read_only=True)
    no_show_today = serializers.IntegerField(read_only=True)
    recent_bookings = ScheduleSerializer(many=True, read_only=True)
    today_schedule = ScheduleSerializer(many=True, read_only=True)
    active_now = ScheduleSerializer(many=True, read_only=True)
