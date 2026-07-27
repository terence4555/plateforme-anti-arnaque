# Intégration dans ton projet Django existant

Ce dossier `signalements/` est une **app Django autonome**, testée de bout en
bout (soumission de signalement, prédiction, seuil "Incertain", score de
risque, détection de campagne persistée en base). Tu peux la déposer telle
quelle dans ton projet.

## 1. Copier l'app

Place le dossier `signalements/` à la racine de ton projet Django, au même
niveau que tes autres apps (là où se trouve `manage.py`).

```
ton_projet/
├── manage.py
├── ton_projet/          <- ton dossier settings.py / urls.py
├── autre_app_existante/
└── signalements/         <- ce dossier
```

## 2. Dépendances

```bash
pip install scikit-learn joblib numpy pandas
```

(scikit-learn embarque numpy ; pandas n'est utile ici que si tu regénères le
dataset d'entraînement, pas pour faire tourner l'app en production.)

## 3. `settings.py`

Ajoute l'app à `INSTALLED_APPS` :

```python
INSTALLED_APPS = [
    ...
    "signalements",
]
```

## 4. `urls.py` du projet

```python
from django.urls import path, include

urlpatterns = [
    ...
    path("signalements/", include("signalements.urls")),
]
```

## 5. Migrations

```bash
python manage.py migrate signalements
```

(la migration `0001_initial.py` est déjà fournie dans `migrations/`, pas
besoin de refaire `makemigrations` sauf si tu modifies `models.py`)

## 6. Accès à la page

Une fois le serveur lancé (`python manage.py runserver`), la page est
disponible sur :

```
http://127.0.0.1:8000/signalements/signaler/
```

## 7. Espace modérateur (optionnel mais recommandé)

Les signalements et leurs entités (téléphones/liens) sont visibles et
corrigibles dans l'admin Django, si tu as un compte admin :

```bash
python manage.py createsuperuser
```

puis va sur `/admin/` → "Signalements d'arnaque". Le champ
`categorie_corrigee` permet à un modérateur de corriger une prédiction
fausse — ces corrections serviront de base pour ré-entraîner le modèle plus
tard.

## Comment ça marche techniquement

- **`apps.py`** charge le modèle (`.joblib`) et le vectorizer **une seule
  fois**, au démarrage du serveur, dans `SignalementsConfig.ready()`. Ils
  restent en mémoire pour toutes les requêtes suivantes — le modèle n'est
  **pas** rechargé à chaque signalement soumis.
- **`ml/predict_service.py`** contient toute la logique métier (prédiction,
  seuil de confiance, explicabilité, score de risque).
- **`models.py`** stocke chaque signalement + les entités qu'il contient
  (téléphone/lien) dans des tables séparées. La détection de campagne
  interroge la base (`EntiteSignalement.objects.filter(...).count()`) plutôt
  que de garder un état en mémoire — indispensable pour que ça fonctionne
  correctement en production (plusieurs workers, redémarrages du serveur).
- **`views.py`** orchestre tout : reçoit le POST, appelle le modèle,
  enregistre en base, renvoie le résultat à la page.
- **`templates/signalements/form.html`** est la page elle-même : formulaire
  + affichage du résultat (catégorie, barres de "signal" représentant le
  score de risque, mots ayant motivé la décision, alerte si campagne
  détectée).

## 8. Nouveauté : détection de nouvelles arnaques par clustering

En plus de la classification dans les 7 catégories connues, l'app peut
maintenant repérer des **types d'arnaque émergents** — des signalements
classés "Incertain" qui, une fois regroupés entre eux (clustering K-Means),
forment un groupe cohérent inédit.

**Comment l'utiliser :**

```bash
python manage.py detecter_nouvelles_arnaques
```

Cette commande :
1. récupère tous les signalements "Incertain" pas encore analysés,
2. les regroupe par similarité de texte (si assez nombreux — 15 par défaut,
   ajustable avec `--min-signalements`),
3. crée un ou plusieurs `ClusterEmergent` avec leurs mots-clés dominants,
4. rattache chaque signalement concerné à son cluster.

**Ensuite**, va dans l'admin Django → "Clusters émergents". Pour chaque
cluster : regarde les mots-clés et les signalements liés (affichés en
inline), et si ça ressemble à un vrai nouveau type d'arnaque, renseigne
`nom_valide` et passe `statut` à "Confirmé". Sinon, "Rejeté" (bruit).

À lancer périodiquement (par exemple une fois par semaine, ou via une
tâche planifiée/cron si le projet grandit).

**Important à savoir pour la soutenance** : c'est une méthode non
supervisée (le modèle ne "sait" pas ce qu'il cherche à l'avance), donc les
clusters ne sont jamais parfaits — l'objectif n'est pas de tout classer
automatiquement, mais de **faire remonter des pistes** qu'un modérateur
humain examine ensuite. C'est cette combinaison supervisé + non supervisé +
validation humaine qui rend le système robuste face à des arnaques qui
n'existaient pas encore au moment de l'entraînement.

## 9. Nouveauté : tableau de bord par catégorie

Une page permet maintenant de voir, pour chaque catégorie, combien de
signalements y sont classés, et de cliquer dessus pour voir la liste
détaillée :

```
http://127.0.0.1:8000/signalements/tableau-de-bord/
```

Un lien "Voir le tableau de bord" a aussi été ajouté en haut de la page de
signalement pour y accéder facilement. Chaque carte de catégorie affiche le
nombre de signalements qu'elle contient ; cliquer dessus filtre la liste en
dessous (avec pagination, 20 signalements par page).

## 10. Pages web pour visualiser les clusters émergents

```
http://127.0.0.1:8000/signalements/clusters/
http://127.0.0.1:8000/signalements/clusters/<id>/
```

**Mise à jour : ces pages sont maintenant accessibles à tous, comme les
autres pages du site** (tableau de bord, statistiques, alertes) — plus
besoin d'être connecté en tant qu'administrateur. Le lien "Clusters
émergents" est visible dans la navigation de toutes les pages.

Pour nommer un cluster ou changer son statut (confirmé/rejeté), ça reste
dans l'admin Django, comme indiqué sur la page — seule la **consultation**
est publique, la validation reste une action de modérateur.

Le fichier `permissions.py` (décorateur `admin_requis`) reste disponible
dans le projet si tu veux restreindre une autre page à l'avenir : il
suffit de l'appliquer en décorateur sur la vue concernée. Pour rappel, sa
vérification "est-ce un administrateur ?" est centralisée dans une seule
fonction (`est_administrateur`), à adapter avec ton camarade quand le vrai
rôle "Administrateur" du diagramme de cas d'utilisation sera implémenté
dans l'app `users`.

## 11. Nouveauté : bannière d'alerte publique automatique

La page de signalement et le tableau de bord affichent maintenant, tout en
haut, une bannière rouge avec des messages d'alerte **générés
automatiquement** -- sans qu'un humain les rédige -- dès que :

- une **campagne active** est détectée (3 signalements ou plus partagent le
  même numéro/lien),
- ou un **cluster émergent** a été confirmé par un modérateur dans l'admin
  (statut "Confirmé" + un nom renseigné dans `nom_valide`).

**Comment ça marche techniquement** (fichier `alertes.py`) : ce sont des
messages par **templates** (phrases pré-écrites remplies avec les vraies
données), pas de l'IA générative. Choix volontaire : gratuit, instantané,
sans dépendance externe, et surtout sans risque qu'un message dise un fait
faux -- contrairement à un texte généré par un modèle de langage.

Exemple de message généré automatiquement :
> ⚠️ 3 personne(s) ont signalé une arnaque sentimentale liée à ce numéro
> repéré sur WhatsApp : +228 90 12 34 56. Ne partage aucune information ni
> argent avec ce contact.

Rien à configurer : ça s'affiche automatiquement dès que les conditions
sont réunies, et disparaît tout seul si plus aucune campagne/cluster ne
correspond.

## 12. Nouveauté : page de statistiques temporelles + alertes de tendance

**Page de statistiques** (répond au besoin "voir les tendances, pas juste
des cas isolés") :

```
http://127.0.0.1:8000/signalements/statistiques/
```

Sélecteur en haut de page : **par jour / semaine / mois / année**. La page
affiche :
- un graphique (courbes, une par catégorie) montrant l'évolution du nombre
  de signalements sur la période choisie,
- un tableau récapitulatif avec les chiffres exacts et le pourcentage de
  chaque catégorie sur la période.

Les graphiques utilisent Chart.js (chargé depuis un CDN, aucune
installation nécessaire).

**Alertes de tendance automatiques** (répond au besoin "prévenir le public
avec un message qui nomme vraiment l'arnaque en cours", pas un message
générique) : la bannière d'alerte (voir section précédente) inclut
maintenant aussi des messages générés dès qu'**une catégorie précise**
augmente nettement sur les 7 derniers jours par rapport à la semaine
d'avant (au moins x1.5, et au moins 3 signalements pour éviter les fausses
alertes sur du bruit). Exemple réel généré lors du test :

> ⚠️ Vague de arnaque crypto en ce moment : 7 signalements ces 7 derniers
> jours contre 2 sur la période précédente (+250%). Sois particulièrement
> vigilant face à ce type d'arnaque.

Toujours par templates (pas d'IA générative), pour les mêmes raisons que
la section précédente : gratuit, fiable, sans risque d'erreur factuelle.

## 13. Nouveauté : page dédiée "Alertes actives"

Jusqu'ici, les alertes générées automatiquement n'apparaissaient qu'en
bannière, mélangées, sur les autres pages. Il y a maintenant une page à
part entière qui les regroupe et les distingue clairement par origine :

```
http://127.0.0.1:8000/signalements/alertes/
```

Trois sections, chacune expliquée :
- **Campagnes détectées** — même numéro/lien réutilisé dans 3+ signalements
- **Nouveaux types d'arnaque confirmés** — clusters émergents validés par
  un modérateur
- **Tendances en hausse** — une catégorie précise en nette augmentation
  sur les 7 derniers jours

Chaque section affiche soit les messages générés, soit un message "aucune
alerte de ce type pour l'instant" si rien n'est détecté. Un lien "Alertes"
a été ajouté dans la navigation de toutes les pages publiques.

## 14. Correction : doublons créés en actualisant la page (F5)

**Problème corrigé** : soumettre un signalement puis actualiser la page
(F5) renvoyait le même formulaire une deuxième fois au serveur, créant un
signalement en double avec un texte identique.

**Cause** : la vue `signaler_arnaque` renvoyait directement le résultat
après un POST, au lieu de rediriger. C'est un piège classique côté web —
tout navigateur qui actualise une page chargée via POST propose de
renvoyer les données du formulaire.

**Correction** : mise en place du pattern standard **Post/Redirect/Get**.
Après une soumission réussie, le serveur redirige maintenant vers une page
dédiée (`/signalements/signaler/resultat/<id>/`) qui affiche le résultat en
GET. Actualiser cette page ne resoumet plus rien -- testé en soumettant un
signalement puis en actualisant deux fois : le compteur en base reste
stable (24 → 24), alors qu'avant il aurait grimpé à chaque actualisation.

## 15. Nouveauté : pages pour l'Autorité compétente

Nouvel acteur couvert (celui de ton diagramme de cas d'utilisation), avec
un nouveau modèle `Dossier` et deux pages dédiées.

**Comment un dossier est créé** : depuis l'admin Django
(`/admin/signalements/signalement/`), sélectionne un ou plusieurs
signalements, puis choisis l'action **"Transmettre à l'autorité
compétente (créer un dossier)"** dans le menu déroulant en haut de la
liste. Ça crée un `Dossier` lié au signalement (un signalement ne peut
avoir qu'un seul dossier -- l'action ignore ceux qui en ont déjà un).

**Pages de l'Autorité compétente** (accès protégé -- même principe
provisoire que les autres pages réservées, voir `permissions.py`,
fonction `est_autorite_competente`, basée sur `is_staff` en attendant le
vrai rôle de l'app `users`) :

```
http://127.0.0.1:8000/signalements/dossiers/
http://127.0.0.1:8000/signalements/dossiers/<id>/
```

- **`/dossiers/`** — "Consulter les dossiers" : liste de tous les dossiers
  transmis, avec des cartes de comptage par statut (cliquables pour
  filtrer), comme le tableau de bord.
- **`/dossiers/<id>/`** — Affiche le signalement concerné (texte, entités
  détectées, score de risque), et deux formulaires séparés :
  - **"Confirmer ou infirmer la véracité"** (cases à cocher : confirmée /
    infirmée / non examinée)
  - **"Mettre à jour le statut du dossier"** (reçu → en cours d'examen →
    transmis à la police/justice → classé sans suite / résolu), avec un
    champ de commentaire libre.

Testé de bout en bout : création d'un dossier via l'action admin,
protection d'accès (redirection si non connecté), et les deux formulaires
de mise à jour (véracité + statut), avec vérification que les changements
sont bien persistés en base.

**Note pour la suite** : si tu ajoutes une vraie authentification propre à
cet acteur (différente de l'admin Django), n'oublie pas de mettre à jour
`est_autorite_competente` dans `permissions.py` -- c'est le seul endroit à
changer, comme pour `est_administrateur`.

## 16. Séparation stricte entre l'interface Utilisateur et l'interface Autorité compétente

Les deux interfaces sont maintenant complètement cloisonnées, dans les
deux sens :

- Un compte **Autorité compétente** ne peut PAS accéder aux pages
  publiques/utilisateur (signalement, tableau de bord, statistiques,
  alertes, clusters) -- il reçoit une erreur 403 s'il essaie.
- Un utilisateur normal (ou un visiteur anonyme) ne peut PAS accéder aux
  pages de l'Autorité compétente (`/dossiers/`) -- redirection vers la
  connexion, puis 403 s'il est connecté mais n'a pas le bon rôle.

**Comment la séparation est réalisée concrètement** (provisoire, en
attendant le système de rôles custom de l'app `users`) : deux groupes
Django distincts, **"Administrateurs"** et **"Autorite_competente"**. Un
compte peut appartenir à l'un, l'autre, les deux, ou aucun -- seuls les
comptes du bon groupe (ou un superutilisateur) passent la vérification.

**Pour créer ces groupes et un compte de test** (dans l'admin Django) :
1. `/admin/auth/group/add/` → crée un groupe nommé exactement
   `Autorite_competente`
2. Fais pareil pour `Administrateurs` si ce n'est pas déjà fait
3. Sur la fiche d'un utilisateur (`/admin/auth/user/<id>/change/`), coche
   "Statut équipe" et ajoute-le à **un seul** des deux groupes selon son
   rôle réel

Testé avec trois comptes différents (anonyme, compte Autorité pur, compte
utilisateur normal) : chacun voit exactement ce qu'il doit voir, rien de
plus.

**À adapter avec ton camarade** quand le vrai système de rôles sera prêt :
seules les fonctions `est_administrateur` et `est_autorite_competente`
dans `permissions.py` sont à modifier (voir les commentaires dans le
fichier) -- tout le reste (décorateurs, vues, templates) n'a pas besoin de
changer.

## 17. Bouton "Transmettre à l'autorité compétente" + bouton d'impression PDF

**Le bouton principal : transmettre les informations critiques, directement sur le site.**
Sur le tableau de bord (`/signalements/tableau-de-bord/`), chaque
signalement affiche un bouton **"Transmettre à l'autorité compétente"**
si tu es connecté avec un compte administrateur -- un visiteur normal ou
non connecté ne voit rien à cet endroit. Un clic crée le `Dossier`
correspondant : les informations critiques du signalement (texte,
catégorie, score de risque, entités détectées) deviennent immédiatement
visibles côté Autorité compétente, sur sa propre page
(`/signalements/dossiers/<id>/`). Une fois transmis, le bouton est
remplacé par un badge **"✓ Transmis à l'autorité"**.

Le même bouton existe aussi dans l'admin Django
(`/admin/signalements/signalement/<id>/change/`), pour ceux qui préfèrent
gérer ça depuis l'admin plutôt que le site public.

**Le bouton secondaire : impression PDF, uniquement côté Autorité.**
Sur sa propre page de détail d'un dossier
(`/signalements/dossiers/<id>/`), l'Autorité compétente dispose d'un
bouton **"Générer le dossier PDF"** si elle veut imprimer ou archiver le
dossier hors de la plateforme. Ce bouton n'est qu'une option de confort --
la transmission réelle des informations s'est déjà faite au moment du clic
sur le premier bouton, pas au moment de la génération du PDF.

**Dépendance à installer** (si pas déjà fait) :
```bash
pip install reportlab
```
Ajoute `reportlab` à ton `requirements.txt`.

## Remplacer le modèle par une version ré-entraînée

Si tu ré-entraînes le modèle plus tard (par exemple avec de vraies données
collectées via l'admin), remplace simplement :

```
signalements/ml/model_signalements.joblib
signalements/ml/vectorizer_signalements.joblib
```

par les nouveaux fichiers générés par ton script d'entraînement, et
redémarre le serveur (le rechargement se fait au démarrage, pas à chaud).

## Note sur la page elle-même

Le design est pensé pour rester lisible sur mobile (public visé : signalement
depuis un téléphone) et évite les couleurs/mises en page "template IA" trop
vues. Le score de risque est représenté par des barres façon "réception de
signal téléphonique" — un clin d'œil volontaire au canal (mobile/WhatsApp)
par lequel arrivent la plupart de ces arnaques. Tu peux librement adapter les
couleurs (variables CSS en haut du fichier `form.html`) à la charte
graphique du reste de ton site.
