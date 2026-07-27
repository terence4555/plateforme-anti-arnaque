# -*- coding: utf-8 -*-
"""
alertes.py
-----------
Transforme les détections internes (campagnes actives, clusters émergents
confirmés) en messages d'alerte lisibles par n'importe quel visiteur du
site -- sans humain qui les rédige à la main, et sans IA générative :
uniquement des phrases-modèles remplies avec les données réelles.

Pourquoi des templates plutôt qu'un modèle génératif :
- gratuit, instantané, pas de clé API ni de dépendance externe
- jamais d'erreur factuelle possible (contrairement à un texte "halluciné")
- cohérent avec le reste du projet, qui est déterministe et explicable
"""

from collections import Counter
from django.db.models import Count


def _mot_entite(type_entite):
    return "numéro" if type_entite == "telephone" else "lien"


def generer_message_alerte_campagne(categorie, canal, nb_signalements, valeur, type_entite):
    """Message d'alerte pour une campagne active (même numéro/lien réutilisé)."""
    mot = _mot_entite(type_entite)
    return (
        f"⚠️ {nb_signalements} personne(s) ont signalé une {categorie.lower()} "
        f"liée à ce {mot} repéré sur {canal.capitalize()} : {valeur}. "
        f"Ne partage aucune information ni argent avec ce contact."
    )


def generer_message_alerte_cluster(nom_categorie, mots_cles, nb_signalements):
    """Message d'alerte pour un nouveau type d'arnaque confirmé par un modérateur."""
    premiers_mots = ", ".join(mots_cles.split(",")[:4]).strip()
    return (
        f"⚠️ Nouveau type d'arnaque repéré : « {nom_categorie} ». "
        f"{nb_signalements} signalement(s) similaire(s) reçus récemment "
        f"(éléments caractéristiques : {premiers_mots})."
    )


def obtenir_alertes_campagnes(limite=5, seuil=3):
    """
    Cherche les numéros/liens partagés par au moins `seuil` signalements
    distincts, et génère un message d'alerte pour chacun.
    """
    from .models import EntiteSignalement, Signalement

    groupes = (
        EntiteSignalement.objects
        .values("type_entite", "valeur")
        .annotate(total=Count("signalement", distinct=True))
        .filter(total__gte=seuil)
        .order_by("-total")[:limite]
    )

    alertes = []
    for g in groupes:
        ids_signalements = (
            EntiteSignalement.objects
            .filter(type_entite=g["type_entite"], valeur=g["valeur"])
            .values_list("signalement_id", flat=True)
            .distinct()
        )
        signalements = list(
            Signalement.objects.filter(id__in=ids_signalements).order_by("-date_creation")
        )
        if not signalements:
            continue

        categories_connues = [
            s.categorie_predite for s in signalements if s.categorie_predite != "Incertain"
        ]
        categorie_dominante = (
            Counter(categories_connues).most_common(1)[0][0]
            if categories_connues else "arnaque"
        )
        canal = signalements[0].canal_detecte or "whatsapp"

        alertes.append({
            "message": generer_message_alerte_campagne(
                categorie_dominante, canal, g["total"], g["valeur"], g["type_entite"]
            ),
            "total": g["total"],
        })

    return alertes


def obtenir_alertes_clusters(limite=5):
    """
    Récupère les clusters émergents CONFIRMÉS par un modérateur (pas les
    "à examiner", uniquement ceux validés comme vrai nouveau phénomène).
    """
    from .models import ClusterEmergent

    clusters = (
        ClusterEmergent.objects
        .filter(statut="confirme")
        .exclude(nom_valide__isnull=True)
        .exclude(nom_valide__exact="")
        .order_by("-date_analyse")[:limite]
    )

    return [
        {
            "message": generer_message_alerte_cluster(
                c.nom_valide, c.mots_cles, c.nb_signalements
            ),
            "total": c.nb_signalements,
        }
        for c in clusters
    ]


def generer_message_tendance(categorie, total_actuel, total_precedent, jours):
    """
    Message d'alerte quand UNE catégorie précise explose récemment --
    nomme explicitement le type d'arnaque concerné, avec des chiffres réels.
    """
    if total_precedent == 0:
        return (
            f"⚠️ Vague de signalements en cours : {total_actuel} cas de "
            f"{categorie.lower()} recensés ces {jours} derniers jours. "
            f"Sois particulièrement vigilant si tu es contacté dans ce contexte."
        )
    variation_pct = round((total_actuel - total_precedent) / total_precedent * 100)
    signe = "+" if variation_pct >= 0 else ""
    return (
        f"⚠️ Vague de {categorie.lower()} en ce moment : {total_actuel} "
        f"signalements ces {jours} derniers jours contre {total_precedent} "
        f"sur la période précédente ({signe}{variation_pct}%). "
        f"Sois particulièrement vigilant face à ce type d'arnaque."
    )


def obtenir_alertes_tendances(jours=7, facteur_min=1.5, minimum_absolu=3):
    """
    Compare le nombre de signalements de chaque catégorie sur les `jours`
    derniers jours à la période équivalente juste avant, et génère un
    message pour toute catégorie en nette augmentation.

    Seuils :
    - minimum_absolu : évite de déclencher une alerte sur du bruit
      statistique (ex: passer de 1 à 2 signalements n'est pas une "vague")
    - facteur_min : la période actuelle doit représenter au moins 1.5x la
      période précédente pour être considérée comme une vraie hausse
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import Signalement

    maintenant = timezone.now()
    debut_actuelle = maintenant - timedelta(days=jours)
    debut_precedente = debut_actuelle - timedelta(days=jours)

    actuelle = (
        Signalement.objects
        .filter(date_creation__gte=debut_actuelle)
        .exclude(categorie_predite="Incertain")
        .values("categorie_predite")
        .annotate(total=Count("id"))
    )
    precedente = (
        Signalement.objects
        .filter(date_creation__gte=debut_precedente, date_creation__lt=debut_actuelle)
        .exclude(categorie_predite="Incertain")
        .values("categorie_predite")
        .annotate(total=Count("id"))
    )
    precedente_par_categorie = {p["categorie_predite"]: p["total"] for p in precedente}

    alertes = []
    for a in actuelle:
        categorie = a["categorie_predite"]
        total_actuel = a["total"]
        total_precedent = precedente_par_categorie.get(categorie, 0)

        if total_actuel < minimum_absolu:
            continue

        en_hausse = (
            total_precedent == 0
            or (total_actuel / total_precedent) >= facteur_min
        )
        if not en_hausse:
            continue

        alertes.append({
            "message": generer_message_tendance(categorie, total_actuel, total_precedent, jours),
            "total": total_actuel,
        })

    return alertes


def obtenir_toutes_les_alertes():
    """Point d'entrée unique utilisé par les vues pour afficher la bannière."""
    return (
        obtenir_alertes_campagnes()
        + obtenir_alertes_clusters()
        + obtenir_alertes_tendances()
    )
