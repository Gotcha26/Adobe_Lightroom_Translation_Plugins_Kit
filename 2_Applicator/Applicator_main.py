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
from common.i18n import _
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
        print(_("ERREUR: Fichier replacements.json introuvable dans {dir}").format(dir=extraction_dir))
        return None

    try:
        with open(replacements_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(_("* replacements.json chargé"))
            print(_("  - {n} fichiers avec remplacements").format(n=len(data.get('files', {}))))
            total_replacements = sum(
                f_data.get('total_replacements', 0)
                for f_data in data.get('files', {}).values()
            )
            print(_("  - {n} remplacements prévus").format(n=total_replacements))
            return data
    except Exception as e:
        print(_("ERREUR lors du chargement de replacements.json: {error}").format(error=e))
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
        # Guillemets doubles uniquement (conformément au SDK Adobe et à Extractor)
        search_str = f'"{original_text}"'
        # Trouver toutes les occurrences de cette chaine
        start = 0
        while True:
            pos = result.find(search_str, start)
            if pos == -1:
                break
            # Verifier que cette position n'est pas deja utilisee
            if pos not in used_positions:
                members_with_pos.append((pos, member, search_str))
                used_positions.add(pos)
                break  # Utiliser la premiere occurrence non-utilisee
            start = pos + 1  # Chercher la suivante

    # Trier par position decroissante pour ne pas decaler les indices
    members_with_pos.sort(key=lambda x: x[0], reverse=True)

    for pos, member, search_str in members_with_pos:
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
                if 'LOC "$$$/' in line:
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
        print(_("ERREUR: Répertoire du plugin introuvable: {path}").format(path=plugin_path))
        return False

    # Auto-détection du dossier d'extraction si non spécifié
    if not extraction_dir:
        extraction_dir = find_latest_tool_output(plugin_path, "Extractor")
        if not extraction_dir:
            print(_("ERREUR: Aucune extraction trouvée dans __i18n_kit__/Extractor/"))
            print(_("        Lancez d'abord Extractor sur ce plugin."))
            return False
        print(_("* Auto-détection: {dir}").format(dir=extraction_dir))

    if not os.path.isdir(extraction_dir):
        print(_("ERREUR: Répertoire Extractor introuvable: {dir}").format(dir=extraction_dir))
        return False

    # Créer le dossier de sortie Applicator
    applicator_output = get_tool_output_path(plugin_path, "Applicator", create=True)
    backup_dir = os.path.join(applicator_output, "backups") if create_backup else None

    print("\n" + "=" * 80)
    print(_("LOCALISATION DU PLUGIN"))
    print("=" * 80)
    print(_("Répertoire du plugin") + f"   : {plugin_path}")
    print(_("Dossier Extractor") + f"      : {extraction_dir}")
    print(_("Sortie Applicator") + f"      : {applicator_output}")
    mode_str = _("DRY-RUN (simulation)") if dry_run else _("MODIFICATION RÉELLE")
    print(_("Mode") + f"                   : {mode_str}")
    backup_str = _("OUI") if create_backup and not dry_run else _("NON")
    print(_("Sauvegardes .bak") + f"       : {backup_str}")
    print("=" * 80 + "\n")

    # Charger replacements.json
    replacements_data = load_replacements_json(extraction_dir)

    if not replacements_data:
        print(_("ERREUR: Impossible de charger les remplacements"))
        return False

    files_data = replacements_data.get('files', {})

    if not files_data:
        print(_("Aucun remplacement à effectuer"))
        return True

    print()
    report = LocalizationReport()

    for file_rel_path, file_replacements in sorted(files_data.items()):
        file_path = os.path.join(plugin_path, file_rel_path)

        if os.path.exists(file_path):
            print(_("Traitement de {file}...").format(file=file_rel_path))
            replacements_count = process_file_with_replacements(
                file_path, file_replacements, report, dry_run, backup_dir, create_backup
            )
            report.stats['files_processed'] += 1
            if replacements_count > 0:
                report.stats['files_modified'] += 1
                print(_("  * {n} chaîne(s) remplacée(s)").format(n=replacements_count))
            else:
                print(_("  - Aucun remplacement"))
        else:
            print(_("  ! Fichier introuvable: {file}").format(file=file_rel_path))
            report.add_error(file_rel_path, 0, "Fichier introuvable")

    # Generer le rapport dans le dossier Applicator
    report_path = os.path.join(applicator_output, "application_report.txt")
    report.generate(report_path)

    print("\n" + "=" * 80)
    print(_("RÉSUMÉ"))
    print("=" * 80)
    print(_("Fichiers traités") + f"        : {report.stats['files_processed']}")
    print(_("Fichiers modifiés") + f"       : {report.stats['files_modified']}")
    print(_("Lignes modifiées") + f"        : {report.stats['total_replacements']}")
    print(_("Chaînes remplacées") + f"      : {report.stats['strings_replaced']}")
    print(_("Chaînes ignorées") + f"        : {len(report.skipped)}")
    print("\n" + _("Sortie Applicator") + f"       : {applicator_output}")
    if not dry_run and report.stats['files_modified'] > 0 and create_backup:
        print(_("Backups") + f"                 : {backup_dir}")
    print(_("Rapport détaillé") + f"        : {report_path}")

    if dry_run:
        print("\n!!! " + _("MODE DRY-RUN: Aucun fichier n'a été modifié"))

    print("\n" + "=" * 80)
    print(_("IMPORTANT: Redémarrez Lightroom après les modifications!"))
    print(_("           (le rechargement du plugin ne suffit pas)"))
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
    Gère les fichiers de traduction apres l'application.

    - Si TranslatedStrings_xx.txt n'existe pas: propose de le créer
    - Si TranslatedStrings_xx.txt existe: propose d'ouvrir Translator
    """
    print("\n" + "-" * 80)
    print(_("GESTION DES TRADUCTIONS"))
    print("-" * 80)

    existing_files = find_translation_files(plugin_path)

    if existing_files:
        # Fichier(s) de traduction existant(s)
        print("\n" + _("Fichier(s) de traduction trouvé(s) à la racine du plugin:"))
        for f in existing_files:
            print(f"  - {os.path.basename(f)}")

        print("\n" + _("Voulez-vous ouvrir le gestionnaire de traductions (Translator)?"))
        print(_("Cela permet de synchroniser les traductions avec les nouvelles clés."))
        print()

        choice = input(_("Ouvrir Translator? [o/N]:") + " ").strip().lower()

        if choice in ['o', 'oui', 'y', 'yes']:
            # Lancer Translator
            tm_script = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "3_Translation_manager",
                "Translator.py"
            )

            if os.path.exists(tm_script):
                print("\n" + _("Lancement de Translator..."))
                try:
                    subprocess.run(
                        [sys.executable, tm_script],
                        cwd=os.path.dirname(tm_script),
                        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                    )
                except Exception as e:
                    print(_("[ERREUR] Impossible de lancer Translator: {error}").format(error=e))
            else:
                print(_("[ERREUR] Translator introuvable: {path}").format(path=tm_script))
        else:
            print(_("[OK] Translator non lancé"))
    else:
        # Aucun fichier de traduction
        print("\n" + _("Aucun fichier TranslatedStrings_xx.txt trouvé à la racine du plugin."))
        print(_("Ce fichier est nécessaire pour les traductions Lightroom."))

        # Chercher un template dans l'extraction
        if not extraction_dir:
            extraction_dir = find_latest_tool_output(plugin_path, "Extractor")

        template_file = find_translation_template(extraction_dir) if extraction_dir else None

        if template_file:
            template_name = os.path.basename(template_file)
            dest_path = os.path.join(plugin_path, template_name)

            print("\n" + _("Un fichier template a été trouvé dans l'extraction:"))
            print(f"  {template_file}")
            print()
            print(_("Voulez-vous le copier à la racine du plugin?"))
            print(f"  -> {dest_path}")
            print()

            choice = input(_("Copier le fichier? [O/n]:") + " ").strip().lower()

            if choice in ['o', 'oui', 'y', 'yes', '']:
                try:
                    shutil.copy2(template_file, dest_path)
                    print("\n" + _("[OK] Fichier copié: {path}").format(path=dest_path))
                    print("     " + _("Vous pouvez maintenant éditer ce fichier pour ajouter les traductions."))
                except Exception as e:
                    print("\n" + _("[ERREUR] Impossible de copier le fichier: {error}").format(error=e))
            else:
                print(_("[OK] Fichier non copié"))
        else:
            print("\n" + _("Pour créer un fichier de traduction:"))
            print(_("  1. Lancez l'Extractor sur le plugin"))
            print(_("  2. Copiez le fichier TranslatedStrings_xx.txt généré à la racine du plugin"))
            print(_("  3. Éditez le fichier pour ajouter vos traductions"))


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
            print("\n" + _("Application annulée"))
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
