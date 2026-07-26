from django.db import models as dj_models
from django.conf import settings
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Signalement, Preuve
from .serializers import (
    SignalementListSerializer,
    SignalementDetailSerializer,
    SignalementCreateSerializer,
)


def est_admin(user):
    return user.is_authenticated and user.role == "admin"

def est_autorite(user):
    return user.is_authenticated and user.role == "autorite"

def est_admin_ou_autorite(user):
    return user.is_authenticated and user.role in ("admin", "autorite")


class SignalementViewSet(viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["numero_telephone", "profil_vendeur", "description"]
    ordering_fields = ["date_signalement", "score"]
    ordering = ["-date_signalement"]

    def get_permissions(self):
        if self.action in ("create",):
            return [permissions.IsAuthenticated()]
        if self.action in ("update", "partial_update", "destroy", "moderer", "transmettre", "statuer"):
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
        t = self.request.query_params.get("type")
        if t:
            qs = qs.filter(type_arnaque=t)
        s = self.request.query_params.get("statut")
        if s:
            qs = qs.filter(statut=s)
        return qs

    def perform_create(self, serializer):
        signalement = serializer.save(id_utilisateur=self.request.user)
        fichiers_urls = self.request.data.get("fichiers_urls", [])
        if isinstance(fichiers_urls, list):
            for url in fichiers_urls:
                tf = "pdf" if url.lower().endswith(".pdf") else "image"
                Preuve.objects.create(id_signalement=signalement, fichier_url=url, type_fichier=tf)

    # ===== MODERATION ADMIN =====

    @action(detail=True, methods=["post"])
    def moderer(self, request, pk=None):
        """POST /api/signalements/{id}/moderer/ — admin : valider ou rejeter."""
        if not est_admin(request.user):
            return Response({"error": "Reserve aux administrateurs."}, status=403)
        signalement = self.get_object()
        action_m = request.data.get("action")
        if action_m == "approuver":
            signalement.statut = "approuve"
        elif action_m == "rejeter":
            signalement.statut = "rejete"
        else:
            return Response({"error": "action doit etre 'approuver' ou 'rejeter'."}, status=400)
        signalement.save(update_fields=["statut"])
        return Response(SignalementDetailSerializer(signalement).data)

    # ===== TRANSMISSION A L'AUTORITE =====

    @action(detail=True, methods=["post"])
    def transmettre(self, request, pk=None):
        """POST /api/signalements/{id}/transmettre/ — admin : transmettre a l'autorite."""
        if not est_admin(request.user):
            return Response({"error": "Reserve aux administrateurs."}, status=403)
        signalement = self.get_object()
        if signalement.statut != "approuve":
            return Response({"error": "Seuls les signalements approuves peuvent etre transmis."}, status=400)
        signalement.statut = "transmis"
        signalement.save(update_fields=["statut"])
        return Response(SignalementDetailSerializer(signalement).data)

    # ===== AUTORITE : STATUER =====

    @action(detail=True, methods=["post"])
    def statuer(self, request, pk=None):
        """POST /api/signalements/{id}/statuer/ — autorite : confirmer ou infirmer."""
        if not est_autorite(request.user):
            return Response({"error": "Reserve aux autorites competentes."}, status=403)
        signalement = self.get_object()
        if signalement.statut != "transmis":
            return Response({"error": "Ce signalement n'a pas ete transmis a l'autorite."}, status=400)
        decision = request.data.get("decision")
        if decision == "confirmer":
            signalement.statut = "confirme"
        elif decision == "infirmer":
            signalement.statut = "infirme"
        else:
            return Response({"error": "decision doit etre 'confirmer' ou 'infirmer'."}, status=400)
        signalement.save(update_fields=["statut"])
        return Response(SignalementDetailSerializer(signalement).data)

    # ===== AUTORITE : LISTE DES DOSSIERS =====

    @action(detail=False, methods=["get"])
    def dossiers(self, request):
        """GET /api/signalements/dossiers/ — autorite : consulter les dossiers transmis."""
        if not est_autorite(request.user):
            return Response({"error": "Reserve aux autorites."}, status=403)
        qs = Signalement.objects.filter(statut__in=["transmis", "confirme", "infirme"]).select_related("id_utilisateur")
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(SignalementDetailSerializer(page, many=True).data)
        return Response(SignalementDetailSerializer(qs, many=True).data)

    # ===== UTILITAIRES =====

    @action(detail=False, methods=["get"])
    def types(self, request):
        return Response([{"value": c[0], "label": c[1]} for c in Signalement.TYPE_CHOICES])

    @action(detail=False, methods=["get"])
    def stats(self, request):
        total = Signalement.objects.count()
        return Response({
            "total": total,
            "approuves": Signalement.objects.filter(statut="approuve").count(),
            "en_attente": Signalement.objects.filter(statut="en_attente").count(),
            "rejetes": Signalement.objects.filter(statut="rejete").count(),
            "transmis": Signalement.objects.filter(statut="transmis").count(),
            "confirmes": Signalement.objects.filter(statut="confirme").count(),
            "infirmes": Signalement.objects.filter(statut="infirme").count(),
        })

    @action(detail=False, methods=["get"])
    def rechercher(self, request):
        q = request.query_params.get("q", "")
        if not q:
            return Response([])
        qs = Signalement.objects.filter(
            dj_models.Q(numero_telephone=q) | dj_models.Q(profil_vendeur__icontains=q)
        ).select_related("id_utilisateur")
        return Response(SignalementListSerializer(qs, many=True).data)


# ===== UPLOAD DE PREUVES =====

import os
import uuid

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def upload_preuve(request):
    """POST /api/signalements/upload/ — upload un fichier preuve et retourne l'URL."""
    fichier = request.FILES.get("fichier")
    if not fichier:
        return Response({"error": "Aucun fichier fourni."}, status=400)

    ext = os.path.splitext(fichier.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return Response({"error": f"Type de fichier non autorisé: {ext}"}, status=400)

    if fichier.size > MAX_FILE_SIZE:
        return Response({"error": "Le fichier dépasse 10 Mo."}, status=400)

    unique_name = f"{uuid.uuid4().hex}{ext}"
    upload_dir = settings.MEDIA_ROOT / "preuves"
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / unique_name
    with open(file_path, "wb") as f:
        for chunk in fichier.chunks():
            f.write(chunk)

    url = f"{settings.MEDIA_URL}preuves/{unique_name}"
    return Response({"url": url, "filename": fichier.name}, status=201)
