#!/usr/bin/env python3
"""
Extractor_config.py

Configuration et constantes pour l'extraction des chaînes localisables.
Basé sur le skill: lightroom-localization-extraction
"""

import re
from typing import List, Set, Dict


# =============================================================================
# REGEX PATTERNS
# =============================================================================

# CONTRAINTE 1: Regex pour ignorer les lignes de log
LOG_LINE_REGEX = re.compile(
    r'\b(log|logInfo|logWarn|logError|logTrace|logDebug)\s*[:(]'
    r'|'
    r'\b(log|info|warn|error|trace|debug)\s*:\s*(log|info|warn|error|trace|debug)?\s*\(',
    re.IGNORECASE
)

# Pattern pour extraire TOUTES les chaînes littérales d'une ligne
ALL_STRINGS_PATTERN = re.compile(r'"([^"]*)"')


# =============================================================================
# SUFFIXES ET CONTEXTES
# =============================================================================

# SUFFIXES COMMUNS à extraire (ordre important : du plus long au plus court)
COMMON_SUFFIXES: List[str] = [
    ' - ',      # " - " (espace-tiret-espace)
    ' -',       # " -" (espace-tiret)
    '...',      # "..." (points de suspension)
]

# Patterns pour détecter les CONTEXTES UI (sans capturer la chaîne)
UI_CONTEXT_PATTERNS: List[tuple] = [
    ('title', re.compile(r'\btitle\s*=\s*')),
    ('tooltip', re.compile(r'\btooltip\s*=\s*')),
    ('label', re.compile(r'\blabel\s*=\s*')),
    ('value', re.compile(r'\bvalue\s*=\s*')),
    ('placeholder', re.compile(r'\bplaceholder\s*=\s*')),
    ('LrDialogs.message', re.compile(r'LrDialogs\.message\s*\(')),
    ('LrDialogs.confirm', re.compile(r'LrDialogs\.confirm\s*\(')),
    ('LrDialogs.showError', re.compile(r'LrDialogs\.showError\s*\(')),
    ('LrDialogs.showBezel', re.compile(r'LrDialogs\.showBezel\s*\(')),
    ('actionVerb', re.compile(r'\bactionVerb\s*=\s*')),
    ('cancelVerb', re.compile(r'\bcancelVerb\s*=\s*')),
    ('otherVerb', re.compile(r'\botherVerb\s*=\s*')),
    ('message', re.compile(r'\bmessage\s*=\s*')),
    ('info', re.compile(r'\binfo\s*=\s*')),
    ('caption', re.compile(r'\bcaption\s*=\s*')),
    ('LrPluginName', re.compile(r'LrPluginName\s*=\s*')),
    ('popup_item', re.compile(r'\{\s*title\s*=\s*"[^"]*"\s*,\s*value\s*=')),
]

# Anciens patterns pour compatibilité (chaîne simple)
UI_PATTERNS: List[tuple] = [
    ('title', re.compile(r'\btitle\s*=\s*"([^"]*)"')),
    ('tooltip', re.compile(r'\btooltip\s*=\s*"([^"]*)"')),
    ('label', re.compile(r'\blabel\s*=\s*"([^"]*)"')),
    ('value', re.compile(r'\bvalue\s*=\s*"([^"]*)"')),
    ('placeholder', re.compile(r'\bplaceholder\s*=\s*"([^"]*)"')),
    ('LrDialogs.message', re.compile(r'LrDialogs\.message\s*\(\s*"([^"]*)"')),
    ('LrDialogs.confirm', re.compile(r'LrDialogs\.confirm\s*\(\s*"([^"]*)"')),
    ('LrDialogs.showError', re.compile(r'LrDialogs\.showError\s*\(\s*"([^"]*)"')),
    ('LrDialogs.showBezel', re.compile(r'LrDialogs\.showBezel\s*\(\s*"([^"]*)"')),
    ('actionVerb', re.compile(r'\bactionVerb\s*=\s*"([^"]*)"')),
    ('cancelVerb', re.compile(r'\bcancelVerb\s*=\s*"([^"]*)"')),
    ('otherVerb', re.compile(r'\botherVerb\s*=\s*"([^"]*)"')),
    ('message', re.compile(r'\bmessage\s*=\s*"([^"]*)"')),
    ('info', re.compile(r'\binfo\s*=\s*"([^"]*)"')),
    ('caption', re.compile(r'\bcaption\s*=\s*"([^"]*)"')),
    ('LrPluginName', re.compile(r'LrPluginName\s*=\s*"([^"]*)"')),
    ('popup_item', re.compile(r'\{\s*title\s*=\s*"([^"]*)"\s*,\s*value\s*=')),
]


# =============================================================================
# LISTES D'EXCLUSION
# =============================================================================

# CONTRAINTE 5: Chaînes à ignorer
IGNORE_EXACT: Set[str] = {
    '', ' ', '  ', '...', '.', ',', ':', ';', '-',
    'nil', 'true', 'false', 'null',
    'GET', 'POST', 'PUT', 'DELETE',
    'UTF-8', 'json', 'xml',
}

TECHNICAL_PATTERNS: List[re.Pattern] = [
    re.compile(r'^https?://'),       # URLs
    re.compile(r'^\d+\.\d+\.\d+'),   # Versions
    re.compile(r'^application/'),    # MIME types
    re.compile(r'^pwg\.'),           # API Piwigo
    re.compile(r'^[a-z_]+$'),        # snake_case pur
    re.compile(r'^Lr[A-Z]'),         # SDK Lightroom
    re.compile(r'^DEBUG'),           # Messages debug
    re.compile(r'\\n'),              # Contient \n
    re.compile(r'^[/\\]'),           # Chemins
]

# Stop words pour génération de clé
STOP_WORDS: Set[str] = {
    'the', 'a', 'an', 'is', 'if', 'to', 'for', 'be', 'will', 
    'as', 'on', 'this', 'in', 'of', 'and', 'or', 'not', 'can',
    'has', 'have', 'been', 'are', 'was', 'were', 'being', 'it'
}

# Fichiers à exclure par défaut
DEFAULT_EXCLUDED_FILES: Set[str] = {'JSON.lua'}
