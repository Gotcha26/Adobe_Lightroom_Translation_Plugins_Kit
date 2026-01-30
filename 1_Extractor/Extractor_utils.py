#!/usr/bin/env python3
"""
Extractor_utils.py

Fonctions utilitaires pour l'extraction des chaînes localisables.
Traitement du texte, détection des suffixes, génération des clés LOC.
"""

import re
import os
from typing import Tuple, List, Optional, Dict, Set

from Extractor_config import (
    COMMON_SUFFIXES, IGNORE_EXACT, TECHNICAL_PATTERNS, STOP_WORDS,
    TECHNICAL_CONTEXT_PATTERNS
)


def extract_spacing(text: str) -> Tuple[str, int, int]:
    """
    CONTRAINTE 3: Extrait les espaces de formatage d'une chaîne.

    Les espaces de formatage sont situés:
    - Immédiatement après le guillemet ouvrant
    - Immédiatement avant le guillemet fermant

    Args:
        text: Le contenu entre guillemets (sans les guillemets)

    Returns:
        (texte_nettoyé, espaces_début, espaces_fin)
    """
    if not text:
        return text, 0, 0

    # Compter espaces en début
    leading = len(text) - len(text.lstrip(' '))

    # Compter espaces en fin
    trailing = len(text) - len(text.rstrip(' '))

    # Texte nettoyé
    clean = text.strip()

    return clean, leading, trailing


def extract_all_string_literals(line: str) -> List[Tuple[str, int, int]]:
    """
    Extrait TOUTES les chaines litterales d'une ligne (guillemets doubles uniquement).

    Note: Les guillemets simples ne sont PAS supportés volontairement.
    Le plugin doit utiliser des guillemets doubles conformément au SDK Adobe.

    Args:
        line: La ligne de code Lua

    Returns:
        Liste de (texte, position_debut, position_fin)
    """
    results = []

    # Guillemets doubles uniquement
    pattern_double = re.compile(r'"([^"]*)"')
    for match in pattern_double.finditer(line):
        text = match.group(1)
        results.append((text, match.start(), match.end()))

    return results


def is_line_concatenated(line: str) -> bool:
    """
    Vérifie si une ligne contient des concaténations avec ..

    Returns:
        True si la ligne contient ".." entre des chaînes
    """
    return '..' in line


def extract_suffix(text: str) -> Tuple[str, str]:
    """
    Extrait les suffixes communs en fin de chaîne.

    Ces suffixes (" - ", " -", "...") sont fréquents et multiplient
    inutilement le nombre de clés à traduire.

    Args:
        text: Texte nettoyé (sans espaces début/fin)

    Returns:
        (texte_base, suffixe)

    Exemples:
        "Cannot upload - " → ("Cannot upload", " - ")
        "Starting..." → ("Starting", "...")
        "Hello World" → ("Hello World", "")
    """
    if not text:
        return text, ""

    # Tester chaque suffixe (du plus long au plus court)
    for suffix in COMMON_SUFFIXES:
        if text.endswith(suffix):
            base = text[:-len(suffix)]
            # S'assurer que le texte de base n'est pas vide
            if base.strip():
                return base, suffix

    return text, ""


def is_in_technical_context(line: str) -> bool:
    """
    Vérifie si la ligne est dans un contexte technique.

    Utilisé pour filtrer les chaînes 'value' dans des contextes
    comme les headers HTTP où elles ne doivent pas être traduites.

    Args:
        line: La ligne de code complète

    Returns:
        True si la ligne est dans un contexte technique
    """
    for pattern in TECHNICAL_CONTEXT_PATTERNS:
        if pattern.search(line):
            return True
    return False


def is_technical_string(text: str, line_context: str = None) -> bool:
    """
    Vérifie si une chaîne est technique et doit être ignorée.

    Args:
        text: Le texte à vérifier
        line_context: La ligne complète (optionnel, pour contexte)

    Returns:
        True si la chaîne est technique
    """
    text_clean = text.strip().lower()
    text_original = text.strip()

    # Chaînes exactes à ignorer (insensible à la casse pour certaines)
    if text_clean in IGNORE_EXACT or text_original in IGNORE_EXACT:
        return True

    # Patterns techniques
    for pattern in TECHNICAL_PATTERNS:
        if pattern.search(text_original):
            return True

    # Si on a le contexte de la ligne, vérifier le contexte technique
    if line_context and is_in_technical_context(line_context):
        # Dans un contexte technique, filtrer plus agressivement
        # Ignorer les chaînes qui ressemblent à des identifiants/headers
        if re.match(r'^[A-Za-z][-A-Za-z0-9]*$', text_original):
            return True

    return False


def generate_loc_key(text: str, file_name: str, prefix: str, existing_keys: set) -> str:
    """
    Génère une clé LOC unique à partir du texte et du nom de fichier.

    Args:
        text: Texte à convertir en clé
        file_name: Nom du fichier source
        prefix: Préfixe LOC (ex: $$$/Piwigo)
        existing_keys: Set des clés déjà utilisées pour éviter les doublons

    Returns:
        Clé LOC unique
    """
    clean = text.strip()

    # Garder trace de certains suffixes significatifs
    has_ellipsis = clean.endswith('...')
    has_colon = clean.endswith(':')
    has_question = clean.endswith('?')

    # Nettoyer pour extraire les mots
    clean_for_words = clean.rstrip(':?.! ')

    # Extraire les mots significatifs
    words = re.findall(r'[A-Za-z]+', clean_for_words)
    if not words:
        return ""

    # Filtrer les stop words SAUF si le mot est en MAJUSCULES (emphase intentionnelle)
    # Exemple: "Connection NOT successful" → garde "NOT" car il est en majuscules
    key_words = [w for w in words[:6] if w.isupper() or w.lower() not in STOP_WORDS]
    if not key_words:
        key_words = words[:4]

    key_part = ''.join(w.capitalize() for w in key_words[:4])

    # Ajouter suffixe si présent
    if has_ellipsis:
        key_part += "Ellipsis"
    elif has_question:
        key_part += "Question"

    # Catégorie basée sur le fichier
    file_base = os.path.splitext(file_name)[0]
    category = file_base.replace('PW', '').replace('Piwigo', '')
    if not category:
        category = 'General'

    base_key = f"{prefix}/{category}/{key_part}"

    # Assurer l'unicité
    final_key = base_key
    counter = 2
    while final_key in existing_keys:
        final_key = f"{base_key}{counter}"
        counter += 1

    return final_key


def generate_replacement_code(pattern_name: str, loc_key: str,
                               leading: int, trailing: int,
                               suffix: str,
                               original_text: str,
                               base_text: str) -> str:
    """
    Génère le code de remplacement Lua avec gestion des espaces ET des suffixes.

    Format ZString du SDK Lightroom: LOC "$$$/Key=Default Value"
    La valeur par défaut EST OBLIGATOIRE sinon Lightroom affiche la clé brute.

    Exemples:
    - Sans rien: LOC "$$$/key=My Text"
    - 1 espace fin: LOC "$$$/key=My Text" .. " "
    - Suffixe " - ": LOC "$$$/key=My Text" .. " - "
    - 2 espaces début + suffixe: "  " .. LOC "$$$/key=My Text" .. " - "
    """
    # Appel LOC avec valeur par défaut
    loc_call = f'LOC "{loc_key}={base_text}"'

    # Construire les parties
    parts = []

    # Espaces en début
    if leading > 0:
        parts.append(f'"{" " * leading}" .. ')

    # Appel LOC
    parts.append(loc_call)

    # Suffixe (remplace trailing_spaces si présent, car le suffixe inclut souvent un espace)
    if suffix:
        parts.append(f' .. "{suffix}"')
    elif trailing > 0:
        parts.append(f' .. "{" " * trailing}"')

    replace_str = ''.join(parts)

    return f'"{original_text}" → {replace_str}'
