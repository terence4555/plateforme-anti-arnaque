from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Vote


def recalculer_score(signalement):
    """Recalcule le score de confiance d'un signalement (0-100)."""
    votes = Vote.objects.filter(id_signalement=signalement)
    ups = votes.filter(type_vote="up").count()
    downs = votes.filter(type_vote="down").count()

    score = 100
    score += ups * 5          # la communaute approuve
    score -= downs * 10       # la communaute desapprouve

    if signalement.statut == "approuve":
        score -= 20           # arnaque confirmee = score bas = dangereux
    elif signalement.statut == "confirme":
        score -= 30
    elif signalement.statut == "rejete":
        score += 15           # faux signalement = remonte

    if signalement.type_arnaque == "faux_vendeur":
        score -= 10

    score = max(0, min(100, score))
    signalement.score = score
    signalement.save(update_fields=["score"])


@receiver(post_save, sender=Vote)
def on_vote_saved(sender, instance, **kwargs):
    recalculer_score(instance.id_signalement)


@receiver(post_delete, sender=Vote)
def on_vote_deleted(sender, instance, **kwargs):
    recalculer_score(instance.id_signalement)
