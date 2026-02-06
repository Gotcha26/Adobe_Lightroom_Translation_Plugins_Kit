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

    print(_("\n{var0}  AUTO-SYNC - Orchestration complète{var1}").format(var0=c.TITLE, var1=c.RESET))
    print(c.separator())

    # Vérifier le plugin
    if not plugin_path or not os.path.isdir(plugin_path):
        print(c.error(_("Plugin non configuré ou introuvable.")))
        return

    # Trouver les fichiers de traduction existants
    translation_files = find_all_translation_files(plugin_path)

    if not translation_files:
        print(c.warning("Aucun fichier TranslatedStrings_xx.txt trouvé dans le plugin."))
        print()
        print(_("{var0}Première installation ?{var1}").format(var0=c.INFO, var1=c.RESET))
        print(_("  → Utilisez la commande INSTALL pour installer les fichiers depuis l'extraction"))
        return

    print(_("\n{var0}[INFO]{var1} Fichiers de traduction détectés:").format(var0=c.INFO, var1=c.RESET))
    for f in translation_files:
        filename = os.path.basename(f)
        print(f"  - {c.VALUE}{filename}{c.RESET}")
    print()

    print(_("{var0}Workflow:{var1}").format(var0=c.INFO, var1=c.RESET))
    print(_("  1. {var0}EXTRACTOR{var1}  → extrait clés depuis code Lua").format(var0=c.VALUE, var1=c.RESET))
    print(_("  2. {var0}APPLICATOR{var1} → applique les remplacements dans le code").format(var0=c.VALUE, var1=c.RESET))
    print(_("  3. {var0}COMPARE{var1}    → génère ").format(var0=c.VALUE, var1=c.RESET) + get_update_filename() + "")
    print(_("  4. {var0}EXTRACT{var1}    → génère fichiers TRANSLATE_xx.txt").format(var0=c.VALUE, var1=c.RESET))
    print(_("  5. {var0}INJECT{var1}     → applique les traductions complétées").format(var0=c.VALUE, var1=c.RESET))
    print(_("  6. {var0}SYNC{var1}       → synchronise avec la référence EN").format(var0=c.VALUE, var1=c.RESET))
    print()

    # Demander confirmation
    choice = input(_("{var0}Lancer le workflow complet? (O/n): {var1}").format(var0=c.PROMPT, var1=c.RESET)).strip().lower()

    if choice in ['n', 'non', 'no']:
        print(c.warning(_("Workflow annulé")))
        return

    # Exécuter le workflow
    print()
    print(c.separator())
    print(_("{var0}Exécution du workflow...{var1}").format(var0=c.TITLE, var1=c.RESET))
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
        results['errors'].append(_("Chemin du plugin invalide"))
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
    original_en_path = os.path.join(plugin_path, "_(" + get_reference_filename() + ")")
    saved_old_en_path = None
    if os.path.isfile(original_en_path):
        saved_old_en_path = os.path.join(output_dir, "_original_" + get_reference_filename() + "")
        shutil.copy2(original_en_path, saved_old_en_path)

    # =========================================================================
    # ETAPE 1: EXTRACTOR (extrait clés depuis code Lua)
    # =========================================================================
    print(_("\n{var0}[Étape 1/6 | EXTRACTOR]{var1} Extraction des clés depuis le code Lua").format(var0=c.INFO, var1=c.RESET))
    print(_("{var0}  → Extraction fraîche pour comparer AVANT vs MAINTENANT{var1}").format(var0=c.DIM, var1=c.RESET))

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
            raise RuntimeError(_("Extraction échouée - aucun répertoire généré"))

        new_en_path = os.path.join(latest_extraction, "_(" + get_reference_filename() + ")")
        if not os.path.isfile(new_en_path):
            raise RuntimeError("_(" + get_reference_filename() + ") non généré par Extractor")

        results['extractor']['output_dir'] = latest_extraction
        results['extractor']['en_file'] = new_en_path

        # Afficher le chemin court
        plugin_name = os.path.basename(plugin_path)
        rel_path = os.path.relpath(latest_extraction, plugin_path).replace('\\', '/')
        print(_("{var0}  Détails  : {var1}{plugin_name}/{rel_path}{var4}").format(var0=c.DIM, var1=c.VALUE, plugin_name=plugin_name, rel_path=rel_path, var4=c.RESET))

    except Exception as e:
        print(c.error(_("ERREUR: {e}").format(e=e)))
        results['errors'].append(_("Extractor: {e}").format(e=e))
        return results

    # =========================================================================
    # ETAPE 2: APPLICATOR (applique les remplacements dans le code Lua)
    # =========================================================================
    print(_("\n{var0}[Étape 2/6 | APPLICATOR]{var1} Application des remplacements LOC").format(var0=c.INFO, var1=c.RESET))
    print(_("{var0}  → Remplacement des chaînes hardcodées par les clés LOC{var1}").format(var0=c.DIM, var1=c.RESET))

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
            raise RuntimeError(_("Applicator a échoué"))

        results['applicator']['success'] = True
        print(_("{var0}  Remplacements appliqués au code source{var1}").format(var0=c.DIM, var1=c.RESET))

    except Exception as e:
        print(c.error(_("ERREUR: {e}").format(e=e)))
        results['errors'].append(_("Applicator: {e}").format(e=e))
        return results

    # =========================================================================
    # ETAPE 3: COMPARE (ancien EN du plugin vs nouveau EN d'Extractor)
    # =========================================================================
    print(_("\n{var0}[Étape 3/6 | COMPARE]{var1} Comparaison ANCIEN vs NOUVEAU").format(var0=c.INFO, var1=c.RESET))

    compare_dir = os.path.join(output_dir, "compare")
    os.makedirs(compare_dir, exist_ok=True)

    try:
        # Ancien EN = celui sauvegardé AU DÉBUT du workflow
        if saved_old_en_path and os.path.isfile(saved_old_en_path):
            old_en_path = saved_old_en_path
        else:
            # Si l'ancien n'existe pas, c'est la première fois
            print(_("  {var0}Première installation - ancien EN non trouvé{var1}").format(var0=c.WARNING, var1=c.RESET))
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
        update_json_path = os.path.join(compare_dir, '_(" + get_update_filename() + ")')
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
                print(_("{var0}  Ancien      : {var1}{old_short}{var3}").format(var0=c.DIM, var1=c.VALUE, old_short=old_short, var3=c.RESET))
                print(_("{var0}  Nouveau     : {var1}{plugin_name}/{new_rel}{var4}").format(var0=c.DIM, var1=c.VALUE, plugin_name=plugin_name, new_rel=new_rel, var4=c.RESET))

                # Afficher résumé des changements
                if added or changed or deleted:
                    print(_("{var0}  Changements : {var1}{added} ajoutées{var3}, ").format(var0=c.DIM, var1=c.GREEN, added=added, var3=c.RESET)
                          _("{var0}{changed} modifiées{var2}, {var3}{deleted} supprimées{var5}").format(var0=c.YELLOW, changed=changed, var2=c.RESET, var3=c.RED, deleted=deleted, var5=c.RESET))

                rel_compare = os.path.relpath(compare_dir, plugin_path).replace('\\', '/')
                print(_("{var0}  Détails     : {var1}{plugin_name}/{rel_compare}{var4}").format(var0=c.DIM, var1=c.VALUE, plugin_name=plugin_name, rel_compare=rel_compare, var4=c.RESET))

    except Exception as e:
        print(c.error(_("ERREUR: {e}").format(e=e)))
        results['errors'].append(_("Compare: {e}").format(e=e))
        return results

    # =========================================================================
    # ETAPE 4: EXTRACT (génère TRANSLATE_xx.txt)
    # =========================================================================
    print(_("\n{var0}[Étape 4/6 | EXTRACT]{var1} Extraction des clés modifiées").format(var0=c.INFO, var1=c.RESET))
    print(_("{var0}  → Sélection uniquement des changements détectés{var1}").format(var0=c.DIM, var1=c.RESET))

    try:
        # Charger les fichiers de langue existants
        translation_files = find_all_translation_files(plugin_path)
        lang_codes = set()
        for tf in translation_files:
            filename = os.path.basename(tf)
            if filename != "_(" + get_reference_filename() + ")":
                lang_code = filename.replace("TranslatedStrings_", "").replace(".txt", "")
                lang_codes.add(lang_code)

        if not lang_codes:
            print(c.warning(_("Aucune langue trouvée dans le plugin")))
            results['errors'].append(_("Aucun fichier de traduction trouvé"))
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
                print(c.error(_("  ERREUR {lang_code}: {e}").format(lang_code=lang_code, e=e)))
                results['errors'].append(_("Extract {lang_code}: {e}").format(lang_code=lang_code, e=e))

        # Afficher le chemin
        plugin_name = os.path.basename(plugin_path)
        rel_extract = os.path.relpath(extract_dir, plugin_path).replace('\\', '/')
        print(_("{var0}  Détails     : {var1}{plugin_name}/{rel_extract}{var4}").format(var0=c.DIM, var1=c.VALUE, plugin_name=plugin_name, rel_extract=rel_extract, var4=c.RESET))

    except Exception as e:
        print(c.error(_("Erreur extraction: {e}").format(e=e)))
        results['errors'].append(_("Extract: {e}").format(e=e))
        return results

    # =========================================================================
    # ETAPE 5: INJECT (applique traductions au plugin)
    # =========================================================================
    print(_("\n{var0}[Étape 5/6 | INJECT]{var1} Injection des traductions").format(var0=c.INFO, var1=c.RESET))
    print(_("{var0}  → Mise à jour des fichiers de traduction{var1}").format(var0=c.DIM, var1=c.RESET))

    translate_files = []
    if extract_dir and os.path.isdir(extract_dir):
        translate_files = find_all_translate_files(extract_dir)

    total_injected = 0
    if translate_files:
        for lang_code, translate_file in translate_files:
            try:
                # Cibler directement le fichier du plugin
                plugin_target = os.path.join(plugin_path, _("TranslatedStrings_{lang_code}.txt").format(lang_code=lang_code))

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
                print(c.error(_("  ERREUR {lang_code}: {e}").format(lang_code=lang_code, e=e)))
                results['errors'].append(_("Inject {lang_code}: {e}").format(lang_code=lang_code, e=e))

        if total_injected > 0:
            print(_("{var0}  {var1}{total_injected}{var3} traduction(s) injectée(s)").format(var0=c.DIM, var1=c.GREEN, total_injected=total_injected, var3=c.RESET))
        else:
            print(_("{var0}  Aucune nouvelle traduction à injecter{var1}").format(var0=c.DIM, var1=c.RESET))
    else:
        print(_("{var0}  Aucune modification détectée{var1}").format(var0=c.DIM, var1=c.RESET))

    # =========================================================================
    # ETAPE 6: SYNC (synchronise directement dans le plugin, SANS marqueurs)
    # =========================================================================
    print(_("\n{var0}[Étape 6/6 | SYNC]{var1} Synchronisation finale").format(var0=c.INFO, var1=c.RESET))
    print(_("{var0}  → Alignement avec la référence EN (sans marqueurs){var1}").format(var0=c.DIM, var1=c.RESET))

    try:
        # Utiliser le nouveau EN généré par Extractor comme référence
        ref_en_path = results['extractor']['en_file']

        # Synchroniser avec compare_dir pour détecter les suppressions
        sync_results = run_sync(
            reference_path=ref_en_path,
            locales_dir=plugin_path,
            update_dir=compare_dir,  # Utilise _(" + get_update_filename() + ") pour détecter suppressions
            backup_dir=backup_dir  # Centraliser les backups
        )

        # Nettoyer les marqueurs des fichiers finaux
        translation_files = find_all_translation_files(plugin_path)
        for tf in translation_files:
            if os.path.basename(tf) != "_(" + get_reference_filename() + ")":
                clean_markers_from_file(tf)

        for lang_code, sync_stats in sync_results.items():
            added = sync_stats.get('added', 0)
            modified = sync_stats.get('needs_review', 0)
            removed = sync_stats.get('removed', 0)
            print(_("{var0}  {lang_code}: {var2}{added}{var4} ajoutées, ").format(var0=c.DIM, lang_code=lang_code, var2=c.GREEN, added=added, var4=c.RESET)
                  _("{var0}{modified}{var2} modifiées, ").format(var0=c.YELLOW, modified=modified, var2=c.RESET)
                  _("{var0}{removed}{var2} supprimées").format(var0=c.RED, removed=removed, var2=c.RESET))
            results['sync'][lang_code] = sync_stats

        # Afficher le lien vers CHANGELOG
        plugin_name = os.path.basename(plugin_path)
        changelog_path = os.path.join(compare_dir, 'CHANGELOG.txt')
        if os.path.isfile(changelog_path):
            rel_changelog = os.path.relpath(changelog_path, plugin_path).replace('\\', '/')
            print(_("{var0}  Détails     : {var1}{plugin_name}/{rel_changelog}{var4}").format(var0=c.DIM, var1=c.VALUE, plugin_name=plugin_name, rel_changelog=rel_changelog, var4=c.RESET))

    except Exception as e:
        print(c.error(_("Erreur sync: {e}").format(e=e)))
        results['errors'].append(_("Sync: {e}").format(e=e))
        return results

    # =========================================================================
    # ETAPE FINALE: Copier le nouveau " + get_reference_filename() + " vers le plugin
    # =========================================================================
    print(_("\n{var0}[Finalisation]{var1} Mise à jour du fichier EN").format(var0=c.INFO, var1=c.RESET))

    try:
        new_en_source = results['extractor']['en_file']
        new_en_target = os.path.join(plugin_path, "_(" + get_reference_filename() + ")")

        # Backup de l'ancien si existe
        if os.path.isfile(new_en_target):
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
                backup_filename = os.path.basename(new_en_target) + '.bak'
                backup_path = os.path.join(backup_dir, backup_filename)
                shutil.copy2(new_en_target, backup_path)
                plugin_name = os.path.basename(plugin_path)
                rel_backup = os.path.relpath(backup_dir, plugin_path).replace('\\', '/')
                print(_("{var0}  Backup      : {var1}{plugin_name}/{rel_backup}/{var4}{var5}").format(var0=c.DIM, var1=c.VALUE, plugin_name=plugin_name, rel_backup=rel_backup, var4=os.path.basename(backup_path), var5=c.RESET))
            else:
                backup_path = new_en_target + ".bak"
                shutil.copy2(new_en_target, backup_path)
                print(_("{var0}  Backup      : {var1}{var2}{var3}").format(var0=c.DIM, var1=c.VALUE, var2=os.path.basename(backup_path), var3=c.RESET))

        # Copier le nouveau
        shutil.copy2(new_en_source, new_en_target)
        print(f"{c.DIM}  " + get_reference_filename() + " → mis à jour{c.RESET}")

    except Exception as e:
        print(c.error(_("ERREUR copie EN: {e}").format(e=e)))
        results['errors'].append(_("Copy EN: {e}").format(e=e))

    return results


def print_autosync_report(results: Dict, plugin_path: str):
    """Affiche le rapport consolidé simplifié du workflow."""
    print()
    print(c.separator())

    # Erreurs
    if results['errors']:
        print(_("{var0}[ERREUR]{var1} Workflow interrompu").format(var0=c.ERROR, var1=c.RESET))
        for error in results['errors']:
            print(f"  {c.ERROR}→{c.RESET} {error}")
    else:
        print(_("{var0}[OK]{var1} Workflow complet sans erreur").format(var0=c.SUCCESS, var1=c.RESET))

    # Statut final
    if results['sync'] and not results['errors']:
        print(_("\n{var0}Tous les fichiers TranslatedStrings_xx.txt à la racine plugin sont à jour.{var1}").format(var0=c.DIM, var1=c.RESET))
