"""Modèle JournalAudit — table dbo.JournalAudit (lecture seule)."""
from django.db import models


class JournalAudit(models.Model):
    id_audit = models.AutoField(primary_key=True)
    table_cible = models.CharField(max_length=50)
    action = models.CharField(max_length=10)
    id_utilisateur = models.IntegerField(null=True, blank=True)
    date_action = models.DateTimeField(auto_now_add=True)
    details = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = "JournalAudit"
        managed = False
        ordering = ["-date_action"]

    def __str__(self):
        return f"[{self.action}] {self.table_cible} — {self.date_action}"
