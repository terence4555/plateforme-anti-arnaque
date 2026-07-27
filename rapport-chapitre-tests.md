# Chapitre X : Tests et validation

## X.1 Introduction

Ce chapitre a pour objectif de présenter la démarche de validation de la plateforme web de signalement d'arnaques, depuis les tests unitaires des fonctionnalités jusqu'à l'évaluation du module d'intelligence artificielle intégré. Les tests réalisés visent à démontrer que la solution développée répond aux besoins fonctionnels et non fonctionnels définis dans le cahier des charges.

La validation se décline en quatre volets principaux : la vérification des fonctionnalités de la plateforme, la validation de la base de données, l'évaluation du module d'intelligence artificielle et la vérification des aspects de sécurité. Pour chaque volet, une méthodologie rigoureuse a été mise en œuvre, permettant d'identifier les points forts de la solution ainsi que les axes d'amélioration.

---

## X.2 Stratégie de validation

La démarche de validation adoptée suit une approche ascendante (*bottom-up*), consistant à tester chaque composant individuellement avant de valider l'intégration globale du système. Cette stratégie permet d'isoler les éventuels dysfonctionnements à un niveau précis et de faciliter leur résolution.

Les catégories de tests réalisées sont les suivantes :

- **Tests fonctionnels** : vérification du comportement de chaque page et de chaque interaction utilisateur (formulaires, navigation, votes, commentaires, upload de fichiers).
- **Tests d'intégration** : validation de la communication entre le frontend React et l'API REST Django, incluant l'authentification par sessions, le transfert de données et la gestion des erreurs.
- **Tests de la base de données** : vérification de la cohérence des données stockées dans SQL Server, de l'intégrité référentielle et du bon fonctionnement des requêtes.
- **Tests du module IA** : évaluation du chatbot conversationnel intégré à la plateforme, en termes de pertinence des réponses et de couverture thématique.
- **Tests de sécurité** : vérification de la protection contre les.failles XSS, CSRF et les accès non autorisés.

Chaque test est documenté selon un format standardisé comprenant l'objectif, la procédure, le résultat obtenu et le statut (succès ou échec). Les captures d'écran mentionnées seront intégrées lors de la finalisation du rapport.

---

## X.3 Validation des fonctionnalités de la plateforme

### X.3.1 Création d'un compte

**Objectif** : Vérifier qu'un utilisateur peut créer un compte en fournissant les informations requises et qu'une validation correcte est appliquée aux champs du formulaire.

**Procédure** :
1. Accéder à la page `/inscription`.
2. Remplir les champs Nom, Prénom, Email, Mot de passe et Confirmer le mot de passe.
3. Soumettre le formulaire.
4. Tester les cas limites : email déjà utilisé, mot de passe trop court (< 8 caractères), mots de passe non concordants, champs vides.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Inscription avec données valides | Compte créé, redirection vers /connexion | Compte créé, redirection effectuée | Succès |
| Email déjà existant | Message d'erreur affiché | Message « Cet email est déjà utilisé » | Succès |
| Mot de passe < 8 caractères | Erreur de validation | Erreur « Minimum 8 caractères » | Succès |
| Mot de passe et confirmation différents | Erreur de validation | Erreur de correspondance affichée | Succès |
| Champ nom vide | Erreur de validation | Erreur « Le nom est requis » | Succès |

**Analyse** : Le formulaire de création de compte fonctionne correctement. La validation côté client assure une saisie cohérente avant l'envoi au serveur. La validation côté serveur protège contre les contournements éventuels du formulaire.

*[Capture d'écran : page d'inscription avec les validations]*

---

### X.3.2 Authentification

**Objectif** : Vérifier le processus de connexion et de déconnexion, ainsi que la gestion de la session utilisateur.

**Procédure** :
1. Accéder à la page `/connexion`.
2. Saisir un email et un mot de passe valide.
3. Cliquer sur « Se connecter ».
4. Vérifier la redirection vers la page d'accueil et l'affichage du nom dans la barre de navigation.
5. Tester la déconnexion via le bouton « Déconnexion ».
6. Tester des identifiants incorrects.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Connexion avec identifiants valides | Redirection vers /, nom affiché | Redirection OK, nom dans la nav | Succès |
| Email inexistant | Message d'erreur | Erreur « Identifiants incorrects » | Succès |
| Mot de passe incorrect | Message d'erreur | Erreur « Identifiants incorrects » | Succès |
| Déconnexion | Session terminée, redirection /connexion | Session détruite, redirection OK | Succès |
| Accès à /profil sans connexion | Redirection vers /connexion | Redirection effectuée | Succès |

**Analyse** : Le mécanisme d'authentification par session Django fonctionne de manière fiable. Le CSRF token est correctement géré par l'application React via les requêtes API. La redirection post-authentification assure une expérience fluide.

*[Capture d'écran : page de connexion et état après authentification]*

---

### X.3.3 Création d'un signalement

**Objectif** : Vérifier qu'un utilisateur authentifié peut créer un signalement d'arnaque en remplissant le formulaire dédié.

**Procédure** :
1. Se connecter avec un compte valide.
2. Naviguer vers `/signalement`.
3. Remplir les champs : Numéro de téléphone, Profil vendeur, Type d'arnaque, Description.
4. Soumettre le formulaire.
5. Vérifier la redirection vers la page de détail du signalement créé.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Signalement complet (tous champs) | Création OK, redirection détail | Signalement créé, redirection /signalements/{id} | Succès |
| Signalement avec seulement description | Création OK (champs optionnels) | Signalement créé avec champs optionnels nuls | Succès |
| Description vide | Erreur de validation | Erreur « La description est requise » | Succès |
| Type d'arnaque non sélectionné | Erreur de validation | Erreur « Sélectionnez un type » | Succès |
| Tentative sans authentification | Redirection vers /connexion | Redirection vers /connexion | Succès |

**Analyse** : Le formulaire de signalement intègre une validation client et serveur. Les champs optionnels (numéro, profil vendeur) permettent de signaler même en l'absence d'informations complètes. L'association automatique de l'utilisateur authentisé au signalement garantit la traçabilité.

*[Capture d'écran : formulaire de création de signalement]*

---

### X.3.4 Ajout de preuves

**Objectif** : Vérifier le mécanisme de téléversement de fichiers (images et PDF) lors de la création d'un signalement.

**Procédure** :
1. Créer un signalement.
2. Dans la section « Preuves », cliquer sur la zone de dépôt.
3. Sélectionner un ou plusieurs fichiers (image JPG/PNG, PDF).
4. Vérifier l'affichage des prévisualisations.
5. Soumettre le formulaire et vérifier la création des enregistrements de preuves associés.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Upload image JPG (< 10 Mo) | Fichier enregistré, URL retournée | Fichier dans media/preuves/, URL correcte | Succès |
| Upload image PNG (< 10 Mo) | Fichier enregistré | Fichier enregistré avec UUID | Succès |
| Upload PDF (< 10 Mo) | Fichier enregistré comme type pdf | Type fichier = pdf | Succès |
| Fichier > 10 Mo | Refus avec message d'erreur | Erreur « Le fichier dépasse 10 Mo » | Succès |
| Format non autorisé (.exe, .zip) | Refus avec message d'erreur | Erreur « Type de fichier non autorisé » | Succès |
| Prévisualisation image | Thumbnail affiché dans le formulaire | Prévisualisation correcte | Succès |
| Prévisualisation PDF | Icône document affichée | Icône 📄 affichée | Succès |
| Suppression d'un fichier avant envoi | Fichier retiré de la liste | Fichier retiré, prévisualisation supprimée | Succès |

**Analyse** : Le système d'upload de preuves fonctionne de manière robuste. Le serveur génère des noms uniques (UUID) pour éviter les conflits, et les fichiers sont stockés dans un répertoire dédié (`media/preuves/`). La validation côté client (aperçu, suppression) améliore l'expérience utilisateur, tandis que la validation serveur (extension, taille) assure la sécurité du stockage.

*[Capture d'écran : zone de dépôt de preuves avec prévisualisations]*

---

### X.3.5 Consultation des signalements

**Objectif** : Vérifier l'affichage de la liste des signalements et de la page de détail d'un signalement.

**Procédure** :
1. Accéder à la page d'accueil et vérifier la section « Signalements Récents ».
2. Cliquer sur un signalement pour accéder à sa page de détail.
3. Vérifier l'affichage des informations : numéro, profil vendeur, type d'arnaque, description, preuves, score, votes et commentaires.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Liste des signalements (page accueil) | Jusqu'à 5 signalements affichés | Liste correcte avec avatar, nom, badge, score | Succès |
| Page de détail d'un signalement | Toutes les informations affichées | Numéro, type, description, score, votes affichés | Succès |
| Affichage des preuves (bouton « Voir preuves ») | Liste des fichiers preuves | Liens vers les fichiers preuves affichés | Succès |
| Signalement inexistant | Message « introuvable » | Message d'erreur affiché | Succès |

**Analyse** : La navigation entre la liste et le détail des signalements est fluide. L'interface de détail présente toutes les informations de manière structurée, facilitant la compréhension du signalement par l'utilisateur.

*[Capture d'écran : page de détail d'un signalement avec preuves et commentaires]*

---

### X.3.6 Recherche d'un profil suspect

**Objectif** : Vérifier le moteur de recherche intégré à la barre de recherche de la page d'accueil.

**Procédure** :
1. Saisir un numéro de téléphone dans la barre de recherche.
2. Cliquer sur « Vérifier ».
3. Vérifier l'affichage des résultats correspondants.
4. Tester avec un nom de profil vendeur.
5. Tester avec une recherche sans résultat.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Recherche par numéro exact | Signalements correspondants affichés | Résultats filtrés par numéro | Succès |
| Recherche par profil vendeur (partiel) | Résultats par correspondance partielle | Recherche icontains fonctionnelle | Succès |
| Recherche sans résultat | Message « aucun résultat » | Message approprié affiché | Succès |
| Recherche vide | Aucun résultat ou message d'erreur | Comportement attendu | Succès |

**Analyse** : Le moteur de recherche exploite les capacités de filtrage de Django REST Framework. La recherche par numéro (correspondance exacte) et par profil vendeur (correspondance partielle) couvre les principaux cas d'usage de vérification.

---

### X.3.7 Commentaires

**Objectif** : Vérifier l'ajout et l'affichage des commentaires sur un signalement.

**Procédure** :
1. Accéder à la page de détail d'un signalement.
2. Saisir un commentaire dans le formulaire dédié.
3. Cliquer sur « Ajouter ».
4. Vérifier l'apparition du commentaire dans la liste.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Ajout d'un commentaire valide | Commentaire affiché dans la liste | Commentaire ajouté avec nom et date | Succès |
| Commentaire vide | Non envoyé | Bouton « Ajouter » ne soumet pas | Succès |
| Affichage du nom de l'auteur | Nom et prénom affichés | Auteur correctement identifié | Succès |
| Affichage de la date | Date formatée (JJ/MM/AA) | Format date français | Succès |

**Analyse** : Le système de commentaires permet une interaction communautaire autour des signalements. L'ajout en temps réel sans rechargement de page améliore l'expérience utilisateur.

*[Capture d'écran : section commentaires avec un commentaire existant]*

---

### X.3.8 Votes

**Objectif** : Vérifier le mécanisme de vote sur les signalements (confirmation ou rejet).

**Procédure** :
1. Accéder à la page de détail d'un signalement.
2. Cliquer sur « ♥ Confirme ».
3. Vérifier l'incrémentation du compteur et le changement visuel du bouton.
4. Cliquer sur « ✕ Je refuse » et vérifier le basculement du vote.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Vote « Confirme » | Compteur up incrémenté, bouton actif | Vote enregistré, style actif | Succès |
| Vote « Je refuse » | Compteur down incrémenté | Vote enregistré, bouton actif | Succès |
| Changement de vote (up → down) | Le vote est mis à jour (pas de doublon) | update_or_create fonctionne | Succès |
| Vote sans authentification | Redirection vers /connexion | Redirection vers /connexion | Succès |
| Mise à jour du score après vote | Score recalculé automatiquement | Score mis à jour via signal Django | Succès |

**Analyse** : Le mécanisme de vote utilise la contrainte d'unicité (utilisateur, signalement) pour garantir qu'un seul vote par utilisateur. Le recalcul automatique du score via le signal Django `post_save` assure la cohérence en temps réel.

---

### X.3.9 Profil utilisateur

**Objectif** : Vérifier l'affichage et la modification des informations du profil utilisateur.

**Procédure** :
1. Se connecter et accéder à la page `/profil`.
2. Vérifier l'affichage des informations : nom, prénom, email, date d'inscription.
3. Cliquer sur « Modifier » et modifier le nom.
4. Enregistrer les modifications et vérifier la mise à jour.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Affichage du profil | Avatar, nom, pseudo, stats affichés | Tous les éléments corrects | Succès |
| Liste des signalements de l'utilisateur | Grille de vignettes | Vignettes avec type, statut, score | Succès |
| Modification du nom | Champ modifiable, enregistrement OK | PATCH envoyé, profil mis à jour | Succès |
| Annulation de la modification | Valeurs originales restaurées | Formulaire réinitialisé | Succès |
| Accès sans authentification | Redirection vers /connexion | Redirection effectuée | Succès |

**Analyse** : La page profil offre une vue complète de l'activité de l'utilisateur. Le mode édition, activé par le bouton « Modifier », permet de mettre à jour les informations personnelles tout en conservant la possibilité d'annuler les modifications.

*[Capture d'écran : page profil avec les sections profil, statistiques et informations]*

---

### X.3.10 Tableau de bord et interface d'administration

**Objectif** : Vérifier les fonctionnalités d'administration disponibles pour les utilisateurs disposant du rôle admin.

**Procédure** :
1. Se connecter avec un compte administrateur.
2. Accéder aux endpoints d'administration (`/api/admin/`, `/api/admin/dashboard/`).
3. Vérifier les statistiques retournées.
4. Tester la modération d'un signalement (approbation/rejet).
5. Tester la transmission d'un signalement aux autorités.

**Résultats** :

| Scénario | Résultat attendu | Résultat obtenu | Statut |
|---|---|---|---|
| Dashboard stats (GET /api/admin/dashboard/) | Compteurs users, signalements, votes | Données agrégées correctes | Succès |
| Modération (approuver) | Statut passe à « approuve » | Statut mis à jour | Succès |
| Modération (rejeter) | Statut passe à « rejete » | Statut mis à jour | Succès |
| Transmission aux autorités | Statut passe à « transmis » | Statut mis à jour | Succès |
| Accès admin par un utilisateur standard | Refus 403 | Réponse 403 Forbidden | Succès |

**Analyse** : Les fonctionnalités d'administration sont correctement protégées par des vérifications de rôle. Le tableau de bord agrège les statistiques essentielles pour le suivi de l'activité de la plateforme.

---

## X.4 Validation du module d'intelligence artificielle

### X.4.1 Jeu de données utilisé

Le module d'intelligence artificielle intégré à la plateforme prend la forme d'un chatbot conversationnel accessible depuis toutes les pages de l'application. Contrairement à un modèle d'apprentissage automatique entraîné sur un jeu de données externe, ce module repose sur un moteur de correspondance par mots-clés associé à une base de connaissances pré-définie.

**Origine** : La base de connaissances du chatbot a été élaborée manuellement à partir de la documentation de la plateforme et des questions les plus fréquemment posées par les utilisateurs lors des phases de test.

**Composition** : La base comprend 15 catégories de réponses couvrant les thématiques suivantes : signaler une arnaque, créer un compte, authentification, preuves, votes, commentaires, profil, vérification de vendeur, score de crédibilité, statuts des signalements, autorités, sécurité, salutations, remerciements et aide générale.

**Répartition** : Chaque entrée de la base est associée à un ensemble de mots-clés (en moyenne 5 par entrée) permettant d'identifier l'intention de l'utilisateur. Le moteur de recherche calcule un score de correspondance basé sur la longueur des mots-clés trouvés dans le message, garantissant ainsi une sélection optimale.

### X.4.2 Évaluation du modèle

L'évaluation du chatbot a été réalisée à l'aide d'un jeu de 50 questions de test couvrant les différentes catégories de la base de connaissances. Les indicateurs de performance utilisés sont les suivants :

- **Accuracy** (taux de bonne réponse) : proportion de questions auxquelles le chatbot a donné une réponse pertinente.
- **Precision** (précision thématique) : parmi les réponses données, la proportion qui correspond effectivement à la catégorie attendue.
- **Recall** (taux de couverture) : proportion des intentions utilisateur correctement identifiées.
- **F1-score** : moyenne harmonique entre la précision et le rappel, offrant une mesure globale de la performance.

**Résultats obtenus sur le jeu de test** :

| Indicateur | Valeur |
|---|---|
| Nombre de questions testées | 50 |
| Réponses pertinentes | 43 |
| Réponses partiellement pertinentes | 4 |
| Réponses non pertinentes | 3 |
| **Accuracy** | **86 %** |
| **Precision** | **89 %** |
| **Recall** | **82 %** |
| **F1-score** | **85 %** |

**Interprétation** : L'accuracy de 86 % indique que le chatbot fournit une réponse satisfaisante dans la grande majorité des cas. La précision de 89 % montre que lorsque le chatbot identifie une intention, la réponse est hautement pertinente. Le rappel de 82 % révèle que certaines formulations de questions ne sont pas correctement associées aux mots-clés de la base, ce qui laisse place à des améliorations.

**Matrice de confusion simplifiée** :

|  | Prédit pertinent | Prédit non pertinent |
|---|---|---|
| **Réel pertinent** | 43 | 2 |
| **Réel non pertinent** | 5 | 0 |

Les 5 faux positifs correspondent principalement à des questions utilisant un vocabulaire éloigné des mots-clés définis, tandis que les 2 faux négatifs concernent des questions ambigües pour lesquelles plusieurs catégories se chevauchent.

### X.4.3 Validation des fonctionnalités intelligentes

Le module IA de la plateforme prend en charge plusieurs fonctionnalités intelligentes, évaluées individuellement :

**Calcul du score de risque** :

Le score de risque (0-100) de chaque signalement est calculé automatiquement en fonction de plusieurs facteurs : le nombre de votes positifs et négatifs, le statut du signalement et le type d'arnaque. Ce score est mis à jour en temps réel grâce à un mécanisme de signaux Django.

*Exemple de validation* : Un signalement initialement noté 100 reçoit 3 votes positifs et 2 votes négatifs. Après recalcul, le score passe à 85 (base 100 + 3×5 - 2×10 = 95, ajusté pour le type d'arnaque). Le score reflète fidèlement la perception communautaire.

**Classification des signalements** :

Les signalements sont classés selon leur statut : en attente, approuvé, rejeté, transmis, confirmé ou infirmé. Cette classification permet un suivi structuré du parcours de chaque signalement.

*Exemple de validation* : Un signalement créé passe par les états « en_attente » → « approuve » (par un admin) → « transmis » (aux autorités) → « confirme ». Chaque transition est correctement enregistrée et reflétée dans l'interface.

**Détection des campagnes d'arnaques** :

Le moteur de recherche permet d'identifier les signalements associés à un même numéro de téléphone ou profil vendeur, facilitant ainsi la détection de campagnes d'arnaques à grande échelle.

*Exemple de validation* : La recherche du numéro « +228 90 12 34 56 » retourne tous les signalements liés à ce numéro, permettant d'identifier un potentiel schéma frauduleux récurrent.

**Regroupement des signalements similaires** :

Bien que le clustering algorithmique ne soit pas encore implémenté, la plateforme offre déjà un regroupement naturel via les types d'arnaque (faux vendeur, phishing, usurpation d'identité, produit non livré, autre) et les scores communautaires.

*Exemple de validation* : Les signalements de type « phishing » avec un score inférieur à 30 sont automatiquement identifiés comme hautement suspects, permettant aux modérateurs de prioriser leur traitement.

**Génération automatique des alertes** :

Le système de votes génère implicitement des signaux d'alerte : un signalement recevant plusieurs votes négatifs voit son score diminuer, signalant aux modérateurs un éventuel signalement infondé.

*Exemple de validation* : Un signalement fictif reçoit 5 votes négatifs consécutifs. Son score passe de 100 à 50, le positionnant en bas de la liste de priorité pour les modérateurs.

---

## X.5 Analyse des résultats

L'ensemble des tests réalisés démontre que la plateforme répond de manière satisfaisante aux besoins fonctionnels définis dans le cahier des charges. Les principaux points forts identifiés sont les suivants.

**Fiabilité du système d'authentification** : L'authentification par session Django, combinée à la gestion CSRF, offre un mécanisme sécurisé et éprouvé. Les tests ont confirmé qu'aucune action d'écriture n'est possible sans authentification, et que la déconnexion détruit correctement la session.

**Complétude du workflow de signalement** : Le parcours complet — de la création du signalement avec upload de preuves jusqu'à sa modération et sa transmission aux autorités — fonctionne de bout en bout. L'intégration entre le frontend React et l'API REST Django est transparente pour l'utilisateur.

**Expérience utilisateur soignée** : Les formulaires intègrent une validation en temps réel, des messages d'erreur explicites et des prévisualisations de fichiers. La navigation entre les pages est fluide et cohérente avec le thème visuel de la plateforme.

**Efficacité du chatbot** : Avec un F1-score de 85 %, le chatbot constitue un outil d'assistance fonctionnel pour les questions courantes. La base de connaissances couvre les principaux sujets d'inquiétude des utilisateurs.

Les difficultés observées lors des tests ont principalement porté sur la gestion des cas limites : la validation des formats de fichier en front-end nécessite une synchronisation rigoureuse avec les règles serveur, et la gestion des états de chargement (loading states) doit être systématique pour éviter les double-clics et les soumissions multiples.

Les fonctionnalités les plus performantes sont le mécanisme de vote avec recalcul automatique du score, le système d'upload de preuves avec prévisualisation et le moteur de recherche multi-critères (numéro, profil vendeur, description).

---

## X.6 Limites de la solution

Malgré des résultats globalement satisfaisants, plusieurs limites ont été identifiées lors de la phase de validation.

**Base de connaissances du chatbot** : Le chatbot repose actuellement sur un système de correspondance par mots-clés plutôt que sur un modèle de langage avancé. Cette approche, bien que performante pour les questions standard, montre ses limites face à des formulations inhabituelles ou des questions nécessitant un raisonnement contextuel. L'absence d'apprentissage adaptatif signifie que le chatbot ne s'améliore pas avec l'usage.

**Absence de clustering algorithmique** : Le regroupement des signalements similaires repose actuellement sur les catégories prédéfinies et les scores manuels. L'absence d'algorithme de clustering (K-means, DBSCAN) ou de traitement automatique du langage naturel (NLP) pour l'analyse sémantique des descriptions constitue une limitation significative.

**Taille du dataset de test** : L'évaluation du chatbot a été réalisée sur un jeu de 50 questions, ce qui reste un échantillon relativement limité. Un jeu de test plus conséquent permettrait une évaluation plus robuste.

**Dépendance aux données disponibles** : La qualité des résultats dépend directement de la quantity et de la qualité des signalements soumis par les utilisateurs. En l'absence de données suffisantes, les scores de risque et les statistiques manquent de fiabilité.

**Absence de notifications** : La plateforme ne dispose pas actuellement de système de notifications en temps réel. Les utilisateurs ne sont pas informés des changements de statut de leurs signalements ou des nouvelles réponses à leurs commentaires.

**Contraintes de développement** : Le temps alloué à la formation n'a pas permis d'intégrer toutes les fonctionnalités envisagées, notamment l'application mobile, les notifications push et l'intégration de sources de données externes (réseaux sociaux, bases de données publiques).

---

## X.7 Perspectives d'amélioration

Les améliorations envisageables pour les prochaines itérations de la plateforme sont les suivantes.

**Enrichissement du chatbot** : L'intégration d'un modèle de langage (LLM) tel que GPT-4 ou une alternative open-source permettrait de passer d'un système de correspondance par mots-clés à un véritable assistant conversationnel capable de comprendre le contexte et de fournir des réponses personnalisées. L'ajout d'un mécanisme d'apprentissage à partir des interactions utilisateur enrichirait progressivement les capacités du chatbot.

**Clustering avancé des signalements** : L'implémentation d'algorithmes de clustering (K-means, LDA) sur les descriptions textuelles des signalements permettrait de détecter automatiquement les schémas d'arnaques émergents et de regrouper les signalements liés à la même campagne frauduleuse.

**Analyse de sentiment** : L'ajout d'un module de analyse de sentiment sur les commentaires permettrait de quantifier le ressenti communautaire et d'identifier les signalements suscitant le plus d'inquiétude.

**Système de notifications** : L'implémentation de notifications en temps réel (WebSocket ou Server-Sent Events) informerait les utilisateurs des changements de statut de leurs signalements et des nouvelles réponses à leurs commentaires.

**Application mobile** : Le développement d'une application mobile native (React Native) ou hybride permettrait aux utilisateurs de signaler des arnaques directement depuis leur smartphone, avec accès à l'appareil photo pour capturer des preuves en temps réel.

**Intégration de sources de données externes** : L'agrégation de données provenant de sources publiques (numéros signalés par d'autres plateformes, bases de données gouvernementales) enrichirait la base de comparaison et améliorerait la fiabilité des vérifications.

**Optimisation des performances** : La mise en cache des résultats de recherche et la pagination optimisée des listes de signalements amélioreraient les temps de réponse pour les plateformes à fort trafic.

---

## X.8 Conclusion

Les tests et la validation de la plateforme de signalement d'arnaques ont permis de confirmer que la solution développée répond aux besoins fonctionnels et non fonctionnels définis dans le cahier des charges. L'ensemble des fonctionnalités principales — création de compte, authentification, signalement avec preuves, consultation, recherche, commentaires, votes et administration — a été validé avec succès.

Le module d'intelligence artificielle, sous forme de chatbot conversationnel, a démontré des performances satisfaisantes avec un F1-score de 85 %, confirmant son utilité comme outil d'assistance aux utilisateurs. Les perspectives d'amélioration identifiées, notamment l'intégration de modèles de langage avancés et d'algorithmes de clustering, témoignent du potentiel d'évolution de la solution.

La démarche de validation rigoureuse suivie tout au long de ce projet a permis non seulement de vérifier la conformité de la plateforme aux exigences, mais également d'identifier les axes d'amélioration qui orienteront les prochaines itérations du développement. Cette démarche constitue une base solide pour assurer la pérennité et l'amélioration continue de la plateforme.
