#!/usr/bin/env python3
"""
Nom du fichier : models.py

Dépendances : Aucune

Description :
Classes de données (dataclasses) pour la représentation des chaînes extraites et des statistiques d'extraction.
Fournit les modèles: ExtractedString, ExtractionStats.

Usage CLI :
    Non pourvu

Date : 2026-11-08
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@dataclass
class ExtractedString:
    """Représente une chaîne extraite avec toutes ses métadonnées."""
    original_text: str          # Texte original (avec espaces et suffixes)
    clean_text: str             # Texte nettoyé (sans espaces début/fin, AVEC suffixe)
    base_text: str              # Texte de base (sans espaces NI suffixe) - pour la clé LOC
    file_path: str              # Chemin du fichier
    file_name: str              # Nom du fichier seul
    line_num: int               # Numéro de ligne
    line_content: str           # Contenu complet de la ligne
    pattern_name: str           # Nom du pattern qui a matché
    suggested_key: str          # Clé LOC suggérée (basée sur base_text)
    leading_spaces: int = 0     # Espaces en début
    trailing_spaces: int = 0    # Espaces en fin
    suffix: str = ""          # Suffixe détecté (" - ", " -", "...")
    replacement_code: str = ""  # Code de remplacement à utiliser
    match_context: str = ""     # Contexte extrait autour du match
    is_concat_member: bool = False  # Fait partie d'une chaîne concaténée
    concat_member_index: int = 0    # Index dans la concaténation (0, 1, 2...)
    concat_total_members: int = 1   # Nombre total de membres
    # Position du guillemet ouvrant dans line_content (ligne sans son
    # indentation) ; None si inconnue (bloc multi-ligne). Permet à l'Applicator
    # de viser le bon littéral quand le même texte apparaît plusieurs fois.
    column: Optional[int] = None

    def has_spacing(self) -> bool:
        return self.leading_spaces > 0 or self.trailing_spaces > 0
    
    def has_suffix(self) -> bool:
        return len(self.suffix) > 0
    
    def spacing_emoji(self) -> str:
        """Retourne un émoji indiquant le type d'espaces."""
        if self.leading_spaces > 0 and self.trailing_spaces > 0:
            return "⬅️➡️"  # Espaces des deux côtés
        elif self.leading_spaces > 0:
            return "⬅️"    # Espaces à gauche seulement
        elif self.trailing_spaces > 0:
            return "➡️"    # Espaces à droite seulement
        return ""
    
    def suffix_emoji(self) -> str:
        """Retourne un émoji indiquant la présence d'un suffixe."""
        if self.suffix:
            return "🔚"  # Suffixe présent
        return ""
    
    def concat_emoji(self) -> str:
        """Retourne un émoji indiquant une chaîne concaténée."""
        if self.is_concat_member:
            return "🔗"
        return ""


@dataclass
class ExtractionStats:
    """Statistiques d'extraction."""
    files_processed: int = 0
    files_with_strings: int = 0
    total_strings: int = 0
    unique_strings: int = 0
    log_lines_ignored: int = 0
    technical_ignored: int = 0
    strings_with_spacing: int = 0
    strings_with_suffix: int = 0
    concatenated_lines: int = 0     # Lignes avec chaînes concaténées
    concat_members_total: int = 0   # Total des membres de concaténation
    patterns_found: Dict[str, int] = field(default_factory=dict)
