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


class AdminDashboardSerializer(serializers.Serializer):
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


class KpiSerializer(serializers.Serializer):
    total_revenue = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    avg_booking_value = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    cancellation_rate = serializers.FloatField(read_only=True)
    no_show_rate = serializers.FloatField(read_only=True)
    repeat_clients_rate = serializers.FloatField(read_only=True)


class RevenueTrendSerializer(serializers.Serializer):
    date = serializers.DateField(read_only=True)
    value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class RevenueByPeriodSerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class PaymentMethodsSerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class BookingStatusSerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    value = serializers.IntegerField(read_only=True)


class PopularServicesSerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    value = serializers.IntegerField(read_only=True)


class RevenueByCitySerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)


class ClientMixSerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    value = serializers.IntegerField(read_only=True)


class PeakHoursSerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    value = serializers.IntegerField(read_only=True)


class BookingsByWeekdaySerializer(serializers.Serializer):
    label = serializers.CharField(read_only=True)
    value = serializers.IntegerField(read_only=True)

class MasterPerformanceSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    specialization = serializers.CharField(read_only=True)
    city = serializers.CharField(read_only=True)
    bookings = serializers.IntegerField(read_only=True)
    revenue = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    rating = serializers.FloatField(read_only=True)


class AdminAnalyticsSerializer(serializers.Serializer):
    period = serializers.CharField(read_only=True)
    date_from = serializers.DateField(read_only=True)
    date_to = serializers.DateField(read_only=True)
    kpi = KpiSerializer(read_only=True)
    revenue_trend = RevenueTrendSerializer(many=True, read_only=True)
    revenue_by_period = RevenueByPeriodSerializer(many=True, read_only=True)
    payment_methods = PaymentMethodsSerializer(many=True, read_only=True)
    booking_status = BookingStatusSerializer(many=True, read_only=True)
    popular_services = PopularServicesSerializer(many=True, read_only=True)
    revenue_by_city = RevenueByCitySerializer(many=True, read_only=True)
    client_mix = ClientMixSerializer(many=True, read_only=True)
    peak_hours = PeakHoursSerializer(many=True, read_only=True)
    bookings_by_weekday = BookingsByWeekdaySerializer(many=True, read_only=True)
    master_performance = MasterPerformanceSerializer(many=True, read_only=True)
