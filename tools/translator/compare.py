#!/usr/bin/env python3
"""
Nom du fichier : compare.py

Dépendances : common

Description :
Module COMPARE pour Translator.
Compare deux versions du fichier de la langue de référence et génère UPDATE_<ref>.json + CHANGELOG.txt

Analyse les différences entre deux versions :
  - Détecte les clés ajoutées, modifiées ou supprimées
  - Génère UPDATE_<ref>.json pour tracer les changements
  - Crée CHANGELOG.txt lisible pour le suivi des modifications
  - Aide à synchroniser les fichiers de langue avec les changements

Usage CLI :
Non fourni

Date : 2026-11-08
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import json
import shutil
import tempfile
from datetime import datetime
from typing import Dict, Optional

from .common import parse_translation_file, resolve_path, c
from .config_loader import get_reference_filename, get_reference_lang, get_update_filename
from core.i18n import _


# =============================================================================
# COMPARATEUR
# =============================================================================

class VersionComparator:
    """Compare deux versions du fichier de la langue de référence."""

    def __init__(self, old_strings: Dict[str, str], new_strings: Dict[str, str]):
        self.old = old_strings
        self.new = new_strings
        self.result = None

    def compare(self) -> Dict:
        """
        Compare les deux versions.

        Returns:
            {
                'added': {key: value},
                'changed': {key: {'old': x, 'new': y}},
                'deleted': [keys],
                'unchanged': [keys]
            }
        """
        added = {}
        changed = {}
        deleted = []
        unchanged = []

        for key, old_val in self.old.items():
            if key in self.new:
                new_val = self.new[key]
                if old_val == new_val:
                    unchanged.append(key)
                else:
                    changed[key] = {'old': old_val, 'new': new_val}
            else:
                deleted.append(key)

        for key, val in self.new.items():
            if key not in self.old:
                added[key] = val

        self.result = {
            'added': added,
            'changed': changed,
            'deleted': sorted(deleted),
            'unchanged': sorted(unchanged)
        }

        return self.result


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def run_compare(old_path: str, new_path: str, output_dir: Optional[str] = None) -> str:
    """
    Compare deux versions du fichier de la langue de référence.

    Args:
        old_path: Ancien fichier de référence (ou répertoire)
        new_path: Nouveau fichier de référence (ou répertoire)
        output_dir: Répertoire de sortie (défaut: dossier temporaire système)

    Returns:
        Chemin du répertoire de sortie
    """
    # Résoudre les chemins
    _dir, old_file = resolve_path(old_path)
    _dir, new_file = resolve_path(new_path)

    # Créer répertoire de sortie
    if not output_dir:
        output_dir = tempfile.mkdtemp(prefix="i18n_kit_")
        print(_("Dossier de sortie temporaire : {path}").format(path=output_dir))
    os.makedirs(output_dir, exist_ok=True)

    # Parser les fichiers
    old_strings = parse_translation_file(old_file)
    new_strings = parse_translation_file(new_file)

    # Comparer
    comparator = VersionComparator(old_strings, new_strings)
    result = comparator.compare()

    # Générer UPDATE_<ref>.json
    update_data = {
        'generated': datetime.now().isoformat(),
        'old_file': os.path.abspath(old_file),
        'new_file': os.path.abspath(new_file),
        'summary': {
            'added': len(result['added']),
            'changed': len(result['changed']),
            'deleted': len(result['deleted']),
            'unchanged': len(result['unchanged']),
            'total_old': len(old_strings),
            'total_new': len(new_strings)
        },
        'added': result['added'],
        'changed': result['changed'],
        'deleted': result['deleted'],
        # Inclure aussi les clés inchangées avec leurs valeurs pour référence complète
        'unchanged_keys': result['unchanged'],
        'all_new_strings': new_strings  # Toutes les clés de la nouvelle version
    }

    update_file = os.path.join(output_dir, get_update_filename())
    with open(update_file, 'w', encoding='utf-8') as f:
        json.dump(update_data, f, indent=2, ensure_ascii=False)

    # Générer CHANGELOG.txt
    changelog_file = os.path.join(output_dir, 'CHANGELOG.txt')
    _generate_changelog(changelog_file, result, old_file, new_file)

    # Copier l'ancien fichier de référence pour traçabilité
    old_ref_file = os.path.join(output_dir, 'old_' + get_reference_filename())
    shutil.copy2(old_file, old_ref_file)

    # Copier le nouveau fichier de référence comme référence
    new_ref_file = os.path.join(output_dir, get_reference_filename())
    shutil.copy2(new_file, new_ref_file)

    return output_dir


def _generate_changelog(file_path: str, result: Dict, old_file: str, new_file: str):
    """Génère le fichier CHANGELOG lisible."""
    from core.i18n import debug_i18n_context

    ref_lang = get_reference_lang()
    with debug_i18n_context(), open(file_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(_("CHANGELOG - Modifications des traductions {lang}\n").format(lang=ref_lang))
        f.write("=" * 80 + "\n\n")

        f.write(_("Date: {var0}\n").format(var0=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.write(_("Ancien: {old_file}\n").format(old_file=old_file))
        f.write(_("Nouveau: {new_file}\n\n").format(new_file=new_file))

        f.write("-" * 80 + "\n")
        f.write(_("RÉSUMÉ\n"))
        f.write("-" * 80 + "\n")
        f.write(_("  Clés ajoutées    : {var0:4d}  [NEW]\n").format(var0=len(result['added'])))
        f.write(_("  Clés modifiées   : {var0:4d}  [CHANGED]\n").format(var0=len(result['changed'])))
        f.write(_("  Clés supprimées  : {var0:4d}  [DELETED]\n").format(var0=len(result['deleted'])))
        f.write(_("  Clés inchangées  : {var0:4d}\n").format(var0=len(result['unchanged'])))
        f.write("\n")

        if result['added']:
            f.write("=" * 80 + "\n")
            f.write(_("CLÉS AJOUTÉES ({var0})\n").format(var0=len(result['added'])))
            f.write(_("Ces clés doivent être traduites dans toutes les langues.\n"))
            f.write("=" * 80 + "\n\n")
            for key in sorted(result['added'].keys()):
                value = result['added'][key]
                f.write(_("  [NEW] {key}\n").format(key=key))
                f.write(_("        {lang}: {value}\n\n").format(lang=ref_lang, value=value))

        if result['changed']:
            f.write("=" * 80 + "\n")
            f.write(_("CLÉS MODIFIÉES ({var0})\n").format(var0=len(result['changed'])))
            f.write(_("Le texte {lang} a changé. Les traductions doivent être révisées.\n").format(lang=ref_lang))
            f.write("=" * 80 + "\n\n")
            for key in sorted(result['changed'].keys()):
                change = result['changed'][key]
                f.write(_("  [CHANGED] {key}\n").format(key=key))
                f.write(_("        AVANT: {var0}\n").format(var0=change['old']))
                f.write(_("        APRÈS: {var0}\n\n").format(var0=change['new']))

        if result['deleted']:
            f.write("=" * 80 + "\n")
            f.write(_("CLÉS SUPPRIMÉES ({var0})\n").format(var0=len(result['deleted'])))
            f.write(_("Ces clés n'existent plus et seront retirées des traductions.\n"))
            f.write("=" * 80 + "\n\n")
            for key in result['deleted']:
                f.write(_("  [DELETED] {key}\n").format(key=key))

        f.write("\n" + "=" * 80 + "\n")
        f.write(_("PROCHAINE ÉTAPE\n"))
        f.write("=" * 80 + "\n")
        f.write(_("Lancez EXTRACT puis INJECT, ou directement SYNC:\n"))
        f.write("  python -m tools.translator.main extract --update {var0}\n".format(var0=os.path.dirname(file_path)))
        f.write("  python -m tools.translator.main sync --update {var0}\n".format(var0=os.path.dirname(file_path)))


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_compare(plugin_path: str = ""):
    """Menu interactif pour COMPARE.

    Args:
        plugin_path: Chemin du plugin (optionnel) pour utiliser __i18n_tmp__
    """
    from .common import clear_screen, print_header
    from core.paths import get_tool_output_path

    clear_screen()
    print_header()
    print(_("\n{var0}COMPARE{var1}: Comparer deux versions {lang}").format(var0=c.INFO, var1=c.RESET, lang=get_reference_lang()))
    print(c.separator())

    print(_("\n{var0}Fichier ANCIEN{var1} ({var2} ou répertoire):").format(var0=c.KEY, var1=c.RESET, var2=get_reference_filename()))
    old_path = input(f"{c.PROMPT}  > {c.RESET}").strip()
    if not old_path:
        print(c.error(_("Chemin requis.")))
        input(_("\nAppuyez sur Entrée..."))
        return None

    print(_("\n{var0}Fichier NOUVEAU{var1} ({var2} ou répertoire):").format(var0=c.KEY, var1=c.RESET, var2=get_reference_filename()))
    new_path = input(f"{c.PROMPT}  > {c.RESET}").strip()
    if not new_path:
        print(c.error(_("Chemin requis.")))
        input(_("\nAppuyez sur Entrée..."))
        return None

    try:
        print(_("\n{var0}[INFO]{var1} Comparaison en cours...").format(var0=c.INFO, var1=c.RESET))

        # Déterminer le répertoire de sortie
        if plugin_path:
            output_dir = get_tool_output_path(plugin_path, "Translator", create=True)
        else:
            output_dir = None  # run_compare utilisera un dossier temporaire

        output_dir = run_compare(old_path, new_path, output_dir)

        # Charger le résultat pour affichage
        with open(os.path.join(output_dir, get_update_filename()), 'r', encoding='utf-8') as f:
            result = json.load(f)

        summary = result['summary']
        print(f"\n{c.HEADER}{'=' * 66}{c.RESET}")
        print(_("{var0}  RÉSUMÉ{var1}").format(var0=c.TITLE, var1=c.RESET))
        print(f"{c.HEADER}{'=' * 66}{c.RESET}")
        print(_("  {var0}Clés ajoutées   {var1}: {var2}{var3:4d}{var4}  {var5}[NEW]{var6}").format(var0=c.KEY, var1=c.RESET, var2=c.GREEN, var3=summary['added'], var4=c.RESET, var5=c.DIM, var6=c.RESET))
        print(_("  {var0}Clés modifiées  {var1}: {var2}{var3:4d}{var4}  {var5}[CHANGED]{var6}").format(var0=c.KEY, var1=c.RESET, var2=c.YELLOW, var3=summary['changed'], var4=c.RESET, var5=c.DIM, var6=c.RESET))
        print(_("  {var0}Clés supprimées {var1}: {var2}{var3:4d}{var4}  {var5}[DELETED]{var6}").format(var0=c.KEY, var1=c.RESET, var2=c.RED, var3=summary['deleted'], var4=c.RESET, var5=c.DIM, var6=c.RESET))
        print(_("  {var0}Clés inchangées {var1}: {var2}{var3:4d}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.DIM, var3=summary['unchanged'], var4=c.RESET))
        print()
        print(c.success(_("Fichiers générés dans: {var0}{output_dir}{var2}").format(var0=c.VALUE, output_dir=output_dir, var2=c.RESET)))
        print(_("    {var0}• {var2}{var1}").format(var0=c.DIM, var1=c.RESET, var2=get_update_filename()))
        print(_("    {var0}• CHANGELOG.txt{var1}").format(var0=c.DIM, var1=c.RESET))
        print(_("    {var0}• {var2}{var1}").format(var0=c.DIM, var1=c.RESET, var2=get_reference_filename()))

        if summary['added'] or summary['changed'] or summary['deleted']:
            print()
            print(_("{var0}[INFO]{var1} PROCHAINE ÉTAPE:").format(var0=c.INFO, var1=c.RESET))
            print(_("  {var0}• EXTRACT pour générer les fichiers de traduction{var1}").format(var0=c.DIM, var1=c.RESET))
            print(_("  {var0}• ou SYNC directement pour utiliser {lang} par défaut{var1}").format(var0=c.DIM, var1=c.RESET, lang=get_reference_lang()))

        return output_dir

    except FileNotFoundError as e:
        print(c.error(_("Fichier non trouvé: {e}").format(e=e)))
    except Exception as e:
        print(c.error(_("Erreur: {e}").format(e=e)))

    input(_("\nAppuyez sur Entrée pour continuer..."))
    return None
