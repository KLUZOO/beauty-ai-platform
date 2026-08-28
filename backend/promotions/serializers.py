from rest_framework import serializers

from promotions.models import Promotion


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = (
            "id",
            "name",
            "description",
            "discount_percent",
            "start_date",
            "end_date",
            "salon",
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        start_date = attrs.get(
            "start_date",
            self.instance.start_date if self.instance else None,
        )
        end_date = attrs.get(
            "end_date",
            self.instance.end_date if self.instance else None,
        )

        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError(
                {"end_date": "The end date must be later than the start date."}
            )

        return attrs
