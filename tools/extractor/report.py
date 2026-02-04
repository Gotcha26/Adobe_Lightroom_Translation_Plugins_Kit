#!/usr/bin/env python3
"""
Nom du fichier : report.py

Dépendances : .models

Description :
Génération des rapports détaillés d'extraction. Classe ReportGenerator pour créer des rapports
texte avec statistiques, légende des émojis, détails par fichier et chaînes avec espaces/suffixes.

Usage CLI :
    Non pourvu

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.i18n import _

from .models import ExtractedString, ExtractionStats


class ReportGenerator:
    """Génère les rapports détaillés d'extraction."""

    def __init__(self, plugin_path: str, prefix: str, stats: ExtractionStats):
        self.plugin_path = plugin_path
        self.prefix = prefix
        self.stats = stats

    def generate_report(self, extracted: List[ExtractedString], spacing_metadata: Dict[str, Dict],
                       output_path: str):
        """Génère le rapport détaillé pour remplacement."""
        # Grouper par fichier
        by_file: Dict[str, List[ExtractedString]] = defaultdict(list)
        for entry in extracted:
            by_file[entry.file_path].append(entry)

        with open(output_path, 'w', encoding='utf-8') as f:
            # En-tête
            f.write("=" * 80 + "\n")
            f.write("RAPPORT D'EXTRACTION DES CHAÎNES LOCALISABLES\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Plugin: {self.plugin_path}\n")
            f.write(f"Préfixe: {self.prefix}\n\n")

            # Légende des émojis
            f.write("LÉGENDE:\n")
            f.write("  ⬅️   = Espace(s) en DÉBUT de chaîne\n")
            f.write("  ➡️   = Espace(s) en FIN de chaîne\n")
            f.write("  ⬅️➡️ = Espaces des DEUX côtés\n")
            f.write("  🔚  = Suffixe détecté (\" - \", \" -\", \"...\")\n")
            f.write("  🔗  = Membre d'une chaîne concaténée\n\n")

            # Statistiques
            f.write("STATISTIQUES\n")
            f.write("-" * 80 + "\n")
            f.write(f"Fichiers analysés          : {self.stats.files_processed}\n")
            f.write(f"Fichiers avec chaînes      : {self.stats.files_with_strings}\n")
            f.write(f"Total chaînes trouvées     : {self.stats.total_strings}\n")
            f.write(f"Clés uniques               : {self.stats.unique_strings}\n")
            f.write(f"Lignes de log ignorées     : {self.stats.log_lines_ignored}\n")
            f.write(f"Chaînes techniques ignorées: {self.stats.technical_ignored}\n")
            f.write(f"Chaînes avec espaces       : {self.stats.strings_with_spacing}\n")
            f.write(f"Chaînes avec suffixes      : {self.stats.strings_with_suffix}\n")
            f.write(f"Lignes concaténées         : {self.stats.concatenated_lines}\n")
            f.write(f"Membres de concaténation   : {self.stats.concat_members_total}\n")

            # Compter les clés existantes
            existing_loc_count = sum(1 for e in extracted if e.pattern_name == "existing_loc")
            f.write(f"Clés LOC existantes        : {existing_loc_count} (déjà localisées, non modifiées)\n\n")

            # Patterns détectés
            f.write("PATTERNS DÉTECTÉS\n")
            f.write("-" * 80 + "\n")
            for pattern, count in sorted(self.stats.patterns_found.items(), key=lambda x: -x[1]):
                f.write(f"  {pattern:25} : {count}\n")
            f.write("\n")

            # Section des clés LOC existantes (pour information)
            existing_entries = [e for e in extracted if e.pattern_name == "existing_loc"]
            if existing_entries:
                f.write("=" * 80 + "\n")
                f.write("CLÉS LOC EXISTANTES (déjà localisées - incluses dans PluginStrings.txt)\n")
                f.write("=" * 80 + "\n\n")
                for entry in existing_entries:
                    f.write(f"  🔒 {entry.file_path}:{entry.line_num}\n")
                    f.write(f"     Clé    : {entry.suggested_key}\n")
                    f.write(f"     Valeur : {entry.base_text}\n\n")
                f.write("\n")

            # Détail par fichier (pour remplacement)
            f.write("=" * 80 + "\n")
            f.write("DÉTAIL PAR FICHIER (pour remplacement)\n")
            f.write("=" * 80 + "\n")

            for file_path in sorted(by_file.keys()):
                entries = by_file[file_path]
                unique_count = len(set(e.base_text for e in entries))

                f.write(f"\n{'-' * 80}\n")
                f.write(f"Fichier: {file_path}\n")
                f.write(f"Chaînes: {len(entries)} ({unique_count} clés uniques)\n")
                f.write(f"{'-' * 80}\n\n")

                # Grouper par numéro de ligne pour afficher les concaténations ensemble
                by_line: Dict[int, List[ExtractedString]] = defaultdict(list)
                for entry in entries:
                    by_line[entry.line_num].append(entry)

                for line_num in sorted(by_line.keys()):
                    line_entries = by_line[line_num]
                    first_entry = line_entries[0]

                    # Afficher l'en-tête de la ligne
                    if first_entry.is_concat_member and len(line_entries) > 1:
                        f.write(f"  [Ligne {line_num}] Pattern: {first_entry.pattern_name} 🔗 CHAÎNE CONCATÉNÉE ({len(line_entries)} membres)\n")
                        f.write(f"  LIGNE    : {first_entry.line_content[:100]}\n")

                        # Afficher chaque membre
                        for idx, entry in enumerate(line_entries, 1):
                            markers = self._get_markers(entry)
                            f.write(f"\n  MEMBRE {idx} : \"{entry.original_text}\"{markers}\n")
                            f.write(f"    BASE   : \"{entry.base_text}\"\n")
                            f.write(f"    CLÉ    : {entry.suggested_key}\n")
                            if entry.has_spacing():
                                f.write(f"    ESPACES: {entry.leading_spaces} début, {entry.trailing_spaces} fin\n")
                            if entry.has_suffix():
                                f.write(f"    SUFFIXE: \"{entry.suffix}\"\n")

                        f.write("\n")
                    else:
                        # Chaîne simple (non concaténée)
                        for entry in line_entries:
                            markers = self._get_markers(entry)
                            f.write(f"  [Ligne {line_num}] Pattern: {entry.pattern_name}{markers}\n")
                            f.write(f"  CHERCHER : \"{entry.original_text}\"\n")
                            f.write(f"  BASE     : \"{entry.base_text}\"\n")
                            f.write(f"  CLÉ      : {entry.suggested_key}\n")
                            if entry.has_spacing():
                                f.write(f"  ESPACES  : {entry.leading_spaces} début, {entry.trailing_spaces} fin\n")
                            if entry.has_suffix():
                                f.write(f"  SUFFIXE  : \"{entry.suffix}\"\n")
                            f.write(f"  REMPLACER: {entry.replacement_code}\n\n")

            # Chaînes avec espaces ou suffixes (résumé)
            if spacing_metadata:
                f.write("=" * 80 + "\n")
                f.write("CHAÎNES AVEC ESPACES OU SUFFIXES\n")
                f.write("=" * 80 + "\n\n")
                f.write("Ces chaînes nécessitent une réinjection des espaces/suffixes.\n\n")

                for i, (key, meta) in enumerate(sorted(spacing_metadata.items()), 1):
                    emojis = self._get_spacing_emojis(meta)
                    emoji_str = "".join(emojis)

                    f.write(f"  {i}. {emoji_str} {key}\n")
                    f.write(f"     Original: \"{meta['original_text']}\"\n")
                    f.write(f"     Base: \"{meta.get('base_text', meta['clean_text'])}\"\n")
                    if meta['leading_spaces'] > 0 or meta['trailing_spaces'] > 0:
                        f.write(f"     Espaces: {meta['leading_spaces']} début + {meta['trailing_spaces']} fin\n")
                    if meta.get('suffix'):
                        f.write(f"     Suffixe: \"{meta['suffix']}\"\n")
                    f.write(f"     Fichier: {meta['file']}:{meta['line']}\n\n")

            # Liste des clés uniques pour PluginStrings
            f.write("=" * 80 + "\n")
            f.write("LISTE DES CLÉS POUR PluginStrings.txt\n")
            f.write("=" * 80 + "\n\n")

            # Construire la liste des clés uniques
            unique_keys: Dict[str, ExtractedString] = {}
            for entry in extracted:
                if entry.suggested_key not in unique_keys:
                    unique_keys[entry.suggested_key] = entry

            f.write(f"-- {len(unique_keys)} clés uniques\n\n")

            for entry in sorted(unique_keys.values(), key=lambda e: e.suggested_key):
                markers = self._get_markers(entry)
                # Utiliser base_text (sans suffixe) pour la valeur
                f.write(f'"{entry.suggested_key}={entry.base_text}"{markers}\n')

        print(_("✓ Rapport: {path}").format(path=output_path))

    def _get_markers(self, entry: ExtractedString) -> str:
        """Retourne la chaîne de marqueurs (émojis) pour une entrée."""
        markers = []
        if entry.spacing_emoji():
            markers.append(entry.spacing_emoji())
        if entry.suffix_emoji():
            markers.append(entry.suffix_emoji())
        if entry.concat_emoji():
            markers.append(entry.concat_emoji())
        marker_str = f" -- {''.join(markers)}" if markers else ""
        return marker_str

    def _get_spacing_emojis(self, meta: Dict) -> list:
        """Retourne les émojis pour les espaces et suffixes."""
        emojis = []
        if meta['leading_spaces'] > 0 and meta['trailing_spaces'] > 0:
            emojis.append("⬅️➡️")
        elif meta['leading_spaces'] > 0:
            emojis.append("⬅️")
        elif meta['trailing_spaces'] > 0:
            emojis.append("➡️")
        if meta.get('suffix'):
            emojis.append("🔚")
        return emojis
