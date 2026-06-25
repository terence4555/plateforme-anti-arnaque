"""Modèle Commentaire — table dbo.Commentaire."""
from django.db import models


class Commentaire(models.Model):
    id_commentaire = models.AutoField(primary_key=True)
    id_signalement = models.ForeignKey(
        "signalements.Signalement",
        on_delete=models.CASCADE,
        db_column="id_signalement",
        related_name="commentaires",
    )
    id_utilisateur = models.ForeignKey(
        "users.User",
        on_delete=models.DO_NOTHING,
        db_column="id_utilisateur",
        related_name="commentaires",
    )
    contenu = models.CharField(max_length=500)
    date_commentaire = models.DateTimeField(auto_now_add=True)
    est_masque = models.BooleanField(default=False)

    class Meta:
        db_table = "Commentaire"
        managed = False
        ordering = ["-date_commentaire"]

    def __str__(self):
        return f"Commentaire de #{self.id_utilisateur_id} sur #{self.id_signalement_id}"
