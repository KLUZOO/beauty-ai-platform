from rest_framework import viewsets

from referral_events.models import LinkTracking
from referral_events.serializers import ReferralEventSerializer


class ReferralEventViewSet(viewsets.ModelViewSet):
    queryset = LinkTracking.objects.all()
    serializer_class = ReferralEventSerializer
    permission_classes = ()

    def perform_create(self, serializer) -> None:
        serializer.save(
            client=self.request.user if self.request.user.is_authenticated else None
        )
