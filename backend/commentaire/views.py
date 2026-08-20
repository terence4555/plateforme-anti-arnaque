from rest_framework import viewsets, permissions
from .models import Commentaire
from .serializers import CommentaireSerializer, CommentaireCreateSerializer


class CommentaireViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == "create":
            return CommentaireCreateSerializer
        return CommentaireSerializer

    def get_queryset(self):
        qs = Commentaire.objects.select_related("id_utilisateur", "id_signalement")
        signalement_id = self.request.query_params.get("signalement")
        if signalement_id:
            qs = qs.filter(id_signalement_id=signalement_id)
        if not self.request.user.is_authenticated or self.request.user.role != "admin":
            qs = qs.filter(est_masque=False)
        return qs.order_by("-date_commentaire")

    def perform_create(self, serializer):
        serializer.save(id_utilisateur=self.request.user)
