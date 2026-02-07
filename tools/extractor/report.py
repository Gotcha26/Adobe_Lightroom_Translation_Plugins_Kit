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

    def __init__(self, plugin_path: str, prefix: str, stats: ExtractionStats, silent: bool = False):
        self.plugin_path = plugin_path
        self.prefix = prefix
        self.stats = stats
        self.silent = silent

    @staticmethod
    def _shorten_path(full_path: str, plugin_path: str) -> str:
        """Raccourcit le chemin en chemin relatif au plugin."""
        if plugin_path and plugin_path in full_path:
            relative = full_path.replace(plugin_path, "").lstrip(os.sep)
            # Normaliser les slashes en forward slashes
            relative = relative.replace("\\", "/")
            return "<plugin>/{relative}".format(relative=relative)
        return full_path

    def generate_report(self, extracted: List[ExtractedString], spacing_metadata: Dict[str, Dict],
                       output_path: str):
        """Génère le rapport détaillé pour remplacement."""
        # Grouper par fichier
        by_file: Dict[str, List[ExtractedString]] = defaultdict(list)
        for entry in extracted:
            by_file[entry.file_path].append(entry)

        from core.i18n import debug_i18n_context
        with debug_i18n_context(), open(output_path, 'w', encoding='utf-8') as f:
            # En-tête
            f.write("=" * 80 + "\n")
            f.write(_("RAPPORT D'EXTRACTION DES CHAÎNES LOCALISABLES\n"))
            f.write("=" * 80 + "\n\n")

            f.write(_("Date: {var0}\n").format(var0=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            f.write(_("Plugin: {var0}\n").format(var0=self.plugin_path))
            f.write(_("Préfixe: {var0}\n\n").format(var0=self.prefix))

            # Légende des émojis
            f.write(_("LÉGENDE:\n"))
            f.write(_("  ⬅️   = Espace(s) en DÉBUT de chaîne\n"))
            f.write(_("  ➡️   = Espace(s) en FIN de chaîne\n"))
            f.write(_("  ⬅️➡️ = Espaces des DEUX côtés\n"))
            f.write(_('  🔚  = Suffixe détecté (" - ", " -", "...")\n'))
            f.write(_("  🔗  = Membre d'une chaîne concaténée\n\n"))

            # Statistiques
            f.write(_("STATISTIQUES\n"))
            f.write("-" * 80 + "\n")
            f.write(_("Fichiers analysés          : {var0}\n").format(var0=self.stats.files_processed))
            f.write(_("Fichiers avec chaînes      : {var0}\n").format(var0=self.stats.files_with_strings))
            f.write(_("Total chaînes trouvées     : {var0}\n").format(var0=self.stats.total_strings))
            f.write(_("Clés uniques               : {var0}\n").format(var0=self.stats.unique_strings))
            f.write(_("Lignes de log ignorées     : {var0}\n").format(var0=self.stats.log_lines_ignored))
            f.write(_("Chaînes techniques ignorées: {var0}\n").format(var0=self.stats.technical_ignored))
            f.write(_("Chaînes avec espaces       : {var0}\n").format(var0=self.stats.strings_with_spacing))
            f.write(_("Chaînes avec suffixes      : {var0}\n").format(var0=self.stats.strings_with_suffix))
            f.write(_("Lignes concaténées         : {var0}\n").format(var0=self.stats.concatenated_lines))
            f.write(_("Membres de concaténation   : {var0}\n").format(var0=self.stats.concat_members_total))

            # Compter les clés existantes
            existing_loc_count = sum(1 for e in extracted if e.pattern_name == "existing_loc")
            f.write(_("Clés LOC existantes        : {existing_loc_count} (déjà localisées, non modifiées)\n\n").format(existing_loc_count=existing_loc_count))

            # Patterns détectés
            f.write(_("PATTERNS DÉTECTÉS\n"))
            f.write("-" * 80 + "\n")
            for pattern, count in sorted(self.stats.patterns_found.items(), key=lambda x: -x[1]):
                f.write(f"  {pattern:25} : {count}\n")
            f.write("\n")

            # Section des clés LOC existantes (pour information)
            existing_entries = [e for e in extracted if e.pattern_name == "existing_loc"]
            if existing_entries:
                f.write("=" * 80 + "\n")
                f.write(_("CLÉS LOC EXISTANTES (déjà localisées - incluses dans TranslatedStrings_xx.txt)\n"))
                f.write("=" * 80 + "\n\n")
                for entry in existing_entries:
                    f.write(f"  🔒 {entry.file_path}:{entry.line_num}\n")
                    f.write(_("     Clé    : {var0}\n").format(var0=entry.suggested_key))
                    f.write(_("     Valeur : {var0}\n\n").format(var0=entry.base_text))
                f.write("\n")

            # Détail par fichier (pour remplacement)
            # → Ne pas tenir compte du champs vide "REMPLACER" si vide !
            f.write("=" * 80 + "\n")
            f.write(_('DÉTAIL PAR FICHIER (pour remplacement) → Ne pas tenir compte du champs "REMPLACER" si vide !\n'))
            f.write("=" * 80 + "\n")

            for file_path in sorted(by_file.keys()):
                entries = by_file[file_path]
                unique_count = len(set(e.base_text for e in entries))

                f.write(f"\n{'-' * 80}\n")
                f.write(_("Fichier: {file_path}\n").format(file_path=file_path))
                f.write(_("Chaînes: {var0} ({unique_count} clés uniques)\n").format(var0=len(entries), unique_count=unique_count))
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
                        f.write(_("  [Ligne {line_num}] Pattern: {var1} 🔗 CHAÎNE CONCATÉNÉE ({var2} membres)\n").format(line_num=line_num, var1=first_entry.pattern_name, var2=len(line_entries)))
                        f.write(_("  LIGNE    : {var0}\n").format(var0=first_entry.line_content[:100]))

                        # Afficher chaque membre
                        for idx, entry in enumerate(line_entries, 1):
                            markers = self._get_markers(entry)
                            f.write(_('\n  MEMBRE {idx} : "{original_text}"{markers}\n').format(idx=idx, original_text=entry.original_text, markers=markers))
                            f.write(_('    BASE   : "{var0}"\n').format(var0=entry.base_text))
                            f.write(_("    CLÉ    : {var0}\n").format(var0=entry.suggested_key))
                            if entry.has_spacing():
                                f.write(_("    ESPACES: {var0} début, {var1} fin\n").format(var0=entry.leading_spaces, var1=entry.trailing_spaces))
                            if entry.has_suffix():
                                f.write(_('    SUFFIXE: "{var0}"\n').format(var0=entry.suffix))

                        f.write("\n")
                    else:
                        # Chaîne simple (non concaténée)
                        for entry in line_entries:
                            markers = self._get_markers(entry)
                            f.write(_("  [Ligne {line_num}] Pattern: {var1}{markers}\n").format(line_num=line_num, var1=entry.pattern_name, markers=markers))
                            f.write(_('  CHERCHER : "{var0}"\n').format(var0=entry.original_text))
                            f.write(_('  BASE     : "{var0}"\n').format(var0=entry.base_text))
                            f.write(_("  CLÉ      : {var0}\n").format(var0=entry.suggested_key))
                            if entry.has_spacing():
                                f.write(_("  ESPACES  : {var0} début, {var1} fin\n").format(var0=entry.leading_spaces, var1=entry.trailing_spaces))
                            if entry.has_suffix():
                                f.write(_('  SUFFIXE  : "{var0}"\n').format(var0=entry.suffix))
                            f.write(_("  REMPLACER: {var0}\n\n").format(var0=entry.replacement_code))

            # Chaînes avec espaces ou suffixes (résumé)
            if spacing_metadata:
                f.write("=" * 80 + "\n")
                f.write(_("CHAÎNES AVEC ESPACES OU SUFFIXES\n"))
                f.write("=" * 80 + "\n\n")
                f.write(_("Ces chaînes nécessitent une réinjection des espaces/suffixes.\n\n"))

                for i, (key, meta) in enumerate(sorted(spacing_metadata.items()), 1):
                    emojis = self._get_spacing_emojis(meta)
                    emoji_str = "".join(emojis)

                    f.write(f"  {i}. {emoji_str} {key}\n")
                    f.write(_('     Original: "{var0}"\n').format(var0=meta['original_text']))
                    f.write(_('     Base: "{var0}"\n').format(var0=meta.get('base_text', meta['clean_text'])))
                    if meta['leading_spaces'] > 0 or meta['trailing_spaces'] > 0:
                        f.write(_("     Espaces: {var0} début + {var1} fin\n").format(var0=meta['leading_spaces'], var1=meta['trailing_spaces']))
                    if meta.get('suffix'):
                        f.write(_('     Suffixe: "{var0}"\n').format(var0=meta['suffix']))
                    f.write(_("     Fichier: {var0}:{var1}\n\n").format(var0=meta['file'], var1=meta['line']))

            # Liste des clés uniques pour PluginStrings
            f.write("=" * 80 + "\n")
            f.write(_("LISTE DES CLÉS POUR TranslatedStrings_xx.txt\n"))
            f.write("=" * 80 + "\n\n")

            # Construire la liste des clés uniques
            unique_keys: Dict[str, ExtractedString] = {}
            for entry in extracted:
                if entry.suggested_key not in unique_keys:
                    unique_keys[entry.suggested_key] = entry

            f.write(_("-- {var0} clés uniques\n\n").format(var0=len(unique_keys)))

            for entry in sorted(unique_keys.values(), key=lambda e: e.suggested_key):
                markers = self._get_markers(entry)
                # Utiliser base_text (sans suffixe) pour la valeur
                f.write(f'"{entry.suggested_key}={entry.base_text}"{markers}\n')

        short_path = self._shorten_path(output_path, self.plugin_path)
        if not self.silent:
            print(_("✓ Rapport               : {path}").format(path=short_path))

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
