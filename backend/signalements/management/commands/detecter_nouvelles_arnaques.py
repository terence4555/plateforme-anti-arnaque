# -*- coding: utf-8 -*-
"""
Commande de gestion : detecter_nouvelles_arnaques
----------------------------------------------------
Analyse tous les signalements classés "Incertain" par le modèle supervisé
et applique du clustering (K-Means) pour repérer des groupes cohérents,
signe possible d'un type d'arnaque émergent non couvert par les 7
catégories connues.

Usage :
    python manage.py detecter_nouvelles_arnaques
    python manage.py detecter_nouvelles_arnaques --min-signalements 20
"""

import numpy as np
from django.core.management.base import BaseCommand
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from signalements.models import Signalement, ClusterEmergent
from signalements.ml.preprocessing import clean_text


class Command(BaseCommand):
    help = "Applique du clustering sur les signalements 'Incertain' pour détecter des types d'arnaque émergents."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-signalements", type=int, default=15,
            help="Nombre minimum de signalements 'Incertain' requis avant de lancer l'analyse (défaut : 15)."
        )
        parser.add_argument(
            "--k-max", type=int, default=6,
            help="Nombre maximum de clusters à tester (défaut : 6)."
        )

    def handle(self, *args, **options):
        min_signalements = options["min_signalements"]
        k_max = options["k_max"]

        incertains = list(
            Signalement.objects.filter(categorie_predite="Incertain")
            .exclude(cluster_emergent__isnull=False)  # pas déjà analysés
        )

        if len(incertains) < min_signalements:
            self.stdout.write(self.style.WARNING(
                f"Seulement {len(incertains)} signalement(s) 'Incertain' non "
                f"encore analysé(s) (minimum requis : {min_signalements}). "
                f"Analyse reportée -- réessaie plus tard, une fois qu'il y en "
                f"aura davantage."
            ))
            return

        textes = [s.texte for s in incertains]
        textes_propres = [clean_text(t) for t in textes]

        # min_df/max_df doivent s'adapter à la taille du lot : avec très peu
        # de documents, min_df=2 et max_df=0.9 peuvent devenir incompatibles
        # (ex: max_df=0.9 sur 2 documents autorise moins de documents que
        # min_df=2 n'en exige). On assouplit automatiquement si le lot est
        # petit.
        n_docs = len(textes_propres)
        if n_docs < 10:
            min_df, max_df = 1, 1.0
        else:
            min_df, max_df = 2, 0.9

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=min_df, max_df=max_df)
        X = vectorizer.fit_transform(textes_propres)

        k_min = 2
        k_max_reel = min(k_max, X.shape[0] - 1)
        if k_max_reel < k_min:
            self.stdout.write(self.style.WARNING(
                "Pas assez de signalements distincts pour un clustering pertinent."
            ))
            return

        scores, modeles = {}, {}
        for k in range(k_min, k_max_reel + 1):
            km = KMeans(n_clusters=k, random_state=7, n_init=10)
            labels = km.fit_predict(X)
            scores[k] = silhouette_score(X, labels)
            modeles[k] = km

        # Méthode du coude : on privilégie le plus petit k qui atteint déjà
        # 92% du meilleur score observé -- évite de sur-découper le
        # phénomène en micro-clusters peu interprétables.
        meilleur_score = max(scores.values())
        seuil = 0.92 * meilleur_score
        meilleur_k = min(k for k, s in scores.items() if s >= seuil)
        meilleur_modele = modeles[meilleur_k]
        labels = meilleur_modele.predict(X)

        feature_names = np.array(vectorizer.get_feature_names_out())

        self.stdout.write(self.style.SUCCESS(
            f"\nAnalyse de {len(incertains)} signalement(s) 'Incertain' -> "
            f"{meilleur_k} cluster(s) retenu(s) (silhouette={scores[meilleur_k]:.3f})\n"
        ))

        for c in range(meilleur_k):
            indices_cluster = [i for i, lab in enumerate(labels) if lab == c]
            if not indices_cluster:
                continue

            centroide = meilleur_modele.cluster_centers_[c]
            top_idx = np.argsort(centroide)[::-1][:8]
            mots_cles = [feature_names[i] for i in top_idx if centroide[i] > 0]

            cluster_obj = ClusterEmergent.objects.create(
                mots_cles=", ".join(mots_cles),
                nb_signalements=len(indices_cluster),
                silhouette_score=scores[meilleur_k],
            )

            for i in indices_cluster:
                incertains[i].cluster_emergent = cluster_obj
                incertains[i].save(update_fields=["cluster_emergent"])

            self.stdout.write(
                f"  Cluster #{cluster_obj.id} : {len(indices_cluster)} signalement(s) "
                f"-- mots-clés : {', '.join(mots_cles[:6])}"
            )

        self.stdout.write(self.style.SUCCESS(
            "\nRendez-vous dans l'admin Django (section 'Clusters émergents') "
            "pour examiner ces groupes et, si pertinent, leur donner un nom "
            "et les confirmer comme nouvelle catégorie."
        ))
