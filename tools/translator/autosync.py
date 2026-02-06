#!/usr/bin/env python3
"""
Nom du fichier : autosync.py

Dépendances : extractor.main, compare, extract, inject, sync, common.paths, common.colors

Description :
Orchestration automatique complète : EXTRACTOR → APPLICATOR → COMPARE → EXTRACT → INJECT → SYNC

Cette commande automatise le workflow entier de synchronisation :
  1. Extrait les clés depuis le code Lua via EXTRACTOR (génère fichier de référence frais)
  2. Applique les remplacements LOC dans le code Lua via APPLICATOR
  3. Compare l'ancienne version avec la nouvelle via COMPARE
  4. Extrait les nouvelles clés/modifications via EXTRACT
  5. Injecte les traductions via INJECT (modifie directement le plugin)
  6. Synchronise les langues avec la référence via SYNC (sans marqueurs)
  7. Copie le nouveau fichier de référence vers le plugin
  8. Génère un rapport consolidé

C'est le raccourci idéal pour la maintenance courante :
  - Une seule commande pour tout le workflow
  - Rapport unifié de toutes les étapes
  - Gestion automatique des fichiers temporaires
  - Pas de marqueurs [NEW]/[NEEDS_REVIEW] dans les fichiers finaux
  - Backups centralisés dans le dossier Applicator

Usage CLI :
    python autosync.py                    # Menu interactif
    python autosync.py /path/to/plugin    # Chemin direct du plugin

Date : 2026-02-06
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Ajouter la racine du projet au path pour importer core
# (remonter de 2 niveaux: tools/xxx/ -> tools/ -> racine)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.paths import find_latest_tool_output, get_tool_output_path
from core.colors import Colors
from tools.extractor.main import run_extraction
from tools.applicator.main import process_plugin_directory
from .compare import run_compare
from .config_loader import get_reference_filename, get_update_filename, get_reference_lang
from .extract import run_extract
from .inject import run_inject
from .sync import run_sync

c = Colors()


def find_all_translation_files(plugin_path: str) -> List[str]:
    """
    Trouve tous les fichiers TranslatedStrings_xx.txt dans le plugin.

    Args:
        plugin_path: Chemin du plugin

    Returns:
        Liste des chemins complets des fichiers trouvés
    """
    translation_files = []

    if not os.path.isdir(plugin_path):
        return []

    for filename in os.listdir(plugin_path):
        if filename.startswith("TranslatedStrings_") and filename.endswith(".txt"):
            full_path = os.path.join(plugin_path, filename)
            translation_files.append(full_path)

    return translation_files


def find_all_translate_files(output_dir: str) -> List[Tuple[str, str]]:
    """
    Trouve tous les fichiers TRANSLATE_xx.txt dans un répertoire.

    Args:
        output_dir: Répertoire à scanner

    Returns:
        Liste de tuples (lang_code, chemin_complet)
    """
    translate_files = []

    if not os.path.isdir(output_dir):
        return []

    for filename in os.listdir(output_dir):
        if filename.startswith("TRANSLATE_") and filename.endswith(".txt"):
            lang_code = filename.replace("TRANSLATE_", "").replace(".txt", "")
            full_path = os.path.join(output_dir, filename)
            translate_files.append((lang_code, full_path))

    return translate_files


def clean_markers_from_file(file_path: str):
    """
    Supprime les marqueurs [NEW] et [NEEDS_REVIEW] d'un fichier de traduction.

    Args:
        file_path: Chemin du fichier à nettoyer
    """
    if not os.path.isfile(file_path):
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    cleaned_lines = []
    for line in lines:
        # Supprimer les lignes contenant les marqueurs
        if '-- [NEW]' in line or '-- [NEEDS_REVIEW]' in line:
            continue
        cleaned_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)


def menu_autosync(plugin_path: str):
    """Menu interactif pour Auto-Sync orchestré."""
    from .common import clear_screen, print_header

    clear_screen()
    print_header()

    print(f"\n{c.TITLE}  AUTO-SYNC - Orchestration complète{c.RESET}")
    print(c.separator())

    # Vérifier le plugin
    if not plugin_path or not os.path.isdir(plugin_path):
        print(c.error("Plugin non configuré ou introuvable."))
        return

    # Trouver les fichiers de traduction existants
    translation_files = find_all_translation_files(plugin_path)

    if not translation_files:
        print(c.warning("Aucun fichier TranslatedStrings_xx.txt trouvé dans le plugin."))
        print()
        print(f"{c.INFO}Première installation ?{c.RESET}")
        print("  → Utilisez la commande INSTALL pour installer les fichiers depuis l'extraction")
        return

    print(f"\n{c.INFO}[INFO]{c.RESET} Fichiers de traduction détectés:")
    for f in translation_files:
        filename = os.path.basename(f)
        print(f"  - {c.VALUE}{filename}{c.RESET}")
    print()

    print(f"{c.INFO}Workflow:{c.RESET}")
    print(f"  1. {c.VALUE}EXTRACTOR{c.RESET}  → extrait clés depuis code Lua")
    print(f"  2. {c.VALUE}APPLICATOR{c.RESET} → applique les remplacements dans le code")
    print(f"  3. {c.VALUE}COMPARE{c.RESET}    → génère " + get_update_filename() + "")
    print(f"  4. {c.VALUE}EXTRACT{c.RESET}    → génère fichiers TRANSLATE_xx.txt")
    print(f"  5. {c.VALUE}INJECT{c.RESET}     → applique les traductions complétées")
    print(f"  6. {c.VALUE}SYNC{c.RESET}       → synchronise avec la référence EN")
    print()

    # Demander confirmation
    choice = input(f"{c.PROMPT}Lancer le workflow complet? (O/n): {c.RESET}").strip().lower()

    if choice in ['n', 'non', 'no']:
        print(c.warning("Workflow annulé"))
        return

    # Exécuter le workflow
    print()
    print(c.separator())
    print(f"{c.TITLE}Exécution du workflow...{c.RESET}")
    print(c.separator())

    results = run_autosync(plugin_path)

    # Afficher le rapport consolidé
    print_autosync_report(results, plugin_path)


def run_autosync(plugin_path: str) -> Dict:
    """
    Orchestrateur AUTO-SYNC : EXTRACTOR -> APPLICATOR -> COMPARE -> EXTRACT -> INJECT -> SYNC

    Lance les 6 commandes en séquence avec rapport consolidé.
    Les fichiers sont modifiés directement dans le plugin (par APPLICATOR, INJECT et SYNC).

    Args:
        plugin_path: Chemin du plugin

    Returns:
        Dict avec les résultats de chaque étape
    """
    results = {
        'extractor': {},
        'applicator': {},
        'compare': {},
        'extract': {},
        'inject': {},
        'sync': {},
        'errors': [],
        'compare_dir': None
    }

    if not plugin_path or not os.path.isdir(plugin_path):
        results['errors'].append("Chemin du plugin invalide")
        return results

    # Créer le dossier de sortie pour les rapports/artefacts
    output_dir = get_tool_output_path(plugin_path, "Translator", create=True)

    # Créer un dossier backup centralisé dans Applicator
    applicator_output = get_tool_output_path(plugin_path, "Applicator", create=False)
    if applicator_output:
        backup_dir = os.path.join(applicator_output, "backups")
        os.makedirs(backup_dir, exist_ok=True)
    else:
        backup_dir = None

    # SAUVEGARDE CRITIQUE: Copier le fichier EN actuel du plugin AVANT toute modification
    # Ce fichier servira de référence "ANCIEN" pour COMPARE
    original_en_path = os.path.join(plugin_path, "" + get_reference_filename() + "")
    saved_old_en_path = None
    if os.path.isfile(original_en_path):
        saved_old_en_path = os.path.join(output_dir, "_original_" + get_reference_filename() + "")
        shutil.copy2(original_en_path, saved_old_en_path)

    # =========================================================================
    # ETAPE 1: EXTRACTOR (extrait clés depuis code Lua)
    # =========================================================================
    print(f"\n{c.INFO}[Étape 1/6 | EXTRACTOR]{c.RESET} Extraction des clés depuis le code Lua")
    print(f"{c.DIM}  → Extraction fraîche pour comparer AVANT vs MAINTENANT{c.RESET}")

    try:
        # Lancer Extractor avec paramètres par défaut
        run_extraction(
            plugin_path=plugin_path,
            output_dir="",  # Chaîne vide = utilise le répertoire par défaut (__i18n_tmp__/1_Extractor)
            prefix="$$$/Piwigo",  # Préfixe par défaut (ajuster si besoin)
            lang=get_reference_lang(),  # Utilise la langue de référence configurée
            exclude_files=[],
            min_length=3,
            ignore_log=True,
            silent=True  # Désactive l'affichage du rapport détaillé
        )

        # Récupérer la dernière extraction
        latest_extraction = find_latest_tool_output(plugin_path, "Extractor")
        if not latest_extraction:
            raise RuntimeError("Extraction échouée - aucun répertoire généré")

        new_en_path = os.path.join(latest_extraction, "" + get_reference_filename() + "")
        if not os.path.isfile(new_en_path):
            raise RuntimeError("" + get_reference_filename() + " non généré par Extractor")

        results['extractor']['output_dir'] = latest_extraction
        results['extractor']['en_file'] = new_en_path

        # Afficher le chemin court
        plugin_name = os.path.basename(plugin_path)
        rel_path = os.path.relpath(latest_extraction, plugin_path).replace('\\', '/')
        print(f"{c.DIM}  Détails  : {c.VALUE}{plugin_name}/{rel_path}{c.RESET}")

    except Exception as e:
        print(c.error(f"ERREUR: {e}"))
        results['errors'].append(f"Extractor: {e}")
        return results

    # =========================================================================
    # ETAPE 2: APPLICATOR (applique les remplacements dans le code Lua)
    # =========================================================================
    print(f"\n{c.INFO}[Étape 2/6 | APPLICATOR]{c.RESET} Application des remplacements LOC")
    print(f"{c.DIM}  → Remplacement des chaînes hardcodées par les clés LOC{c.RESET}")

    try:
        # Lancer Applicator avec le répertoire d'extraction
        extraction_dir = results['extractor']['output_dir']
        success = process_plugin_directory(
            plugin_path=plugin_path,
            extraction_dir=extraction_dir,
            dry_run=False,
            create_backup=True,
            silent=True  # Désactive l'affichage du rapport détaillé
        )

        if not success:
            raise RuntimeError("Applicator a échoué")

        results['applicator']['success'] = True
        print(f"{c.DIM}  Remplacements appliqués au code source{c.RESET}")

    except Exception as e:
        print(c.error(f"ERREUR: {e}"))
        results['errors'].append(f"Applicator: {e}")
        return results

    # =========================================================================
    # ETAPE 3: COMPARE (ancien EN du plugin vs nouveau EN d'Extractor)
    # =========================================================================
    print(f"\n{c.INFO}[Étape 3/6 | COMPARE]{c.RESET} Comparaison ANCIEN vs NOUVEAU")

    compare_dir = os.path.join(output_dir, "compare")
    os.makedirs(compare_dir, exist_ok=True)

    try:
        # Ancien EN = celui sauvegardé AU DÉBUT du workflow
        if saved_old_en_path and os.path.isfile(saved_old_en_path):
            old_en_path = saved_old_en_path
        else:
            # Si l'ancien n'existe pas, c'est la première fois
            print(f"  {c.WARNING}Première installation - ancien EN non trouvé{c.RESET}")
            old_en_path = results['extractor']['en_file']  # Comparer avec lui-même

        # Nouveau EN = celui généré par Extractor
        new_en_path = results['extractor']['en_file']

        compare_result_dir = run_compare(
            old_path=old_en_path,
            new_path=new_en_path,
            output_dir=compare_dir
        )
        results['compare'] = compare_result_dir
        results['compare_dir'] = compare_dir
        compare_output_dir = compare_dir

        # Charger le JSON pour obtenir le summary
        import json
        update_json_path = os.path.join(compare_dir, '" + get_update_filename() + "')
        if os.path.isfile(update_json_path):
            with open(update_json_path, 'r', encoding='utf-8') as f:
                update_data = json.load(f)
                summary = update_data.get('summary', {})
                added = summary.get('added', 0)
                changed = summary.get('changed', 0)
                deleted = summary.get('deleted', 0)

                # Afficher les fichiers comparés
                plugin_name = os.path.basename(plugin_path)
                old_short = os.path.basename(old_en_path)
                new_rel = os.path.relpath(new_en_path, plugin_path).replace('\\', '/')
                print(f"{c.DIM}  Ancien      : {c.VALUE}{old_short}{c.RESET}")
                print(f"{c.DIM}  Nouveau     : {c.VALUE}{plugin_name}/{new_rel}{c.RESET}")

                # Afficher résumé des changements
                if added or changed or deleted:
                    print(f"{c.DIM}  Changements : {c.GREEN}{added} ajoutées{c.RESET}, "
                          f"{c.YELLOW}{changed} modifiées{c.RESET}, {c.RED}{deleted} supprimées{c.RESET}")

                rel_compare = os.path.relpath(compare_dir, plugin_path).replace('\\', '/')
                print(f"{c.DIM}  Détails     : {c.VALUE}{plugin_name}/{rel_compare}{c.RESET}")

    except Exception as e:
        print(c.error(f"ERREUR: {e}"))
        results['errors'].append(f"Compare: {e}")
        return results

    # =========================================================================
    # ETAPE 4: EXTRACT (génère TRANSLATE_xx.txt)
    # =========================================================================
    print(f"\n{c.INFO}[Étape 4/6 | EXTRACT]{c.RESET} Extraction des clés modifiées")
    print(f"{c.DIM}  → Sélection uniquement des changements détectés{c.RESET}")

    try:
        # Charger les fichiers de langue existants
        translation_files = find_all_translation_files(plugin_path)
        lang_codes = set()
        for tf in translation_files:
            filename = os.path.basename(tf)
            if filename != "" + get_reference_filename() + "":
                lang_code = filename.replace("TranslatedStrings_", "").replace(".txt", "")
                lang_codes.add(lang_code)

        if not lang_codes:
            print(c.warning("Aucune langue trouvée dans le plugin"))
            results['errors'].append("Aucun fichier de traduction trouvé")
            return results

        # Extraire pour chaque langue
        extract_dir = os.path.join(output_dir, "extract")
        os.makedirs(extract_dir, exist_ok=True)

        for lang_code in sorted(lang_codes):
            try:
                translate_file = run_extract(
                    update_dir=compare_output_dir,
                    lang=lang_code,
                    locales_dir=plugin_path,
                    output_dir=extract_dir
                )
                results['extract'][lang_code] = translate_file
            except Exception as e:
                print(c.error(f"  ERREUR {lang_code}: {e}"))
                results['errors'].append(f"Extract {lang_code}: {e}")

        # Afficher le chemin
        plugin_name = os.path.basename(plugin_path)
        rel_extract = os.path.relpath(extract_dir, plugin_path).replace('\\', '/')
        print(f"{c.DIM}  Détails     : {c.VALUE}{plugin_name}/{rel_extract}{c.RESET}")

    except Exception as e:
        print(c.error(f"Erreur extraction: {e}"))
        results['errors'].append(f"Extract: {e}")
        return results

    # =========================================================================
    # ETAPE 5: INJECT (applique traductions au plugin)
    # =========================================================================
    print(f"\n{c.INFO}[Étape 5/6 | INJECT]{c.RESET} Injection des traductions")
    print(f"{c.DIM}  → Mise à jour des fichiers de traduction{c.RESET}")

    translate_files = []
    if extract_dir and os.path.isdir(extract_dir):
        translate_files = find_all_translate_files(extract_dir)

    total_injected = 0
    if translate_files:
        for lang_code, translate_file in translate_files:
            try:
                # Cibler directement le fichier du plugin
                plugin_target = os.path.join(plugin_path, f"TranslatedStrings_{lang_code}.txt")

                # Injecter directement (crée le fichier s'il n'existe pas)
                inject_result = run_inject(
                    translate_file=translate_file,
                    target_file=plugin_target,
                    update_dir=extract_dir,
                    create_backup=True,  # Garder une sauvegarde
                    backup_dir=backup_dir  # Centraliser les backups
                )
                results['inject'][lang_code] = inject_result
                total_injected += inject_result.get('injected', 0)
            except Exception as e:
                print(c.error(f"  ERREUR {lang_code}: {e}"))
                results['errors'].append(f"Inject {lang_code}: {e}")

        if total_injected > 0:
            print(f"{c.DIM}  {c.GREEN}{total_injected}{c.RESET} traduction(s) injectée(s)")
        else:
            print(f"{c.DIM}  Aucune nouvelle traduction à injecter{c.RESET}")
    else:
        print(f"{c.DIM}  Aucune modification détectée{c.RESET}")

    # =========================================================================
    # ETAPE 6: SYNC (synchronise directement dans le plugin, SANS marqueurs)
    # =========================================================================
    print(f"\n{c.INFO}[Étape 6/6 | SYNC]{c.RESET} Synchronisation finale")
    print(f"{c.DIM}  → Alignement avec la référence EN (sans marqueurs){c.RESET}")

    try:
        # Utiliser le nouveau EN généré par Extractor comme référence
        ref_en_path = results['extractor']['en_file']

        # Synchroniser avec compare_dir pour détecter les suppressions
        sync_results = run_sync(
            reference_path=ref_en_path,
            locales_dir=plugin_path,
            update_dir=compare_dir,  # Utilise " + get_update_filename() + " pour détecter suppressions
            backup_dir=backup_dir  # Centraliser les backups
        )

        # Nettoyer les marqueurs des fichiers finaux
        translation_files = find_all_translation_files(plugin_path)
        for tf in translation_files:
            if os.path.basename(tf) != "" + get_reference_filename() + "":
                clean_markers_from_file(tf)

        for lang_code, sync_stats in sync_results.items():
            added = sync_stats.get('added', 0)
            modified = sync_stats.get('needs_review', 0)
            removed = sync_stats.get('removed', 0)
            print(f"{c.DIM}  {lang_code}: {c.GREEN}{added}{c.RESET} ajoutées, "
                  f"{c.YELLOW}{modified}{c.RESET} modifiées, "
                  f"{c.RED}{removed}{c.RESET} supprimées")
            results['sync'][lang_code] = sync_stats

        # Afficher le lien vers CHANGELOG
        plugin_name = os.path.basename(plugin_path)
        changelog_path = os.path.join(compare_dir, 'CHANGELOG.txt')
        if os.path.isfile(changelog_path):
            rel_changelog = os.path.relpath(changelog_path, plugin_path).replace('\\', '/')
            print(f"{c.DIM}  Détails     : {c.VALUE}{plugin_name}/{rel_changelog}{c.RESET}")

    except Exception as e:
        print(c.error(f"Erreur sync: {e}"))
        results['errors'].append(f"Sync: {e}")
        return results

    # =========================================================================
    # ETAPE FINALE: Copier le nouveau " + get_reference_filename() + " vers le plugin
    # =========================================================================
    print(f"\n{c.INFO}[Finalisation]{c.RESET} Mise à jour du fichier EN")

    try:
        new_en_source = results['extractor']['en_file']
        new_en_target = os.path.join(plugin_path, "" + get_reference_filename() + "")

        # Backup de l'ancien si existe
        if os.path.isfile(new_en_target):
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
                backup_filename = os.path.basename(new_en_target) + '.bak'
                backup_path = os.path.join(backup_dir, backup_filename)
                shutil.copy2(new_en_target, backup_path)
                plugin_name = os.path.basename(plugin_path)
                rel_backup = os.path.relpath(backup_dir, plugin_path).replace('\\', '/')
                print(f"{c.DIM}  Backup      : {c.VALUE}{plugin_name}/{rel_backup}/{os.path.basename(backup_path)}{c.RESET}")
            else:
                backup_path = new_en_target + ".bak"
                shutil.copy2(new_en_target, backup_path)
                print(f"{c.DIM}  Backup      : {c.VALUE}{os.path.basename(backup_path)}{c.RESET}")

        # Copier le nouveau
        shutil.copy2(new_en_source, new_en_target)
        print(f"{c.DIM}  " + get_reference_filename() + " → mis à jour{c.RESET}")

    except Exception as e:
        print(c.error(f"ERREUR copie EN: {e}"))
        results['errors'].append(f"Copy EN: {e}")

    return results


def print_autosync_report(results: Dict, plugin_path: str):
    """Affiche le rapport consolidé simplifié du workflow."""
    print()
    print(c.separator())

    # Erreurs
    if results['errors']:
        print(f"{c.ERROR}[ERREUR]{c.RESET} Workflow interrompu")
        for error in results['errors']:
            print(f"  {c.ERROR}→{c.RESET} {error}")
    else:
        print(f"{c.SUCCESS}[OK]{c.RESET} Workflow complet sans erreur")

    # Statut final
    if results['sync'] and not results['errors']:
        print(f"\n{c.DIM}Tous les fichiers TranslatedStrings_xx.txt à la racine plugin sont à jour.{c.RESET}")
