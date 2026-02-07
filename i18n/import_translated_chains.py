#!/usr/bin/env python3
"""
Nom du fichier : import_translated_chains.py

Dépendances : core.colors

Description :
Importe les traductions depuis tmp_chains_tofrom_translation.txt et met à jour
le fichier .po correspondant. Recherche les correspondances via msgid, remplace
msgstr, et retire les marqueurs fuzzy pour les chaînes traduites.

Crée une sauvegarde automatique avant modification (.po.backup).
Propose de supprimer tmp_chains_tofrom_translation.txt après import.

Usage CLI :
    python i18n/import_translated_chains.py fr              # Import pour français
    python i18n/import_translated_chains.py de --no-backup  # Sans sauvegarde
    python i18n/import_translated_chains.py en --keep-tmp   # Garder le fichier tmp

Date : 2026-02-07
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.colors import Colors

c = Colors()


class POUpdater:
    """Met à jour un fichier .po avec les traductions importées."""

    def __init__(self, po_filepath: Path):
        self.po_filepath = po_filepath
        self.original_content = ""
        self.translations = []
        self.updated_count = 0
        self.fuzzy_removed_count = 0

    def load_po_file(self) -> bool:
        """Charge le contenu du fichier .po."""
        try:
            with open(self.po_filepath, 'r', encoding='utf-8') as f:
                self.original_content = f.read()
            return True
        except Exception as e:
            print(f"{c.ERROR}[X] Impossible de lire {self.po_filepath}: {e}{c.RESET}")
            return False

    def parse_translation_file(self, txt_filepath: Path) -> bool:
        """Parse le fichier de traductions exporté."""
        try:
            with open(txt_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"{c.ERROR}[X] Impossible de lire {txt_filepath}: {e}{c.RESET}")
            return False

        # Extraire les blocs msgid/msgstr
        self.translations = []

        # Pattern pour capturer les blocs
        pattern = r'msgid\s+"([^"]*)"\s*\nmsgstr\s+"([^"]*)"'
        matches = re.findall(pattern, content, re.MULTILINE)

        for msgid_escaped, msgstr_escaped in matches:
            # Désechapper
            msgid = self._unescape_string(msgid_escaped)
            msgstr = self._unescape_string(msgstr_escaped)

            # Ne garder que les traductions non vides
            if msgstr.strip():
                self.translations.append({
                    'msgid': msgid,
                    'msgstr': msgstr
                })

        return len(self.translations) > 0

    @staticmethod
    def _unescape_string(s: str) -> str:
        """Déséchappe une chaîne du format .po."""
        s = s.replace('\\n', '\n')
        s = s.replace('\\r', '\r')
        s = s.replace('\\t', '\t')
        s = s.replace('\\"', '"')
        s = s.replace('\\\\', '\\')
        return s

    @staticmethod
    def _escape_string(s: str) -> str:
        """Échappe une chaîne pour format .po."""
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        return s

    def update_po_content(self) -> str:
        """Met à jour le contenu .po avec les nouvelles traductions."""
        updated_content = self.original_content
        self.updated_count = 0
        self.fuzzy_removed_count = 0

        for trans in self.translations:
            msgid = trans['msgid']
            new_msgstr = trans['msgstr']

            # Échapper pour regex
            msgid_escaped = self._escape_string(msgid)
            new_msgstr_escaped = self._escape_string(new_msgstr)

            # Pattern pour trouver le bloc correspondant
            # On cherche msgid, et on remplace msgstr (même si vide ou existant)
            # On gère aussi le marqueur fuzzy optionnel

            # Pattern avec fuzzy optionnel
            pattern = (
                r'((?:#[^\n]*\n)*?)'  # Groupe 1: commentaires avant (optionnel)
                r'(#,\s*fuzzy\s*\n)?'  # Groupe 2: marqueur fuzzy (optionnel)
                r'(msgid\s+"' + re.escape(msgid_escaped) + r'"\s*\n)'  # Groupe 3: msgid
                r'msgstr\s+"[^"]*"'  # msgstr existant (à remplacer)
            )

            def replacer(match):
                comments = match.group(1) or ''
                fuzzy = match.group(2) or ''
                msgid_line = match.group(3)

                # Compter les actions
                if fuzzy:
                    self.fuzzy_removed_count += 1
                self.updated_count += 1

                # Retourner sans fuzzy et avec nouveau msgstr
                return f'{comments}{msgid_line}msgstr "{new_msgstr_escaped}"'

            # Appliquer le remplacement
            updated_content, count = re.subn(
                pattern,
                replacer,
                updated_content,
                count=1,  # Une seule occurrence
                flags=re.MULTILINE
            )

            if count == 0:
                print(f"{c.WARNING}⚠️  msgid non trouvé (ignoré): {msgid[:50]}...{c.RESET}")

        return updated_content

    def save_po_file(self, content: str) -> bool:
        """Sauvegarde le fichier .po mis à jour."""
        try:
            with open(self.po_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"{c.ERROR}[X] Impossible de sauvegarder {self.po_filepath}: {e}{c.RESET}")
            return False

    def create_backup(self) -> bool:
        """Crée une sauvegarde du fichier .po."""
        backup_path = Path(str(self.po_filepath) + '.backup')
        try:
            shutil.copy2(self.po_filepath, backup_path)
            print(c.config_line("Sauvegarde créée", str(backup_path.name)))
            return True
        except Exception as e:
            print(f"{c.ERROR}[X] Impossible de créer la sauvegarde: {e}{c.RESET}")
            return False


def ask_yes_no(question: str) -> bool:
    """Demande une confirmation oui/non."""
    while True:
        response = input(f"{c.INFO}{question} (o/n): {c.RESET}").strip().lower()
        if response in ['o', 'oui', 'y', 'yes']:
            return True
        elif response in ['n', 'non', 'no']:
            return False
        else:
            print(f"{c.WARNING}Répondre par 'o' ou 'n'{c.RESET}")


def main():
    """Point d'entrée principal."""
    print()
    print(c.box_header("IMPORT DES TRADUCTIONS"))

    # Définir txt_file
    txt_file = Path(__file__).parent.parent / "tmp_chains_tofrom_translation.txt"

    # Mode interactif si aucun argument
    if len(sys.argv) < 2:
        print()
        print(c.info("🔍 Recherche du fichier de traductions..."))

        if not txt_file.exists():
            print()
            print(f"{c.ERROR}[X] Fichier tmp_chains_tofrom_translation.txt introuvable{c.RESET}")
            print()
            print(f"{c.INFO}💡 Lancez d'abord: python i18n/export_untranslated_chains.py <lang>{c.RESET}")
            return 1

        # Détecter la langue depuis le fichier
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # Lire le début

            # Chercher la langue dans les instructions
            match = re.search(r"python i18n/import_translated_chains\.py (\w+)", content)
            if match:
                lang_code = match.group(1)
                print(f"{c.OK}✓ Langue détectée: {lang_code.upper()}{c.RESET}")
            else:
                print()
                print(f"{c.WARNING}⚠️  Impossible de détecter la langue{c.RESET}")
                lang_code = input(f"{c.INFO}Entrez le code langue (ex: fr, en, de): {c.RESET}").strip().lower()

                if not lang_code:
                    print(f"{c.ERROR}[X] Code langue requis{c.RESET}")
                    return 1
        except Exception as e:
            print(f"{c.ERROR}[X] Erreur lecture fichier: {e}{c.RESET}")
            return 1

        # Options par défaut en mode interactif
        create_backup = True
        keep_tmp = False

    else:
        # Mode CLI classique
        lang_code = sys.argv[1].lower()
        create_backup = '--no-backup' not in sys.argv
        keep_tmp = '--keep-tmp' in sys.argv

    # Chemins
    locale_dir = Path(__file__).parent.parent / "locale"
    po_file = locale_dir / lang_code / "LC_MESSAGES" / "messages.po"

    # Vérifications
    if not po_file.exists():
        print()
        print(f"{c.ERROR}[X] Fichier .po introuvable pour la langue '{lang_code}'{c.RESET}")
        print(f"    Chemin attendu: {po_file}")
        return 1

    if not txt_file.exists():
        print()
        print(f"{c.ERROR}[X] Fichier de traductions introuvable{c.RESET}")
        print(f"    Chemin attendu: {txt_file}")
        print()
        print(f"{c.INFO}💡 Lancez d'abord: python i18n/export_untranslated_chains.py {lang_code}{c.RESET}")
        return 1

    print()
    print(c.config_line("Langue", lang_code.upper()))
    print(c.config_line("Fichier .po", str(po_file.name)))
    print(c.config_line("Fichier traductions", str(txt_file.name)))
    print()

    # Créer l'updater
    updater = POUpdater(po_file)

    # Charger le .po
    print(c.info("📖 Lecture du fichier .po..."))
    if not updater.load_po_file():
        return 1

    # Parser les traductions
    print(c.info("📖 Lecture des traductions..."))
    if not updater.parse_translation_file(txt_file):
        print()
        print(f"{c.ERROR}[X] Aucune traduction trouvée dans {txt_file.name}{c.RESET}")
        print(f"{c.INFO}💡 Vérifiez que les msgstr sont remplis{c.RESET}")
        return 1

    print(c.config_line("Traductions trouvées", f"{c.OK}{len(updater.translations)}{c.RESET}"))
    print()

    # Sauvegarde
    if create_backup:
        if not updater.create_backup():
            if not ask_yes_no("⚠️  Continuer sans sauvegarde ?"):
                return 1

    # Mise à jour
    print(c.info("🔄 Mise à jour du fichier .po..."))
    updated_content = updater.update_po_content()

    if updater.updated_count == 0:
        print()
        print(f"{c.WARNING}⚠️  Aucune correspondance trouvée{c.RESET}")
        print(f"{c.INFO}💡 Vérifiez que les msgid correspondent exactement{c.RESET}")
        return 1

    # Sauvegarder
    print(c.info("💾 Sauvegarde des modifications..."))
    if not updater.save_po_file(updated_content):
        return 1

    # Résumé
    print()
    print(c.separator("─", 70))
    print(f"{c.OK}✓ Import terminé avec succès !{c.RESET}")
    print(c.separator("─", 70))
    print()
    print(c.config_line("Chaînes mises à jour", f"{c.OK}{updater.updated_count}{c.RESET}"))

    if updater.fuzzy_removed_count > 0:
        print(c.config_line("Marqueurs fuzzy retirés", f"{c.OK}{updater.fuzzy_removed_count}{c.RESET}"))

    print()

    # Proposer de supprimer le fichier tmp
    if not keep_tmp:
        print(c.info("🗑️  Nettoyage..."))
        if ask_yes_no(f"Supprimer {txt_file.name} ?"):
            try:
                txt_file.unlink()
                print(f"{c.OK}✓ Fichier supprimé{c.RESET}")
            except Exception as e:
                print(f"{c.WARNING}⚠️  Impossible de supprimer: {e}{c.RESET}")
        print()

    # Prochaines étapes
    print(c.info("📝 Prochaines étapes :"))
    print(f"   1. Vérifier les traductions : python i18n/check_translations.py {lang_code}")
    print(f"   2. Compiler les traductions : python i18n/compile_translations.py")
    print(f"   3. Tester dans Lightroom Classic")
    print()

    # Proposition de vérification
    print(c.separator("─", 70))
    print(c.info("🔍 Vérification des traductions..."))
    print()

    response = input(f"{c.INFO}Lancer la vérification maintenant ? (o/n): {c.RESET}").strip().lower()

    if response in ['o', 'oui', 'y', 'yes']:
        print()
        print(c.info("🚀 Lancement de la vérification..."))
        print()
        import subprocess
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "check_translations.py"), lang_code, "-v"],
            cwd=Path(__file__).parent.parent
        )
        return result.returncode

    return 0


if __name__ == "__main__":
    sys.exit(main())
