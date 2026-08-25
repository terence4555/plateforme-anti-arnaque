import json
from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils import timezone

from .alertes import (
    obtenir_toutes_les_alertes,
    obtenir_alertes_campagnes,
    obtenir_alertes_clusters,
    obtenir_alertes_tendances,
)

from .ml.predict_service import (
    predict_categorie,
    expliquer_prediction,
    score_de_risque,
    calculer_recurrence,
)
from .ml.preprocessing import extract_entities
from .permissions import (
    autorite_requise, interface_utilisateur_requise, admin_ou_autorite_requis,
    admin_requis, est_administrateur,
)
from .models import Signalement, EntiteSignalement, ClusterEmergent, Dossier


# Ordre d'affichage fixe des catégories connues (informatif uniquement --
# les cartes du tableau de bord sont générées à partir des données réelles,
# pas de cette liste)
CATEGORIES = [
    "Phishing",
    "Arnaque sentimentale",
    "Faux site e-commerce",
    "Fausse offre d'emploi",
    "Usurpation d'identité",
    "Arnaque crypto",
    "Arnaque à la loterie",
    "Incertain",
]


@interface_utilisateur_requise
def signaler_arnaque(request):
    texte_soumis = ""
    erreur = None

    if request.method == "POST":
        texte_soumis = request.POST.get("texte", "").strip()

        if len(texte_soumis) < 15:
            erreur = "Décris un peu plus la situation (15 caractères minimum) pour que l'analyse soit fiable."
        else:
            categorie, confiance = predict_categorie(texte_soumis)
            entites = extract_entities(texte_soumis)

            # Recurrence AVANT d'enregistrer les entités de CE signalement
            recurrence = calculer_recurrence(entites)
            score, detail_score = score_de_risque(texte_soumis, categorie, recurrence)
            campagne_detectee = (recurrence + 1) >= 3

            with transaction.atomic():
                signalement = Signalement.objects.create(
                    texte=texte_soumis,
                    categorie_predite=categorie,
                    confiance=confiance,
                    score_risque=score,
                    canal_detecte=detail_score["canal_detecte"],
                    campagne_detectee=campagne_detectee,
                    signalements_lies=recurrence,
                )
                for tel in entites["telephones"]:
                    EntiteSignalement.objects.create(
                        signalement=signalement, type_entite="telephone", valeur=tel
                    )
                for lien in entites["liens"]:
                    EntiteSignalement.objects.create(
                        signalement=signalement, type_entite="lien", valeur=lien
                    )

            # Post/Redirect/Get : on redirige après un POST réussi au lieu de
            # renvoyer directement le rendu. Sans ça, actualiser la page (F5)
            # après soumission renvoie le même formulaire une deuxième fois
            # et crée un signalement en double.
            return redirect("signalements:resultat_signalement", signalement_id=signalement.id)

    return render(
        request,
        "signalements/form.html",
        {
            "resultat": None,
            "texte_soumis": texte_soumis,
            "erreur": erreur,
            "alertes": obtenir_toutes_les_alertes(),
        },
    )


@interface_utilisateur_requise
def resultat_signalement(request, signalement_id):
    """
    Affiche le résultat d'un signalement déjà enregistré (accessible en GET
    uniquement -- actualiser cette page ne resoumet rien, contrairement à
    l'ancien comportement).
    """
    signalement = get_object_or_404(Signalement, id=signalement_id)

    mots_importants = expliquer_prediction(signalement.texte, signalement.categorie_predite)
    entites = extract_entities(signalement.texte)

    resultat = {
        "id": signalement.id,
        "categorie": signalement.categorie_predite,
        "confiance_pct": round(signalement.confiance * 100, 1),
        "score": signalement.score_risque,
        "niveau": (
            "eleve" if signalement.score_risque >= 65
            else "moyen" if signalement.score_risque >= 35
            else "faible"
        ),
        "mots_importants": mots_importants,
        "telephones": entites["telephones"],
        "liens": entites["liens"],
        "montants": entites["montants"],
        "campagne_detectee": signalement.campagne_detectee,
        "signalements_lies": signalement.signalements_lies,
    }

    return render(
        request,
        "signalements/form.html",
        {
            "resultat": resultat,
            "texte_soumis": "",
            "erreur": None,
            "alertes": obtenir_toutes_les_alertes(),
        },
    )


@interface_utilisateur_requise
def tableau_de_bord(request):
    """
    Vue de consultation : compte les signalements par catégorie et permet
    de filtrer la liste pour voir précisément ce qui a été classé où.
    """
    comptes_par_categorie = (
        Signalement.objects.values("categorie_predite")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    categorie_filtree = request.GET.get("categorie", "").strip()

    signalements_qs = Signalement.objects.select_related("dossier").order_by("-date_creation")
    if categorie_filtree:
        signalements_qs = signalements_qs.filter(categorie_predite=categorie_filtree)

    paginator = Paginator(signalements_qs, 20)
    numero_page = request.GET.get("page", 1)
    page = paginator.get_page(numero_page)

    return render(
        request,
        "signalements/dashboard.html",
        {
            "comptes_par_categorie": comptes_par_categorie,
            "categorie_filtree": categorie_filtree,
            "page": page,
            "total_general": Signalement.objects.count(),
            "categories_connues": CATEGORIES,
            "alertes": obtenir_toutes_les_alertes(),
            "est_admin": est_administrateur(request.user),
        },
    )


@admin_requis
def transmettre_signalement(request, signalement_id):
    """
    Bouton "Transmettre à l'autorité compétente" accessible depuis le site
    (tableau de bord), pas seulement depuis l'admin Django. Crée le
    Dossier puis revient à la page d'où venait la demande.
    """
    from django.contrib import messages

    signalement = get_object_or_404(Signalement, id=signalement_id)

    if hasattr(signalement, "dossier"):
        messages.warning(request, f"Le signalement #{signalement.id} avait déjà été transmis.")
    else:
        Dossier.objects.create(signalement=signalement)
        messages.success(
            request,
            f"Informations critiques du signalement #{signalement.id} transmises à l'autorité compétente."
        )

    page_retour = request.META.get("HTTP_REFERER")
    if page_retour:
        return redirect(page_retour)
    return redirect("signalements:tableau_de_bord")


@interface_utilisateur_requise
def liste_clusters(request):
    """
    Vue de consultation des clusters émergents détectés par la commande
    `python manage.py detecter_nouvelles_arnaques`. Permet à un modérateur
    de voir d'un coup d'œil les phénomènes potentiellement nouveaux
    repérés par clustering, avant validation.
    """
    clusters = (
        ClusterEmergent.objects.all()
        .annotate(nb_reel=Count("signalements"))
        .order_by("-date_analyse")
    )

    return render(
        request,
        "signalements/clusters.html",
        {"clusters": clusters},
    )


@interface_utilisateur_requise
def detail_cluster(request, cluster_id):
    """Liste des signalements rattachés à un cluster émergent précis."""
    cluster = get_object_or_404(ClusterEmergent, id=cluster_id)

    signalements_qs = cluster.signalements.all().order_by("-date_creation")
    paginator = Paginator(signalements_qs, 20)
    numero_page = request.GET.get("page", 1)
    page = paginator.get_page(numero_page)

    return render(
        request,
        "signalements/cluster_detail.html",
        {"cluster": cluster, "page": page},
    )


# Config par granularité : fonction de regroupement Django, fenêtre de temps
# affichée, et format d'affichage des étiquettes sur les graphes.
GRANULARITES = {
    "jour": {"trunc": TruncDate, "fenetre": timedelta(days=14), "format": "%d/%m"},
    "semaine": {"trunc": TruncWeek, "fenetre": timedelta(weeks=12), "format": "%d/%m"},
    "mois": {"trunc": TruncMonth, "fenetre": timedelta(days=365), "format": "%m/%Y"},
    "annee": {"trunc": TruncYear, "fenetre": timedelta(days=365 * 5), "format": "%Y"},
}

PALETTE_GRAPHIQUE = [
    "#12203B", "#E3A23B", "#2E6B52", "#B8432E",
    "#3C4A63", "#8A6D3B", "#5B7FAE", "#7A4B6D",
]


@interface_utilisateur_requise
def statistiques(request):
    """
    Statistiques par catégorie sur différentes échelles de temps (jour,
    semaine, mois, année), avec graphiques -- pour repérer des tendances
    ("les arnaques crypto explosent ce mois-ci") plutôt que des cas isolés.
    """
    granularite = request.GET.get("granularite", "mois")
    if granularite not in GRANULARITES:
        granularite = "mois"
    config = GRANULARITES[granularite]

    depuis = timezone.now() - config["fenetre"]

    lignes = (
        Signalement.objects
        .filter(date_creation__gte=depuis)
        .annotate(periode=config["trunc"]("date_creation"))
        .values("periode", "categorie_predite")
        .annotate(total=Count("id"))
        .order_by("periode")
    )

    periodes = sorted({l["periode"] for l in lignes})
    categories_presentes = sorted({l["categorie_predite"] for l in lignes})

    matrice = {cat: {p: 0 for p in periodes} for cat in categories_presentes}
    for l in lignes:
        matrice[l["categorie_predite"]][l["periode"]] = l["total"]

    labels = [p.strftime(config["format"]) for p in periodes]

    datasets = [
        {
            "label": cat,
            "data": [matrice[cat][p] for p in periodes],
            "couleur": PALETTE_GRAPHIQUE[i % len(PALETTE_GRAPHIQUE)],
        }
        for i, cat in enumerate(categories_presentes)
    ]

    # Tableau récapitulatif : total par catégorie sur toute la fenêtre + tendance
    totaux = (
        Signalement.objects
        .filter(date_creation__gte=depuis)
        .values("categorie_predite")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    total_general = sum(t["total"] for t in totaux)

    return render(
        request,
        "signalements/statistiques.html",
        {
            "granularite": granularite,
            "labels_json": json.dumps(labels),
            "datasets_json": json.dumps(datasets),
            "totaux": totaux,
            "total_general": total_general,
            "alertes": obtenir_toutes_les_alertes(),
        },
    )


@interface_utilisateur_requise
def alertes_actives(request):
    """
    Page dédiée à TOUTES les alertes actives, regroupées par origine :
    - campagnes détectées (même numéro/lien réutilisé 3+ fois)
    - clusters émergents confirmés par un modérateur
    - tendances (une catégorie précise en nette hausse récente)

    Contrairement à la bannière (qui résume tout en un bloc sur les autres
    pages), cette page distingue explicitement l'origine de chaque alerte
    et explique comment/pourquoi elle a été générée.
    """
    alertes_campagnes = obtenir_alertes_campagnes()
    alertes_clusters = obtenir_alertes_clusters()
    alertes_tendances = obtenir_alertes_tendances()

    return render(
        request,
        "signalements/alertes.html",
        {
            "alertes_campagnes": alertes_campagnes,
            "alertes_clusters": alertes_clusters,
            "alertes_tendances": alertes_tendances,
            "total_alertes": (
                len(alertes_campagnes) + len(alertes_clusters) + len(alertes_tendances)
            ),
        },
    )


# ---------------------------------------------------------------------
# Pages "Autorité compétente" (cf. diagramme de cas d'utilisation) :
# consulter les dossiers, confirmer/infirmer la véracité, mettre à jour
# le statut d'un dossier transmis.
# ---------------------------------------------------------------------

@autorite_requise
def dossiers_liste(request):
    """Consulter les dossiers -- liste de tous les dossiers transmis,
    filtrable par statut."""
    statut_filtre = request.GET.get("statut", "").strip()

    dossiers_qs = Dossier.objects.select_related("signalement").all()
    if statut_filtre:
        dossiers_qs = dossiers_qs.filter(statut=statut_filtre)

    paginator = Paginator(dossiers_qs, 20)
    numero_page = request.GET.get("page", 1)
    page = paginator.get_page(numero_page)

    comptes_par_statut = (
        Dossier.objects.values("statut").annotate(total=Count("id")).order_by("statut")
    )

    return render(
        request,
        "signalements/dossiers.html",
        {
            "page": page,
            "statut_filtre": statut_filtre,
            "comptes_par_statut": comptes_par_statut,
            "total_general": Dossier.objects.count(),
            "statut_choices": Dossier.STATUT_CHOICES,
        },
    )


@autorite_requise
def dossier_detail(request, dossier_id):
    """
    Confirmer/infirmer la véracité d'une arnaque signalée + mettre à jour
    le statut d'un dossier transmis -- les deux actions se font sur la
    même page, via deux formulaires séparés (identifiés par le champ
    'action' du POST).
    """
    dossier = get_object_or_404(Dossier.objects.select_related("signalement"), id=dossier_id)
    message = None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "veracite":
            veracite = request.POST.get("veracite")
            if veracite in dict(Dossier.VERACITE_CHOICES):
                dossier.veracite = veracite
                dossier.save(update_fields=["veracite", "date_maj"])
                message = "Véracité mise à jour."

        elif action == "statut":
            statut = request.POST.get("statut")
            commentaire = request.POST.get("commentaire_autorite", "").strip()
            if statut in dict(Dossier.STATUT_CHOICES):
                dossier.statut = statut
                dossier.commentaire_autorite = commentaire
                dossier.save(update_fields=["statut", "commentaire_autorite", "date_maj"])
                message = "Statut du dossier mis à jour."

        dossier.refresh_from_db()

    entites = extract_entities(dossier.signalement.texte)

    return render(
        request,
        "signalements/dossier_detail.html",
        {
            "dossier": dossier,
            "entites": entites,
            "message": message,
        },
    )


@admin_ou_autorite_requis
def dossier_pdf(request, dossier_id):
    """
    Génère un document PDF reprenant les informations critiques d'un
    dossier -- destiné à être transmis à l'autorité compétente par un
    autre canal (email, impression) si elle n'utilise pas encore la
    plateforme directement, ou archivé de son côté sinon.
    """
    import io
    from django.http import FileResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib import colors

    dossier = get_object_or_404(Dossier.objects.select_related("signalement"), id=dossier_id)
    signalement = dossier.signalement
    entites = extract_entities(signalement.texte)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle(
        "TitreDossier", parent=styles["Title"], fontSize=16, alignment=TA_CENTER,
        textColor=colors.HexColor("#12203B"),
    )
    sous_titre_style = ParagraphStyle(
        "SousTitre", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER,
        textColor=colors.HexColor("#3C4A63"),
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"], fontSize=12,
        textColor=colors.HexColor("#12203B"), spaceBefore=14, spaceAfter=6,
    )
    corps_style = styles["Normal"]

    story = []
    story.append(Paragraph("SignalArnaque Togo", titre_style))
    story.append(Paragraph("Dossier transmis à l'autorité compétente", sous_titre_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#D7D9CF")))
    story.append(Spacer(1, 14))

    # Informations générales du dossier
    donnees_generales = [
        ["Numéro de dossier", f"#{dossier.id}"],
        ["Date de transmission", dossier.date_transmission.strftime("%d/%m/%Y %H:%M")],
        ["Statut actuel", dossier.get_statut_display()],
        ["Véracité", dossier.get_veracite_display()],
        ["Catégorie d'arnaque (IA)", signalement.categorie_predite],
        ["Confiance du modèle", f"{signalement.confiance * 100:.1f} %"],
        ["Score de risque", f"{signalement.score_risque} / 100"],
        ["Canal détecté", signalement.canal_detecte or "Non déterminé"],
        ["Campagne active détectée", "Oui" if signalement.campagne_detectee else "Non"],
    ]
    table_generale = Table(donnees_generales, colWidths=[6 * cm, 10 * cm])
    table_generale.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#3C4A63")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#D7D9CF")),
    ]))
    story.append(table_generale)

    # Texte du signalement
    story.append(Paragraph("Texte du signalement", section_style))
    story.append(Paragraph(signalement.texte.replace("\n", "<br/>"), corps_style))

    # Entités détectées
    if entites["telephones"] or entites["liens"] or entites["montants"]:
        story.append(Paragraph("Éléments détectés automatiquement", section_style))
        elements_detectes = (
            entites["telephones"] + entites["liens"] + entites["montants"]
        )
        story.append(Paragraph(", ".join(elements_detectes), corps_style))

    # Commentaire de l'autorité, s'il existe
    if dossier.commentaire_autorite:
        story.append(Paragraph("Commentaire de l'autorité compétente", section_style))
        story.append(Paragraph(dossier.commentaire_autorite.replace("\n", "<br/>"), corps_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#D7D9CF")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Document généré automatiquement par la plateforme SignalArnaque Togo. "
        "Ce dossier est basé sur un signalement soumis par un utilisateur et une "
        "analyse automatique -- il ne constitue pas une preuve judiciaire en soi.",
        ParagraphStyle("Pied", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#3C4A63")),
    ))

    doc.build(story)
    buffer.seek(0)

    return FileResponse(
        buffer, as_attachment=True,
        filename=f"dossier_{dossier.id}_signalarnaque.pdf",
        content_type="application/pdf",
    )


@admin_requis
def moderation_signalement(request, signalement_id):
    """
    Page de modération d'UN signalement, sur le site (pas dans l'admin
    Django brut) -- réservée aux administrateurs. Permet de transmettre
    les informations critiques à l'autorité compétente en un clic.
    """
    signalement = get_object_or_404(Signalement, id=signalement_id)
    message = None

    if request.method == "POST" and request.POST.get("action") == "transmettre":
        if not hasattr(signalement, "dossier"):
            Dossier.objects.create(signalement=signalement)
            message = "Informations critiques transmises à l'autorité compétente."
        else:
            message = "Ce signalement avait déjà été transmis."
        signalement.refresh_from_db()

    entites = extract_entities(signalement.texte)
    mots_importants = expliquer_prediction(signalement.texte, signalement.categorie_predite)
    deja_transmis = hasattr(signalement, "dossier")

    return render(
        request,
        "signalements/moderation_signalement.html",
        {
            "signalement": signalement,
            "entites": entites,
            "mots_importants": mots_importants,
            "deja_transmis": deja_transmis,
            "dossier": signalement.dossier if deja_transmis else None,
            "message": message,
        },
    )
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
    search_fields = ["numero_telephone","email", "profil_vendeur", "description"]
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
        from django.contrib.auth import get_user_model
        User = get_user_model()
        total = Signalement.objects.count()
        return Response({
            "total": total,
            "utilisateurs": User.objects.filter(est_actif=True).count(),
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


from azure.storage.blob import BlobServiceClient

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def upload_preuve(request):
    fichier = request.FILES.get("fichier")
    if not fichier:
        return Response({"error": "Aucun fichier fourni."}, status=400)

    ext = os.path.splitext(fichier.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return Response({"error": f"Type de fichier non autorisé: {ext}"}, status=400)
    if fichier.size > MAX_FILE_SIZE:
        return Response({"error": "Le fichier dépasse 10 Mo."}, status=400)

    unique_name = f"{uuid.uuid4().hex}{ext}"
    client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
    container = client.get_container_client(settings.AZURE_CONTAINER_NAME)
    container.upload_blob(unique_name, fichier.read())

    url = f"https://{settings.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{settings.AZURE_CONTAINER_NAME}/{unique_name}"
    return Response({"url": url, "filename": fichier.name}, status=201)