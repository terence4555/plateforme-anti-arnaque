# -*- coding: utf-8 -*-
"""
permissions.py
----------------
Point UNIQUE de vérification des rôles pour toute l'app signalements :
Administrateur vs Autorité compétente. Ce sont deux acteurs DISTINCTS dans
le diagramme de cas d'utilisation -- l'un ne doit pas pouvoir accéder aux
pages réservées à l'autre.

ÉTAT ACTUEL (provisoire) :
Le système d'utilisateurs custom (app `users`, avec les rôles du diagramme
de cas d'utilisation) n'est pas encore implémenté par l'équipe. En
attendant, la séparation utilise deux GROUPES Django distincts
("Administrateurs" et "Autorite_competente") plutôt qu'un simple is_staff
partagé -- ça permet une vraie séparation testable dès maintenant, avec
deux comptes différents, sans dépendre du travail en cours sur `users`.

Un compte superutilisateur (is_superuser) garde accès aux deux, ce qui est
normal pour un compte de développement/administration technique.

COMMENT CRÉER LES DEUX GROUPES (à faire une fois, dans l'admin Django) :
1. Va sur /admin/auth/group/add/
2. Crée un groupe nommé exactement "Administrateurs"
3. Crée un second groupe nommé exactement "Autorite_competente"
4. Pour chaque utilisateur, va sur /admin/auth/user/<id>/change/, coche
   "Statut équipe" (is_staff) et ajoute-le à UN SEUL des deux groupes,
   selon son rôle réel.

QUAND LE MODÈLE UTILISATEUR CUSTOM SERA PRÊT :
Il suffira de modifier UNIQUEMENT les deux fonctions ci-dessous pour
qu'elles vérifient le vrai rôle (ex: request.user.role == "administrateur"
), par exemple :

    def est_administrateur(user):
        return user.is_authenticated and user.role == "administrateur"

    def est_autorite_competente(user):
        return user.is_authenticated and user.role == "autorite_competente"

Aucune autre modification n'est nécessaire ailleurs dans le code -- toutes
les vues protégées appellent ces fonctions via les décorateurs
`admin_requis` / `autorite_requise`.
"""

from functools import wraps
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

GROUPE_ADMINISTRATEURS = "Administrateurs"
GROUPE_AUTORITE_COMPETENTE = "Autorite_competente"


def est_administrateur(user):
    """
    Retourne True si l'utilisateur a le droit de voir les pages réservées
    aux administrateurs (clusters émergents, etc.).

    -- PROVISOIRE : basé sur l'appartenance au groupe Django
    "Administrateurs" (ou is_superuser), en attendant le vrai rôle
    "Administrateur" du modèle utilisateur custom. Un membre du groupe
    "Autorite_competente" qui n'est PAS aussi dans "Administrateurs" n'a
    PAS accès à ces pages -- séparation stricte entre les deux rôles. --
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=GROUPE_ADMINISTRATEURS).exists()


def est_autorite_competente(user):
    """
    Retourne True si l'utilisateur a le droit de voir les pages réservées à
    l'Autorité compétente (dossiers transmis, mise à jour de statut,
    confirmation/infirmation de véracité).

    -- PROVISOIRE : basé sur l'appartenance au groupe Django
    "Autorite_competente" (ou is_superuser). Un membre du groupe
    "Administrateurs" qui n'est PAS aussi dans "Autorite_competente" n'a
    PAS accès à ces pages -- séparation stricte entre les deux rôles. --
    """
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=GROUPE_AUTORITE_COMPETENTE).exists()


def interface_utilisateur_requise(view_func):
    """
    Décorateur à appliquer sur les pages "publiques" côté Utilisateur
    (signalement, tableau de bord, statistiques, alertes, clusters).

    Un visiteur anonyme ou un utilisateur normal accède normalement. En
    revanche, un compte identifié comme Autorité compétente (et qui n'est
    pas administrateur ni superutilisateur) est bloqué : les deux
    interfaces sont strictement séparées, un acteur ne doit voir que son
    propre espace.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and not user.is_superuser:
            si_autorite = est_autorite_competente(user)
            si_admin = est_administrateur(user)
            if si_autorite and not si_admin:
                raise PermissionDenied(
                    "Cette page ne fait pas partie de l'espace Autorité compétente. "
                    "Rends-toi sur /signalements/dossiers/."
                )
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_requis(view_func):
    """
    Décorateur à appliquer sur toute vue réservée aux administrateurs.
    - Utilisateur non connecté -> redirigé vers la page de connexion.
    - Utilisateur connecté mais avec le mauvais rôle (ex: Autorité
      compétente) -> erreur 403 explicite, pas une redirection vers une
      connexion à laquelle il est déjà identifié.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not est_administrateur(request.user):
            raise PermissionDenied("Cette page est réservée aux administrateurs.")
        return view_func(request, *args, **kwargs)
    return wrapper


def autorite_requise(view_func):
    """
    Décorateur à appliquer sur toute vue réservée à l'Autorité compétente.
    - Utilisateur non connecté -> redirigé vers la page de connexion.
    - Utilisateur connecté mais avec le mauvais rôle (ex: Administrateur)
      -> erreur 403 explicite, pas une redirection vers une connexion à
      laquelle il est déjà identifié.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not est_autorite_competente(request.user):
            raise PermissionDenied("Cette page est réservée à l'autorité compétente.")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_ou_autorite_requis(view_func):
    """
    Décorateur pour les actions légitimement partagées par les deux rôles
    (ex : générer le PDF d'un dossier -- l'administrateur peut vouloir le
    transmettre par un autre canal, l'autorité peut vouloir l'archiver).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not (est_administrateur(request.user) or est_autorite_competente(request.user)):
            raise PermissionDenied("Cette action est réservée aux administrateurs et à l'autorité compétente.")
        return view_func(request, *args, **kwargs)
    return wrapper
