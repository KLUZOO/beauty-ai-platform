from rest_framework import serializers

from referral_events.models import ReferralEvent


class ReferralEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralEvent
        fields = (
            "id",
            "client",
            "session_id",
            "salon",
            "service",
            "source",
            "destination_url",
            "created_at",
            "event_type",
        )
        read_only_fields = (
            "id",
            "client",
            "created_at",
        )
