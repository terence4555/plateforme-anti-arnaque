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
    predict_categorie, expliquer_prediction,
    score_de_risque, calculer_recurrence,
)
from .ml.preprocessing import extract_entities
from .permissions import (
    autorite_requise, interface_utilisateur_requise,
    admin_ou_autorite_requis, admin_requis, est_administrateur,
)
from .models import Signalement, EntiteSignalement, ClusterEmergent, Dossier

CATEGORIES = [
    "Phishing", "Arnaque sentimentale", "Faux site e-commerce",
    "Fausse offre d'emploi", "Usurpation d'identite",
    "Arnaque crypto", "Arnaque a la loterie", "Incertain",
]

@interface_utilisateur_requise
def signaler_arnaque(request):
    texte_soumis = ""
    erreur = None

    if request.method == "POST":
        texte_soumis = request.POST.get("texte", "").strip()
        if len(texte_soumis) < 15:
            erreur = "Decris un peu plus la situation (15 caracteres minimum)."
        else:
            categorie, confiance = predict_categorie(texte_soumis)
            entites = extract_entities(texte_soumis)
            recurrence = calculer_recurrence(entites)
            score, detail_score = score_de_risque(texte_soumis, categorie, recurrence)
            campagne_detectee = (recurrence + 1) >= 3

            with transaction.atomic():
                signalement = Signalement.objects.create(
                    texte=texte_soumis, categorie_predite=categorie,
                    confiance=confiance, score_risque=score,
                    canal_detecte=detail_score["canal_detecte"],
                    campagne_detectee=campagne_detectee,
                    signalements_lies=recurrence,
                )
                for tel in entites["telephones"]:
                    EntiteSignalement.objects.create(
                        signalement=signalement, type_entite="telephone", valeur=tel)
                for lien in entites["liens"]:
                    EntiteSignalement.objects.create(
                        signalement=signalement, type_entite="lien", valeur=lien)
            return redirect("signalements:resultat_signalement", signalement_id=signalement.id)

    return render(request, "signalements/form.html", {
        "resultat": None, "texte_soumis": texte_soumis,
        "erreur": erreur, "alertes": obtenir_toutes_les_alertes(),
    })

@interface_utilisateur_requise
def resultat_signalement(request, signalement_id):
    signalement = get_object_or_404(Signalement, id=signalement_id)
    mots_importants = expliquer_prediction(signalement.texte, signalement.categorie_predite)
    entites = extract_entities(signalement.texte)
    resultat = {
        "id": signalement.id, "categorie": signalement.categorie_predite,
        "confiance_pct": round(signalement.confiance * 100, 1),
        "score": signalement.score_risque,
        "niveau": ("eleve" if signalement.score_risque >= 65 else "moyen" if signalement.score_risque >= 35 else "faible"),
        "mots_importants": mots_importants,
        "telephones": entites["telephones"], "liens": entites["liens"],
        "montants": entites["montants"],
        "campagne_detectee": signalement.campagne_detectee,
        "signalements_lies": signalement.signalements_lies,
    }
    return render(request, "signalements/form.html", {
        "resultat": resultat, "texte_soumis": "",
        "erreur": None, "alertes": obtenir_toutes_les_alertes(),
    })

@interface_utilisateur_requise
def tableau_de_bord(request):
    comptes_par_categorie = (
        Signalement.objects.values("categorie_predite")
        .annotate(total=Count("id")).order_by("-total"))
    categorie_filtree = request.GET.get("categorie", "").strip()
    signalements_qs = Signalement.objects.select_related("dossier").order_by("-date_creation")
    if categorie_filtree:
        signalements_qs = signalements_qs.filter(categorie_predite=categorie_filtree)
    paginator = Paginator(signalements_qs, 20)
    page = paginator.get_page(request.GET.get("page", 1))
    return render(request, "signalements/dashboard.html", {
        "comptes_par_categorie": comptes_par_categorie,
        "categorie_filtree": categorie_filtree, "page": page,
        "total_general": Signalement.objects.count(),
        "categories_connues": CATEGORIES,
        "alertes": obtenir_toutes_les_alertes(),
        "est_admin": est_administrateur(request.user),
    })

@admin_requis
def transmettre_signalement(request, signalement_id):
    from django.contrib import messages
    signalement = get_object_or_404(Signalement, id=signalement_id)
    if hasattr(signalement, "dossier"):
        messages.warning(request, f"Le signalement #{signalement.id} avait deja ete transmis.")
    else:
        Dossier.objects.create(signalement=signalement)
        messages.success(request, f"Signalement #{signalement.id} transmis a l'autorite competente.")
    page_retour = request.META.get("HTTP_REFERER")
    return redirect(page_retour) if page_retour else redirect("signalements:tableau_de_bord")

@interface_utilisateur_requise
def liste_clusters(request):
    clusters = ClusterEmergent.objects.all().annotate(nb_reel=Count("signalements")).order_by("-date_analyse")
    return render(request, "signalements/clusters.html", {"clusters": clusters})

@interface_utilisateur_requise
def detail_cluster(request, cluster_id):
    cluster = get_object_or_404(ClusterEmergent, id=cluster_id)
    signalements_qs = cluster.signalements.all().order_by("-date_creation")
    paginator = Paginator(signalements_qs, 20)
    page = paginator.get_page(request.GET.get("page", 1))
    return render(request, "signalements/cluster_detail.html", {"cluster": cluster, "page": page})

GRANULARITES = {
    "jour":  {"trunc": TruncDate,  "fenetre": timedelta(days=14),     "format": "%d/%m"},
    "semaine": {"trunc": TruncWeek,  "fenetre": timedelta(weeks=12),    "format": "%d/%m"},
    "mois":   {"trunc": TruncMonth, "fenetre": timedelta(days=365),    "format": "%m/%Y"},
    "annee":  {"trunc": TruncYear,  "fenetre": timedelta(days=365 * 5), "format": "%Y"},
}

PALETTE_GRAPHIQUE = [
    "#12203B", "#E3A23B", "#2E6B52", "#B8432E",
    "#3C4A63", "#8A6D3B", "#5B7FAE", "#7A4B6D",
]

@interface_utilisateur_requise
def statistiques(request):
    granularite = request.GET.get("granularite", "mois")
    if granularite not in GRANULARITES:
        granularite = "mois"
    config = GRANULARITES[granularite]
    depuis = timezone.now() - config["fenetre"]

    lignes = (
        Signalement.objects.filter(date_creation__gte=depuis)
        .annotate(periode=config["trunc"]("date_creation"))
        .values("periode", "categorie_predite")
        .annotate(total=Count("id")).order_by("periode"))

    periodes = sorted({l["periode"] for l in lignes})
    categories_presentes = sorted({l["categorie_predite"] for l in lignes})
    matrice = {cat: {p: 0 for p in periodes} for cat in categories_presentes}
    for l in lignes:
        matrice[l["categorie_predite"]][l["periode"]] = l["total"]

    labels = [p.strftime(config["format"]) for p in periodes]
    datasets = [{"label": cat, "data": [matrice[cat][p] for p in periodes],
                 "couleur": PALETTE_GRAPHIQUE[i % len(PALETTE_GRAPHIQUE)]}
                for i, cat in enumerate(categories_presentes)]

    totaux = (
        Signalement.objects.filter(date_creation__gte=depuis)
        .values("categorie_predite").annotate(total=Count("id")).order_by("-total"))
    total_general = sum(t["total"] for t in totaux)

    return render(request, "signalements/statistiques.html", {
        "granularite": granularite, "labels_json": json.dumps(labels),
        "datasets_json": json.dumps(datasets), "totaux": totaux,
        "total_general": total_general, "alertes": obtenir_toutes_les_alertes(),
    })

@interface_utilisateur_requise
def alertes_actives(request):
    alertes_campagnes = obtenir_alertes_campagnes()
    alertes_clusters = obtenir_alertes_clusters()
    alertes_tendances = obtenir_alertes_tendances()
    return render(request, "signalements/alertes.html", {
        "alertes_campagnes": alertes_campagnes,
        "alertes_clusters": alertes_clusters,
        "alertes_tendances": alertes_tendances,
        "total_alertes": len(alertes_campagnes) + len(alertes_clusters) + len(alertes_tendances),
    })

@autorite_requise
def dossiers_liste(request):
    statut_filtre = request.GET.get("statut", "").strip()
    dossiers_qs = Dossier.objects.select_related("signalement").all()
    if statut_filtre:
        dossiers_qs = dossiers_qs.filter(statut=statut_filtre)
    paginator = Paginator(dossiers_qs, 20)
    page = paginator.get_page(request.GET.get("page", 1))
    comptes_par_statut = (
        Dossier.objects.values("statut").annotate(total=Count("id")).order_by("statut"))
    return render(request, "signalements/dossiers.html", {
        "page": page, "statut_filtre": statut_filtre,
        "comptes_par_statut": comptes_par_statut,
        "total_general": Dossier.objects.count(),
        "statut_choices": Dossier.STATUT_CHOICES,
    })

@autorite_requise
def dossier_detail(request, dossier_id):
    dossier = get_object_or_404(Dossier.objects.select_related("signalement"), id=dossier_id)
    message = None
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "veracite":
            veracite = request.POST.get("veracite")
            if veracite in dict(Dossier.VERACITE_CHOICES):
                dossier.veracite = veracite
                dossier.save(update_fields=["veracite", "date_maj"])
                message = "Veracite mise a jour."
        elif action == "statut":
            statut = request.POST.get("statut")
            commentaire = request.POST.get("commentaire_autorite", "").strip()
            if statut in dict(Dossier.STATUT_CHOICES):
                dossier.statut = statut
                dossier.commentaire_autorite = commentaire
                dossier.save(update_fields=["statut", "commentaire_autorite", "date_maj"])
                message = "Statut du dossier mis a jour."
        dossier.refresh_from_db()
    entites = extract_entities(dossier.signalement.texte)
    return render(request, "signalements/dossier_detail.html", {
        "dossier": dossier, "entites": entites, "message": message,
    })

@admin_ou_autorite_requis
def dossier_pdf(request, dossier_id):
    import io
    from django.http import FileResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable)
    from reportlab.lib import colors

    dossier = get_object_or_404(Dossier.objects.select_related("signalement"), id=dossier_id)
    signalement = dossier.signalement
    entites = extract_entities(signalement.texte)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        topMargin=2*cm, bottomMargin=2*cm, leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle("TitreDossier", parent=styles["Title"],
        fontSize=16, alignment=TA_CENTER, textColor=colors.HexColor("#12203B"))
    corps_style = styles["Normal"]

    story = []
    story.append(Paragraph("SignalArnaque Togo", titre_style))
    story.append(Spacer(1, 14))
    donnees = [
        ["Numero de dossier", f"#{dossier.id}"],
        ["Date de transmission", dossier.date_transmission.strftime("%d/%m/%Y %H:%M")],
        ["Statut", dossier.get_statut_display()],
        ["Veracite", dossier.get_veracite_display()],
        ["Categorie (IA)", signalement.categorie_predite],
        ["Score de risque", f"{signalement.score_risque} / 100"],
    ]
    table = Table(donnees, colWidths=[6*cm, 10*cm])
    table.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(table)
    story.append(Paragraph(signalement.texte.replace("\n", "<br/>"), corps_style))
    doc.build(story)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True,
        filename=f"dossier_{dossier.id}.pdf", content_type="application/pdf")
