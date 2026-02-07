#!/usr/bin/env python3
"""
Nom du fichier : extract.py

Dépendances : common

Description :
Module EXTRACT pour Translator.
Génère les fichiers TRANSLATE_xx.txt pour faciliter la traduction.

Produit des fichiers de traduction contenant :
  - Les clés nouvelles ou modifiées depuis la dernière version
  - Les clés à traduire pour une langue spécifique
  - Format simple pour traduction manuelle ou semi-automatique

Usage CLI :
Non fourni

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from .common import parse_translation_file, load_update_json, find_languages, c
from .config_loader import get_update_filename, get_reference_lang


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def run_extract(update_dir: str, lang: str, locales_dir: Optional[str] = None,
                output_dir: Optional[str] = None) -> str:
    """
    Génère un fichier TRANSLATE_xx.txt avec les clés à traduire.

    Args:
        update_dir: Répertoire contenant UPDATE_{lang}.json
        lang: Code langue cible (fr, de, es...)
        locales_dir: Répertoire des fichiers de langues existants
        output_dir: Répertoire de sortie (défaut: update_dir)

    Returns:
        Chemin du fichier généré
    """
    # Charger UPDATE_{lang}.json
    update_data = load_update_json(update_dir)
    if not update_data:
        update_filename = get_update_filename()
        raise FileNotFoundError(_("{update_filename} non trouvé dans: {update_dir}").format(update_filename=update_filename, update_dir=update_dir))

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

    from core.i18n import debug_i18n_context
    with debug_i18n_context(), open(output_file, 'w', encoding='utf-8') as f:
        f.write("# " + "=" * 70 + "\n")
        f.write(_("# FICHIER DE TRADUCTION - {var0}\n").format(var0=lang.upper()))
        f.write(_("# Généré: {var0}\n").format(var0=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.write(_("# Source: {update_dir}\n").format(update_dir=update_dir))
        f.write("# " + "=" * 70 + "\n")
        f.write(_("#\n"))
        f.write(_("# INSTRUCTIONS:\n"))
        f.write(_("# 1. Pour chaque entrée, écrivez la traduction après le symbole →\n"))
        f.write(_("# 2. Laissez vide pour garder la valeur EN par défaut\n"))
        f.write(_("# 3. Les lignes commençant par # sont ignorées\n"))
        f.write(_("#\n"))
        f.write("# " + "=" * 70 + "\n\n")

        # Section: Nouvelles clés
        if added_keys:
            f.write("# " + "-" * 70 + "\n")
            f.write(_("# NOUVELLES CLÉS ({var0})\n").format(var0=len(added_keys)))
            f.write("# " + "-" * 70 + "\n\n")

            for key in sorted(added_keys.keys()):
                en_value = added_keys[key]
                f.write(_("[KEY] {key}\n").format(key=key))
                f.write(_("[EN]  {en_value}\n").format(en_value=en_value))
                f.write(_("[{var0}] → \n").format(var0=lang.upper()))
                f.write("\n")

        # Section: Clés modifiées
        if changed_keys:
            f.write("# " + "-" * 70 + "\n")
            ref_lang = get_reference_lang().upper()
            f.write(_("# CLÉS MODIFIÉES ({var0}) - Le texte {ref_lang} a changé\n").format(var0=len(changed_keys), ref_lang=ref_lang))
            f.write("# " + "-" * 70 + "\n\n")

            for key in sorted(changed_keys.keys()):
                change = changed_keys[key]
                old_ref = change['old']
                new_ref = change['new']
                current_trans = existing_translations.get(key, '')

                f.write(_("[KEY] {key}\n").format(key=key))
                f.write(_("[{ref_lang} AVANT]  {old_ref}\n").format(ref_lang=ref_lang, old_ref=old_ref))
                f.write(_("[{ref_lang} APRÈS]  {new_ref}\n").format(ref_lang=ref_lang, new_ref=new_ref))
                if current_trans and current_trans != old_ref:
                    f.write(_("[{var0} ACTUEL] {current_trans}\n").format(var0=lang.upper(), current_trans=current_trans))
                f.write(_("[{var0}] → \n").format(var0=lang.upper()))
                f.write("\n")

        # Résumé
        f.write("# " + "=" * 70 + "\n")
        f.write(_("# TOTAL: {var0} nouvelles + {var1} modifiées\n").format(var0=len(added_keys), var1=len(changed_keys)))
        f.write("# " + "=" * 70 + "\n")

    return output_file


def run_extract_all(update_dir: str, locales_dir: Optional[str] = None,
                    output_dir: Optional[str] = None) -> List[str]:
    """
    Génère les fichiers TRANSLATE pour toutes les langues détectées.

    Args:
        update_dir: Répertoire contenant UPDATE_{lang}.json
        locales_dir: Répertoire des fichiers de langues existants
        output_dir: Répertoire de sortie

    Returns:
        Liste des fichiers générés
    """
    # Trouver les langues existantes
    languages = []

    if locales_dir and os.path.isdir(locales_dir):
        languages = find_languages(locales_dir, exclude_reference=True)

    # Si aucune langue trouvée, proposer français par défaut
    if not languages:
        languages = ['fr']

    generated_files = []
    for lang in sorted(languages):
        try:
            output_file = run_extract(update_dir, lang, locales_dir, output_dir)
            generated_files.append(output_file)
        except Exception as e:
            print(c.warning(_("Erreur pour {lang}: {e}").format(lang=lang, e=e)))

    return generated_files


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_extract(plugin_path: str = ""):
    """Menu interactif pour EXTRACT.

    Args:
        plugin_path: Chemin du plugin (optionnel) pour auto-détection
    """
    from .common import clear_screen, print_header, load_update_json
    from core.paths import find_latest_tool_output
    from core.menu_helpers import select_tool_output_dir

    clear_screen()
    print_header()
    print(_("\n{var0}EXTRACT{var1}: Générer fichiers de traduction").format(var0=c.INFO, var1=c.RESET))
    print(c.separator())

    # Auto-détection et sélection interactive du dossier UPDATE
    update_dir = None
    if plugin_path:
        update_dir = select_tool_output_dir(plugin_path, "Translator", "")
        if update_dir:
            print(_("\n{var0}[INFO]{var1} Dossier sélectionné: {var2}{update_dir}{var4}").format(var0=c.INFO, var1=c.RESET, var2=c.VALUE, update_dir=update_dir, var4=c.RESET))
        else:
            print(c.warning(_("Aucun dossier Translator sélectionné")))
            print(f"{c.DIM}  " + _("Lancez d'abord COMPARE ou spécifiez le dossier UPDATE manuellement") + f"{c.RESET}")

    if not update_dir:
        update_filename = get_update_filename()
        print(_("\n{var0}Dossier UPDATE{var1} (contenant {update_filename}):").format(var0=c.KEY, var1=c.RESET, update_filename=update_filename))
        update_dir = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not update_dir or not os.path.isdir(update_dir):
            print(c.error(_("Répertoire invalide.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

    # Vérifier UPDATE_{lang}.json
    if not load_update_json(update_dir):
        update_filename = get_update_filename()
        print(c.error(_("{update_filename} non trouvé.").format(update_filename=update_filename)))
        input(_("\nAppuyez sur Entrée..."))
        return None

    print(_("\n{var0}Répertoire des traductions existantes{var1} (Locales):").format(var0=c.KEY, var1=c.RESET))
    print(_("{var0}  (Pour récupérer les traductions actuelles des clés modifiées){var1}").format(var0=c.DIM, var1=c.RESET))
    print(_("{var0}  (Entrée pour ignorer){var1}").format(var0=c.DIM, var1=c.RESET))
    locales_dir = input(f"{c.PROMPT}  > {c.RESET}").strip() or None

    print(_("\n{var0}Langue(s) à générer{var1}:").format(var0=c.KEY, var1=c.RESET))
    print(_("{var0}  • Entrée = toutes les langues trouvées dans Locales{var1}").format(var0=c.DIM, var1=c.RESET))
    print(_("{var0}  • Ou spécifier: fr, de, es...{var1}").format(var0=c.DIM, var1=c.RESET))
    lang_input = input(f"{c.PROMPT}  > {c.RESET}").strip().lower()

    try:
        print(_("\n{var0}[INFO]{var1} Génération en cours...").format(var0=c.INFO, var1=c.RESET))

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
            print(_("{var0}  FICHIERS GÉNÉRÉS{var1}").format(var0=c.TITLE, var1=c.RESET))
            print(f"{c.HEADER}{'=' * 66}{c.RESET}")
            for f in generated:
                print(_("  {var0}[OK]{var1} {var2}{var3}{var4}").format(var0=c.OK, var1=c.RESET, var2=c.VALUE, var3=os.path.basename(f), var4=c.RESET))
            print()
            print(_("{var0}[INFO]{var1} PROCHAINE ÉTAPE:").format(var0=c.INFO, var1=c.RESET))
            print(_("  {var0}1. Éditez les fichiers et remplissez après chaque →{var1}").format(var0=c.DIM, var1=c.RESET))
            print(_("  {var0}2. Lancez INJECT pour réinjecter les traductions{var1}").format(var0=c.DIM, var1=c.RESET))
            print(_("  {var0}3. Lancez SYNC pour finaliser{var1}").format(var0=c.DIM, var1=c.RESET))

            return generated
        else:
            print(c.warning(_("Aucun fichier généré")))

    except Exception as e:
        print(c.error(_("Erreur: {e}").format(e=e)))

    input(_("\nAppuyez sur Entrée pour continuer..."))
    return None
