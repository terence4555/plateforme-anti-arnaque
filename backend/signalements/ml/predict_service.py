"""
predict_service.py
--------------------
Version Django du pipeline de prédiction : mêmes règles métier que le
predict.py du prototype (seuil de confiance, explicabilité, score de risque),
mais la récurrence pour la détection de campagne est calculée par requête
en base de données plutôt qu'en mémoire.
"""

import numpy as np
from django.apps import apps

from .preprocessing import clean_text

SEUIL_CONFIANCE = 0.50

POIDS_GRAVITE_CATEGORIE = {
    "Phishing": 0.7,
    "Arnaque sentimentale": 0.8,
    "Faux site e-commerce": 0.5,
    "Fausse offre d'emploi": 0.6,
    "Usurpation d'identité": 0.9,
    "Arnaque crypto": 0.85,
    "Arnaque à la loterie": 0.6,
    "Incertain": 0.5,
}

POIDS_CANAL = {
    "whatsapp": 0.7,
    "facebook": 0.6,
    "instagram": 0.6,
    "telegram": 0.75,
    "sms": 0.65,
    "appel": 0.8,
    "email": 0.5,
}


def _get_model_and_vectorizer():
    config = apps.get_app_config("signalements")
    return config.model, config.vectorizer


def _detecter_canal(texte: str) -> str:
    t = texte.lower()
    for canal in POIDS_CANAL:
        if canal in t:
            return canal
    return "sms"


def _montant_en_nombre(montants_extraits: list) -> float:
    if not montants_extraits:
        return 0.0
    m = montants_extraits[0].lower()
    m = m.replace("fcfa", "").replace("f cfa", "").replace("francs", "")
    m = m.replace(" ", "").replace(".", "")
    try:
        return float(m)
    except ValueError:
        return 0.0


def predict_categorie(texte: str):
    """Retourne (categorie, confiance)."""
    model, vectorizer = _get_model_and_vectorizer()
    texte_propre = clean_text(texte)
    X = vectorizer.transform([texte_propre])
    probas = model.predict_proba(X)[0]

    idx_max = np.argmax(probas)
    categorie = model.classes_[idx_max]
    confiance = float(probas[idx_max])

    if confiance < SEUIL_CONFIANCE:
        return "Incertain", confiance
    return categorie, confiance


def expliquer_prediction(texte: str, categorie: str, top_n: int = 6):
    """Mots (TF-IDF) qui ont le plus pesé dans la décision, pour affichage."""
    if categorie == "Incertain":
        return []

    model, vectorizer = _get_model_and_vectorizer()
    texte_propre = clean_text(texte)
    X = vectorizer.transform([texte_propre])
    feature_names = np.array(vectorizer.get_feature_names_out())

    class_idx = list(model.classes_).index(categorie)
    coefs = model.coef_[class_idx]

    present_idx = X.nonzero()[1]
    scores = coefs[present_idx] * X[0, present_idx].toarray().flatten()

    ordre = np.argsort(scores)[::-1][:top_n]
    return [
        feature_names[present_idx[i]] for i in ordre if scores[i] > 0
    ]


def calculer_recurrence(entites: dict) -> int:
    """Compte combien de signalements EXISTANTS (déjà en base) partagent un
    téléphone ou un lien avec ce nouveau signalement. Appeler AVANT
    d'enregistrer les entités du nouveau signalement, sinon il se compterait
    lui-même."""
    from ..models import EntiteSignalement  # import tardif, évite les cycles

    recurrence = 0
    for tel in entites.get("telephones", []):
        n = EntiteSignalement.objects.filter(
            type_entite="telephone", valeur=tel
        ).count()
        recurrence = max(recurrence, n)

    for lien in entites.get("liens", []):
        n = EntiteSignalement.objects.filter(
            type_entite="lien", valeur=lien
        ).count()
        recurrence = max(recurrence, n)

    return recurrence


def score_de_risque(texte: str, categorie: str, recurrence: int = 0):
    """Formule transparente et explicable (voir README pour le détail)."""
    from .preprocessing import extract_entities

    entites = extract_entities(texte)
    montant = _montant_en_nombre(entites["montants"])
    poids_montant = min(montant / 1_000_000, 1.0)

    poids_categorie = POIDS_GRAVITE_CATEGORIE.get(categorie, 0.5)

    canal = _detecter_canal(texte)
    poids_canal = POIDS_CANAL.get(canal, 0.5)

    poids_recurrence = min(recurrence / 5, 1.0)

    score = 100 * (
        0.40 * poids_montant
        + 0.30 * poids_categorie
        + 0.15 * poids_canal
        + 0.15 * poids_recurrence
    )

    detail = {
        "montant_detecte_fcfa": montant,
        "canal_detecte": canal,
        "recurrence": recurrence,
    }
    return round(score, 1), detail
