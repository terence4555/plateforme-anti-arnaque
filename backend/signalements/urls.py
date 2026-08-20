from django.urls import path
from . import views

app_name = "signalements"

urlpatterns = [
    path("signaler/", views.signaler_arnaque, name="signaler"),
    path("signaler/resultat/<int:signalement_id>/", views.resultat_signalement, name="resultat_signalement"),
    path("tableau-de-bord/", views.tableau_de_bord, name="tableau_de_bord"),
    path("signalement/<int:signalement_id>/transmettre/", views.transmettre_signalement, name="transmettre_signalement"),
    path("statistiques/", views.statistiques, name="statistiques"),
    path("alertes/", views.alertes_actives, name="alertes_actives"),
    path("clusters/", views.liste_clusters, name="liste_clusters"),
    path("clusters/<int:cluster_id>/", views.detail_cluster, name="detail_cluster"),
    path("dossiers/", views.dossiers_liste, name="dossiers_liste"),
    path("dossiers/<int:dossier_id>/", views.dossier_detail, name="dossier_detail"),
    path("dossiers/<int:dossier_id>/pdf/", views.dossier_pdf, name="dossier_pdf"),
]
﻿from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignalementViewSet

router = DefaultRouter()
router.register("", SignalementViewSet, basename="signalement")

urlpatterns = [path("", include(router.urls))]
