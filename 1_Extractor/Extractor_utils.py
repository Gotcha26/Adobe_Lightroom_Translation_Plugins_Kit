#!/usr/bin/env python3
"""
Extractor_utils.py

Fonctions utilitaires pour l'extraction des chaînes localisables.
Traitement du texte, détection des suffixes, génération des clés LOC.
"""

import re
import os
from typing import Tuple, List, Optional, Dict, Set

from Extractor_config import COMMON_SUFFIXES, IGNORE_EXACT, TECHNICAL_PATTERNS, STOP_WORDS


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
    Extrait TOUTES les chaines litterales d'une ligne.
    
    Args:
        line: La ligne de code Lua
        
    Returns:
        Liste de (texte, position_debut, position_fin)
    """
    # Guillemets doubles: toujours extraits
    pattern_double = re.compile(r'"([^"]*)"')
    
    # Guillemets simples: uniquement apres des proprietes UI connues
    # Pattern: (title|tooltip|label|actionVerb|cancelVerb|otherVerb|message|info|caption)\s*=\s*'([^']*)'
    pattern_single_ui = re.compile(
        r'\b(title|tooltip|label|actionVerb|cancelVerb|otherVerb|message|info|caption)\s*=\s*' + r"'([^']*)'"
    )
    
    results = []
    
    # Extraire toutes les chaines entre guillemets doubles
    for match in pattern_double.finditer(line):
        text = match.group(1)
        results.append((text, match.start(), match.end()))
    
    # Extraire les chaines entre guillemets simples UNIQUEMENT pour les proprietes UI
    for match in pattern_single_ui.finditer(line):
        text = match.group(2)  # groupe 2 = le contenu de la chaine
        # Calculer la position de la chaine (pas du pattern complet)
        # Trouver la position du guillemet simple ouvrant
        full_match = match.group(0)
        quote_pos = full_match.rfind("'")
        start_pos = match.start() + full_match.find("'")
        end_pos = match.end()
        results.append((text, start_pos, end_pos))
    
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


def is_technical_string(text: str) -> bool:
    """Vérifie si une chaîne est technique et doit être ignorée."""
    text_clean = text.strip().lower()
    
    # Chaînes exactes à ignorer
    if text_clean in IGNORE_EXACT or text.strip() in IGNORE_EXACT:
        return True
    
    # Patterns techniques
    for pattern in TECHNICAL_PATTERNS:
        if pattern.search(text.strip()):
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
    
    key_words = [w for w in words[:6] if w.lower() not in STOP_WORDS]
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
