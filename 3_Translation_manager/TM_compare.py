#!/usr/bin/env python3
"""
TM_compare.py

Module COMPARE pour TranslationManager.
Compare deux versions du fichier EN et génère UPDATE_en.json + CHANGELOG.txt
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Optional

from TM_common import parse_translation_file, resolve_path, c


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

def run_compare(old_path: str, new_path: str, output_dir: str = None) -> str:
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
    
    # Copier le nouveau fichier EN comme référence
    new_en_file = os.path.join(output_dir, 'TranslatedStrings_en.txt')
    shutil.copy2(new_file, new_en_file)
    
    return output_dir


def _generate_changelog(file_path: str, result: Dict, old_file: str, new_file: str):
    """Génère le fichier CHANGELOG lisible."""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("CHANGELOG - Modifications des traductions EN\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Ancien: {old_file}\n")
        f.write(f"Nouveau: {new_file}\n\n")
        
        f.write("-" * 80 + "\n")
        f.write("RÉSUMÉ\n")
        f.write("-" * 80 + "\n")
        f.write(f"  Clés ajoutées    : {len(result['added']):4d}  [NEW]\n")
        f.write(f"  Clés modifiées   : {len(result['changed']):4d}  [CHANGED]\n")
        f.write(f"  Clés supprimées  : {len(result['deleted']):4d}  [DELETED]\n")
        f.write(f"  Clés inchangées  : {len(result['unchanged']):4d}\n")
        f.write("\n")
        
        if result['added']:
            f.write("=" * 80 + "\n")
            f.write(f"CLÉS AJOUTÉES ({len(result['added'])})\n")
            f.write("Ces clés doivent être traduites dans toutes les langues.\n")
            f.write("=" * 80 + "\n\n")
            for key in sorted(result['added'].keys()):
                value = result['added'][key]
                f.write(f"  [NEW] {key}\n")
                f.write(f"        EN: {value}\n\n")
        
        if result['changed']:
            f.write("=" * 80 + "\n")
            f.write(f"CLÉS MODIFIÉES ({len(result['changed'])})\n")
            f.write("Le texte anglais a changé. Les traductions doivent être révisées.\n")
            f.write("=" * 80 + "\n\n")
            for key in sorted(result['changed'].keys()):
                change = result['changed'][key]
                f.write(f"  [CHANGED] {key}\n")
                f.write(f"        AVANT: {change['old']}\n")
                f.write(f"        APRÈS: {change['new']}\n\n")
        
        if result['deleted']:
            f.write("=" * 80 + "\n")
            f.write(f"CLÉS SUPPRIMÉES ({len(result['deleted'])})\n")
            f.write("Ces clés n'existent plus et seront retirées des traductions.\n")
            f.write("=" * 80 + "\n\n")
            for key in result['deleted']:
                f.write(f"  [DELETED] {key}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("PROCHAINE ÉTAPE\n")
        f.write("=" * 80 + "\n")
        f.write("Lancez EXTRACT puis INJECT, ou directement SYNC:\n")
        f.write(f"  python TranslationManager.py extract --update {os.path.dirname(file_path)}\n")
        f.write(f"  python TranslationManager.py sync --update {os.path.dirname(file_path)}\n")


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_compare(plugin_path: str = ""):
    """Menu interactif pour COMPARE.

    Args:
        plugin_path: Chemin du plugin (optionnel) pour utiliser __i18n_tmp__
    """
    from TM_common import clear_screen, print_header
    from common.paths import get_tool_output_path

    clear_screen()
    print_header()
    print(f"\n{c.INFO}COMPARE{c.RESET}: Comparer deux versions EN")
    print(c.separator())

    print(f"\n{c.KEY}Fichier ANCIEN{c.RESET} (TranslatedStrings_en.txt ou répertoire):")
    old_path = input(f"{c.PROMPT}  > {c.RESET}").strip()
    if not old_path:
        print(c.error("Chemin requis."))
        input("\nAppuyez sur Entrée...")
        return None

    print(f"\n{c.KEY}Fichier NOUVEAU{c.RESET} (TranslatedStrings_en.txt ou répertoire):")
    new_path = input(f"{c.PROMPT}  > {c.RESET}").strip()
    if not new_path:
        print(c.error("Chemin requis."))
        input("\nAppuyez sur Entrée...")
        return None

    try:
        print(f"\n{c.INFO}[INFO]{c.RESET} Comparaison en cours...")

        # Déterminer le répertoire de sortie
        if plugin_path:
            output_dir = get_tool_output_path(plugin_path, "TranslationManager", create=True)
        else:
            output_dir = None  # run_compare créera un dossier local

        output_dir = run_compare(old_path, new_path, output_dir)

        # Charger le résultat pour affichage
        with open(os.path.join(output_dir, 'UPDATE_en.json'), 'r', encoding='utf-8') as f:
            result = json.load(f)

        summary = result['summary']
        print(f"\n{c.HEADER}{'=' * 66}{c.RESET}")
        print(f"{c.TITLE}  RÉSUMÉ{c.RESET}")
        print(f"{c.HEADER}{'=' * 66}{c.RESET}")
        print(f"  {c.KEY}Clés ajoutées   {c.RESET}: {c.GREEN}{summary['added']:4d}{c.RESET}  {c.DIM}[NEW]{c.RESET}")
        print(f"  {c.KEY}Clés modifiées  {c.RESET}: {c.YELLOW}{summary['changed']:4d}{c.RESET}  {c.DIM}[CHANGED]{c.RESET}")
        print(f"  {c.KEY}Clés supprimées {c.RESET}: {c.RED}{summary['deleted']:4d}{c.RESET}  {c.DIM}[DELETED]{c.RESET}")
        print(f"  {c.KEY}Clés inchangées {c.RESET}: {c.DIM}{summary['unchanged']:4d}{c.RESET}")
        print()
        print(c.success(f"Fichiers générés dans: {c.VALUE}{output_dir}{c.RESET}"))
        print(f"    {c.DIM}• UPDATE_en.json{c.RESET}")
        print(f"    {c.DIM}• CHANGELOG.txt{c.RESET}")
        print(f"    {c.DIM}• TranslatedStrings_en.txt{c.RESET}")

        if summary['added'] or summary['changed'] or summary['deleted']:
            print()
            print(f"{c.INFO}[INFO]{c.RESET} PROCHAINE ÉTAPE:")
            print(f"  {c.DIM}• EXTRACT pour générer les fichiers de traduction{c.RESET}")
            print(f"  {c.DIM}• ou SYNC directement pour utiliser EN par défaut{c.RESET}")

        return output_dir

    except FileNotFoundError as e:
        print(c.error(f"Fichier non trouvé: {e}"))
    except Exception as e:
        print(c.error(f"Erreur: {e}"))

    input("\nAppuyez sur Entrée pour continuer...")
    return None
