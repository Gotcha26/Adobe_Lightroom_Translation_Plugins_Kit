#!/usr/bin/env python3
"""
Nom du fichier : main.py

Dépendances : core.paths, core.colors, core.i18n, .menu

Description :
Script d'application des localisations aux plugins Lightroom. Remplace les chaînes
en anglais hardcodées par des appels LOC au format "$$$/Key=Default Value" en
utilisant les fichiers générés par Extractor. Supporte le mode interactif (menu)
et le mode CLI avec arguments.

Usage CLI :
    python -m tools.applicator.main

    Mode interactif (menu):
        python -m tools.applicator.main

    Mode CLI avec auto-détection:
        python -m tools.applicator.main --plugin-path /path/to/plugin
        python -m tools.applicator.main --plugin-path /path/to/plugin --dry-run

    Mode CLI avec extraction spécifique:
        python -m tools.applicator.main --plugin-path /path/to/plugin --extraction-dir /path/to/extraction

    Options:
        --plugin-path PATH          Chemin du plugin (OBLIGATOIRE en CLI)
        --extraction-dir PATH       Dossier Extractor (défaut : auto-détection)
        --dry-run                   Mode simulation (affichage sans modification)
        --no-backup                 Ne pas créer de .bak (défaut : backups activées)

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import re
import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.paths import get_tool_output_path, find_latest_tool_output
from core.colors import Colors
from core.i18n import _
import glob
import subprocess

from .menu import show_interactive_menu

c = Colors()


def _shorten(path: str, plugin_path: str) -> str:
    """Remplace le préfixe plugin_path par <plugin> dans un chemin."""
    plugin_norm = os.path.normpath(plugin_path)
    path_norm = os.path.normpath(path)
    if path_norm.startswith(plugin_norm):
        return "<plugin>" + path_norm[len(plugin_norm):]
    return path


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
                                    backup_dir: Optional[str] = None, create_backup: bool = True) -> int:
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


def process_plugin_directory(plugin_path: str, extraction_dir: Optional[str] = None, dry_run: bool = False,
                              create_backup: bool = True) -> bool:
    """Traite tous les fichiers Lua du plugin en utilisant replacements.json."""

    if not os.path.isdir(plugin_path):
        print(_("ERREUR: Répertoire du plugin introuvable: {path}").format(path=plugin_path))
        return False

    # Auto-détection du dossier d'extraction si non spécifié
    if not extraction_dir:
        extraction_dir = find_latest_tool_output(plugin_path, "Extractor")
        if not extraction_dir:
            print(_("ERREUR: Aucune extraction trouvée dans __i18n_tmp__/Extractor/"))
            print(_("        Lancez d'abord Extractor sur ce plugin."))
            return False
        print(_("* Auto-détection: {dir}").format(dir=extraction_dir))

    if not os.path.isdir(extraction_dir):
        print(_("ERREUR: Répertoire Extractor introuvable: {dir}").format(dir=extraction_dir))
        return False

    # Créer le dossier de sortie Applicator
    applicator_output = get_tool_output_path(plugin_path, "Applicator", create=True)
    backup_dir = os.path.join(applicator_output, "backups") if create_backup else None

    print()

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

    print("\n" + c.separator("─", 70))
    print(c.header(_("RÉSUMÉ")))
    print(c.separator("─", 70))
    print(c.config_line(_("Fichiers traités"),    str(report.stats['files_processed'])))
    print(c.config_line(_("Fichiers modifiés"),   str(report.stats['files_modified'])))
    print(c.config_line(_("Lignes modifiées"),    str(report.stats['total_replacements'])))
    print(c.config_line(_("Chaînes remplacées"),  str(report.stats['strings_replaced'])))
    print(c.config_line(_("Chaînes ignorées"),    str(len(report.skipped))))
    print()
    print(c.config_line(_("Sortie Applicator"),   _shorten(applicator_output, plugin_path)))
    if not dry_run and report.stats['files_modified'] > 0 and create_backup and backup_dir:
        print(c.config_line(_("Backups"),         _shorten(backup_dir, plugin_path)))
    print(c.config_line(_("Rapport détaillé"),    _shorten(report_path, plugin_path)))

    if dry_run:
        print("\n" + c.warning(_("MODE DRY-RUN: Aucun fichier n'a été modifié")))

    print("\n" + c.separator("═", 70))
    print(c.warning(_("IMPORTANT: Redémarrez Lightroom après les modifications!")))
    print(f"{c.DIM}" + _("           (le rechargement du plugin ne suffit pas)") + f"{c.RESET}")
    print(c.separator("═", 70))

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
    templates = find_all_translation_templates(extraction_dir)
    return templates[0] if templates else None


def find_all_translation_templates(extraction_dir: str) -> List[str]:
    """
    Recherche tous les fichiers TranslatedStrings_*.txt dans l'extraction.

    Returns:
        Liste des chemins trouvés, triés par nom
    """
    if not extraction_dir or not os.path.isdir(extraction_dir):
        return []

    pattern = os.path.join(extraction_dir, "TranslatedStrings_*.txt")
    return sorted(glob.glob(pattern))


def _extract_lang_code(filename: str) -> Optional[str]:
    """Extrait le code de langue d'un fichier TranslatedStrings_xx.txt."""
    m = re.match(r'TranslatedStrings_(\w+)\.txt$', os.path.basename(filename))
    return m.group(1) if m else None


def _launch_autosync(plugin_path: str) -> None:
    """Lance run_autosync() depuis tools.translator.autosync."""
    try:
        from tools.translator.autosync import run_autosync
        print("\n" + c.info(_("Lancement de AUTOSYNC...")))
        run_autosync(plugin_path)
    except ImportError:
        # Fallback : appel via subprocess sur le fichier autosync.py
        autosync_script = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "translator",
            "autosync.py"
        )
        if os.path.exists(autosync_script):
            print("\n" + c.info(_("Lancement de AUTOSYNC...")))
            try:
                subprocess.run(
                    [sys.executable, autosync_script, plugin_path],
                    env={**os.environ, 'PYTHONIOENCODING': 'utf-8'}
                )
            except Exception as e:
                print(c.error(_("Impossible de lancer AUTOSYNC: {error}").format(error=e)))
        else:
            print(c.error(_("autosync.py introuvable: {path}").format(path=autosync_script)))
    except Exception as e:
        print(c.error(_("Erreur lors du lancement de AUTOSYNC: {error}").format(error=e)))


def _copy_template_to_plugin(template_file: str, plugin_path: str) -> None:
    """Copie un fichier template vers la racine du plugin."""
    template_name = os.path.basename(template_file)
    dest_path = os.path.join(plugin_path, template_name)
    try:
        shutil.copy2(template_file, dest_path)
        print("\n" + c.success(
            _("Fichier mis en place : {name}").format(name=template_name)))
    except Exception as e:
        print("\n" + c.error(
            _("Impossible de copier le fichier: {error}").format(error=e)))


def _select_and_copy_template(plugin_path: str, extraction_dir: Optional[str]) -> None:
    """
    Sous-menu après refus du template par défaut.

    Permet de :
      1. Choisir un autre fichier depuis l'extraction
      2. Importer un fichier depuis l'extérieur
      0. Sortir sans copier
    """
    templates = find_all_translation_templates(extraction_dir) if extraction_dir else []

    print("\n" + c.separator("─", 70))
    print(c.title(_("Que voulez-vous faire ?")))
    print()

    if templates:
        print(c.menu_option("1", _("Choisir un autre fichier depuis une extraction précédente.")))
    print(c.menu_option("2", _("Importer un fichier depuis l'extérieur")))
    print(c.menu_option("0", _("Sortir sans copier")))
    print()

    choice = input(c.prompt(_("Votre choix:") + " ")).strip()

    if choice == '1' and templates:
        # Lister les templates disponibles
        print()
        print(c.title(_("Fichiers disponibles dans l'extraction :")))
        for i, t in enumerate(templates, 1):
            # Afficher le chemin relatif depuis <temp_dir>/<timestamp>/
            # Extraire les 2 derniers niveaux du chemin (timestamp/nomfichier)
            path_parts = t.replace('\\', '/').split('/')
            if len(path_parts) >= 2:
                display_path = f"<temp_dir>/{path_parts[-2]}/{path_parts[-1]}"
            else:
                display_path = os.path.basename(t)
            print(c.menu_option(str(i), display_path))
        print(c.menu_option("0", _("Retour")))
        print()

        sel = input(c.prompt(_("Votre choix:") + " ")).strip()
        try:
            idx = int(sel)
            if 1 <= idx <= len(templates):
                _copy_template_to_plugin(templates[idx - 1], plugin_path)
            else:
                print(c.info(_("Rien copié")))
        except ValueError:
            print(c.info(_("Rien copié")))

    elif choice == '2':
        # Importer depuis l'extérieur
        print()
        path = input(c.prompt(
            _("Chemin du fichier TranslatedStrings_xx.txt :") + " ")).strip()
        if not path:
            print(c.info(_("Rien copié")))
            return

        path = os.path.normpath(path)
        if not os.path.isfile(path):
            print(c.error(_("Fichier introuvable: {path}").format(path=path)))
            return

        _copy_template_to_plugin(path, plugin_path)

    else:
        print(c.info(_("Rien copié")))


def handle_translation_files(plugin_path: str, extraction_dir: Optional[str] = None) -> None:
    """
    Gère les fichiers de traduction après l'application.

    3 cas :
      1. Aucun fichier à la racine          → première installation, copie du template
      2. Un fichier avec même langue         → mise à jour, proposition de remplacement
      3. Plusieurs langues détectées         → mise à jour manuelle détectée, lancement AUTOSYNC
    """
    print("\n" + c.separator("─", 70))
    print(c.header(_("GESTION DES TRADUCTIONS")))
    print(c.separator("─", 70))

    existing_files = find_translation_files(plugin_path)

    # Chercher le template dans l'extraction
    if not extraction_dir:
        extraction_dir = find_latest_tool_output(plugin_path, "Extractor")
    template_file = find_translation_template(extraction_dir) if extraction_dir else None

    # --- CAS 1 : Aucun fichier à la racine ---
    if not existing_files:
        if not template_file:
            # Pas de template non plus → instructions manuelles
            print("\n" + c.warning(
                _("Aucun fichier TranslatedStrings_xx.txt à la racine.")))
            print(_("  1. Lancez l'Extractor sur le plugin"))
            print(_("  2. Copiez le fichier TranslatedStrings_xx.txt"))
            print(_("     généré à la racine du plugin"))
            print(_("  3. Éditez le fichier pour ajouter vos traductions"))
            return

        template_name = os.path.basename(template_file)

        print("\n" + _(
            "Il semble que ce soit votre première installation d'une langue à traduire."))
        print(_("Utiliseriez-vous le dernier fichier extrait depuis Extractor comme référence ?"))
        print()
        print(_("Il sera alors simplement mis en place à la racine du plugin,\n"
                "prêt pour de futurs traductions."))
        print(_("Rien d'autre à faire si ce n'est d'inciter des contributeurs à\n"
                "venir enrichir la communauté autour de ce plugin."))
        print()
        print(f"  {c.VALUE}{template_name}{c.RESET}"
              f"  →  <plugin>\\{template_name}")
        print()

        choice = input(c.prompt(
            _("Copier le fichier? [O/n]:") + " ")).strip().lower()

        if choice in ['o', 'oui', 'y', 'yes', '']:
            _copy_template_to_plugin(template_file, plugin_path)
        else:
            _select_and_copy_template(plugin_path, extraction_dir)
        return

    # --- Plusieurs fichiers existants : extraire les codes de langue ---
    existing_langs = {}  # code_langue -> chemin complet
    for f in existing_files:
        code = _extract_lang_code(f)
        if code:
            existing_langs[code] = f

    template_lang = _extract_lang_code(template_file) if template_file else None

    # --- CAS 3 : Plusieurs langues détectées → AUTOSYNC ---
    if len(existing_langs) > 1:
        print("\n" + c.warning(_("Plusieurs langues détectées à la racine du plugin :")))
        for code, f in sorted(existing_langs.items()):
            print(f"  - {c.VALUE}{os.path.basename(f)}{c.RESET}")
        print()
        print(_("Cela indique une mise à jour manuelle sans passer par les outils standard."))
        print(_("Lancement automatique de AUTOSYNC pour synchroniser l'ensemble."))
        print()

        choice = input(c.prompt(_("Lancer AUTOSYNC ? [O/n]:") + " ")).strip().lower()
        if choice in ['o', 'oui', 'y', 'yes', '']:
            _launch_autosync(plugin_path)
        else:
            print(c.info(_("AUTOSYNC non lancé")))
        return

    # --- CAS 2 : Un seul fichier, même langue que le template → mise à jour ---
    if template_file and template_lang and template_lang in existing_langs:
        existing_name = os.path.basename(existing_langs[template_lang])

        print("\n" + _("Vous venez certainement de mettre à jour vos clés dans votre lua."))
        print(_("Un fichier {name} se trouve déjà à la racine de votre plugin.").format(name=existing_name))
        print(_("Il est très fortement conseillé de le remplacer afin de le mettre à jour avec"))
        print(_("votre dernière mise à jour."))
        print()

        choice = input(c.prompt(_("Remplacer le fichier déjà présent? [O/n]:") + " ")).strip().lower()

        if choice in ['o', 'oui', 'y', 'yes', '']:
            try:
                shutil.copy2(template_file, existing_langs[template_lang])
                print("\n" + c.success(_("Fichier remplacé : {name}").format(name=existing_name)))
            except Exception as e:
                print("\n" + c.error(_("Impossible de remplacer le fichier: {error}").format(error=e)))
        else:
            print(c.info(_("Fichier non remplacé")))
        return

    # --- Fichier existant mais pas de template correspondant : info simple ---
    print("\n" + _("Fichier(s) de traduction trouvé(s) à la racine du plugin :"))
    for f in existing_files:
        print(f"  - {c.VALUE}{os.path.basename(f)}{c.RESET}")
    print()
    print(c.info(_("Aucun template d'extraction ne correspond. Rien à faire.")))


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
  python Applicator_main.py --plugin-path ./plugin.lrplugin --extraction-dir ./plugin.lrplugin/__i18n_tmp__/Extractor/20260127_091234
            """
        )

        parser.add_argument('--plugin-path', required=True,
                            help='Chemin vers le repertoire du plugin (OBLIGATOIRE)')
        parser.add_argument('--extraction-dir', default=None,
                            help='Repertoire Extractor (defaut: auto-detection __i18n_tmp__/Extractor/)')
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
    # Si lancé directement (python main.py), re-lancer avec -m pour
    # préserver le contexte de package nécessaire aux imports relatifs
    if __package__ is None or __package__ == "":
        import subprocess
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.exit(subprocess.run(
            [sys.executable, "-m", "tools.applicator.main"] + sys.argv[1:],
            cwd=project_root
        ).returncode)
    main()
