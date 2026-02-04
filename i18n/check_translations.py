#!/usr/bin/env python3
"""
check_translations.py - Vérifier rapidement l'état des traductions

Affiche:
- Nombre de chaînes traduites vs non traduites
- Liste des chaînes non traduites (msgstr vide)
- Chaînes marquées fuzzy (à revoir)
- Statistiques par langue

Usage:
    python i18n/check_translations.py           # Toutes les langues
    python i18n/check_translations.py en        # Anglais
    python i18n/check_translations.py fr        # Français
    python i18n/check_translations.py fr -v     # Verbose (affiche les détails)

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-02-04
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.colors import Colors

c = Colors()


class POChecker:
    """Vérifie l'état des traductions."""

    def __init__(self):
        self.entries = []
        self.translated = 0
        self.untranslated = 0
        self.fuzzy = 0

    def parse_po_file(self, filepath: Path) -> bool:
        """Parse un fichier .po et collecte les statistiques."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"{c.ERROR}[X] Impossible de lire {filepath}: {e}{c.RESET}")
            return False

        self.entries = []
        self.translated = 0
        self.untranslated = 0
        self.fuzzy = 0

        lines = content.split('\n')
        i = 0
        current_entry = {
            'msgid': '',
            'msgstr': '',
            'fuzzy': False,
            'line': 0
        }
        in_msgid = False
        in_msgstr = False

        while i < len(lines):
            line = lines[i]

            # Déterminer si fuzzy
            if line.startswith('#,') and 'fuzzy' in line:
                current_entry['fuzzy'] = True

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
                    if current_entry['msgstr']:
                        self.translated += 1
                    else:
                        self.untranslated += 1
                    if current_entry['fuzzy']:
                        self.fuzzy += 1
                    current_entry = {'msgid': '', 'msgstr': '', 'fuzzy': False, 'line': 0}
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

    def get_stats(self) -> Dict:
        """Retourne les statistiques."""
        total = self.translated + self.untranslated
        percent = (self.translated / total * 100) if total > 0 else 0
        return {
            'total': total,
            'translated': self.translated,
            'untranslated': self.untranslated,
            'fuzzy': self.fuzzy,
            'percent': percent
        }

    def get_untranslated(self) -> List[Dict]:
        """Retourne la liste des chaînes non traduites."""
        return [e for e in self.entries if not e['msgstr'] and e['msgid']]

    def get_fuzzy(self) -> List[Dict]:
        """Retourne la liste des chaînes fuzzy."""
        return [e for e in self.entries if e['fuzzy'] and e['msgid']]


def print_stats(lang_code: str, checker: POChecker, verbose: bool = False):
    """Affiche les statistiques pour une langue."""
    stats = checker.get_stats()

    print()
    print(c.separator("─", 70))
    print(c.header(f"LANGUE: {lang_code.upper()}"))
    print(c.separator("─", 70))
    print()

    # Barre de progression
    total = stats['total']
    translated = stats['translated']
    untranslated = stats['untranslated']
    percent = stats['percent']

    bar_length = 40
    filled = int(bar_length * translated / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_length - filled)

    color = c.OK if percent == 100 else c.WARNING if percent >= 75 else c.ERROR
    print(f"{color}{bar}{c.RESET}")
    print()

    print(c.config_line("Total chaînes",     f"{total}"))
    print(c.config_line("Traduites",         f"{c.OK}{translated}{c.RESET} ({percent:.1f}%)"))
    print(c.config_line("Non traduites",     f"{c.ERROR}{untranslated}{c.RESET}"))
    if stats['fuzzy'] > 0:
        print(c.config_line("Marquées fuzzy",    f"{c.WARNING}{stats['fuzzy']}{c.RESET}"))

    # Chaînes fuzzy
    if stats['fuzzy'] > 0 and verbose:
        print()
        print(c.warning("⚠️  CHAÎNES MARQUÉES FUZZY (à revoir) :"))
        for entry in checker.get_fuzzy()[:10]:  # Afficher max 10
            preview = entry['msgid'][:60]
            if len(entry['msgid']) > 60:
                preview += "..."
            print(f"   {c.VALUE}{preview}{c.RESET}")
        if len(checker.get_fuzzy()) > 10:
            print(f"   ... et {len(checker.get_fuzzy()) - 10} autres")

    # Chaînes non traduites
    if untranslated > 0 and verbose:
        print()
        print(c.error("❌ CHAÎNES NON TRADUITES :"))
        for entry in checker.get_untranslated()[:10]:  # Afficher max 10
            preview = entry['msgid'][:60]
            if len(entry['msgid']) > 60:
                preview += "..."
            print(f"   Ligne {entry['line']}: {c.VALUE}{preview}{c.RESET}")
        if len(checker.get_untranslated()) > 10:
            print(f"   ... et {len(checker.get_untranslated()) - 10} autres")

    print()


def main():
    """Point d'entrée principal."""
    print()
    print(c.box_header("VÉRIFICATION DE L'ÉTAT DES TRADUCTIONS"))

    # Récupérer les arguments
    target_lang = None
    verbose = False

    if len(sys.argv) > 1:
        target_lang = sys.argv[1].lower()
        if len(sys.argv) > 2 and sys.argv[2] == '-v':
            verbose = True

    locale_dir = Path(__file__).parent.parent / "locale"

    if not locale_dir.exists():
        print()
        print(f"{c.ERROR}[X] Dossier locale/ introuvable{c.RESET}")
        return 1

    # Trouver les langues
    languages = []

    for lang_dir in sorted(locale_dir.iterdir()):
        if not lang_dir.is_dir() or lang_dir.name in ['__pycache__']:
            continue

        lang_code = lang_dir.name
        if target_lang and lang_code != target_lang:
            continue

        po_file = lang_dir / "LC_MESSAGES" / "messages.po"
        if po_file.exists():
            languages.append((lang_code, po_file))

    if not languages:
        print()
        if target_lang:
            print(f"{c.ERROR}[X] Langue non trouvée: {target_lang}{c.RESET}")
        else:
            print(f"{c.ERROR}[X] Aucune traduction trouvée{c.RESET}")
        return 1

    # Analyser chaque langue
    total_translated = 0
    total_untranslated = 0

    for lang_code, po_file in languages:
        checker = POChecker()
        if checker.parse_po_file(po_file):
            print_stats(lang_code, checker, verbose)
            total_translated += checker.translated
            total_untranslated += checker.untranslated

    # Résumé global
    if len(languages) > 1:
        print(c.separator("═", 70))
        print(c.header("RÉSUMÉ GLOBAL"))
        print(c.separator("═", 70))
        print()
        total = total_translated + total_untranslated
        percent = (total_translated / total * 100) if total > 0 else 0
        print(c.config_line("Total chaînes",     f"{total}"))
        print(c.config_line("Total traduites",   f"{c.OK}{total_translated}{c.RESET} ({percent:.1f}%)"))
        print(c.config_line("Total non traduites", f"{c.ERROR}{total_untranslated}{c.RESET}"))
        print()

    if verbose:
        print()
        print(c.info("💡 Conseil: Utilisez Poedit pour traduire rapidement"))
        print(f"   https://poedit.net/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
