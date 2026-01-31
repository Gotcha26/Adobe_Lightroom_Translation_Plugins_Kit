#!/usr/bin/env python3
"""
WebBridge_utils.py

Fonctions utilitaires pour le parsing et la manipulation de données.

Fonctions principales:
    - parse_loc_line: Parse une ligne TranslatedStrings_xx.txt
    - build_loc_line: Reconstruit une ligne avec métadonnées
    - extract_placeholders: Extrait les placeholders d'une chaîne
    - find_file: Recherche un fichier dans un dossier
    - load_json_file: Charge un fichier JSON de manière sûre
    - save_json_file: Sauvegarde un fichier JSON avec formatage

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-31
Version : 1.0
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


# Regex pour parser les lignes LOC du format Lightroom SDK
# Format: "$$$/Prefix/Category/Key=Value"
LOC_LINE_PATTERN = re.compile(r'"(\$\$\$/[^/]+)/([^/]+)/([^=]+)=([^"]*)"')

# Regex pour détecter les placeholders de format
# Supporte: %s, %d, %f, %x, etc. et séquences d'échappement \n, \t, \", \\
PLACEHOLDER_PATTERN = re.compile(r'%[sdfuxXoceEgG\d]|\\[nt"\\]')

# Suffixes courants à détecter
COMMON_SUFFIXES = [" -", " :", ":", "...", " - ", ": "]


def parse_loc_line(line: str) -> Optional[Dict[str, str]]:
    """
    Parse une ligne du fichier TranslatedStrings_xx.txt.

    Args:
        line: Ligne à parser (format: "$$$/Prefix/Category/Key=Value")

    Returns:
        Dictionnaire avec prefix, category, key, value ou None si format invalide

    Example:
        >>> parse_loc_line('"$$$/Piwigo/API/AddTags=to add tags"')
        {
            'prefix': '$$$/Piwigo',
            'category': 'API',
            'key': 'AddTags',
            'value': 'to add tags'
        }
    """
    line = line.strip()

    # Ignorer les commentaires et lignes vides
    if not line or line.startswith('--'):
        return None

    match = LOC_LINE_PATTERN.match(line)
    if not match:
        return None

    return {
        'prefix': match.group(1),
        'category': match.group(2),
        'key': match.group(3),
        'value': match.group(4)
    }


def build_loc_line(prefix: str, category: str, key: str, text: str,
                   metadata: Optional[Dict[str, any]] = None) -> str:
    """
    Reconstruit une ligne TranslatedStrings_xx.txt avec métadonnées.

    Applique les espaces de début/fin et suffixes si présents dans metadata.

    Args:
        prefix: Préfixe LOC (ex: "$$$/Piwigo")
        category: Catégorie (ex: "API")
        key: Nom de la clé (ex: "AddTags")
        text: Texte de base (sans espaces/suffixes)
        metadata: Métadonnées optionnelles avec leading_spaces, trailing_spaces, suffix

    Returns:
        Ligne formatée pour fichier .txt

    Example:
        >>> build_loc_line("$$$/Piwigo", "API", "CannotLogPiwigo",
        ...                "Cannot log in to Piwigo",
        ...                {"suffix": " -"})
        '"$$$/Piwigo/API/CannotLogPiwigo=Cannot log in to Piwigo -"'
    """
    if metadata is None:
        metadata = {}

    # Appliquer espaces de début
    leading = " " * metadata.get("leading_spaces", 0)

    # Appliquer espaces de fin
    trailing = " " * metadata.get("trailing_spaces", 0)

    # Appliquer suffixe
    suffix = metadata.get("suffix", "")

    # Construire valeur finale
    value = f"{leading}{text}{suffix}{trailing}"

    # Construire ligne complète
    return f'"{prefix}/{category}/{key}={value}"'


def extract_placeholders(text: str) -> Set[str]:
    """
    Extrait tous les placeholders d'une chaîne.

    Args:
        text: Texte à analyser

    Returns:
        Ensemble des placeholders trouvés

    Example:
        >>> extract_placeholders("Albums created: %s, links updated: %s")
        {'%s'}
        >>> extract_placeholders("Error on line %d\\nPlease check")
        {'%d', '\\n'}
    """
    return set(PLACEHOLDER_PATTERN.findall(text))


def compare_placeholders(en_text: str, target_text: str) -> Tuple[bool, Set[str], Set[str]]:
    """
    Compare les placeholders entre deux textes.

    Args:
        en_text: Texte anglais de référence
        target_text: Texte traduit à vérifier

    Returns:
        Tuple (match, en_only, target_only)
        - match: True si les placeholders sont identiques
        - en_only: Placeholders présents uniquement en EN
        - target_only: Placeholders présents uniquement dans la cible

    Example:
        >>> compare_placeholders("Error: %s on line %d", "Erreur: %s")
        (False, {'%d'}, set())
    """
    en_placeholders = extract_placeholders(en_text)
    target_placeholders = extract_placeholders(target_text)

    match = en_placeholders == target_placeholders
    en_only = en_placeholders - target_placeholders
    target_only = target_placeholders - en_placeholders

    return match, en_only, target_only


def detect_suffix(text: str) -> Tuple[str, str]:
    """
    Détecte un suffixe courant à la fin d'une chaîne.

    Args:
        text: Texte à analyser

    Returns:
        Tuple (base_text, suffix)
        - base_text: Texte sans le suffixe (mais avec espaces de fin)
        - suffix: Suffixe détecté sans espaces de fin (ou "" si aucun)

    Example:
        >>> detect_suffix("Cannot log in to Piwigo - ")
        ("Cannot log in to Piwigo ", " -")
        >>> detect_suffix("Select album:")
        ("Select album", ":")
    """
    # D'abord, retirer les espaces de fin pour vérifier le suffixe
    text_stripped = text.rstrip()

    for suffix in COMMON_SUFFIXES:
        if text_stripped.endswith(suffix):
            base = text_stripped[:-len(suffix)]
            # Retourner le texte avec espaces de fin préservés
            trailing_spaces = text[len(text_stripped):]
            return base + trailing_spaces, suffix

    return text, ""


def analyze_spacing(text: str) -> Dict[str, any]:
    """
    Analyse les espaces et suffixes d'une chaîne.

    Args:
        text: Texte à analyser

    Returns:
        Dictionnaire avec:
        - original_text: Texte original
        - base_text: Texte sans espaces ni suffixes
        - leading_spaces: Nombre d'espaces de début
        - trailing_spaces: Nombre d'espaces de fin
        - suffix: Suffixe détecté (ou "")
        - has_metadata: True si métadonnées présentes

    Example:
        >>> analyze_spacing("Cannot log in to Piwigo - ")
        {
            'original_text': 'Cannot log in to Piwigo - ',
            'base_text': 'Cannot log in to Piwigo',
            'leading_spaces': 0,
            'trailing_spaces': 0,
            'suffix': ' -',
            'has_metadata': True
        }
    """
    original = text

    # Compter espaces de début
    leading_spaces = len(text) - len(text.lstrip(' '))
    text_no_leading = text.lstrip(' ')

    # Détecter suffixe
    text_with_trailing, suffix = detect_suffix(text_no_leading)

    # Compter espaces de fin
    # Si un suffixe est détecté, text_with_trailing contient le texte base + espaces de fin
    # Sinon, text_with_trailing est le texte complet
    if suffix:
        # Le suffixe a été détecté, retirer les espaces de fin de text_with_trailing
        trailing_spaces = len(text_with_trailing) - len(text_with_trailing.rstrip(' '))
        base_text = text_with_trailing.rstrip(' ')
    else:
        # Pas de suffixe, compter normalement les espaces de fin
        trailing_spaces = len(text_no_leading) - len(text_no_leading.rstrip(' '))
        base_text = text_no_leading.rstrip(' ')

    has_metadata = leading_spaces > 0 or trailing_spaces > 0 or len(suffix) > 0

    return {
        'original_text': original,
        'base_text': base_text,
        'leading_spaces': leading_spaces,
        'trailing_spaces': trailing_spaces,
        'suffix': suffix,
        'has_metadata': has_metadata
    }


def find_file(directory: str, filename: str, recursive: bool = True) -> Optional[str]:
    """
    Recherche un fichier dans un dossier.

    Args:
        directory: Dossier de recherche
        filename: Nom du fichier à trouver
        recursive: Si True, recherche récursive

    Returns:
        Chemin complet du fichier ou None si non trouvé

    Example:
        >>> find_file("/path/to/plugin", "TranslatedStrings_en.txt")
        '/path/to/plugin/__i18n_tmp__/Extractor/20260130_223727/TranslatedStrings_en.txt'
    """
    if not os.path.exists(directory):
        return None

    if recursive:
        for root, dirs, files in os.walk(directory):
            if filename in files:
                return os.path.join(root, filename)
    else:
        path = os.path.join(directory, filename)
        if os.path.exists(path):
            return path

    return None


def find_files_by_pattern(directory: str, pattern: str, recursive: bool = True) -> List[str]:
    """
    Recherche des fichiers correspondant à un pattern.

    Args:
        directory: Dossier de recherche
        pattern: Pattern regex ou simple (ex: "TranslatedStrings_*.txt")
        recursive: Si True, recherche récursive

    Returns:
        Liste des chemins complets des fichiers trouvés

    Example:
        >>> find_files_by_pattern("/path/to/plugin", "TranslatedStrings_*.txt")
        [
            '/path/to/.../TranslatedStrings_en.txt',
            '/path/to/.../TranslatedStrings_fr.txt'
        ]
    """
    # Convertir pattern simple en regex
    if '*' in pattern or '?' in pattern:
        import fnmatch
        regex = fnmatch.translate(pattern)
        pattern_re = re.compile(regex)
    else:
        pattern_re = re.compile(pattern)

    results = []

    if not os.path.exists(directory):
        return results

    if recursive:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if pattern_re.match(filename):
                    results.append(os.path.join(root, filename))
    else:
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)):
                if pattern_re.match(filename):
                    results.append(os.path.join(directory, filename))

    return sorted(results)


def load_json_file(filepath: str) -> Optional[dict]:
    """
    Charge un fichier JSON de manière sûre.

    Args:
        filepath: Chemin du fichier JSON

    Returns:
        Dictionnaire chargé ou None si erreur

    Example:
        >>> data = load_json_file("spacing_metadata.json")
    """
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Erreur JSON dans {filepath}: {e}")
        return None
    except Exception as e:
        print(f"Erreur lors de la lecture de {filepath}: {e}")
        return None


def save_json_file(filepath: str, data: dict, indent: int = 2) -> bool:
    """
    Sauvegarde un fichier JSON avec formatage.

    Args:
        filepath: Chemin du fichier de sortie
        data: Données à sauvegarder
        indent: Indentation (défaut: 2 espaces)

    Returns:
        True si succès, False sinon

    Example:
        >>> save_json_file("output.json", {"key": "value"})
        True
    """
    try:
        # Créer le dossier parent si nécessaire
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de {filepath}: {e}")
        return False


def extract_prefix_from_loc_key(loc_key: str) -> Optional[str]:
    """
    Extrait le préfixe d'une clé LOC complète.

    Args:
        loc_key: Clé LOC complète (ex: "$$$/Piwigo/API/AddTags")

    Returns:
        Préfixe (ex: "$$$/Piwigo") ou None si format invalide

    Example:
        >>> extract_prefix_from_loc_key("$$$/Piwigo/API/AddTags")
        '$$$/Piwigo'
    """
    if not loc_key or not loc_key.startswith("$$$/"):
        return None

    parts = loc_key.split('/')
    if len(parts) < 4:  # $$$/Prefix/Category/Key minimum
        return None

    # Reconstruire le préfixe: $$$/ + parts[1]
    return f"$$$/{parts[1]}"


def parse_extraction_timestamp(path: str) -> Optional[str]:
    """
    Extrait le timestamp d'un chemin d'extraction.

    Args:
        path: Chemin contenant un timestamp (ex: "Extractor/20260130_223727/")

    Returns:
        Timestamp au format YYYYMMDD_HHMMSS ou None

    Example:
        >>> parse_extraction_timestamp("__i18n_tmp__/Extractor/20260130_223727/")
        '20260130_223727'
    """
    # Chercher un pattern YYYYMMDD_HHMMSS (15 caractères)
    timestamp_pattern = re.compile(r'(\d{8}_\d{6})')
    match = timestamp_pattern.search(path)

    if match:
        return match.group(1)

    return None


def get_language_from_filename(filename: str) -> Optional[str]:
    """
    Extrait le code langue d'un nom de fichier TranslatedStrings.

    Args:
        filename: Nom de fichier (ex: "TranslatedStrings_fr.txt")

    Returns:
        Code langue (ex: "fr") ou None si non trouvé

    Example:
        >>> get_language_from_filename("TranslatedStrings_fr.txt")
        'fr'
        >>> get_language_from_filename("TranslatedStrings_en.txt")
        'en'
    """
    # Pattern: TranslatedStrings_XX.txt où XX est le code langue
    pattern = re.compile(r'TranslatedStrings_([a-z]{2})\.txt', re.IGNORECASE)
    match = pattern.search(filename)

    if match:
        return match.group(1).lower()

    return None


def normalize_category_name(category: str) -> str:
    """
    Normalise un nom de catégorie pour l'utilisation comme clé JSON.

    Args:
        category: Nom de catégorie brut

    Returns:
        Nom normalisé (sans espaces, caractères spéciaux)

    Example:
        >>> normalize_category_name("API Errors")
        'APIErrors'
        >>> normalize_category_name("dialog-buttons")
        'DialogButtons'
    """
    # Supprimer caractères spéciaux et mettre en PascalCase
    import re

    # Remplacer séparateurs par espaces
    category = re.sub(r'[-_\s]+', ' ', category)

    # Mettre en PascalCase
    words = category.split()
    return ''.join(word.capitalize() for word in words)


def count_keys_in_i18n(i18n_data: dict, lang: str = "en") -> int:
    """
    Compte le nombre de clés dans un fichier i18n pour une langue donnée.

    Args:
        i18n_data: Données i18n chargées
        lang: Code langue (défaut: "en")

    Returns:
        Nombre de clés

    Example:
        >>> count_keys_in_i18n({"translations": {"en": {"API": {"Key1": {}, "Key2": {}}}}})
        2
    """
    count = 0
    translations = i18n_data.get("translations", {}).get(lang, {})

    for category, keys in translations.items():
        count += len(keys)

    return count
