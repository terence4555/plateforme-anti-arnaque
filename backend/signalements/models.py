"""
Modèles Signalement et Preuve — mappent les tables existantes.
"""
from django.db import models


class Signalement(models.Model):
    """Signalement d'arnaque — table dbo.Signalement."""

    TYPE_CHOICES = [
        ("faux_vendeur", "Faux vendeur"),
        ("phishing", "Hameçonnage (phishing)"),
        ("usurpation_identite", "Usurpation d'identité"),
        ("produit_non_livre", "Produit non livré"),
        ("autre", "Autre type d'arnaque"),
    ]
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("approuve", "Approuvé"),
        ("rejete", "Rejeté"),
    ]

    id_signalement = models.AutoField(primary_key=True)
    id_utilisateur = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        db_column="id_utilisateur",
        related_name="signalements",
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
        tel = self.numero_telephone or ""
        profil = self.profil_vendeur or ""
        identifiant = profil or tel or f"#{self.id_signalement}"
        return f"{self.get_type_arnaque_display()} — {identifiant}"


class Preuve(models.Model):
    """Preuve rattachée à un signalement — table dbo.Preuve."""

    TYPE_CHOICES = [
        ("image", "Image"),
        ("pdf", "PDF"),
        ("document", "Document"),
    ]

    id_preuve = models.AutoField(primary_key=True)
    id_signalement = models.ForeignKey(
        Signalement,
        on_delete=models.CASCADE,
        db_column="id_signalement",
        related_name="preuves",
    )
    fichier_url = models.CharField(max_length=300)
    type_fichier = models.CharField(max_length=10, choices=TYPE_CHOICES)
    date_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Preuve"
        managed = False
        ordering = ["date_upload"]

    def __str__(self):
        return f"Preuve {self.id_preuve} — Signalement #{self.id_signalement_id}"
