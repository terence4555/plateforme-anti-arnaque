from django.db import models
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Signalement
from .serializers import (
    SignalementListSerializer,
    SignalementDetailSerializer,
    SignalementCreateSerializer,
)


class SignalementViewSet(viewsets.ModelViewSet):
    """CRUD signalements avec recherche par téléphone/profil."""
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["numero_telephone", "profil_vendeur", "description"]
    ordering_fields = ["date_signalement", "score"]
    ordering = ["-date_signalement"]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == "list":
            return SignalementListSerializer
        if self.action == "create":
            return SignalementCreateSerializer
        return SignalementDetailSerializer

    def get_queryset(self):
        qs = Signalement.objects.select_related("id_utilisateur").prefetch_related("preuves")
        type_filter = self.request.query_params.get("type")
        if type_filter:
            qs = qs.filter(type_arnaque=type_filter)
        statut_filter = self.request.query_params.get("statut")
        if statut_filter:
            qs = qs.filter(statut=statut_filter)
        return qs

    def perform_create(self, serializer):
        serializer.save(id_utilisateur=self.request.user)

    @action(detail=False, methods=["get"])
    def types(self, request):
        return Response([{"value": c[0], "label": c[1]} for c in Signalement.TYPE_CHOICES])

    @action(detail=False, methods=["get"])
    def rechercher(self, request):
        """GET /api/signalements/rechercher/?q= — comme la procédure RechercherProfil."""
        q = request.query_params.get("q", "")
        if not q:
            return Response([])
        qs = Signalement.objects.filter(
            models.Q(numero_telephone=q) | models.Q(profil_vendeur__icontains=q)
        ).select_related("id_utilisateur")
        serializer = SignalementListSerializer(qs, many=True)
        return Response(serializer.data)


