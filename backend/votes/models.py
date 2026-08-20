"""Modèle Vote — table dbo.Vote."""
from django.db import models


class Vote(models.Model):
    TYPE_CHOICES = [("up", "Utile (+1)"), ("down", "Pas utile (-1)")]

    id_vote = models.AutoField(primary_key=True)
    id_signalement = models.ForeignKey(
        "signalements.Signalement",
        on_delete=models.CASCADE,
        db_column="id_signalement",
        related_name="votes",
    )
    id_utilisateur = models.ForeignKey(
        "users.User",
        on_delete=models.DO_NOTHING,
        db_column="id_utilisateur",
        related_name="votes",
    )
    type_vote = models.CharField(max_length=4, choices=TYPE_CHOICES)
    date_vote = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Vote"
        managed = False
        unique_together = [("id_signalement", "id_utilisateur")]
        ordering = ["-date_vote"]

    def __str__(self):
        return f"{self.type_vote} — #{self.id_utilisateur_id} → #{self.id_signalement_id}"
