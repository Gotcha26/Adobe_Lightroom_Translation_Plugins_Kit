#!/usr/bin/env python3
"""
Nom du fichier : compare.py

Dépendances : common

Description :
Module COMPARE pour Translator.
Compare deux versions du fichier EN et génère UPDATE_en.json + CHANGELOG.txt

Analyse les différences entre deux versions :
  - Détecte les clés ajoutées, modifiées ou supprimées
  - Génère UPDATE_en.json pour tracer les changements
  - Crée CHANGELOG.txt lisible pour le suivi des modifications
  - Aide à synchroniser les fichiers de langue avec les changements

Usage CLI :
Non fourni

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Optional

from .common import parse_translation_file, resolve_path, c
from core.i18n import _


# =============================================================================
# COMPARATEUR
# =============================================================================

class VersionComparator:
    """Compare deux versions du fichier EN."""

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
    Compare deux versions du fichier EN.

    Args:
        old_path: Ancien fichier EN (ou répertoire)
        new_path: Nouveau fichier EN (ou répertoire)
        output_dir: Répertoire de sortie (défaut: timestampé)

    Returns:
        Chemin du répertoire de sortie
    """
    # Résoudre les chemins
    _, old_file = resolve_path(old_path)
    _, new_file = resolve_path(new_path)

    # Créer répertoire de sortie
    if not output_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), timestamp)
    os.makedirs(output_dir, exist_ok=True)

    # Parser les fichiers
    old_strings = parse_translation_file(old_file)
    new_strings = parse_translation_file(new_file)

    # Comparer
    comparator = VersionComparator(old_strings, new_strings)
    result = comparator.compare()

    # Générer UPDATE_en.json
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

    update_file = os.path.join(output_dir, 'UPDATE_en.json')
    with open(update_file, 'w', encoding='utf-8') as f:
        json.dump(update_data, f, indent=2, ensure_ascii=False)

    # Générer CHANGELOG.txt
    changelog_file = os.path.join(output_dir, 'CHANGELOG.txt')
    _generate_changelog(changelog_file, result, old_file, new_file)

    # Copier l'ancien fichier EN pour traçabilité
    old_en_file = os.path.join(output_dir, 'old_TranslatedStrings_en.txt')
    shutil.copy2(old_file, old_en_file)

    # Copier le nouveau fichier EN comme référence
    new_en_file = os.path.join(output_dir, 'TranslatedStrings_en.txt')
    shutil.copy2(new_file, new_en_file)

    return output_dir


def _generate_changelog(file_path: str, result: Dict, old_file: str, new_file: str):
    """Génère le fichier CHANGELOG lisible."""
    from core.i18n import debug_i18n_context

    with debug_i18n_context(), open(file_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(_("CHANGELOG - Modifications des traductions EN\n"))
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
                f.write(_("        EN: {value}\n\n").format(value=value))

        if result['changed']:
            f.write("=" * 80 + "\n")
            f.write(_("CLÉS MODIFIÉES ({var0})\n").format(var0=len(result['changed'])))
            f.write(_("Le texte anglais a changé. Les traductions doivent être révisées.\n"))
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
        f.write("  python Translator_main.py extract --update {var0}\n".format(var0=os.path.dirname(file_path)))
        f.write("  python Translator_main.py sync --update {var0}\n".format(var0=os.path.dirname(file_path)))


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
    print(_("\n{var0}COMPARE{var1}: Comparer deux versions EN").format(var0=c.INFO, var1=c.RESET))
    print(c.separator())

    print(_("\n{var0}Fichier ANCIEN{var1} (TranslatedStrings_en.txt ou répertoire):").format(var0=c.KEY, var1=c.RESET))
    old_path = input(f"{c.PROMPT}  > {c.RESET}").strip()
    if not old_path:
        print(c.error(_("Chemin requis.")))
        input(_("\nAppuyez sur Entrée..."))
        return None

    print(_("\n{var0}Fichier NOUVEAU{var1} (TranslatedStrings_en.txt ou répertoire):").format(var0=c.KEY, var1=c.RESET))
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
            output_dir = None  # run_compare créera un dossier local

        output_dir = run_compare(old_path, new_path, output_dir)

        # Charger le résultat pour affichage
        with open(os.path.join(output_dir, 'UPDATE_en.json'), 'r', encoding='utf-8') as f:
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
        print(_("    {var0}• UPDATE_en.json{var1}").format(var0=c.DIM, var1=c.RESET))
        print(_("    {var0}• CHANGELOG.txt{var1}").format(var0=c.DIM, var1=c.RESET))
        print(_("    {var0}• TranslatedStrings_en.txt{var1}").format(var0=c.DIM, var1=c.RESET))

        if summary['added'] or summary['changed'] or summary['deleted']:
            print()
            print(_("{var0}[INFO]{var1} PROCHAINE ÉTAPE:").format(var0=c.INFO, var1=c.RESET))
            print(_("  {var0}• EXTRACT pour générer les fichiers de traduction{var1}").format(var0=c.DIM, var1=c.RESET))
            print(_("  {var0}• ou SYNC directement pour utiliser EN par défaut{var1}").format(var0=c.DIM, var1=c.RESET))

        return output_dir

    except FileNotFoundError as e:
        print(c.error(_("Fichier non trouvé: {e}").format(e=e)))
    except Exception as e:
        print(c.error(_("Erreur: {e}").format(e=e)))

    input(_("\nAppuyez sur Entrée pour continuer..."))
    return None
