from django.db import models


# ============================================================
#  Modèles ML / Dashboard (issus de la branche "second")
# ============================================================


class ClusterEmergent(models.Model):
    """Groupe de signalements 'Incertain' détecté automatiquement par
    clustering (K-Means)."""

    mots_cles = models.CharField(max_length=500)
    nb_signalements = models.PositiveIntegerField(default=0)
    silhouette_score = models.FloatField(null=True, blank=True)
    nom_valide = models.CharField(max_length=100, blank=True, null=True)
    STATUT_CHOICES = [
        ("a_examiner", "À examiner"),
        ("confirme", "Confirmé comme nouvelle catégorie"),
        ("rejete", "Rejeté (bruit / faux positif)"),
    ]
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default="a_examiner")
    date_analyse = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_analyse"]

    def __str__(self):
        nom = self.nom_valide or "(non nommé)"
        return f"Cluster #{self.id} — {nom} ({self.nb_signalements} signalements)"


class Dossier(models.Model):
    """Dossier d'infraction transmis à l'Autorité compétente."""

    signalement = models.OneToOneField(
        "Signalement", on_delete=models.CASCADE, related_name="dossier"
    )
    STATUT_CHOICES = [
        ("recu", "Reçu"),
        ("en_examen", "En cours d'examen"),
        ("transmis_police", "Transmis à la police / justice"),
        ("classe_sans_suite", "Classé sans suite"),
        ("resolu", "Résolu"),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="recu")
    VERACITE_CHOICES = [
        ("non_examine", "Non examinée"),
        ("confirme", "Confirmée : c'est une arnaque"),
        ("infirme", "Infirmée : signalement non fondé"),
    ]
    veracite = models.CharField(max_length=15, choices=VERACITE_CHOICES, default="non_examine")
    commentaire_autorite = models.TextField(blank=True)
    date_transmission = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_transmission"]

    def __str__(self):
        return f"Dossier #{self.id} — signalement #{self.signalement_id} ({self.get_statut_display()})"


class EntiteSignalement(models.Model):
    """Entité extraite d'un signalement pour détection de campagne."""

    TYPE_CHOICES = [("telephone", "Téléphone"), ("lien", "Lien")]
    signalement = models.ForeignKey(
        "Signalement", on_delete=models.CASCADE, related_name="entites"
    )
    type_entite = models.CharField(max_length=15, choices=TYPE_CHOICES)
    valeur = models.CharField(max_length=255, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["type_entite", "valeur"])]

    def __str__(self):
        return f"{self.type_entite}: {self.valeur}"

from django.db import models


class Signalement(models.Model):
    TYPE_CHOICES = [
        ("faux_vendeur", "Faux vendeur"),
        ("phishing", "Hameconnage (phishing)"),
        ("usurpation_identite", "Usurpation d'identite"),
        ("produit_non_livre", "Produit non livre"),
        ("autre", "Autre type d'arnaque"),
    ]
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("approuve", "Approuve"),
        ("rejete", "Rejete"),
        ("transmis", "Transmis a l'autorite"),
        ("confirme", "Confirme par l'autorite"),
        ("infirme", "Infirme par l'autorite"),
    ]

    id_signalement = models.AutoField(primary_key=True)
    id_utilisateur = models.ForeignKey(
        "users.User", on_delete=models.CASCADE,
        db_column="id_utilisateur", related_name="signalements",
    )
    numero_telephone = models.CharField(max_length=20, blank=True, null=True)
    profil_vendeur = models.CharField(max_length=100, blank=True, null=True)
    type_arnaque = models.CharField(max_length=30, choices=TYPE_CHOICES)
    description = models.TextField()
    date_signalement = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default="en_attente")
    score = models.PositiveSmallIntegerField(default=100)

    class Meta:
        db_table = "Signalement"
        managed = False
        ordering = ["-date_signalement"]

    def __str__(self):
        identifiant = self.profil_vendeur or self.numero_telephone or f"#{self.id_signalement}"
        return f"{self.get_type_arnaque_display()} - {identifiant}"


class Preuve(models.Model):
    TYPE_CHOICES = [("image", "Image"), ("pdf", "PDF"), ("document", "Document")]

    id_preuve = models.AutoField(primary_key=True)
    id_signalement = models.ForeignKey(
        Signalement, on_delete=models.CASCADE,
        db_column="id_signalement", related_name="preuves",
    )
    fichier_url = models.CharField(max_length=300)
    type_fichier = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Preuve"
        managed = False
        ordering = ["date_upload"]

    def __str__(self):
        return f"Preuve {self.id_preuve} - Signalement #{self.id_signalement_id}"

