#!/usr/bin/env python3
"""
i18n.py - Module d'internationalisation pour LocalisationToolKit

Ce module fournit le support gettext pour traduire l'interface utilisateur.
La langue source est le français, les traductions sont dans locale/<lang>/LC_MESSAGES/

Usage:
    from common.i18n import _, set_language, get_current_language

    # Dans le code:
    print(_("Bonjour le monde"))

    # Changer de langue:
    set_language("en")

Structure des fichiers de traduction:
    locale/
    ├── messages.pot          # Template (chaînes françaises extraites)
    ├── en/
    │   └── LC_MESSAGES/
    │       ├── messages.po   # Traductions anglaises (éditable)
    │       └── messages.mo   # Fichier compilé (utilisé par gettext)
    └── es/
        └── LC_MESSAGES/
            ├── messages.po
            └── messages.mo

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-02-03
"""

import gettext
import os
import locale
from pathlib import Path
from typing import Optional, Callable

# =============================================================================
# CONFIGURATION
# =============================================================================

# Domaine gettext (nom des fichiers .po/.mo sans extension)
DOMAIN = "messages"

# Langue de l'interface utilisateur
# - "fr" = Français (langue source, pas de traduction)
# - "en" = English
# - "auto" = Détection automatique selon le système
UI_LANGUAGE = "fr"

# Langues supportées (à mettre à jour quand on ajoute des traductions)
SUPPORTED_LANGUAGES = ["fr", "en"]

# Langue de fallback si UI_LANGUAGE="auto" et détection échoue
FALLBACK_LANGUAGE = "fr"

# =============================================================================
# VARIABLES GLOBALES
# =============================================================================

# Répertoire racine du toolkit (parent de common/)
_toolkit_root: Optional[Path] = None

# Répertoire des traductions
_locale_dir: Optional[Path] = None

# Langue actuelle (initialisée plus tard)
_current_language: str = "fr"

# Fonction de traduction active
_translator: Callable[[str], str] = lambda s: s  # Par défaut: pas de traduction


# =============================================================================
# INITIALISATION
# =============================================================================

def _get_toolkit_root() -> Path:
    """Retourne le répertoire racine du toolkit."""
    global _toolkit_root
    if _toolkit_root is None:
        # Ce fichier est dans common/, donc parent = racine
        _toolkit_root = Path(__file__).parent.parent.resolve()
    return _toolkit_root


def _get_locale_dir() -> Path:
    """Retourne le répertoire des traductions."""
    global _locale_dir
    if _locale_dir is None:
        _locale_dir = _get_toolkit_root() / "locale"
    return _locale_dir


def _detect_system_language() -> str:
    """Détecte la langue du système."""
    try:
        # Essayer de récupérer la langue du système
        lang_code = locale.getdefaultlocale()[0]
        if lang_code:
            # Extraire le code langue (ex: "fr_FR" -> "fr")
            lang = lang_code.split("_")[0].lower()
            if lang in SUPPORTED_LANGUAGES:
                return lang
    except Exception:
        pass
    return FALLBACK_LANGUAGE


def _get_initial_language() -> str:
    """Détermine la langue à utiliser au démarrage.

    Utilise UI_LANGUAGE de la configuration:
    - "auto" : détection automatique du système
    - "fr", "en", etc. : langue fixe
    """
    if UI_LANGUAGE == "auto":
        return _detect_system_language()
    elif UI_LANGUAGE in SUPPORTED_LANGUAGES:
        return UI_LANGUAGE
    else:
        return FALLBACK_LANGUAGE


def _load_translator(language: str) -> Callable[[str], str]:
    """Charge le traducteur pour une langue donnée.

    Args:
        language: Code langue (ex: "en", "fr", "es")

    Returns:
        Fonction de traduction
    """
    locale_dir = _get_locale_dir()

    # Si c'est la langue source (français), pas de traduction
    if language == "fr":
        return lambda s: s

    # Vérifier si la traduction existe
    mo_file = locale_dir / language / "LC_MESSAGES" / f"{DOMAIN}.mo"

    if not mo_file.exists():
        # Pas de fichier .mo, essayer avec le .po (moins performant)
        po_file = locale_dir / language / "LC_MESSAGES" / f"{DOMAIN}.po"
        if not po_file.exists():
            # Aucune traduction disponible
            return lambda s: s

    try:
        # Charger les traductions
        translation = gettext.translation(
            DOMAIN,
            localedir=str(locale_dir),
            languages=[language],
            fallback=True
        )
        return translation.gettext
    except Exception:
        # En cas d'erreur, retourner la fonction identité
        return lambda s: s


def init(language: Optional[str] = None) -> str:
    """Initialise le système i18n.

    Args:
        language: Code langue à utiliser (None = utilise UI_LANGUAGE de la config)

    Returns:
        Code de la langue initialisée
    """
    global _current_language, _translator

    if language is None:
        language = _get_initial_language()

    # Normaliser le code langue
    language = language.lower().split("_")[0]

    # Vérifier si la langue est supportée
    if language not in SUPPORTED_LANGUAGES:
        language = FALLBACK_LANGUAGE

    _current_language = language
    _translator = _load_translator(language)

    return _current_language


def set_language(language: str) -> bool:
    """Change la langue active.

    Args:
        language: Code langue (ex: "en", "fr")

    Returns:
        True si la langue a été changée, False sinon
    """
    global _current_language, _translator

    # Normaliser
    language = language.lower().split("_")[0]

    if language not in SUPPORTED_LANGUAGES:
        return False

    if language == _current_language:
        return True

    _current_language = language
    _translator = _load_translator(language)
    return True


def get_current_language() -> str:
    """Retourne le code de la langue actuelle."""
    return _current_language


def get_supported_languages() -> list:
    """Retourne la liste des langues supportées."""
    return SUPPORTED_LANGUAGES.copy()


# =============================================================================
# FONCTION DE TRADUCTION PRINCIPALE
# =============================================================================

def _(message: str) -> str:
    """Traduit un message dans la langue actuelle.

    C'est la fonction principale à utiliser dans le code:
        print(_("Bonjour"))

    Args:
        message: Message en français (langue source)

    Returns:
        Message traduit (ou original si pas de traduction)
    """
    return _translator(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Traduction avec support du pluriel.

    Usage:
        print(ngettext("{n} fichier", "{n} fichiers", count).format(n=count))

    Args:
        singular: Forme singulière
        plural: Forme plurielle
        n: Nombre pour déterminer la forme

    Returns:
        Message traduit avec la forme appropriée
    """
    # Pour l'instant, implémentation simple basée sur n
    # TODO: Utiliser gettext.ngettext quand les traductions seront prêtes
    if n == 1:
        return _translator(singular)
    else:
        return _translator(plural)


# =============================================================================
# INITIALISATION AUTOMATIQUE
# =============================================================================

# Initialiser avec la langue du système au chargement du module
init()


# =============================================================================
# UTILITAIRES POUR LE DÉVELOPPEMENT
# =============================================================================

def get_locale_dir() -> Path:
    """Retourne le chemin du répertoire locale/ (pour les scripts)."""
    return _get_locale_dir()


def get_toolkit_root() -> Path:
    """Retourne le chemin racine du toolkit (pour les scripts)."""
    return _get_toolkit_root()
