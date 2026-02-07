#!/usr/bin/env python3
"""
Nom du fichier : export_untranslated_chains.py

Dépendances : core.colors

Description :
Extrait les chaînes fuzzy et non traduites d'un fichier .po et les exporte dans un
fichier texte formaté pour traduction par un LLM (Claude, GPT, etc.).
Génère tmp_chains_tofrom_translation.txt avec instructions intégrées.

Le format exporté préserve msgid et permet la réimportation via import_translated_chains.py.

Usage CLI :
    python i18n/export_untranslated_chains.py fr              # Export pour français
    python i18n/export_untranslated_chains.py de --all        # Fuzzy + non traduites
    python i18n/export_untranslated_chains.py en --fuzzy-only # Seulement fuzzy
    python i18n/export_untranslated_chains.py es --untranslated-only # Seulement non traduites

Date : 2026-02-07
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.colors import Colors

c = Colors()


class POExporter:
    """Exporte les chaînes à traduire depuis un fichier .po."""

    def __init__(self):
        self.entries = []

    def parse_po_file(self, filepath: Path) -> bool:
        """Parse un fichier .po et collecte les entrées."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"{c.ERROR}[X] Impossible de lire {filepath}: {e}{c.RESET}")
            return False

        self.entries = []
        lines = content.split('\n')
        i = 0
        current_entry = {
            'msgid': '',
            'msgstr': '',
            'fuzzy': False,
            'line': 0,
            'comments': []
        }
        in_msgid = False
        in_msgstr = False

        while i < len(lines):
            line = lines[i]

            # Commentaires
            if line.startswith('#'):
                if 'fuzzy' in line:
                    current_entry['fuzzy'] = True
                elif not line.startswith('#,'):
                    current_entry['comments'].append(line)

            # Début d'un msgid
            if line.startswith('msgid '):
                in_msgid = True
                in_msgstr = False
                current_entry['msgid'] = self._extract_string(line[6:])
                current_entry['line'] = i + 1

            # Début d'un msgstr
            elif line.startswith('msgstr '):
                in_msgid = False
                in_msgstr = True
                current_entry['msgstr'] = self._extract_string(line[7:])

            # Continuation
            elif line.strip().startswith('"') and line.strip().endswith('"'):
                continuation = self._extract_string(line)
                if in_msgid:
                    current_entry['msgid'] += continuation
                elif in_msgstr:
                    current_entry['msgstr'] += continuation

            # Ligne vide = fin d'entrée
            elif not line.strip():
                if current_entry['msgid']:
                    self.entries.append(current_entry.copy())
                    current_entry = {'msgid': '', 'msgstr': '', 'fuzzy': False, 'line': 0, 'comments': []}
                    in_msgid = False
                    in_msgstr = False

            i += 1

        return True

    @staticmethod
    def _extract_string(s: str) -> str:
        """Extrait une chaîne entre guillemets."""
        s = s.strip()
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        # Désechapper
        s = s.replace('\\n', '\n')
        s = s.replace('\\r', '\r')
        s = s.replace('\\t', '\t')
        s = s.replace('\\"', '"')
        s = s.replace('\\\\', '\\')
        return s

    def get_fuzzy_entries(self) -> List[Dict]:
        """Retourne les entrées fuzzy."""
        return [e for e in self.entries if e['fuzzy'] and e['msgid']]

    def get_untranslated_entries(self) -> List[Dict]:
        """Retourne les entrées non traduites."""
        return [e for e in self.entries if not e['msgstr'] and e['msgid']]


def escape_for_po(s: str) -> str:
    """Échappe une chaîne pour format .po."""
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '\\r')
    s = s.replace('\t', '\\t')
    return s


def export_entries(entries: List[Dict], output_file: Path, lang_code: str, export_type: str):
    """Exporte les entrées dans un fichier texte formaté."""

    instructions = f"""════════════════════════════════════════════════════════════════════════════════
INSTRUCTIONS POUR IA - TRADUCTION FICHIER .PO ({lang_code.upper()})
════════════════════════════════════════════════════════════════════════════════

CONTEXTE :
----------
Ce fichier contient des chaînes de traduction extraites d'un fichier .po de
Lightroom Classic pour la langue '{lang_code}'.

Type d'export : {export_type}

TÂCHE :
-------
1. Traduire UNIQUEMENT le contenu de la ligne "msgstr" pour chaque bloc
2. NE PAS modifier les lignes "msgid" (texte source)
3. Respecter les codes de formatage : {{1}}, {{2}}, ^1, ^2, etc.
4. Préserver les retours à la ligne (\\n) et caractères spéciaux
5. Ne pas traduire les termes techniques Lightroom (ex: "Publish Service", "Smart Collection")

FORMAT À RESPECTER :
--------------------
Chaque bloc suit cette structure :

    ┌─────────────────────────────────────────┐
    │ msgid "Texte source en anglais"        │  ← NE PAS MODIFIER
    │ msgstr "Votre traduction ici"          │  ← À TRADUIRE
    └─────────────────────────────────────────┘

IMPORTANT :
-----------
- Ne pas supprimer les lignes vides entre les blocs
- Ne pas ajouter de commentaires personnels
- Garder exactement la même structure
- Si incertain sur une traduction, laisser msgstr vide

APRÈS TRADUCTION :
------------------
Sauvegarder ce fichier et utiliser le script :
    python i18n/import_translated_chains.py {lang_code}

════════════════════════════════════════════════════════════════════════════════
DÉBUT DES CHAÎNES À TRADUIRE ({len(entries)} entrées)
════════════════════════════════════════════════════════════════════════════════

"""

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(instructions)

            for idx, entry in enumerate(entries, 1):
                # Séparateur visuel
                f.write(f"\n{'─' * 80}\n")
                f.write(f"ENTRÉE {idx}/{len(entries)}\n")
                f.write(f"{'─' * 80}\n\n")

                # msgid (échappé pour .po)
                msgid_escaped = escape_for_po(entry['msgid'])
                f.write(f'msgid "{msgid_escaped}"\n')

                # msgstr (prérempli si fuzzy, vide sinon)
                if entry['fuzzy'] and entry['msgstr']:
                    msgstr_escaped = escape_for_po(entry['msgstr'])
                    f.write(f'msgstr "{msgstr_escaped}"\n')
                else:
                    f.write(f'msgstr ""\n')

                f.write("\n")

            # Pied de page
            f.write(f"\n{'═' * 80}\n")
            f.write(f"FIN DU FICHIER - {len(entries)} chaînes à traduire\n")
            f.write(f"{'═' * 80}\n")

        return True

    except Exception as e:
        print(f"{c.ERROR}[X] Erreur lors de l'export : {e}{c.RESET}")
        return False


def main():
    """Point d'entrée principal."""
    print()
    print(c.box_header("EXPORT DES CHAÎNES À TRADUIRE"))

    # Récupérer les arguments
    if len(sys.argv) < 2:
        print()
        print(f"{c.ERROR}[X] Usage: python i18n/export_untranslated_chains.py <lang> [--all|--fuzzy-only|--untranslated-only]{c.RESET}")
        print()
        print(f"{c.INFO}Exemples:{c.RESET}")
        print(f"  python i18n/export_untranslated_chains.py fr")
        print(f"  python i18n/export_untranslated_chains.py de --all")
        print(f"  python i18n/export_untranslated_chains.py en --fuzzy-only")
        print()
        return 1

    lang_code = sys.argv[1].lower()

    # Options
    export_fuzzy = True
    export_untranslated = True

    if len(sys.argv) > 2:
        option = sys.argv[2]
        if option == '--fuzzy-only':
            export_untranslated = False
        elif option == '--untranslated-only':
            export_fuzzy = False
        elif option != '--all':
            print(f"{c.WARNING}⚠️  Option inconnue: {option}, export tout par défaut{c.RESET}")

    # Vérifier le fichier .po
    locale_dir = Path(__file__).parent.parent / "locale"
    po_file = locale_dir / lang_code / "LC_MESSAGES" / "messages.po"

    if not po_file.exists():
        print()
        print(f"{c.ERROR}[X] Fichier .po introuvable pour la langue '{lang_code}'{c.RESET}")
        print(f"    Chemin attendu: {po_file}")
        return 1

    print()
    print(c.config_line("Langue", lang_code.upper()))
    print(c.config_line("Fichier source", str(po_file.name)))
    print()

    # Parser le fichier
    exporter = POExporter()
    print(c.info("📖 Lecture du fichier .po..."))

    if not exporter.parse_po_file(po_file):
        return 1

    # Collecter les entrées à exporter
    entries_to_export = []

    if export_fuzzy:
        fuzzy = exporter.get_fuzzy_entries()
        entries_to_export.extend(fuzzy)
        print(c.config_line("Chaînes fuzzy", f"{c.WARNING}{len(fuzzy)}{c.RESET}"))

    if export_untranslated:
        untranslated = exporter.get_untranslated_entries()
        entries_to_export.extend(untranslated)
        print(c.config_line("Chaînes non traduites", f"{c.ERROR}{len(untranslated)}{c.RESET}"))

    if not entries_to_export:
        print()
        print(f"{c.OK}✓ Aucune chaîne à exporter ! Traduction complète.{c.RESET}")
        return 0

    # Déterminer le type d'export pour les instructions
    if export_fuzzy and export_untranslated:
        export_type = "Chaînes fuzzy + non traduites"
    elif export_fuzzy:
        export_type = "Chaînes fuzzy uniquement"
    else:
        export_type = "Chaînes non traduites uniquement"

    # Export
    output_file = Path(__file__).parent.parent / "tmp_chains_tofrom_translation.txt"

    print()
    print(c.info(f"💾 Export de {len(entries_to_export)} chaînes..."))

    if export_entries(entries_to_export, output_file, lang_code, export_type):
        print()
        print(c.separator("─", 70))
        print(f"{c.OK}✓ Export terminé avec succès !{c.RESET}")
        print(c.separator("─", 70))
        print()
        print(c.config_line("Fichier généré", str(output_file.name)))
        print(c.config_line("Chaînes exportées", f"{len(entries_to_export)}"))
        print()
        print(c.info("📝 Prochaines étapes :"))
        print(f"   1. Ouvrir {output_file.name}")
        print(f"   2. Faire traduire par Claude/GPT (instructions incluses)")
        print(f"   3. Lancer : python i18n/import_translated_chains.py {lang_code}")
        print()

        # Proposition d'import une fois traduit
        print(c.separator("─", 70))
        print(c.info("📥 Une fois les traductions complétées..."))
        print()

        response = input(f"{c.INFO}Lancer l'import maintenant ? (o/n): {c.RESET}").strip().lower()

        if response in ['o', 'oui', 'y', 'yes']:
            print()
            print(c.info("🚀 Lancement de l'import..."))
            print()
            import subprocess
            result = subprocess.run(
                [sys.executable, str(Path(__file__).parent / "import_translated_chains.py"), lang_code],
                cwd=Path(__file__).parent.parent
            )
            return result.returncode

        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
