#!/usr/bin/env python3
"""
Nom du fichier : config_loader.py

Description :
Module centralisé pour charger la configuration de la langue de référence.
Permet de rendre flexible le système en utilisant config.json["lang"] au lieu
de hardcoder "en" partout dans le code.

Date : 2026-02-06
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr
"""

import os
import sys
import json
from typing import Optional

# Permet d'importer core.* depuis ce module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.i18n import _


# =============================================================================
# CONFIGURATION PAR DÉFAUT
# =============================================================================

DEFAULT_REFERENCE_LANG = "en"  # Fallback si config.json absent ou invalide


# =============================================================================
# FONCTIONS DE CHARGEMENT
# =============================================================================

def _get_root_dir() -> str:
    """
    Retourne le répertoire racine du projet (où se trouvent config.json / config.local.json).

    Structure : tools/translator/config_loader.py → remonter 2 niveaux.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(current_dir))


def get_config_path() -> Optional[str]:
    """
    Trouve le fichier config.json en remontant depuis le module actuel.

    Returns:
        Chemin vers config.json ou None si non trouvé
    """
    root_dir = _get_root_dir()

    config_path = os.path.join(root_dir, "config.json")
    if os.path.isfile(config_path):
        return config_path

    config_local_path = os.path.join(root_dir, "config.local.json")
    if os.path.isfile(config_local_path):
        return config_local_path

    return None


def load_config() -> dict:
    """
    Charge la configuration avec merge config.json + config.local.json.

    Ordre de priorité : config.json < config.local.json
    (config.local.json surcharge les valeurs de config.json)

    Returns:
        Dictionnaire de configuration (vide si aucun fichier trouvé)
    """
    root_dir = _get_root_dir()
    config = {}

    # 1) Charger config.json (base partagée)
    config_path = os.path.join(root_dir, "config.json")
    if os.path.isfile(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            pass

    # 2) Surcharger avec config.local.json (local, non versionné)
    config_local_path = os.path.join(root_dir, "config.local.json")
    if os.path.isfile(config_local_path):
        try:
            with open(config_local_path, 'r', encoding='utf-8') as f:
                config = {**config, **json.load(f)}
        except Exception:
            pass

    return config


def get_reference_lang() -> str:
    """
    Récupère la langue de référence depuis config.json.

    Cette langue est utilisée comme "source de vérité" pour :
    - Les fichiers TranslatedStrings_{lang}.txt
    - Les fichiers UPDATE_{lang}.json
    - Les comparaisons et synchronisations

    Returns:
        Code langue (ex: "en", "fr", "de")
    """
    config = load_config()
    return config.get("lang", DEFAULT_REFERENCE_LANG)


def get_reference_filename(prefix: str = "TranslatedStrings", extension: str = ".txt") -> str:
    """
    Construit le nom du fichier de référence avec la langue configurée.

    Args:
        prefix: Préfixe du fichier (défaut: "TranslatedStrings")
        extension: Extension (défaut: ".txt")

    Returns:
        Nom du fichier (ex: "TranslatedStrings_en.txt", "UPDATE_fr.json")

    Examples:
        >>> get_reference_filename()
        'TranslatedStrings_en.txt'

        >>> get_reference_filename("UPDATE", ".json")
        'UPDATE_en.json'
    """
    lang = get_reference_lang()
    return f"{prefix}_{lang}{extension}"


def get_update_filename() -> str:
    """
    Raccourci pour obtenir le nom du fichier UPDATE.

    Returns:
        Nom du fichier UPDATE (ex: "UPDATE_en.json")
    """
    return get_reference_filename("UPDATE", ".json")


def is_reference_lang(lang_code: str) -> bool:
    """
    Vérifie si un code langue correspond à la langue de référence.

    Args:
        lang_code: Code langue à vérifier (ex: "en", "fr")

    Returns:
        True si c'est la langue de référence
    """
    return lang_code.lower() == get_reference_lang().lower()


def get_debug_i18n() -> bool:
    """
    Récupère le flag debug_i18n depuis config.json.

    Quand activé, les fichiers générés (rapports, CHANGELOG) utilisent l'anglais
    au lieu du français pour tester les traductions.

    Returns:
        True si le mode debug i18n est activé
    """
    config = load_config()
    return config.get("debug_i18n", False)


# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def debug_config_info() -> str:
    """
    Génère un message de debug avec les informations de configuration.

    Returns:
        Chaîne formatée avec les infos de config
    """
    config_path = get_config_path()
    lang = get_reference_lang()
    ref_file = get_reference_filename()
    update_file = get_update_filename()

    lines = [
        _("Configuration de la langue de référence:"),
        f"  - Fichier config   : {config_path or '(non trouvé)'}",
        _("  - Langue référence : {lang}").format(lang=lang),
        _("  - Fichier référence: {ref_file}").format(ref_file=ref_file),
        _("  - Fichier UPDATE   : {update_file}").format(update_file=update_file)
    ]

    return "\n".join(lines)


# =============================================================================
# TEST DU MODULE
# =============================================================================

if __name__ == "__main__":
    print(debug_config_info())
