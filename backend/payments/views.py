from rest_framework import viewsets

from payments.models import Payment
from payments.permissions import IsAdminOrAuthenticatedReadOnly
from payments.serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = (IsAdminOrAuthenticatedReadOnly,)

    def get_queryset(self):
        queryset = Payment.objects.select_related("appointment")

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(appointment__client=self.request.user)
