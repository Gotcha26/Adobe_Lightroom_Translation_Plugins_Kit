#!/usr/bin/env python3
"""
Applicator_main.py

Script pour remplacer les chaines hardcodees en anglais dans le plugin Lightroom
par des appels LOC "$$$/Piwigo/...=Default Value" en utilisant les fichiers generes
par Extractor.

Usage (Menu interactif):
    python Applicator_main.py

Usage (CLI):
    python Applicator_main.py --plugin-path /path/to/plugin [--extraction-dir /path/to/extraction] [--dry-run] [--no-backup]

Options CLI:
    --plugin-path PATH     Chemin vers le repertoire du plugin (OBLIGATOIRE)
    --extraction-dir PATH  Repertoire Extractor (defaut: auto-detection __i18n_kit__/Extractor/)
    --dry-run              Mode simulation (affiche sans modifier)
    --no-backup            Ne pas creer de fichiers de sauvegarde .bak (defaut: backup active)

Sorties générées dans: <plugin>/__i18n_kit__/2_Applicator/<timestamp>/
  - application_report.txt (rapport détaillé)
  - backups/ (sauvegardes .bak des fichiers modifiés)

Le script :
1. Détecte automatiquement la dernière extraction (__i18n_kit__/Extractor/)
2. Lit le fichier replacements.json genere par Extractor
3. Cree des sauvegardes dans __i18n_kit__/2_Applicator/<timestamp>/backups/
4. Remplace les chaines hardcodees par des appels LOC avec valeur par defaut
5. Genere un rapport detaille des changements

IMPORTANT: Le format LOC du SDK Lightroom est:
    LOC "$$$/Key=Default Value"
La valeur par defaut est OBLIGATOIRE sinon Lightroom affiche la cle brute.

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-29
Version : 7.0 - Structure __i18n_kit__ avec auto-detection Extractor
"""

import os
import re
import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Ajouter le répertoire parent au path pour importer common
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.paths import get_tool_output_path, find_latest_tool_output
import glob
import subprocess

from Applicator_menu import show_interactive_menu


class LocalizationReport:
    """Genere un rapport detaille des modifications."""

    def __init__(self):
        self.changes = []
        self.skipped = []
        self.errors = []
        self.stats = {
            'files_processed': 0,
            'files_modified': 0,
            'total_replacements': 0,
            'strings_replaced': 0,
        }

    def add_change(self, file_path: str, line_num: int, before: str, after: str,
                   members: List[Dict]):
        self.changes.append({
            'file': file_path,
            'line': line_num,
            'before': before.strip(),
            'after': after.strip(),
            'members': members
        })
        self.stats['total_replacements'] += 1
        self.stats['strings_replaced'] += len(members)

    def add_skip(self, file_path: str, line_num: int, reason: str, content: str):
        self.skipped.append({
            'file': file_path,
            'line': line_num,
            'reason': reason,
            'content': content.strip()
        })

    def add_error(self, file_path: str, line_num: int, error: str):
        self.errors.append({
            'file': file_path,
            'line': line_num,
            'error': error
        })

    def generate(self, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RAPPORT DE LOCALISATION - PiwigoPublish Plugin\n")
            f.write("=" * 80 + "\n\n")

            f.write("STATISTIQUES GLOBALES\n")
            f.write("-" * 80 + "\n")
            f.write(f"Fichiers traites        : {self.stats['files_processed']}\n")
            f.write(f"Fichiers modifies       : {self.stats['files_modified']}\n")
            f.write(f"Lignes modifiees        : {self.stats['total_replacements']}\n")
            f.write(f"Chaines remplacees      : {self.stats['strings_replaced']}\n")
            f.write(f"Chaines ignorees        : {len(self.skipped)}\n")
            f.write(f"Erreurs                 : {len(self.errors)}\n\n")

            if self.changes:
                f.write("\n" + "=" * 80 + "\n")
                f.write("MODIFICATIONS EFFECTUEES\n")
                f.write("=" * 80 + "\n\n")

                current_file = None
                for change in self.changes:
                    if change['file'] != current_file:
                        current_file = change['file']
                        f.write(f"\n{'-' * 80}\n")
                        f.write(f"Fichier: {change['file']}\n")
                        f.write(f"{'-' * 80}\n\n")

                    f.write(f"  Ligne {change['line']}:\n")
                    f.write(f"  AVANT : {change['before'][:100]}\n")
                    f.write(f"  APRES : {change['after'][:100]}\n")
                    for member in change['members']:
                        f.write(f"    - \"{member['original_text']}\" -> {member['loc_key']}\n")
                    f.write("\n")

            if self.skipped:
                f.write("\n" + "=" * 80 + "\n")
                f.write("CHAINES IGNOREES\n")
                f.write("=" * 80 + "\n\n")

                for skip in self.skipped:
                    f.write(f"  {skip['file']}:{skip['line']}\n")
                    f.write(f"    Raison: {skip['reason']}\n")
                    f.write(f"    Contenu: {skip['content'][:80]}\n\n")

            if self.errors:
                f.write("\n" + "=" * 80 + "\n")
                f.write("ERREURS\n")
                f.write("=" * 80 + "\n\n")

                for err in self.errors:
                    f.write(f"  {err['file']}:{err['line']}\n")
                    f.write(f"    Erreur: {err['error']}\n\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("RECOMMANDATIONS POST-TRAITEMENT\n")
            f.write("=" * 80 + "\n\n")
            f.write("1. Verifier les modifications avec Git diff\n")
            f.write("2. REDEMARRER Lightroom Classic (reload ne suffit pas)\n")
            f.write("3. Verifier que TranslatedStrings_fr.txt existe a la racine\n")
            f.write("4. Tester les textes dans l'interface\n\n")


def load_replacements_json(extraction_dir: str) -> Optional[Dict]:
    """Charge le fichier replacements.json."""
    replacements_file = os.path.join(extraction_dir, "replacements.json")

    if not os.path.exists(replacements_file):
        print(f"ERREUR: Fichier replacements.json introuvable dans {extraction_dir}")
        return None

    try:
        with open(replacements_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"* replacements.json charge")
            print(f"  - {len(data.get('files', {}))} fichiers avec remplacements")
            total_replacements = sum(
                f_data.get('total_replacements', 0)
                for f_data in data.get('files', {}).values()
            )
            print(f"  - {total_replacements} remplacements prevus")
            return data
    except Exception as e:
        print(f"ERREUR lors du chargement de replacements.json: {e}")
        return None


def build_loc_call(member: Dict) -> str:
    """
    Construit l'appel LOC pour un membre.

    Format SDK Lightroom: LOC "$$$/Key=Default Value"
    """
    loc_key = member['loc_key']
    base_text = member['base_text']
    leading_spaces = member.get('leading_spaces', 0)
    trailing_spaces = member.get('trailing_spaces', 0)
    suffix = member.get('suffix', '')

    parts = []

    # Espaces en debut
    if leading_spaces > 0:
        parts.append('"' + ' ' * leading_spaces + '" .. ')

    # Appel LOC avec valeur par defaut
    parts.append(f'LOC "{loc_key}={base_text}"')

    # Suffixe ou espaces en fin
    if suffix:
        parts.append(f' .. "{suffix}"')
    elif trailing_spaces > 0:
        parts.append(' .. "' + ' ' * trailing_spaces + '"')

    return ''.join(parts)


def apply_replacements_to_line(line: str, members: List[Dict]) -> Tuple[str, List[Dict]]:
    """
    Applique les remplacements a une ligne.

    Retourne (nouvelle_ligne, membres_appliques)
    """
    result = line
    applied_members = []

    # Trouver TOUTES les positions de chaque chaine, en evitant les doublons
    members_with_pos = []
    used_positions = set()  # Pour eviter d'utiliser la meme position deux fois

    for member in members:
        original_text = member['original_text']
        # Chercher avec guillemets doubles ET simples
        for quote in ['"', "'"]:
            search_str = f'{quote}{original_text}{quote}'
            # Trouver toutes les occurrences de cette chaine
            start = 0
            while True:
                pos = result.find(search_str, start)
                if pos == -1:
                    break
                # Verifier que cette position n'est pas deja utilisee
                if pos not in used_positions:
                    members_with_pos.append((pos, member, search_str, quote))
                    used_positions.add(pos)
                    break  # Utiliser la premiere occurrence non-utilisee
                start = pos + 1  # Chercher la suivante

    # Trier par position decroissante pour ne pas decaler les indices
    members_with_pos.sort(key=lambda x: x[0], reverse=True)

    for pos, member, search_str, quote in members_with_pos:
        # Verifier que cette chaine n'est pas deja dans un LOC
        # Chercher "LOC" avant la position
        before_context = result[max(0, pos-20):pos]
        if 'LOC ' in before_context or 'LOC"' in before_context or "LOC'" in before_context:
            continue  # Deja localisee

        # Construire le remplacement
        loc_call = build_loc_call(member)

        # Remplacer a cette position exacte
        result = result[:pos] + loc_call + result[pos + len(search_str):]
        applied_members.append(member)

    return result, applied_members


def process_file_with_replacements(file_path: str, file_replacements: Dict,
                                    report: LocalizationReport, dry_run: bool,
                                    backup_dir: str = None, create_backup: bool = True) -> int:
    """
    Traite un fichier en utilisant les remplacements du JSON.

    Retourne le nombre de remplacements effectues.
    """
    if not os.path.exists(file_path):
        report.add_error(file_path, 0, "Fichier introuvable")
        return 0

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Indexer les remplacements par numero de ligne
    replacements_by_line = {}
    for replacement in file_replacements.get('replacements', []):
        line_num = replacement['line_num']
        replacements_by_line[line_num] = replacement

    modified = False
    new_lines = []
    total_applied = 0

    for line_num, line in enumerate(lines, 1):
        if line_num in replacements_by_line:
            replacement = replacements_by_line[line_num]
            members = replacement.get('members', [])

            # Appliquer les remplacements
            new_line, applied_members = apply_replacements_to_line(line, members)

            if new_line != line and applied_members:
                report.add_change(file_path, line_num, line, new_line, applied_members)
                new_lines.append(new_line)
                modified = True
                total_applied += len(applied_members)
            else:
                # Verifier si c'est parce que c'est deja localise
                if 'LOC "$$$/' in line or "LOC '$$$/'" in line:
                    # Ligne deja (partiellement?) localisee
                    # Essayer quand meme d'appliquer les membres non-localises
                    new_line, applied_members = apply_replacements_to_line(line, members)
                    if new_line != line and applied_members:
                        report.add_change(file_path, line_num, line, new_line, applied_members)
                        new_lines.append(new_line)
                        modified = True
                        total_applied += len(applied_members)
                    else:
                        new_lines.append(line)
                else:
                    # Pas de modification possible
                    report.add_skip(file_path, line_num,
                                   "Chaine non trouvee ou deja localisee",
                                   line)
                    new_lines.append(line)
        else:
            new_lines.append(line)

    # Sauvegarder les modifications
    if modified and not dry_run:
        # Créer le backup si demandé
        if create_backup:
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, os.path.basename(file_path) + '.bak')
            else:
                backup_path = file_path + '.bak'
            shutil.copy2(file_path, backup_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return total_applied


def process_plugin_directory(plugin_path: str, extraction_dir: str = None, dry_run: bool = False,
                              create_backup: bool = True) -> bool:
    """Traite tous les fichiers Lua du plugin en utilisant replacements.json."""

    if not os.path.isdir(plugin_path):
        print(f"ERREUR: Repertoire du plugin introuvable: {plugin_path}")
        return False

    # Auto-détection du dossier d'extraction si non spécifié
    if not extraction_dir:
        extraction_dir = find_latest_tool_output(plugin_path, "Extractor")
        if not extraction_dir:
            print("ERREUR: Aucune extraction trouvée dans __i18n_kit__/Extractor/")
            print("        Lancez d'abord Extractor sur ce plugin.")
            return False
        print(f"* Auto-détection: {extraction_dir}")

    if not os.path.isdir(extraction_dir):
        print(f"ERREUR: Repertoire Extractor introuvable: {extraction_dir}")
        return False

    # Créer le dossier de sortie Applicator
    applicator_output = get_tool_output_path(plugin_path, "Applicator", create=True)
    backup_dir = os.path.join(applicator_output, "backups") if create_backup else None

    print("\n" + "=" * 80)
    print("LOCALISATION DU PLUGIN (v7.0 - structure __i18n_kit__)")
    print("=" * 80)
    print(f"Repertoire du plugin   : {plugin_path}")
    print(f"Dossier Extractor      : {extraction_dir}")
    print(f"Sortie Applicator      : {applicator_output}")
    print(f"Mode                   : {'DRY-RUN (simulation)' if dry_run else 'MODIFICATION REELLE'}")
    print(f"Sauvegardes .bak       : {'OUI' if create_backup and not dry_run else 'NON'}")
    print("=" * 80 + "\n")

    # Charger replacements.json
    replacements_data = load_replacements_json(extraction_dir)

    if not replacements_data:
        print("ERREUR: Impossible de charger les remplacements")
        return False

    files_data = replacements_data.get('files', {})

    if not files_data:
        print("Aucun remplacement a effectuer")
        return True

    print()
    report = LocalizationReport()

    for file_rel_path, file_replacements in sorted(files_data.items()):
        file_path = os.path.join(plugin_path, file_rel_path)

        if os.path.exists(file_path):
            print(f"Traitement de {file_rel_path}...")
            replacements_count = process_file_with_replacements(
                file_path, file_replacements, report, dry_run, backup_dir, create_backup
            )
            report.stats['files_processed'] += 1
            if replacements_count > 0:
                report.stats['files_modified'] += 1
                print(f"  * {replacements_count} chaine(s) remplacee(s)")
            else:
                print(f"  - Aucun remplacement")
        else:
            print(f"  ! Fichier introuvable: {file_rel_path}")
            report.add_error(file_rel_path, 0, "Fichier introuvable")

    # Generer le rapport dans le dossier Applicator
    report_path = os.path.join(applicator_output, "application_report.txt")
    report.generate(report_path)

    print("\n" + "=" * 80)
    print("RESUME")
    print("=" * 80)
    print(f"Fichiers traites        : {report.stats['files_processed']}")
    print(f"Fichiers modifies       : {report.stats['files_modified']}")
    print(f"Lignes modifiees        : {report.stats['total_replacements']}")
    print(f"Chaines remplacees      : {report.stats['strings_replaced']}")
    print(f"Chaines ignorees        : {len(report.skipped)}")
    print(f"\nSortie Applicator       : {applicator_output}")
    if not dry_run and report.stats['files_modified'] > 0 and create_backup:
        print(f"Backups                 : {backup_dir}")
    print(f"Rapport detaille        : {report_path}")

    if dry_run:
        print("\n!!! MODE DRY-RUN: Aucun fichier n'a ete modifie")

    print("\n" + "=" * 80)
    print("IMPORTANT: Redemarrez Lightroom apres les modifications!")
    print("           (le rechargement du plugin ne suffit pas)")
    print("=" * 80)

    return True


def find_translation_files(plugin_path: str) -> List[str]:
    """
    Recherche les fichiers TranslatedStrings_xx.txt a la racine du plugin.

    Returns:
        Liste des fichiers trouves
    """
    pattern = os.path.join(plugin_path, "TranslatedStrings_*.txt")
    return glob.glob(pattern)


def find_translation_template(extraction_dir: str) -> Optional[str]:
    """
    Recherche le fichier template TranslatedStrings dans le dossier d'extraction.

    Returns:
        Chemin du fichier template ou None
    """
    if not extraction_dir or not os.path.isdir(extraction_dir):
        return None

    pattern = os.path.join(extraction_dir, "TranslatedStrings_*.txt")
    files = glob.glob(pattern)
    return files[0] if files else None


def handle_translation_files(plugin_path: str, extraction_dir: str = None) -> None:
    """
    Gere les fichiers de traduction apres l'application.

    - Si TranslatedStrings_xx.txt n'existe pas: propose de le creer
    - Si TranslatedStrings_xx.txt existe: propose d'ouvrir TranslationManager
    """
    print("\n" + "-" * 80)
    print("GESTION DES TRADUCTIONS")
    print("-" * 80)

    existing_files = find_translation_files(plugin_path)

    if existing_files:
        # Fichier(s) de traduction existant(s)
        print("\nFichier(s) de traduction trouve(s):")
        for f in existing_files:
            print(f"  - {os.path.basename(f)}")

        print("\nVoulez-vous ouvrir le gestionnaire de traductions (TranslationManager)?")
        print("Cela permet de synchroniser les traductions avec les nouvelles cles.")
        print()

        choice = input("Ouvrir TranslationManager? [o/N]: ").strip().lower()

        if choice in ['o', 'oui', 'y', 'yes']:
            # Lancer TranslationManager
            tm_script = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "3_Translation_manager",
                "TranslationManager.py"
            )

            if os.path.exists(tm_script):
                print(f"\nLancement de TranslationManager...")
                try:
                    subprocess.run(
                        [sys.executable, tm_script],
                        cwd=os.path.dirname(tm_script),
                        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                    )
                except Exception as e:
                    print(f"[ERREUR] Impossible de lancer TranslationManager: {e}")
            else:
                print(f"[ERREUR] TranslationManager introuvable: {tm_script}")
        else:
            print("[OK] TranslationManager non lance")
    else:
        # Aucun fichier de traduction
        print("\nAucun fichier TranslatedStrings_xx.txt trouve a la racine du plugin.")
        print("Ce fichier est necessaire pour les traductions Lightroom.")

        # Chercher un template dans l'extraction
        if not extraction_dir:
            extraction_dir = find_latest_tool_output(plugin_path, "Extractor")

        template_file = find_translation_template(extraction_dir) if extraction_dir else None

        if template_file:
            template_name = os.path.basename(template_file)
            dest_path = os.path.join(plugin_path, template_name)

            print(f"\nUn fichier template a ete trouve dans l'extraction:")
            print(f"  {template_file}")
            print()
            print(f"Voulez-vous le copier à la racine du plugin?")
            print(f"  -> {dest_path}")
            print()

            choice = input("Copier le fichier? [O/n]: ").strip().lower()

            if choice in ['o', 'oui', 'y', 'yes', '']:
                try:
                    shutil.copy2(template_file, dest_path)
                    print(f"\n[OK] Fichier copie: {dest_path}")
                    print("     Vous pouvez maintenant editer ce fichier pour ajouter les traductions.")
                except Exception as e:
                    print(f"\n[ERREUR] Impossible de copier le fichier: {e}")
            else:
                print("[OK] Fichier non copie")
        else:
            print("\nPour creer un fichier de traduction:")
            print("  1. Lancez l'Extractor sur le plugin")
            print("  2. Copiez le fichier TranslatedStrings_xx.txt genere a la racine du plugin")
            print("  3. Editez le fichier pour ajouter vos traductions")


def main():
    """Point d'entree principal."""

    # Verifier si mode interactif (aucun argument ou seulement --default-plugin)
    if len(sys.argv) == 1 or (len(sys.argv) == 3 and sys.argv[1] == '--default-plugin'):
        # Recuperer le chemin par defaut si fourni
        default_plugin = ""
        if len(sys.argv) == 3 and sys.argv[1] == '--default-plugin':
            default_plugin = sys.argv[2]

        # Menu interactif avec plugin pre-configure
        result = show_interactive_menu(default_plugin)

        if result is None:
            print("\nApplication annulee")
            sys.exit(1)

        plugin_path, extraction_dir, dry_run, create_backup = result

        success = process_plugin_directory(plugin_path, extraction_dir, dry_run, create_backup)

        # Proposer la gestion des fichiers de traduction si succes et pas en dry-run
        if success and not dry_run:
            handle_translation_files(plugin_path, extraction_dir)

        sys.exit(0 if success else 1)
    else:
        # Arguments en ligne de commande
        parser = argparse.ArgumentParser(
            description="Applique les localisations generees par Extractor au plugin",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Exemples:
  # Mode interactif (menu)
  python Applicator_main.py

  # Mode CLI avec auto-detection de l'extraction
  python Applicator_main.py --plugin-path ./plugin.lrplugin
  python Applicator_main.py --plugin-path ./plugin.lrplugin --dry-run

  # Mode CLI avec extraction specifique
  python Applicator_main.py --plugin-path ./plugin.lrplugin --extraction-dir ./plugin.lrplugin/__i18n_kit__/Extractor/20260127_091234
            """
        )

        parser.add_argument('--plugin-path', required=True,
                            help='Chemin vers le repertoire du plugin (OBLIGATOIRE)')
        parser.add_argument('--extraction-dir', default=None,
                            help='Repertoire Extractor (defaut: auto-detection __i18n_kit__/Extractor/)')
        parser.add_argument('--dry-run', action='store_true',
                            help='Mode simulation (affiche sans modifier)')
        parser.add_argument('--no-backup', action='store_true',
                            help='Ne pas creer de fichiers de sauvegarde .bak (par defaut: backup active)')

        args = parser.parse_args()

        success = process_plugin_directory(
            args.plugin_path,
            args.extraction_dir,
            args.dry_run,
            create_backup=not args.no_backup
        )

        # Proposer la gestion des fichiers de traduction si succes et pas en dry-run
        if success and not args.dry_run:
            handle_translation_files(args.plugin_path, args.extraction_dir)

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
