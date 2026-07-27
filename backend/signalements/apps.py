import os
import joblib
from django.apps import AppConfig


class SignalementsConfig(AppConfig):
    default = True  # auto-détecté par Django comme AppConfig par défaut
    default_auto_field = "django.db.models.BigAutoField"
    name = "signalements"
    verbose_name = "Signalements d'arnaque"

    # Chargés une seule fois au démarrage du serveur (voir ready() ci-dessous),
    # pas à chaque requête -> évite de recharger le modèle sur chaque appel.
    model = None
    vectorizer = None

    def ready(self):
        ml_dir = os.path.join(os.path.dirname(__file__), "ml")
        model_path = os.path.join(ml_dir, "model_signalements.joblib")
        vectorizer_path = os.path.join(ml_dir, "vectorizer_signalements.joblib")

        SignalementsConfig.model = joblib.load(model_path)
        SignalementsConfig.vectorizer = joblib.load(vectorizer_path)
