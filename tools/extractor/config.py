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
# IMPORTANT: L'ordre compte - les patterns plus spécifiques doivent venir en premier
UI_CONTEXT_PATTERNS: List[tuple] = [
    # Patterns LrDialogs - tous les arguments sont potentiellement localisables
    ('LrDialogs.message', re.compile(r'LrDialogs\.message\s*\(')),
    ('LrDialogs.confirm', re.compile(r'LrDialogs\.confirm\s*\(')),
    ('LrDialogs.showError', re.compile(r'LrDialogs\.showError\s*\(')),
    ('LrDialogs.showBezel', re.compile(r'LrDialogs\.showBezel\s*\(')),
    ('LrDialogs.runOpenPanel', re.compile(r'LrDialogs\.runOpenPanel\s*\(')),
    ('LrDialogs.runSavePanel', re.compile(r'LrDialogs\.runSavePanel\s*\(')),
    ('LrDialogs.presentModalDialog', re.compile(r'LrDialogs\.presentModalDialog\s*\(')),
    # LrErrors - messages d'erreur à localiser
    ('LrErrors.throwUserError', re.compile(r'LrErrors\.throwUserError\s*\(')),
    ('LrErrors.throwCanceled', re.compile(r'LrErrors\.throwCanceled\s*\(')),
    # Propriétés UI standard
    ('title', re.compile(r'\btitle\s*=\s*')),
    ('tooltip', re.compile(r'\btooltip\s*=\s*')),
    ('label', re.compile(r'\blabel\s*=\s*')),
    ('placeholder', re.compile(r'\bplaceholder\s*=\s*')),
    ('actionVerb', re.compile(r'\bactionVerb\s*=\s*')),
    ('cancelVerb', re.compile(r'\bcancelVerb\s*=\s*')),
    ('otherVerb', re.compile(r'\botherVerb\s*=\s*')),
    ('message', re.compile(r'\bmessage\s*=\s*')),
    ('info', re.compile(r'\binfo\s*=\s*')),
    ('caption', re.compile(r'\bcaption\s*=\s*')),
    # Status messages (callStatus.statusMsg, etc.)
    ('statusMsg', re.compile(r'\bstatusMsg\s*=\s*')),
    # LrPluginName - MAIS sera filtré par IGNORE_EXACT pour "Piwigo Publisher"
    ('LrPluginName', re.compile(r'LrPluginName\s*=\s*')),
    ('popup_item', re.compile(r'\{\s*title\s*=\s*"[^"]*"\s*,\s*value\s*=')),
    # ATTENTION: 'value' est trop générique et capture des valeurs techniques
    # On le garde mais avec filtrage renforcé dans is_technical_string
    ('value', re.compile(r'\bvalue\s*=\s*')),
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

# CONTRAINTE 5: Chaînes à ignorer (exactes)
IGNORE_EXACT: Set[str] = {
    '', ' ', '  ', '...', '.', ',', ':', ';', '-',
    'nil', 'true', 'false', 'null',
    'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS',
    'UTF-8', 'utf-8', 'json', 'xml', 'html', 'text',
    # Headers HTTP
    'Accept', 'User-Agent', 'Content-Type', 'Authorization', 'Cookie',
    'Cache-Control', 'If-None-Match', 'If-Modified-Since',
    # Types MIME courants
    'application/json', 'application/xml', 'application/x-www-form-urlencoded',
    'text/plain', 'text/html', 'text/xml',
    'application/vnd.github.v3+json',
    'multipart/form-data',
    # Identifiants techniques
    'PiwigoPublish-Lightroom-Plugin',
    # Nom du plugin (non traduisible car identifiant technique)
    'Piwigo Publisher',
    # Boutons standards LrDialogs (identifiants internes, pas des labels UI)
    'ok', 'cancel', 'other',
    'Ok', 'Cancel', 'Other',
    'OK', 'CANCEL', 'OTHER',
    # Verbes d'action courants utilisés comme identifiants dans LrDialogs.confirm
    'Reset', 'Import', 'Check', 'Delete', 'Remove', 'Apply', 'Save', 'Load',
    'Yes', 'No', 'Abort', 'Retry', 'Ignore', 'Continue', 'Stop', 'Close',
    # Types de messages LrDialogs.message (3ème argument)
    'info', 'warning', 'critical', 'error',
    # Identifiants techniques dans concaténations
    'boundary',
}

TECHNICAL_PATTERNS: List[re.Pattern] = [
    re.compile(r'^https?://'),           # URLs
    re.compile(r'^\d+\.\d+\.\d+'),        # Versions (1.0.0)
    re.compile(r'^application/'),         # MIME types
    re.compile(r'^text/'),                # MIME types text/*
    re.compile(r'^image/'),               # MIME types image/*
    re.compile(r'^pwg\.'),                # API Piwigo
    re.compile(r'^[a-z_]+$'),             # snake_case pur (identifiants)
    re.compile(r'^[a-z]{3,15}$'),         # Mots courts minuscules = variables (boundary, length, etc.)
    re.compile(r'^[A-Z][a-z]+(-[A-Z][a-z]+)+$'),  # Headers HTTP (Content-Type, User-Agent)
    re.compile(r'^Lr[A-Z]'),              # SDK Lightroom
    re.compile(r'^DEBUG'),                # Messages debug
    # Note: \\n est retiré car légitime dans les messages UI pour le formatage
    re.compile(r'^[/\\]'),                # Chemins
    re.compile(r'^\d+$'),                 # Nombres purs
    re.compile(r'^[a-f0-9-]{36}$', re.IGNORECASE),  # UUIDs
]

# Patterns de contexte technique - si la ligne matche, ignorer les chaînes 'value'
# Utilisé pour éviter d'extraire les valeurs dans des contextes techniques
TECHNICAL_CONTEXT_PATTERNS: List[re.Pattern] = [
    re.compile(r'\bfield\s*=\s*["\']'),       # { field = "Accept", value = "..." }
    re.compile(r'headers?\s*=\s*\{'),          # headers = { ... }
    re.compile(r'http\.request'),              # Requêtes HTTP
    re.compile(r'LrHttp\.'),                   # SDK Lightroom HTTP
    re.compile(r'multipart/form-data'),        # Multipart requests (boundary, etc.)
    re.compile(r'\bboundary\b'),               # Contexte avec boundary
]

# Stop words pour génération de clé
STOP_WORDS: Set[str] = {
    'the', 'a', 'an', 'is', 'if', 'to', 'for', 'be', 'will',
    'as', 'on', 'this', 'in', 'of', 'and', 'or', 'not', 'can',
    'has', 'have', 'been', 'are', 'was', 'were', 'being', 'it'
}

# Fichiers à exclure par défaut
DEFAULT_EXCLUDED_FILES: Set[str] = {'JSON.lua'}

# =============================================================================
# CLÉS LOC TECHNIQUES À IGNORER
# =============================================================================

# Patterns de clés LOC existantes à ignorer (éléments techniques non-traduisibles)
# Ces clés sont utilisées pour des headers HTTP, identifiants, etc.
IGNORE_LOC_KEY_PATTERNS: List[re.Pattern] = [
    re.compile(r'/UpdateChecker/Accept$'),      # Header HTTP Accept
    re.compile(r'/UpdateChecker/UserAgent$'),   # Header HTTP User-Agent
    re.compile(r'/UpdateChecker/PiwigopublishLightroomPlugin$'),  # Identifiant User-Agent
]

# Valeurs techniques à ignorer dans les LOC existantes
IGNORE_LOC_VALUES: Set[str] = {
    'Accept',
    'User-Agent',
    'PiwigoPublish-Lightroom-Plugin',
}
