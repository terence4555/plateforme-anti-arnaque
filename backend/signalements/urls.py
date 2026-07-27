from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignalementViewSet, upload_preuve

router = DefaultRouter()
router.register("", SignalementViewSet, basename="signalement")

urlpatterns = [
    path("upload/", upload_preuve, name="upload-preuve"),
    path("", include(router.urls)),
]

# --- URLs Templates (dashboard, clusters, dossiers, etc.) ---
from django.urls import path
from .views_templates import (
    signaler_arnaque, resultat_signalement, tableau_de_bord,
    transmettre_signalement, statistiques, alertes_actives,
    liste_clusters, detail_cluster, dossiers_liste,
    dossier_detail, dossier_pdf,
)

urlpatterns += [
    path("signaler/", signaler_arnaque, name="signaler"),
    path("signaler/resultat/<int:signalement_id>/", resultat_signalement, name="resultat_signalement"),
    path("tableau-de-bord/", tableau_de_bord, name="tableau_de_bord"),
    path("transmettre/<int:signalement_id>/", transmettre_signalement, name="transmettre_signalement"),
    path("statistiques/", statistiques, name="statistiques"),
    path("alertes/", alertes_actives, name="alertes_actives"),
    path("clusters/", liste_clusters, name="liste_clusters"),
    path("clusters/<int:cluster_id>/", detail_cluster, name="detail_cluster"),
    path("dossiers/", dossiers_liste, name="dossiers_liste"),
    path("dossiers/<int:dossier_id>/", dossier_detail, name="dossier_detail"),
    path("dossiers/<int:dossier_id>/pdf/", dossier_pdf, name="dossier_pdf"),
]
