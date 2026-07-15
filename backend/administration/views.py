from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from signalements.models import Signalement
from commentaire.models import Commentaire
from votes.models import Vote
from .models import JournalAudit
from .serializers import JournalAuditSerializer

User = get_user_model()


class DashboardView(APIView):
    """GET /api/admin/dashboard/ — tableau de bord administrateur."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"error": "Reserve aux administrateurs."}, status=403)

        total_signalements = Signalement.objects.count()
        total_utilisateurs = User.objects.count()
        total_contacts = Signalement.objects.filter(
            Q(numero_telephone__isnull=False) & ~Q(numero_telephone="")
        ).values("numero_telephone").distinct().count()

        return Response({
            "utilisateurs": {
                "total": total_utilisateurs,
                "actifs": User.objects.filter(est_actif=True).count(),
                "admins": User.objects.filter(role="admin").count(),
                "autorites": User.objects.filter(role="autorite").count(),
            },
            "signalements": {
                "total": total_signalements,
                "en_attente": Signalement.objects.filter(statut="en_attente").count(),
                "approuves": Signalement.objects.filter(statut="approuve").count(),
                "rejetes": Signalement.objects.filter(statut="rejete").count(),
                "transmis": Signalement.objects.filter(statut="transmis").count(),
                "confirmes": Signalement.objects.filter(statut="confirme").count(),
                "infirmes": Signalement.objects.filter(statut="infirme").count(),
            },
            "par_type": [
                {"type": c[0], "label": c[1], "count": Signalement.objects.filter(type_arnaque=c[0]).count()}
                for c in Signalement.TYPE_CHOICES
            ],
            "interactions": {
                "commentaires": Commentaire.objects.count(),
                "votes": Vote.objects.count(),
            },
            "contacts_suspects": total_contacts,
            "taux_verification": round(
                (Signalement.objects.filter(statut__in=["approuve", "confirme"]).count() / max(total_signalements, 1)) * 100,
                1,
            ),
        })


class AuditListView(generics.ListAPIView):
    serializer_class = JournalAuditSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != "admin":
            return JournalAudit.objects.none()
        return JournalAudit.objects.all()
