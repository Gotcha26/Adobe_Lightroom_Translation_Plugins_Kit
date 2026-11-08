#!/usr/bin/env python3
"""
Nom du fichier : i18n.py

Dépendances : Aucune

Description :
Module d'internationalisation (i18n) pour le toolkit. Fournit le support gettext pour traduire
l'interface utilisateur. La langue source est le français. Les traductions sont stockées dans
locale/<lang>/LC_MESSAGES/ et chargées dynamiquement selon la langue sélectionnée.

Usage CLI :
    Non pourvu

Date : 2026-11-08
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import gettext
import os
import locale
import sys
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
UI_LANGUAGE = "auto"

# Langues supportées (à mettre à jour quand on ajoute des traductions)
SUPPORTED_LANGUAGES = ["fr", "en"]

# Langue de fallback si UI_LANGUAGE="auto" et détection échoue
FALLBACK_LANGUAGE = "en"

# =============================================================================
# VARIABLES GLOBALES
# =============================================================================

# Répertoire racine du toolkit (parent de common/)
_toolkit_root: Optional[Path] = None

# Répertoire des traductions
_locale_dir: Optional[Path] = None

# Langue actuelle (initialisée plus tard)
_current_language: str = "fr"

# Catalogue gettext chargé (None pour la langue source : pas de traduction)
_translation: Optional[gettext.NullTranslations] = None

# Fonction de traduction active
_translator: Callable[[str], str] = lambda s: s  # Par défaut: pas de traduction


# =============================================================================
# INITIALISATION
# =============================================================================

def _get_toolkit_root() -> Path:
    """Retourne le répertoire racine du toolkit."""
    global _toolkit_root
    if _toolkit_root is None:
        # Ce fichier est dans core/, donc parent = racine
        _toolkit_root = Path(__file__).parent.parent.resolve()
    return _toolkit_root


def _get_locale_dir() -> Path:
    """Retourne le répertoire des traductions."""
    global _locale_dir
    if _locale_dir is None:
        _locale_dir = _get_toolkit_root() / "locale"
    return _locale_dir


def _detect_system_language() -> str:
    """Détecte la langue du système.

    Ordre de priorité :
        1. Variable d'environnement TOOLKIT_LANG (ex: "de", "en_US", "fr")
        2. Variables LC_ALL, LC_MESSAGES, LANG, LANGUAGE
        3. Locale système via locale.getlocale() (mapping Windows French*/English*)
        4. FALLBACK_LANGUAGE
    """
    # Override via variable d'environnement (utile pour tester)
    env_lang = os.environ.get("TOOLKIT_LANG", "").strip()
    if env_lang:
        lang = env_lang.split("_")[0].lower()
        if lang in SUPPORTED_LANGUAGES:
            return lang
        # Langue valide mais non supportée → fallback (ne pas ignorer silencieusement)
        return FALLBACK_LANGUAGE

    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        for part in os.environ.get(var, "").split(":"):
            lang = _language_from_code(part)
            if lang:
                return lang

    lang = _language_from_code(_get_locale_code())
    if lang:
        return lang
    return FALLBACK_LANGUAGE


def _language_from_code(code: Optional[str]) -> Optional[str]:
    """Convertit un code de locale (fr_FR.UTF-8, French_France, en...) en langue supportée."""
    if not code:
        return None
    code = code.strip().lower()
    if code.startswith("french"):
        return "fr"
    if code.startswith("english"):
        return "en"
    lang = code[:2]
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return None


def _get_locale_code() -> Optional[str]:
    """Retourne le code de locale courant via locale.getlocale() (None si indisponible)."""
    try:
        return locale.getlocale()[0]
    except Exception:
        return None


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


def _load_translation(language: str) -> Optional[gettext.NullTranslations]:
    """Charge le catalogue gettext d'une langue donnée.

    Args:
        language: Code langue (ex: "en", "fr", "es")

    Returns:
        Objet de traduction gettext (NullTranslations si aucun .mo n'est trouvé),
        ou None pour la langue source (français) ou en cas d'erreur de lecture.
    """
    # Si c'est la langue source (français), pas de traduction
    if language == "fr":
        return None

    try:
        return gettext.translation(
            DOMAIN,
            localedir=str(_get_locale_dir()),
            languages=[language],
            fallback=True
        )
    except Exception as exc:
        # Catalogue illisible : on continue en langue source, mais on le signale
        print("[i18n] {lang}: {error}".format(lang=language, error=exc), file=sys.stderr)
        return None


def _activate(language: str) -> None:
    """Active une langue : charge son catalogue et met à jour le traducteur."""
    global _current_language, _translation, _translator
    _current_language = language
    _translation = _load_translation(language)
    _translator = _translation.gettext if _translation is not None else (lambda s: s)


def init(language: Optional[str] = None) -> str:
    """Initialise le système i18n.

    Args:
        language: Code langue à utiliser (None = utilise UI_LANGUAGE de la config)

    Returns:
        Code de la langue initialisée
    """
    if language is None:
        language = _get_initial_language()

    # Normaliser le code langue
    language = language.lower().split("_")[0]

    # Vérifier si la langue est supportée
    if language not in SUPPORTED_LANGUAGES:
        language = FALLBACK_LANGUAGE

    _activate(language)

    return _current_language


def set_language(language: str) -> bool:
    """Change la langue active.

    Args:
        language: Code langue (ex: "en", "fr")

    Returns:
        True si la langue a été changée, False sinon
    """
    # Normaliser
    language = language.lower().split("_")[0]

    if language not in SUPPORTED_LANGUAGES:
        return False

    if language == _current_language:
        return True

    _activate(language)
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

    Usage (les deux formes sont des littéraux, sans _() autour) :
        print(ngettext("{n} fichier", "{n} fichiers", count).format(n=count))

    Quand un catalogue est chargé, la forme est choisie par
    gettext.GNUTranslations.ngettext selon l'en-tête Plural-Forms du .po
    (entrée msgid/msgid_plural/msgstr[N]) ; sans entrée plurielle dans le
    catalogue, gettext applique la règle anglaise (n == 1 → singulier).
    Pour la langue source (français, pas de catalogue) : règle n == 1.

    Args:
        singular: Forme singulière (français)
        plural: Forme plurielle (français)
        n: Nombre pour déterminer la forme

    Returns:
        Message traduit avec la forme appropriée
    """
    if _translation is not None:
        return _translation.ngettext(singular, plural, n)
    return singular if n == 1 else plural


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


class temporary_language:
    """Context manager pour changer temporairement la langue i18n.

    Usage:
        with temporary_language("en"):
            print(_("Bonjour"))  # Affiche "Hello"
        print(_("Bonjour"))      # Affiche "Bonjour" (langue d'origine restaurée)
    """

    def __init__(self, language: str):
        """
        Args:
            language: Code langue temporaire (ex: "en", "fr")
        """
        self.temp_language = language
        self.original_language = None

    def __enter__(self):
        """Active la langue temporaire."""
        self.original_language = get_current_language()
        set_language(self.temp_language)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restaure la langue d'origine."""
        if self.original_language:
            set_language(self.original_language)


def debug_i18n_context():
    """Context manager pour le mode debug i18n (génération de fichiers en anglais).

    Lit config.json["debug_i18n"] et, si activé, force la langue EN pendant
    la génération de fichiers (rapports, CHANGELOG, etc.).

    Usage (dans les modules qui génèrent des fichiers):
        from core.i18n import debug_i18n_context

        with debug_i18n_context():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(_("Date: {var0}\\n").format(var0=...))
                # Écrit "Date: ..." si debug_i18n=false
                # Écrit "Date: ..." en EN si debug_i18n=true

    Returns:
        Context manager (temporary_language ou no-op)
    """
    try:
        # Import local pour éviter la dépendance circulaire
        from tools.translator.config_loader import get_debug_i18n

        if get_debug_i18n():
            return temporary_language("en")
    except Exception as exc:
        # Config illisible : génération en langue courante, mais on le signale
        # (texte brut : core.colors dépend de ce module)
        print("[i18n] debug_i18n: {error}".format(error=exc), file=sys.stderr)

    # Si le flag n'est pas activé ou config indisponible, no-op context
    from contextlib import nullcontext
    return nullcontext()


def debug_language_detection() -> str:
    """Affiche les informations de détection de langue (pour le debugging).

    Returns:
        Chaîne formatée avec les infos de détection
    """
    info = []

    env_lang = os.environ.get("TOOLKIT_LANG", "")
    if env_lang:
        info.append(_("Locale système: {locale}").format(locale=f"TOOLKIT_LANG={env_lang}"))
    else:
        env_value = next(
            (f"{v}={os.environ[v]}" for v in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE") if os.environ.get(v)),
            None,
        )
        lang_code = env_value or _get_locale_code()
        info.append(_("Locale système: {locale}").format(locale=lang_code or "None"))

    info.append(_("Langue détectée: {lang}").format(lang=_current_language))

    locale_dir = _get_locale_dir()
    mo_file = locale_dir / _current_language / "LC_MESSAGES" / "{DOMAIN}.mo".format(DOMAIN=DOMAIN)
    mo_status = "✓ OK" if mo_file.exists() else "✓ " + _("défaut")
    info.append(_("Fichier .mo chargé: {status}").format(status=mo_status))

    return "\n".join(info)
