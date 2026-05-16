#!/usr/bin/env python3
"""
Nom du fichier : addlang.py

Dépendances : common.paths, common.colors

Description :
Ajoute ou réinstalle un fichier de langue spécifique dans le plugin.

Cette commande permet d'installer une langue individuellement, soit depuis
une extraction Extractor existante, soit en créant un nouveau fichier basé
sur le fichier EN de référence.

Cas d'usage :
  1. Installation différée: installer une langue non installée initialement
  2. Ajout de nouvelles langues: préparer de nouveaux fichiers pour traduction
  3. Réinstallation: remplacer un fichier de langue corrompu ou supprimé

Modes disponibles :
  Mode A: Installer depuis Extractor (copie d'un fichier existant)
  Mode B: Créer un nouveau fichier (basé sur le fichier EN de référence)

Usage CLI :
    python addlang.py                    # Menu interactif
    python addlang.py /path/to/plugin    # Chemin direct du plugin

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import re
import shutil
from typing import Optional, List, Tuple, Dict
from datetime import datetime

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.paths import find_latest_tool_output, get_tool_output_path
from core.colors import Colors
from core.i18n import _

from .common import (
    clear_screen, print_header, parse_translation_file,
    write_translation_file
)

c = Colors()


# =============================================================================
# VALIDATION
# =============================================================================

def validate_language_code(lang_code: str) -> Tuple[bool, str, Optional[str]]:
    """
    Valide un code langue selon ISO 639-1 (2 lettres).

    Args:
        lang_code: Code langue à valider

    Returns:
        (is_valid, normalized_code, error_message)
    """
    if not lang_code:
        return False, "", "Code langue vide"

    # Normaliser: minuscules, strip
    normalized = lang_code.strip().lower()

    # Vérifier format: exactement 2 lettres
    if not re.match(r'^[a-z]{2}$', normalized):
        return False, normalized, _("Code langue invalide (doit être 2 lettres, ex: fr, de, es)")

    # Réserver la langue de référence pour éviter confusion
    if is_reference_lang(normalized):
        ref_lang = get_reference_lang().upper()
        return False, normalized, _("Utilisez INSTALL pour le fichier {ref_lang} de référence").format(ref_lang=ref_lang)

    return True, normalized, None


def check_existing_language(plugin_path: str, lang_code: str) -> Tuple[bool, Optional[str]]:
    """
    Vérifie si un fichier de langue existe déjà dans le plugin.

    Args:
        plugin_path: Chemin du plugin
        lang_code: Code langue (2 lettres)

    Returns:
        (exists, file_path or None)
    """
    if not os.path.isdir(plugin_path):
        return False, None

    filename = "TranslatedStrings_{lang_code}.txt".format(lang_code=lang_code)
    file_path = os.path.join(plugin_path, filename)

    if os.path.isfile(file_path):
        return True, file_path

    return False, None


# =============================================================================
# DETECTION ET LISTING
# =============================================================================

def list_installed_languages(plugin_path: str) -> List[str]:
    """
    Liste toutes les langues installées dans le plugin.

    Args:
        plugin_path: Chemin du plugin

    Returns:
        Liste des codes langue (ex: ['en', 'fr'])
    """
    languages = []

    if not os.path.isdir(plugin_path):
        return languages

    for filename in os.listdir(plugin_path):
        if filename.startswith("TranslatedStrings_") and filename.endswith(".txt"):
            lang_code = filename.replace("TranslatedStrings_", "").replace(".txt", "")
            languages.append(lang_code)

    return sorted(languages)


def list_available_languages_in_extraction(extraction_dir: str) -> List[str]:
    """
    Liste les langues disponibles dans un dossier d'extraction.

    Args:
        extraction_dir: Chemin du dossier d'extraction

    Returns:
        Liste des codes langue (ex: ['en', 'fr', 'de'])
    """
    languages = []

    if not os.path.isdir(extraction_dir):
        return languages

    for filename in os.listdir(extraction_dir):
        if filename.startswith("TranslatedStrings_") and filename.endswith(".txt"):
            lang_code = filename.replace("TranslatedStrings_", "").replace(".txt", "")
            languages.append(lang_code)

    return sorted(languages)


def get_reference_file(plugin_path: str) -> Optional[str]:
    """
    Trouve le fichier de référence (basé sur config.json["lang"]).

    Priorité:
      1. Dernière extraction Extractor
      2. Plugin racine

    Args:
        plugin_path: Chemin du plugin

    Returns:
        Chemin du fichier de référence ou None
    """
    ref_filename = get_reference_filename()

    # Priorité 1: Dernière extraction
    latest_extraction = find_latest_tool_output(plugin_path, "Extractor")
    if latest_extraction:
        ref_file = os.path.join(latest_extraction, ref_filename)
        if os.path.isfile(ref_file):
            return ref_file

    # Priorité 2: Plugin racine
    ref_file = os.path.join(plugin_path, ref_filename)
    if os.path.isfile(ref_file):
        return ref_file

    return None


# =============================================================================
# MODE A : INSTALLER DEPUIS EXTRACTOR
# =============================================================================

def install_language_from_extraction(plugin_path: str, lang_code: str,
                                     extraction_dir: Optional[str] = None,
                                     force: bool = False) -> bool:
    """
    Installe un fichier de langue depuis l'extraction Extractor.

    Args:
        plugin_path: Chemin du plugin
        lang_code: Code langue (2 lettres)
        extraction_dir: Dossier d'extraction (auto-détecté si None)
        force: Écraser sans demander si fichier existe

    Returns:
        True si succès
    """
    # Auto-détecter l'extraction si non fournie
    if not extraction_dir:
        extraction_dir = find_latest_tool_output(plugin_path, "Extractor")
        if not extraction_dir:
            print(c.error(_("Aucune extraction Extractor trouvée")))
            return False

    # Vérifier que le fichier source existe
    source_filename = "TranslatedStrings_{lang_code}.txt".format(lang_code=lang_code)
    source_path = os.path.join(extraction_dir, source_filename)

    if not os.path.isfile(source_path):
        print(c.error(f"Fichier {source_filename} introuvable dans l'extraction"))
        print(f"  {c.DIM}→ {extraction_dir}{c.RESET}")
        return False

    # Vérifier si le fichier existe déjà dans le plugin
    dest_path = os.path.join(plugin_path, source_filename)
    exists = os.path.isfile(dest_path)

    if exists and not force:
        print(_("\n{var0}[ATTENTION]{var1} Le fichier {var2}{source_filename}{var4} existe déjà dans le plugin.").format(var0=c.WARNING, var1=c.RESET, var2=c.VALUE, source_filename=source_filename, var4=c.RESET))
        print()
        choice = input(_("{var0}Écraser? (o/N): {var1}").format(var0=c.PROMPT, var1=c.RESET)).strip().lower()
        if choice not in ['o', 'oui', 'y', 'yes']:
            print(c.warning(_("Installation annulée")))
            return False

        # Créer backup avant écrasement
        backup_created = create_backup(plugin_path, lang_code)
        if backup_created:
            print(c.success(_("Backup créé: {backup_created}").format(backup_created=backup_created)))

    # Copier le fichier
    try:
        shutil.copy2(source_path, dest_path)
        print()
        print(c.success(_("✓ Fichier installé: {source_filename}").format(source_filename=source_filename)))
        print(f"  {c.DIM}→ {dest_path}{c.RESET}")
        return True
    except Exception as e:
        print(c.error(_("Erreur lors de la copie: {e}").format(e=e)))
        return False


# =============================================================================
# MODE B : CREER NOUVEAU FICHIER
# =============================================================================

def create_language_from_reference(plugin_path: str, lang_code: str,
                                   ref_file: Optional[str] = None,
                                   force: bool = False) -> bool:
    """
    Crée un nouveau fichier de langue basé sur le fichier EN de référence.

    Args:
        plugin_path: Chemin du plugin
        lang_code: Code langue (2 lettres)
        ref_file: Fichier EN de référence (auto-détecté si None)
        force: Écraser sans demander si fichier existe

    Returns:
        True si succès
    """
    # Trouver le fichier EN de référence si non fourni
    if not ref_file:
        ref_file = get_reference_file(plugin_path)
        if not ref_file:
            ref_lang = get_reference_lang().upper()
            ref_filename = get_reference_filename()
            print(c.error(_("Aucun fichier {ref_lang} de référence trouvé").format(ref_lang=ref_lang)))
            print()
            print(_("{var0}Vérifiez que:{var1}").format(var0=c.DIM, var1=c.RESET))
            print(f"  - {c.DIM}L'Extractor a été lancé{c.RESET}")
            print(_("  - {var0}{ref_filename} existe dans le plugin{var2}").format(var0=c.DIM, ref_filename=ref_filename, var2=c.RESET))
            return False

    # Parser le fichier de référence
    try:
        ref_translations = parse_translation_file(ref_file)
    except Exception as e:
        ref_lang = get_reference_lang().upper()
        print(c.error(_("Erreur lors de la lecture du fichier {ref_lang}: {e}").format(ref_lang=ref_lang, e=e)))
        return False

    if not ref_translations:
        print(c.error(_("Aucune clé trouvée dans le fichier EN de référence")))
        return False

    # Vérifier si le fichier existe déjà
    dest_filename = "TranslatedStrings_{lang_code}.txt".format(lang_code=lang_code)
    dest_path = os.path.join(plugin_path, dest_filename)
    exists = os.path.isfile(dest_path)

    if exists and not force:
        print(_("\n{var0}[ATTENTION]{var1} Le fichier {var2}{dest_filename}{var4} existe déjà dans le plugin.").format(var0=c.WARNING, var1=c.RESET, var2=c.VALUE, dest_filename=dest_filename, var4=c.RESET))
        print()
        choice = input(_("{var0}Écraser? (o/N): {var1}").format(var0=c.PROMPT, var1=c.RESET)).strip().lower()
        if choice not in ['o', 'oui', 'y', 'yes']:
            print(c.warning(_("Création annulée")))
            return False

        # Créer backup avant écrasement
        backup_created = create_backup(plugin_path, lang_code)
        if backup_created:
            print(c.success(_("Backup créé: {backup_created}").format(backup_created=backup_created)))

    # Créer le nouveau fichier avec valeurs EN par défaut
    try:
        metadata = {
            'source': ref_file,
            'note': 'Generated with default EN values - Ready for translation'
        }

        write_translation_file(
            dest_path,
            lang_code,
            ref_translations,
            markers={},
            metadata=metadata
        )

        print()
        print(c.success(_("✓ Fichier créé: {dest_filename}").format(dest_filename=dest_filename)))
        print(f"  {c.DIM}→ {dest_path}{c.RESET}")
        print()
        print(_("{var0}[INFO]{var1} Le fichier contient:").format(var0=c.INFO, var1=c.RESET))
        print(_("  • {var0}{var1}{var2} clés").format(var0=c.WHITE, var1=len(ref_translations), var2=c.RESET))
        print(_("  • Valeurs EN par défaut (à traduire)"))
        print()
        print(_("{var0}Prochaines étapes:{var1}").format(var0=c.INFO, var1=c.RESET))
        print(_("  1. Ouvrez {var0}{dest_filename}{var2} dans un éditeur").format(var0=c.VALUE, dest_filename=dest_filename, var2=c.RESET))
        print(_("  2. Traduisez les valeurs dans la langue cible"))
        print(_("  3. Testez le plugin dans Lightroom"))

        return True

    except Exception as e:
        print(c.error(_("Erreur lors de la création du fichier: {e}").format(e=e)))
        return False


# =============================================================================
# BACKUP
# =============================================================================

def create_backup(plugin_path: str, lang_code: str) -> Optional[str]:
    """
    Crée un backup d'un fichier de langue avant écrasement.

    Args:
        plugin_path: Chemin du plugin
        lang_code: Code langue

    Returns:
        Chemin du backup créé ou None si erreur
    """
    source_filename = "TranslatedStrings_{lang_code}.txt".format(lang_code=lang_code)
    source_path = os.path.join(plugin_path, source_filename)

    if not os.path.isfile(source_path):
        return None

    # Créer le dossier de backup dans __i18n_tmp__/Translator/<timestamp>/backups/
    translator_output = get_tool_output_path(plugin_path, "Translator", create=True)
    backup_dir = os.path.join(translator_output, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    # Nom du backup avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = _("{source_filename}.{timestamp}.bak").format(source_filename=source_filename, timestamp=timestamp)
    backup_path = os.path.join(backup_dir, backup_filename)

    try:
        shutil.copy2(source_path, backup_path)
        return backup_path
    except Exception as e:
        print(c.warning(_("Impossible de créer le backup: {e}").format(e=e)))
        return None


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_addlang(plugin_path: str):
    """Menu interactif pour ajouter une langue."""
    clear_screen()
    print_header()

    print(_("\n{var0}  ADD LANGUAGE - Ajouter une langue au plugin{var1}").format(var0=c.TITLE, var1=c.RESET))
    print(c.separator())

    # Vérifier si le plugin est configuré
    if not plugin_path or not os.path.isdir(plugin_path):
        print(c.error(_("Plugin non configuré ou introuvable.")))
        print()
        print(_("Configurez d'abord le chemin du plugin dans le menu principal."))
        return

    plugin_name = os.path.basename(plugin_path)
    print(_("\n{var0}[INFO]{var1} Plugin: {var2}{plugin_name}{var4}").format(var0=c.INFO, var1=c.RESET, var2=c.VALUE, plugin_name=plugin_name, var4=c.RESET))

    # Lister les langues installées
    installed_langs = list_installed_languages(plugin_path)
    if installed_langs:
        print(_("\n{var0}Langues actuellement installées:{var1}").format(var0=c.INFO, var1=c.RESET))
        for lang in installed_langs:
            print(_("  {var0}✓{var1} {var2}{lang}{var4} (TranslatedStrings_{lang}.txt)").format(var0=c.OK, var1=c.RESET, var2=c.VALUE, lang=lang, var4=c.RESET))
    else:
        print(_("\n{var0}Aucune langue installée dans le plugin{var1}").format(var0=c.WARNING, var1=c.RESET))

    # Menu de sélection du mode
    print()
    print(c.separator())
    print(f"{c.INFO}Sélectionnez le mode d'ajout:{c.RESET}")
    print(c.separator())
    print()
    print(_("  {var0}1{var1}. {var2}Installer depuis Extractor{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.SUCCESS, var3=c.RESET))
    print(_("     {var0}Copie un fichier TranslatedStrings_xx.txt existant depuis la{var1}").format(var0=c.DIM, var1=c.RESET))
    print(_("     {var0}dernière extraction Extractor vers le plugin.{var1}").format(var0=c.DIM, var1=c.RESET))
    print(f"     {c.DIM}→ Utile si le fichier existe déjà dans l'extraction{c.RESET}")
    print()
    print(_("  {var0}2{var1}. {var2}Créer un nouveau fichier de langue{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.SUCCESS, var3=c.RESET))
    print(_("     {var0}Génère un nouveau TranslatedStrings_xx.txt basé sur le fichier EN{var1}").format(var0=c.DIM, var1=c.RESET))
    print(_("     {var0}de référence, avec toutes les clés et valeurs EN par défaut.{var1}").format(var0=c.DIM, var1=c.RESET))
    print(_("     {var0}→ Utile pour préparer une nouvelle langue à traduire{var1}").format(var0=c.DIM, var1=c.RESET))
    print()
    print(_("  {var0}0{var1}. {var2}Retour{var3}").format(var0=c.YELLOW, var1=c.RESET, var2=c.DIM, var3=c.RESET))
    print()

    choice = input(c.prompt(_("Votre choix:") + " (0-2): ")).strip()

    if choice == '1':
        menu_mode_a_install_from_extraction(plugin_path, installed_langs)
    elif choice == '2':
        menu_mode_b_create_new(plugin_path, installed_langs)
    elif choice == '0':
        return
    else:
        print(c.error(_("Choix invalide")))


def menu_mode_a_install_from_extraction(plugin_path: str, installed_langs: List[str]):
    """Sous-menu Mode A : Installer depuis Extractor."""
    clear_screen()
    print_header()

    print(_("\n{var0}  MODE : Installer depuis Extractor{var1}").format(var0=c.TITLE, var1=c.RESET))
    print(c.separator())

    # Trouver la dernière extraction
    latest_extraction = find_latest_tool_output(plugin_path, "Extractor")

    if not latest_extraction:
        print(c.error(_("Aucune extraction Extractor trouvée")))
        print()
        print(_("Lancez d'abord l'Extractor pour générer les fichiers de langue."))
        return

    print(_("\n{var0}[INFO]{var1} Dernière extraction détectée:").format(var0=c.INFO, var1=c.RESET))
    print(f"  {c.VALUE}→ {os.path.basename(latest_extraction)}{c.RESET}")

    # Lister les langues disponibles dans l'extraction
    available_langs = list_available_languages_in_extraction(latest_extraction)

    if not available_langs:
        print(c.error("Aucun fichier TranslatedStrings_xx.txt trouvé dans l'extraction"))
        return

    print(f"\n{c.INFO}Langues disponibles dans l'extraction:{c.RESET}")
    for i, lang in enumerate(available_langs, 1):
        status = _("{var0}[DÉJÀ INSTALLÉ]{var1}").format(var0=c.DIM, var1=c.RESET) if lang in installed_langs else ""
        print(_("  {var0}{i}{var2}. {var3}{lang}{var5} (TranslatedStrings_{lang}.txt) {status}").format(var0=c.YELLOW, i=i, var2=c.RESET, var3=c.VALUE, lang=lang, var5=c.RESET, lang=lang, status=status))

    print()
    user_input = input(_("{var0}Sélectionnez la langue à installer (numéro ou code langue): {var1}").format(var0=c.PROMPT, var1=c.RESET)).strip()

    # Déterminer le code langue
    lang_code = None
    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(available_langs):
            lang_code = available_langs[idx]
    else:
        # Valider le code langue entré
        is_valid, normalized, error = validate_language_code(user_input)
        if is_valid and normalized in available_langs:
            lang_code = normalized
        elif not is_valid and is_reference_lang(user_input):
            # Cas spécial: permettre la langue de référence en mode A
            lang_code = get_reference_lang()
        else:
            print(c.error(_("Langue non disponible dans l'extraction")))
            return

    if not lang_code:
        print(c.error(_("Sélection invalide")))
        return

    # Installer
    print()
    success = install_language_from_extraction(plugin_path, lang_code, latest_extraction)

    if success and lang_code not in installed_langs:
        print()
        print(c.success(_("✓ Langue {var0}{lang_code}{var2} ajoutée au plugin").format(var0=c.VALUE, lang_code=lang_code, var2=c.RESET)))


def menu_mode_b_create_new(plugin_path: str, installed_langs: List[str]):
    """Sous-menu Mode B : Créer nouveau fichier."""
    clear_screen()
    print_header()

    print(_("\n{var0}  MODE : Créer un nouveau fichier de langue{var1}").format(var0=c.TITLE, var1=c.RESET))
    print(c.separator())

    # Trouver le fichier EN de référence
    ref_file = get_reference_file(plugin_path)

    if not ref_file:
        ref_lang = get_reference_lang().upper()
        ref_filename = get_reference_filename()
        print(c.error(_("Aucun fichier {ref_lang} de référence trouvé").format(ref_lang=ref_lang)))
        print()
        print(_("Lancez d'abord l'Extractor pour générer {ref_filename}").format(ref_filename=ref_filename))
        return

    # Afficher info sur la source
    if "Extractor" in ref_file:
        source_info = _("Dernière extraction: {var0}").format(var0=os.path.basename(os.path.dirname(ref_file)))
    else:
        source_info = "Plugin racine"

    # Compter les clés
    try:
        ref_translations = parse_translation_file(ref_file)
        key_count = len(ref_translations)
    except Exception:
        key_count = "?"

    print(_("\n{var0}[INFO]{var1} Fichier EN de référence:").format(var0=c.INFO, var1=c.RESET))
    print(f"  → {c.VALUE}{source_info}{c.RESET}")
    print(_("  → Total: {var0}{key_count}{var2} clés").format(var0=c.WHITE, key_count=key_count, var2=c.RESET))

    # Demander le code langue
    print()
    lang_input = input(_("{var0}Code de la nouvelle langue (ex: de, es, it, pt, ja...): {var1}").format(var0=c.PROMPT, var1=c.RESET)).strip()

    # Valider
    is_valid, lang_code, error = validate_language_code(lang_input)
    if not is_valid:
        if error:
            print(c.error(error))
        return

    # Afficher résumé avant création
    print()
    print(c.separator())
    print(_("{var0}Fichier qui sera créé:{var1}").format(var0=c.INFO, var1=c.RESET))
    dest_filename = "TranslatedStrings_{lang_code}.txt".format(lang_code=lang_code)
    print(f"  → {c.VALUE}{os.path.join(os.path.basename(plugin_path), dest_filename)}{c.RESET}")
    print()
    print(_("{var0}Contenu:{var1}").format(var0=c.INFO, var1=c.RESET))
    print(_("  • {var0}{key_count}{var2} clés depuis le fichier EN de référence").format(var0=c.WHITE, key_count=key_count, var2=c.RESET))
    print(_("  • Valeurs EN par défaut (à traduire)"))
    print()

    # Confirmer
    choice = input(_("{var0}Créer ce fichier? (O/n): {var1}").format(var0=c.PROMPT, var1=c.RESET)).strip().lower()

    if choice in ['n', 'non', 'no']:
        print(c.warning(_("Création annulée")))
        return

    # Créer
    success = create_language_from_reference(plugin_path, lang_code, ref_file)

    if success and lang_code not in installed_langs:
        print()
        print(c.success(_("✓ Nouvelle langue {var0}{lang_code}{var2} ajoutée au plugin").format(var0=c.VALUE, lang_code=lang_code, var2=c.RESET)))


# =============================================================================
# CLI (pour appels depuis scripts)
# =============================================================================

def run_addlang_cli(plugin_path: str, lang_code: str, mode: str = 'auto',
                    extraction_dir: Optional[str] = None, force: bool = False) -> bool:
    """
    Exécute l'ajout de langue en mode CLI.

    Args:
        plugin_path: Chemin du plugin
        lang_code: Code langue (2 lettres)
        mode: 'auto', 'extraction', ou 'create'
        extraction_dir: Dossier d'extraction (optionnel)
        force: Écraser sans demander

    Returns:
        True si succès
    """
    # Valider le code langue
    is_valid, normalized, error = validate_language_code(lang_code)
    if not is_valid:
        if error:
            print(c.error(error))
        return False

    lang_code = normalized

    if mode == 'extraction':
        return install_language_from_extraction(plugin_path, lang_code, extraction_dir, force)
    elif mode == 'create':
        return create_language_from_reference(plugin_path, lang_code, None, force)
    elif mode == 'auto':
        # Essayer d'abord l'extraction, puis créer si non trouvé
        if not extraction_dir:
            extraction_dir = find_latest_tool_output(plugin_path, "Extractor")

        if extraction_dir:
            source_filename = "TranslatedStrings_{lang_code}.txt".format(lang_code=lang_code)
            source_path = os.path.join(extraction_dir, source_filename)
            if os.path.isfile(source_path):
                return install_language_from_extraction(plugin_path, lang_code, extraction_dir, force)

        # Fallback: créer nouveau fichier
        return create_language_from_reference(plugin_path, lang_code, None, force)
    else:
        print(c.error(_("Mode invalide: {mode}").format(mode=mode)))
        return False
