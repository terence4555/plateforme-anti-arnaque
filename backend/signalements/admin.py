from django.contrib import admin
from .models import Signalement, EntiteSignalement, ClusterEmergent, Dossier


class SignalementInlineCluster(admin.TabularInline):
    model = Signalement
    fk_name = "cluster_emergent"
    extra = 0
    fields = ("id", "texte", "confiance")
    readonly_fields = ("id", "texte", "confiance")
    can_delete = False
    max_num = 0  # lecture seule, on ne rajoute pas de signalement manuellement ici


@admin.register(ClusterEmergent)
class ClusterEmergentAdmin(admin.ModelAdmin):
    """
    Espace de validation des clusters émergents détectés par
    `python manage.py detecter_nouvelles_arnaques`. Un modérateur regarde
    les mots-clés + les signalements liés, puis :
    - renseigne 'nom_valide' si c'est un vrai nouveau type d'arnaque
    - passe 'statut' à 'confirme' ou 'rejete'
    """
    list_display = ("id", "mots_cles", "nb_signalements", "silhouette_score",
                     "nom_valide", "statut", "date_analyse")
    list_filter = ("statut",)
    list_editable = ("statut",)
    fields = ("mots_cles", "nb_signalements", "silhouette_score",
              "nom_valide", "statut", "date_analyse")
    readonly_fields = ("mots_cles", "nb_signalements", "silhouette_score", "date_analyse")
    inlines = [SignalementInlineCluster]


class EntiteInline(admin.TabularInline):
    model = EntiteSignalement
    extra = 0
    readonly_fields = ("type_entite", "valeur")
    can_delete = False


@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    """
    Permet à un modérateur de consulter les signalements et de corriger une
    prédiction fausse via 'categorie_corrigee'. Ces corrections constituent
    la base d'un futur ré-entraînement du modèle (boucle d'amélioration
    continue).
    """
    list_display = (
        "id", "categorie_predite", "categorie_corrigee", "confiance",
        "score_risque", "campagne_detectee", "cluster_emergent",
        "a_un_dossier", "date_creation",
    )
    list_filter = ("categorie_predite", "campagne_detectee", "canal_detecte")
    search_fields = ("texte",)
    readonly_fields = (
        "texte", "categorie_predite", "confiance", "score_risque",
        "canal_detecte", "campagne_detectee", "signalements_lies",
        "date_creation", "bouton_transmission",
    )
    fields = (
        "texte", "categorie_predite", "categorie_corrigee", "confiance",
        "score_risque", "canal_detecte", "campagne_detectee",
        "signalements_lies", "bouton_transmission", "date_creation",
    )
    inlines = [EntiteInline]
    actions = ["transmettre_a_autorite"]

    @admin.display(boolean=True, description="Dossier transmis")
    def a_un_dossier(self, obj):
        return hasattr(obj, "dossier")

    @admin.display(description="Transmission à l'autorité compétente")
    def bouton_transmission(self, obj):
        """
        Bouton visible directement sur la fiche d'un signalement : envoie
        ses informations critiques vers l'espace de l'Autorité compétente
        (crée un Dossier). Un lien de secours vers l'action groupée reste
        disponible dans le menu déroulant de la liste, mais ce bouton est
        le moyen le plus direct pour transmettre UN signalement à la fois.
        """
        from django.utils.html import format_html
        from django.urls import reverse

        if obj.pk is None:
            return "-- enregistre d'abord le signalement --"

        if hasattr(obj, "dossier"):
            url_dossier = reverse("admin:signalements_dossier_change", args=[obj.dossier.id])
            return format_html(
                '<span style="color:#2E6B52; font-weight:600;">✓ Déjà transmis</span> '
                '&mdash; <a href="{}">voir le dossier #{}</a>',
                url_dossier, obj.dossier.id,
            )

        url_transmettre = reverse("admin:signalements_signalement_transmettre", args=[obj.id])
        return format_html(
            '<a href="{}" style="display:inline-block; background:#12203B; color:#fff; '
            'padding:8px 16px; border-radius:8px; text-decoration:none; font-weight:600;">'
            'Transmettre à l\'autorité compétente</a>',
            url_transmettre,
        )

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        urls_custom = [
            path(
                "<int:signalement_id>/transmettre/",
                self.admin_site.admin_view(self.vue_transmettre),
                name="signalements_signalement_transmettre",
            ),
        ]
        return urls_custom + urls

    def vue_transmettre(self, request, signalement_id):
        """Vue appelée par le bouton -- crée le Dossier puis revient à la fiche."""
        from django.shortcuts import get_object_or_404, redirect
        from django.urls import reverse

        signalement = get_object_or_404(Signalement, id=signalement_id)
        if not hasattr(signalement, "dossier"):
            Dossier.objects.create(signalement=signalement)
            self.message_user(
                request,
                f"Informations critiques du signalement #{signalement.id} transmises à l'autorité compétente."
            )
        else:
            self.message_user(
                request, "Ce signalement avait déjà été transmis.", level="warning"
            )
        return redirect(reverse("admin:signalements_signalement_change", args=[signalement.id]))

    @admin.action(description="Transmettre à l'autorité compétente (créer un dossier)")
    def transmettre_a_autorite(self, request, queryset):
        crees = 0
        deja_existants = 0
        for signalement in queryset:
            if hasattr(signalement, "dossier"):
                deja_existants += 1
                continue
            Dossier.objects.create(signalement=signalement)
            crees += 1

        if crees:
            self.message_user(request, f"{crees} dossier(s) transmis à l'autorité compétente.")
        if deja_existants:
            self.message_user(
                request,
                f"{deja_existants} signalement(s) avaient déjà un dossier, ignorés.",
                level="warning",
            )


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    """Vue admin de secours sur les dossiers -- l'usage normal pour
    l'autorité compétente se fait via les pages dédiées du site, pas ici."""
    list_display = ("id", "signalement", "statut", "veracite", "date_transmission", "date_maj", "lien_pdf")
    list_filter = ("statut", "veracite")
    readonly_fields = ("signalement", "date_transmission", "date_maj", "lien_pdf")
    fields = ("signalement", "statut", "veracite", "commentaire_autorite", "date_transmission", "date_maj", "lien_pdf")

    @admin.display(description="Dossier PDF")
    def lien_pdf(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        url = reverse("signalements:dossier_pdf", args=[obj.id])
        return format_html('<a href="{}" target="_blank">Télécharger le PDF</a>', url)


@admin.register(EntiteSignalement)
class EntiteSignalementAdmin(admin.ModelAdmin):
    list_display = ("id", "type_entite", "valeur", "signalement")
    list_filter = ("type_entite",)
    search_fields = ("valeur",)
﻿from django.contrib import admin
from .models import Signalement, Preuve

class PreuveInline(admin.TabularInline):
    model = Preuve
    extra = 0

@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display = ["id_signalement", "type_arnaque", "numero_telephone", "profil_vendeur", "statut", "score", "date_signalement"]
    list_filter = ["type_arnaque", "statut"]
    search_fields = ["numero_telephone", "profil_vendeur", "description"]
    ordering = ["-date_signalement"]
    inlines = [PreuveInline]

@admin.register(Preuve)
class PreuveAdmin(admin.ModelAdmin):
    list_display = ["id_preuve", "id_signalement", "type_fichier", "date_upload"]
