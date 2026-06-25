from rest_framework import generics, permissions
from .models import JournalAudit
from .serializers import JournalAuditSerializer


class AuditListView(generics.ListAPIView):
    """GET /api/audit/ — journal d'audit (admin)."""
    serializer_class = JournalAuditSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != "admin":
            return JournalAudit.objects.none()
        return JournalAudit.objects.all()
