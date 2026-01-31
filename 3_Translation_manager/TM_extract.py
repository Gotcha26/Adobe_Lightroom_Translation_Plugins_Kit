#!/usr/bin/env python3
"""
TM_extract.py

Module EXTRACT pour TranslationManager.
Génère les fichiers TRANSLATE_xx.txt pour faciliter la traduction.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from TM_common import parse_translation_file, load_update_json, find_languages, c


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def run_extract(update_dir: str, lang: str, locales_dir: str = None,
                output_dir: str = None) -> str:
    """
    Génère un fichier TRANSLATE_xx.txt avec les clés à traduire.
    
    Args:
        update_dir: Répertoire contenant UPDATE_en.json
        lang: Code langue cible (fr, de, es...)
        locales_dir: Répertoire des fichiers de langues existants
        output_dir: Répertoire de sortie (défaut: update_dir)
    
    Returns:
        Chemin du fichier généré
    """
    # Charger UPDATE_en.json
    update_data = load_update_json(update_dir)
    if not update_data:
        raise FileNotFoundError(f"UPDATE_en.json non trouvé dans: {update_dir}")
    
    # Charger les traductions existantes si disponibles
    existing_translations = {}
    if locales_dir:
        existing_file = os.path.join(locales_dir, f'TranslatedStrings_{lang}.txt')
        if os.path.isfile(existing_file):
            existing_translations = parse_translation_file(existing_file)
    
    # Répertoire de sortie
    if not output_dir:
        output_dir = update_dir
    os.makedirs(output_dir, exist_ok=True)
    
    # Générer le fichier TRANSLATE
    output_file = os.path.join(output_dir, f'TRANSLATE_{lang}.txt')
    
    added_keys = update_data.get('added', {})
    changed_keys = update_data.get('changed', {})
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# " + "=" * 70 + "\n")
        f.write(f"# FICHIER DE TRADUCTION - {lang.upper()}\n")
        f.write(f"# Généré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Source: {update_dir}\n")
        f.write("# " + "=" * 70 + "\n")
        f.write("#\n")
        f.write("# INSTRUCTIONS:\n")
        f.write("# 1. Pour chaque entrée, écrivez la traduction après le symbole →\n")
        f.write("# 2. Laissez vide pour garder la valeur EN par défaut\n")
        f.write("# 3. Les lignes commençant par # sont ignorées\n")
        f.write("#\n")
        f.write("# " + "=" * 70 + "\n\n")
        
        # Section: Nouvelles clés
        if added_keys:
            f.write("# " + "-" * 70 + "\n")
            f.write(f"# NOUVELLES CLÉS ({len(added_keys)})\n")
            f.write("# " + "-" * 70 + "\n\n")
            
            for key in sorted(added_keys.keys()):
                en_value = added_keys[key]
                f.write(f"[KEY] {key}\n")
                f.write(f"[EN]  {en_value}\n")
                f.write(f"[{lang.upper()}] → \n")
                f.write("\n")
        
        # Section: Clés modifiées
        if changed_keys:
            f.write("# " + "-" * 70 + "\n")
            f.write(f"# CLÉS MODIFIÉES ({len(changed_keys)}) - Le texte EN a changé\n")
            f.write("# " + "-" * 70 + "\n\n")
            
            for key in sorted(changed_keys.keys()):
                change = changed_keys[key]
                old_en = change['old']
                new_en = change['new']
                current_trans = existing_translations.get(key, '')
                
                f.write(f"[KEY] {key}\n")
                f.write(f"[EN AVANT]  {old_en}\n")
                f.write(f"[EN APRÈS]  {new_en}\n")
                if current_trans and current_trans != old_en:
                    f.write(f"[{lang.upper()} ACTUEL] {current_trans}\n")
                f.write(f"[{lang.upper()}] → \n")
                f.write("\n")
        
        # Résumé
        f.write("# " + "=" * 70 + "\n")
        f.write(f"# TOTAL: {len(added_keys)} nouvelles + {len(changed_keys)} modifiées\n")
        f.write("# " + "=" * 70 + "\n")
    
    return output_file


def run_extract_all(update_dir: str, locales_dir: str = None,
                    output_dir: str = None) -> List[str]:
    """
    Génère les fichiers TRANSLATE pour toutes les langues détectées.
    
    Args:
        update_dir: Répertoire contenant UPDATE_en.json
        locales_dir: Répertoire des fichiers de langues existants
        output_dir: Répertoire de sortie
    
    Returns:
        Liste des fichiers générés
    """
    # Trouver les langues existantes
    languages = []
    
    if locales_dir and os.path.isdir(locales_dir):
        languages = find_languages(locales_dir, exclude_en=True)
    
    # Si aucune langue trouvée, proposer français par défaut
    if not languages:
        languages = ['fr']
    
    generated_files = []
    for lang in sorted(languages):
        try:
            output_file = run_extract(update_dir, lang, locales_dir, output_dir)
            generated_files.append(output_file)
        except Exception as e:
            print(f"  ⚠️  Erreur pour {lang}: {e}")
    
    return generated_files


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_extract(plugin_path: str = ""):
    """Menu interactif pour EXTRACT.

    Args:
        plugin_path: Chemin du plugin (optionnel) pour auto-détection
    """
    from TM_common import clear_screen, print_header, load_update_json
    from common.paths import find_latest_tool_output
    from common.menu_helpers import select_tool_output_dir

    clear_screen()
    print_header()
    print(f"\n{c.INFO}EXTRACT{c.RESET}: Générer fichiers de traduction")
    print(c.separator())

    # Auto-détection et sélection interactive du dossier UPDATE
    update_dir = None
    if plugin_path:
        update_dir = select_tool_output_dir(plugin_path, "TranslationManager", "")
        if update_dir:
            print(f"\n{c.INFO}[INFO]{c.RESET} Dossier sélectionné: {c.VALUE}{update_dir}{c.RESET}")
        else:
            print(c.warning("Aucun dossier TranslationManager sélectionné"))
            print(f"{c.DIM}  Lancez d'abord COMPARE ou spécifiez le dossier UPDATE manuellement{c.RESET}")

    if not update_dir:
        print(f"\n{c.KEY}Dossier UPDATE{c.RESET} (contenant UPDATE_en.json):")
        update_dir = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not update_dir or not os.path.isdir(update_dir):
            print(c.error("Répertoire invalide."))
            input("\nAppuyez sur Entrée...")
            return None

    # Vérifier UPDATE_en.json
    if not load_update_json(update_dir):
        print(c.error("UPDATE_en.json non trouvé."))
        input("\nAppuyez sur Entrée...")
        return None

    print(f"\n{c.KEY}Répertoire des traductions existantes{c.RESET} (Locales):")
    print(f"{c.DIM}  (Pour récupérer les traductions actuelles des clés modifiées){c.RESET}")
    print(f"{c.DIM}  (Entrée pour ignorer){c.RESET}")
    locales_dir = input(f"{c.PROMPT}  > {c.RESET}").strip() or None

    print(f"\n{c.KEY}Langue(s) à générer{c.RESET}:")
    print(f"{c.DIM}  • Entrée = toutes les langues trouvées dans Locales{c.RESET}")
    print(f"{c.DIM}  • Ou spécifier: fr, de, es...{c.RESET}")
    lang_input = input(f"{c.PROMPT}  > {c.RESET}").strip().lower()

    try:
        print(f"\n{c.INFO}[INFO]{c.RESET} Génération en cours...")

        if lang_input:
            languages = [l.strip() for l in lang_input.split(',')]
            generated = []
            for lang in languages:
                output_file = run_extract(update_dir, lang, locales_dir)
                generated.append(output_file)
        else:
            generated = run_extract_all(update_dir, locales_dir)

        if generated:
            print(f"\n{c.HEADER}{'=' * 66}{c.RESET}")
            print(f"{c.TITLE}  FICHIERS GÉNÉRÉS{c.RESET}")
            print(f"{c.HEADER}{'=' * 66}{c.RESET}")
            for f in generated:
                print(f"  {c.OK}[OK]{c.RESET} {c.VALUE}{os.path.basename(f)}{c.RESET}")
            print()
            print(f"{c.INFO}[INFO]{c.RESET} PROCHAINE ÉTAPE:")
            print(f"  {c.DIM}1. Éditez les fichiers et remplissez après chaque →{c.RESET}")
            print(f"  {c.DIM}2. Lancez INJECT pour réinjecter les traductions{c.RESET}")
            print(f"  {c.DIM}3. Lancez SYNC pour finaliser{c.RESET}")

            return generated
        else:
            print(c.warning("Aucun fichier généré"))

    except Exception as e:
        print(c.error(f"Erreur: {e}"))

    input("\nAppuyez sur Entrée pour continuer...")
    return None
