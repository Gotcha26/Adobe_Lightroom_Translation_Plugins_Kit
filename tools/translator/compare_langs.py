#!/usr/bin/env python3
"""
Nom du fichier : compare_langs.py

Dépendances : common

Description :
Module COMPARE-LANGS pour Translator.
Compare deux fichiers TranslatedStrings de langues différentes.

Permet de comparer deux fichiers de traduction pour :
  - Identifier les clés présentes dans un fichier mais absentes de l'autre
  - Détecter les traductions identiques (possibles oublis de traduction)
  - Comparer deux versions d'une même langue (avant/après révision)
  - Générer des rapports de complétude et de cohérence

Cas d'usage :
  1. Vérifier la cohérence entre langues (FR vs EN, DE vs FR, etc.)
  2. Audit qualité (identifier traductions non faites)
  3. Suivi de versions (comparer avant/après révision)

Usage CLI :
    python Translator_main.py compare-langs --lang1 fr --lang2 de --locales ./Locales
    python Translator_main.py compare-langs --file1 ./v1/fr.txt --file2 ./v2/fr.txt

Date : 2026-02-03
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Set, Tuple, Optional

# Ajouter la racine du projet au path pour importer core
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.i18n import _

from .common import (
    parse_translation_file, resolve_path, find_languages, c
)


# =============================================================================
# COMPARATEUR DE LANGUES
# =============================================================================

class LanguageComparator:
    """Compare deux fichiers de traduction de langues différentes ou identiques."""

    def __init__(self, lang1_strings: Dict[str, str], lang2_strings: Dict[str, str],
                 lang1_name: str = "Lang1", lang2_name: str = "Lang2"):
        """
        Initialize le comparateur.

        Args:
            lang1_strings: Dictionnaire {clé: valeur} pour la langue 1
            lang2_strings: Dictionnaire {clé: valeur} pour la langue 2
            lang1_name: Nom de la langue 1 (pour affichage)
            lang2_name: Nom de la langue 2 (pour affichage)
        """
        self.lang1 = lang1_strings
        self.lang2 = lang2_strings
        self.lang1_name = lang1_name.upper()
        self.lang2_name = lang2_name.upper()
        self.result = None

    def compare(self) -> Dict:
        """
        Compare les deux langues.

        Returns:
            {
                'only_in_lang1': [keys],          # Clés seulement dans lang1
                'only_in_lang2': [keys],          # Clés seulement dans lang2
                'in_both': [keys],                # Clés présentes dans les deux
                'identical_values': {key: value}, # Même clé = même valeur (possibles oublis)
                'different_values': [keys],       # Même clé mais valeurs différentes
                'statistics': {...}
            }
        """
        keys1 = set(self.lang1.keys())
        keys2 = set(self.lang2.keys())

        # Clés présentes dans chaque langue
        only_in_lang1 = sorted(keys1 - keys2)
        only_in_lang2 = sorted(keys2 - keys1)
        in_both = sorted(keys1 & keys2)

        # Parmi les clés communes, identifier valeurs identiques vs différentes
        identical_values = {}
        different_values = []

        for key in in_both:
            val1 = self.lang1[key]
            val2 = self.lang2[key]
            if val1 == val2:
                identical_values[key] = val1
            else:
                different_values.append(key)

        # Statistiques
        total_keys = len(keys1 | keys2)  # Union de toutes les clés
        coverage_lang1 = (len(keys1) / total_keys * 100) if total_keys > 0 else 0
        coverage_lang2 = (len(keys2) / total_keys * 100) if total_keys > 0 else 0

        self.result = {
            'only_in_lang1': only_in_lang1,
            'only_in_lang2': only_in_lang2,
            'in_both': in_both,
            'identical_values': identical_values,
            'different_values': different_values,
            'statistics': {
                'total_unique_keys': total_keys,
                'keys_in_lang1': len(keys1),
                'keys_in_lang2': len(keys2),
                'keys_in_both': len(in_both),
                'only_lang1': len(only_in_lang1),
                'only_lang2': len(only_in_lang2),
                'identical_values_count': len(identical_values),
                'different_values_count': len(different_values),
                'coverage_lang1_pct': round(coverage_lang1, 2),
                'coverage_lang2_pct': round(coverage_lang2, 2)
            }
        }

        return self.result


# =============================================================================
# FONCTIONS PRINCIPALES
# =============================================================================

def run_compare_langs(file1_path: str, file2_path: str,
                      lang1_name: Optional[str] = None, lang2_name: Optional[str] = None,
                      output_dir: Optional[str] = None, comparison_mode: str = "keys") -> str:
    """
    Compare deux fichiers de traduction.

    Args:
        file1_path: Chemin du premier fichier (ou répertoire)
        file2_path: Chemin du second fichier (ou répertoire)
        lang1_name: Nom de la langue 1 (auto-détecté si None)
        lang2_name: Nom de la langue 2 (auto-détecté si None)
        output_dir: Répertoire de sortie (défaut: timestampé local)
        comparison_mode: Mode de comparaison ("keys" ou "values")

    Returns:
        Chemin du répertoire de sortie
    """
    # Résoudre les chemins
    _, file1 = resolve_path(file1_path)
    _, file2 = resolve_path(file2_path)

    # Auto-détecter les noms de langues depuis les noms de fichiers
    if not lang1_name:
        lang1_name = _extract_lang_from_filename(file1)
    if not lang2_name:
        lang2_name = _extract_lang_from_filename(file2)

    # Créer répertoire de sortie
    if not output_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"compare_langs_{timestamp}"
        )
    os.makedirs(output_dir, exist_ok=True)

    # Parser les fichiers
    lang1_strings = parse_translation_file(file1)
    lang2_strings = parse_translation_file(file2)

    # Comparer
    comparator = LanguageComparator(lang1_strings, lang2_strings, lang1_name, lang2_name)
    result = comparator.compare()

    # Générer les sorties
    _generate_json_output(output_dir, result, file1, file2, lang1_name, lang2_name, comparison_mode)
    _generate_text_report(output_dir, result, file1, file2, lang1_name, lang2_name,
                         lang1_strings, lang2_strings, comparison_mode)

    return output_dir


def _extract_lang_from_filename(filepath: str) -> str:
    """Extrait le code langue depuis un nom de fichier TranslatedStrings_xx.txt."""
    basename = os.path.basename(filepath)
    if basename.startswith('TranslatedStrings_') and basename.endswith('.txt'):
        return basename.replace('TranslatedStrings_', '').replace('.txt', '')
    return "unknown"


def _generate_json_output(output_dir: str, result: Dict, file1: str, file2: str,
                          lang1_name: str, lang2_name: str, comparison_mode: str = "keys"):
    """Génère le fichier JSON avec les données structurées."""
    data = {
        'generated': datetime.now().isoformat(),
        'file1': os.path.abspath(file1),
        'file2': os.path.abspath(file2),
        'lang1_name': lang1_name.upper(),
        'lang2_name': lang2_name.upper(),
        'comparison_mode': comparison_mode,
        'statistics': result['statistics']
    }

    # Adapter le contenu selon le mode
    if comparison_mode == "keys":
        # Mode CLÉS : focus sur les différences structurelles
        data['only_in_lang1'] = result['only_in_lang1']
        data['only_in_lang2'] = result['only_in_lang2']
        data['in_both'] = result['in_both']
    else:
        # Mode VALEURS : focus sur les traductions
        data['identical_values'] = result['identical_values']
        data['different_values'] = result['different_values']
        # Inclure les clés manquantes comme info contextuelle
        if result['only_in_lang1'] or result['only_in_lang2']:
            data['info_missing_keys'] = {
                'only_in_lang1': result['only_in_lang1'],
                'only_in_lang2': result['only_in_lang2']
            }

    output_file = os.path.join(output_dir, 'COMPARE_LANGS_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _generate_text_report(output_dir: str, result: Dict, file1: str, file2: str,
                          lang1_name: str, lang2_name: str,
                          lang1_strings: Dict[str, str], lang2_strings: Dict[str, str],
                          comparison_mode: str = "keys"):
    """Génère le rapport texte lisible."""
    stats = result['statistics']
    lang1_upper = lang1_name.upper()
    lang2_upper = lang2_name.upper()

    report_file = os.path.join(output_dir, 'COMPARE_LANGS_report.txt')

    with open(report_file, 'w', encoding='utf-8') as f:
        # En-tête
        f.write("=" * 80 + "\n")
        mode_label = "CLÉS" if comparison_mode == "keys" else "VALEURS"
        f.write(_("RAPPORT DE COMPARAISON DE LANGUES (MODE: {mode_label})\n").format(mode_label=mode_label))
        f.write("=" * 80 + "\n\n")

        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(_("Mode de comparaison: {mode_label}\n").format(mode_label=mode_label))
        f.write(_("Langue 1: {lang1_upper}\n").format(lang1_upper=lang1_upper))
        f.write(_("Langue 2: {lang2_upper}\n").format(lang2_upper=lang2_upper))
        f.write(_("Fichier 1: {file1}\n").format(file1=file1))
        f.write(_("Fichier 2: {file2}\n\n").format(file2=file2))

        # Statistiques globales
        f.write("-" * 80 + "\n")
        f.write(_("STATISTIQUES GLOBALES\n"))
        f.write("-" * 80 + "\n")
        f.write(_("  Total de clés uniques            : {var0:4d}\n").format(var0=stats['total_unique_keys']))
        f.write(_("  Clés dans {lang1_upper:<20s}     : {var1:4d}  ({var2:6.2f}%)\n").format(lang1_upper=lang1_upper, var1=stats['keys_in_lang1'], var2=stats['coverage_lang1_pct']))
        f.write(_("  Clés dans {lang2_upper:<20s}     : {var1:4d}  ({var2:6.2f}%)\n").format(lang2_upper=lang2_upper, var1=stats['keys_in_lang2'], var2=stats['coverage_lang2_pct']))
        f.write(_("  Clés présentes dans les deux     : {var0:4d}\n").format(var0=stats['keys_in_both']))
        f.write(_("  Clés seulement dans {lang1_upper:<12s} : {var1:4d}\n").format(lang1_upper=lang1_upper, var1=stats['only_lang1']))
        f.write(_("  Clés seulement dans {lang2_upper:<12s} : {var1:4d}\n").format(lang2_upper=lang2_upper, var1=stats['only_lang2']))
        f.write("\n")

        # Section adaptée au mode de comparaison
        if comparison_mode == "keys":
            # Mode CLÉS : mettre en avant les différences structurelles
            f.write("-" * 80 + "\n")
            f.write(_("ANALYSE DE LA STRUCTURE (MODE CLÉS)\n"))
            f.write("-" * 80 + "\n")
            if stats['only_lang1'] > 0 or stats['only_lang2'] > 0:
                f.write(_("  ⚠ DÉSYNCHRONISATION DÉTECTÉE\n"))
                f.write(_("  Clés manquantes dans {lang2_upper:<12s} : {var1:4d}\n").format(lang2_upper=lang2_upper, var1=stats['only_lang1']))
                f.write(_("  Clés manquantes dans {lang1_upper:<12s} : {var1:4d}\n").format(lang1_upper=lang1_upper, var1=stats['only_lang2']))
            else:
                f.write(_("  ✓ FICHIERS SYNCHRONISÉS (même structure de clés)\n"))
            f.write("\n")
        else:
            # Mode VALEURS : focus sur les traductions
            f.write("-" * 80 + "\n")
            f.write(_("ANALYSE DES TRADUCTIONS (MODE VALEURS)\n"))
            f.write("-" * 80 + "\n")
            f.write(_("  Clés communes analysées               : {var0:4d}\n").format(var0=stats['keys_in_both']))
            f.write(_("  Valeurs identiques (possibles oublis) : {var0:4d}\n").format(var0=stats['identical_values_count']))
            f.write(_("  Valeurs différentes (traduites)       : {var0:4d}\n").format(var0=stats['different_values_count']))
            f.write("\n")
            if stats['only_lang1'] > 0 or stats['only_lang2'] > 0:
                f.write(_("  Info: Clés manquantes dans {lang2_upper:<8s} : {var1:4d}\n").format(lang2_upper=lang2_upper, var1=stats['only_lang1']))
                f.write(_("  Info: Clés manquantes dans {lang1_upper:<8s} : {var1:4d}\n").format(lang1_upper=lang1_upper, var1=stats['only_lang2']))
                f.write("\n")

        # Sections adaptées au mode de comparaison
        if comparison_mode == "keys":
            # Mode CLÉS : focus sur les clés manquantes
            if result['only_in_lang1']:
                f.write("=" * 80 + "\n")
                f.write(_("CLÉS PRÉSENTES SEULEMENT DANS {lang1_upper} ({var1})\n").format(lang1_upper=lang1_upper, var1=len(result['only_in_lang1'])))
                f.write(_("Ces clés existent dans {lang1_upper} mais sont absentes de {lang2_upper}.\n").format(lang1_upper=lang1_upper, lang2_upper=lang2_upper))
                f.write("=" * 80 + "\n\n")
                for key in result['only_in_lang1']:
                    value = lang1_strings[key]
                    f.write(_("  [ONLY-{lang1_upper}] {key}\n").format(lang1_upper=lang1_upper, key=key))
                    f.write(_("        {lang1_upper}: {value}\n\n").format(lang1_upper=lang1_upper, value=value))

            if result['only_in_lang2']:
                f.write("=" * 80 + "\n")
                f.write(_("CLÉS PRÉSENTES SEULEMENT DANS {lang2_upper} ({var1})\n").format(lang2_upper=lang2_upper, var1=len(result['only_in_lang2'])))
                f.write(_("Ces clés existent dans {lang2_upper} mais sont absentes de {lang1_upper}.\n").format(lang2_upper=lang2_upper, lang1_upper=lang1_upper))
                f.write("=" * 80 + "\n\n")
                for key in result['only_in_lang2']:
                    value = lang2_strings[key]
                    f.write(_("  [ONLY-{lang2_upper}] {key}\n").format(lang2_upper=lang2_upper, key=key))
                    f.write(_("        {lang2_upper}: {value}\n\n").format(lang2_upper=lang2_upper, value=value))

        else:
            # Mode VALEURS : focus sur les traductions identiques/différentes
            if result['identical_values']:
                f.write("=" * 80 + "\n")
                f.write(_("CLÉS AVEC VALEURS IDENTIQUES ({var0})\n").format(var0=len(result['identical_values'])))
                f.write(_("Ces clés existent dans les deux langues avec la même valeur.\n"))

                # Avertissement si l'une des langues est EN
                if lang1_name.lower() == 'en' or lang2_name.lower() == 'en':
                    f.write(_("⚠️  ATTENTION: Valeurs identiques à l'anglais = possibles oublis de traduction!\n"))

                f.write("=" * 80 + "\n\n")
                for key in sorted(result['identical_values'].keys()):
                    value = result['identical_values'][key]
                    f.write(_("  [IDENTICAL] {key}\n").format(key=key))
                    f.write(_("        Valeur commune: {value}\n\n").format(value=value))

            if result['different_values']:
                f.write("=" * 80 + "\n")
                f.write(_("CLÉS AVEC VALEURS DIFFÉRENTES ({var0})\n").format(var0=len(result['different_values'])))
                f.write(_("Ces clés existent dans les deux langues avec des valeurs différentes.\n"))

                display_count = min(20, len(result['different_values']))
                if len(result['different_values']) > 20:
                    f.write(_("(Affichage des {display_count} premières différences)\n").format(display_count=display_count))

                f.write("=" * 80 + "\n\n")
                for key in result['different_values'][:display_count]:
                    val1 = lang1_strings[key]
                    val2 = lang2_strings[key]
                    f.write(_("  [DIFFERENT] {key}\n").format(key=key))
                    f.write(f"        {lang1_upper}: {val1}\n")
                    f.write(_("        {lang2_upper}: {val2}\n\n").format(lang2_upper=lang2_upper, val2=val2))

                if len(result['different_values']) > 20:
                    f.write(_("  ... et {var0} autres différences\n").format(var0=len(result['different_values']) - 20))
                    f.write(_("  (voir COMPARE_LANGS_data.json pour la liste complète)\n\n"))

        # Recommandations adaptées au mode
        f.write("\n" + "=" * 80 + "\n")
        f.write(_("RECOMMANDATIONS\n"))
        f.write("=" * 80 + "\n")

        if comparison_mode == "keys":
            # Recommandations pour le mode CLÉS
            if stats['only_lang1'] > 0:
                f.write(_("• {var0} clé(s) manquante(s) dans {lang2_upper}\n").format(var0=stats['only_lang1'], lang2_upper=lang2_upper))
                f.write(_("  → Ajouter ces traductions dans {lang2_upper}\n\n").format(lang2_upper=lang2_upper))

            if stats['only_lang2'] > 0:
                f.write(_("• {var0} clé(s) manquante(s) dans {lang1_upper}\n").format(var0=stats['only_lang2'], lang1_upper=lang1_upper))
                f.write(_("  → Ajouter ces traductions dans {lang1_upper}\n\n").format(lang1_upper=lang1_upper))

            if stats['only_lang1'] == 0 and stats['only_lang2'] == 0:
                f.write(_("✓ Les deux fichiers contiennent exactement les mêmes clés ({var0})\n").format(var0=stats['keys_in_both']))
                f.write(_("  Structure synchronisée avec succès!\n\n"))

        else:
            # Recommandations pour le mode VALEURS
            if stats['identical_values_count'] > 0:
                # Avertissement spécial si comparaison avec EN
                if lang1_name.lower() == 'en' or lang2_name.lower() == 'en':
                    f.write(f"⚠️  {stats['identical_values_count']} traduction(s) identique(s) à l'anglais détectée(s)!\n")
                    f.write(_("  → Vérifier si ces clés ont bien été traduites\n\n"))
                else:
                    f.write(_("• {var0} valeur(s) identique(s) entre les deux langues\n").format(var0=stats['identical_values_count']))
                    f.write(_("  → Vérifier si c'est intentionnel (noms propres, termes techniques)\n\n"))

            if stats['different_values_count'] > 0:
                f.write(_("✓ {var0} traduction(s) différente(s) détectée(s)\n").format(var0=stats['different_values_count']))
                f.write(_("  Cela indique des traductions effectuées correctement.\n\n"))

            if stats['only_lang1'] > 0 or stats['only_lang2'] > 0:
                f.write(_("\nInfo: Des clés sont manquantes dans l'un des fichiers.\n"))
                f.write(_("  Pour analyser la structure, relancez en mode CLÉS.\n\n"))


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_compare_langs(plugin_path: str = ""):
    """Menu interactif pour COMPARE-LANGS.

    Args:
        plugin_path: Chemin du plugin (optionnel) pour utiliser __i18n_tmp__
    """
    from .common import clear_screen, print_header
    from core.paths import get_tool_output_path

    clear_screen()
    print_header()
    print(_("\n{var0}COMPARE-LANGS{var1}: Comparer deux fichiers de traduction").format(var0=c.INFO, var1=c.RESET))
    print(c.separator())

    print(_("\n{var0}Vous pouvez comparer:{var1}").format(var0=c.DIM, var1=c.RESET))
    print(_("  {var0}• Deux langues différentes (ex: FR vs DE){var1}").format(var0=c.DIM, var1=c.RESET))
    print(f"  {c.DIM}• Deux versions d'une même langue (ex: ancien FR vs nouveau FR){c.RESET}")
    print(f"  {c.DIM}• Une langue vs EN (pour voir ce qui n'est pas traduit){c.RESET}")

    print(_("\n{var0}Mode de comparaison:{var1}").format(var0=c.KEY, var1=c.RESET))
    print(_("  {var0}1{var1}. {var2}Par clés{var3} - Identifie les clés manquantes/ajoutées (recommandé pour synchronisation)").format(var0=c.YELLOW, var1=c.RESET, var2=c.INFO, var3=c.RESET))
    print(_("  {var0}2{var1}. {var2}Par valeurs{var3} - Identifie les traductions identiques (recommandé pour audit qualité)").format(var0=c.YELLOW, var1=c.RESET, var2=c.INFO, var3=c.RESET))

    comparison_mode = input(c.prompt(_("Mode de comparaison") + " (1-2, défaut=1): ")).strip()
    if not comparison_mode:
        comparison_mode = "1"  # Défaut: mode clés

    if comparison_mode not in ["1", "2"]:
        print(c.error(_("Choix invalide.")))
        input(_("\nAppuyez sur Entrée..."))
        return None

    print(_("\n{var0}Mode de sélection:{var1}").format(var0=c.KEY, var1=c.RESET))
    print(_("  {var0}1{var1}. Par codes langue (ex: fr, de) - cherche dans un répertoire").format(var0=c.YELLOW, var1=c.RESET))
    print(_("  {var0}2{var1}. Par chemins de fichiers complets").format(var0=c.YELLOW, var1=c.RESET))

    mode = input(c.prompt(_("Votre choix (1-2, défaut=1): "))).strip()
    if not mode:
        mode = "1"  # Défaut: mode par codes langue

    file1 = None
    file2 = None
    lang1_name = None
    lang2_name = None

    if mode == '1':
        # Mode: sélection par codes langue
        print(_("\n{var0}Répertoire contenant les fichiers de langue{var1}:").format(var0=c.KEY, var1=c.RESET))
        print(_("{var0}  (par défaut: {var1}{plugin_path}{var3}{var4}){var5}").format(var0=c.DIM, var1=c.VALUE, plugin_path=plugin_path, var3=c.RESET, var4=c.DIM, var5=c.RESET))
        print(_("{var0}  Appuyez sur Entrée pour utiliser le répertoire par défaut, ou saisissez un autre chemin{var1}").format(var0=c.DIM, var1=c.RESET))
        user_input = input(f"{c.PROMPT}  > {c.RESET}").strip()

        # Utiliser le plugin par défaut si rien saisi
        locales_dir = user_input if user_input else plugin_path

        if not locales_dir or not os.path.isdir(locales_dir):
            print(c.error(_("Répertoire invalide.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

        # Trouver les langues disponibles
        available_langs = find_languages(locales_dir, exclude_reference=False)
        if not available_langs:
            print(c.error(_("Aucun fichier TranslatedStrings trouvé dans ce répertoire.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

        print(f"\n{c.INFO}Langues disponibles{c.RESET}: {c.VALUE}{', '.join(available_langs)}{c.RESET}")

        print(_("\n{var0}Code de la première langue{var1} (ex: fr, en, de):").format(var0=c.KEY, var1=c.RESET))
        lang1_name = input(f"{c.PROMPT}  > {c.RESET}").strip().lower()
        if not lang1_name or lang1_name not in available_langs:
            print(c.error(_("Langue '{lang1_name}' non trouvée.").format(lang1_name=lang1_name)))
            input(_("\nAppuyez sur Entrée..."))
            return None

        print(_("\n{var0}Code de la seconde langue{var1} (ex: fr, en, de):").format(var0=c.KEY, var1=c.RESET))
        lang2_name = input(f"{c.PROMPT}  > {c.RESET}").strip().lower()
        if not lang2_name or lang2_name not in available_langs:
            print(c.error(_("Langue '{lang2_name}' non trouvée.").format(lang2_name=lang2_name)))
            input(_("\nAppuyez sur Entrée..."))
            return None

        file1 = os.path.join(locales_dir, f'TranslatedStrings_{lang1_name}.txt')
        file2 = os.path.join(locales_dir, f'TranslatedStrings_{lang2_name}.txt')

    elif mode == '2':
        # Mode: chemins complets
        print(_("\n{var0}Chemin du PREMIER fichier{var1} (TranslatedStrings_*.txt ou répertoire):").format(var0=c.KEY, var1=c.RESET))
        file1 = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not file1:
            print(c.error(_("Chemin requis.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

        print(_("\n{var0}Chemin du SECOND fichier{var1} (TranslatedStrings_*.txt ou répertoire):").format(var0=c.KEY, var1=c.RESET))
        file2 = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not file2:
            print(c.error(_("Chemin requis.")))
            input(_("\nAppuyez sur Entrée..."))
            return None

    else:
        print(c.error(_("Choix invalide.")))
        input(_("\nAppuyez sur Entrée..."))
        return None

    # Exécuter la comparaison
    try:
        print(_("\n{var0}[INFO]{var1} Comparaison en cours...").format(var0=c.INFO, var1=c.RESET))

        # Déterminer le répertoire de sortie
        if plugin_path:
            output_dir = get_tool_output_path(plugin_path, "Translator", create=True)
        else:
            output_dir = None  # run_compare_langs créera un dossier local

        # Convertir le mode de comparaison
        comp_mode = "keys" if comparison_mode == "1" else "values"

        output_dir = run_compare_langs(file1, file2, lang1_name, lang2_name, output_dir, comp_mode)

        # Charger le résultat pour affichage
        with open(os.path.join(output_dir, 'COMPARE_LANGS_data.json'), 'r', encoding='utf-8') as f:
            result = json.load(f)

        stats = result['statistics']
        l1 = result['lang1_name']
        l2 = result['lang2_name']
        mode = result.get('comparison_mode', 'keys')

        # Afficher le résumé
        print(f"\n{c.HEADER}{'=' * 66}{c.RESET}")
        mode_label = "CLÉS" if mode == "keys" else "VALEURS"
        print(_("{var0}  RÉSUMÉ DE LA COMPARAISON ({mode_label}){var2}").format(var0=c.TITLE, mode_label=mode_label, var2=c.RESET))
        print(f"{c.HEADER}{'=' * 66}{c.RESET}")
        print(_("  {var0}Langue 1{var1}: {var2}{l1}{var4}  ({var5}{var6}{var7} clés)").format(var0=c.KEY, var1=c.RESET, var2=c.CYAN, l1=l1, var4=c.RESET, var5=c.VALUE, var6=stats['keys_in_lang1'], var7=c.RESET))
        print(_("  {var0}Langue 2{var1}: {var2}{l2}{var4}  ({var5}{var6}{var7} clés)").format(var0=c.KEY, var1=c.RESET, var2=c.CYAN, l2=l2, var4=c.RESET, var5=c.VALUE, var6=stats['keys_in_lang2'], var7=c.RESET))
        print()

        if mode == "keys":
            # Mode CLÉS : focus sur les différences structurelles
            print(_("  {var0}Total de clés uniques       {var1}: {var2}{var3:4d}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.VALUE, var3=stats['total_unique_keys'], var4=c.RESET))
            print(_("  {var0}Clés dans les deux langues  {var1}: {var2}{var3:4d}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.GREEN, var3=stats['keys_in_both'], var4=c.RESET))
            print(_("  {var0}Seulement dans {l1:<12s}{var2}: {var3}{var4:4d}{var5}").format(var0=c.KEY, l1=l1, var2=c.RESET, var3=c.YELLOW, var4=stats['only_lang1'], var5=c.RESET))
            print(_("  {var0}Seulement dans {l2:<12s}{var2}: {var3}{var4:4d}{var5}").format(var0=c.KEY, l2=l2, var2=c.RESET, var3=c.YELLOW, var4=stats['only_lang2'], var5=c.RESET))
        else:
            # Mode VALEURS : focus sur la qualité des traductions
            print(_("  {var0}Clés communes analysées     {var1}: {var2}{var3:4d}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.VALUE, var3=stats['keys_in_both'], var4=c.RESET))
            print(_("  {var0}Valeurs identiques          {var1}: {var2}{var3:4d}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.WARNING, var3=stats['identical_values_count'], var4=c.RESET))
            print(_("  {var0}Valeurs différentes         {var1}: {var2}{var3:4d}{var4}").format(var0=c.KEY, var1=c.RESET, var2=c.GREEN, var3=stats['different_values_count'], var4=c.RESET))
            print()
            print(_("  {var0}Info: Total de clés uniques : {var1:4d}{var2}").format(var0=c.DIM, var1=stats['total_unique_keys'], var2=c.RESET))
            print(_("  {var0}Info: Seulement dans {l1:<8s}: {var2:4d}{var3}").format(var0=c.DIM, l1=l1, var2=stats['only_lang1'], var3=c.RESET))
            print(_("  {var0}Info: Seulement dans {l2:<8s}: {var2:4d}{var3}").format(var0=c.DIM, l2=l2, var2=stats['only_lang2'], var3=c.RESET))

        print()

        # Avertissements
        if mode == "values" and stats['identical_values_count'] > 0:
            print(_("  {var0}⚠️  {var1} traduction(s) identique(s) détectée(s)!{var2}").format(var0=c.WARNING, var1=stats['identical_values_count'], var2=c.RESET))
            if l1 == 'EN' or l2 == 'EN':
                print(_("  {var0}   Possibles traductions oubliées (identiques à EN){var1}").format(var0=c.WARNING, var1=c.RESET))
        elif mode == "keys" and (stats['only_lang1'] > 0 or stats['only_lang2'] > 0):
            print(_("  {var0}⚠️  Fichiers désynchronisés : clés manquantes détectées{var1}").format(var0=c.WARNING, var1=c.RESET))

        print(_("\n{var0}Fichiers générés dans:{var1} {var2}{output_dir}{var4}").format(var0=c.SUCCESS, var1=c.RESET, var2=c.VALUE, output_dir=output_dir, var4=c.RESET))
        print(_("  {var0}• COMPARE_LANGS_report.txt{var1}").format(var0=c.DIM, var1=c.RESET))
        print(_("  {var0}• COMPARE_LANGS_data.json{var1}").format(var0=c.DIM, var1=c.RESET))

        input(_("\nAppuyez sur Entrée pour continuer..."))
        return output_dir

    except FileNotFoundError as e:
        print(c.error(_("Fichier non trouvé: {e}").format(e=e)))
        input(_("\nAppuyez sur Entrée..."))
    except Exception as e:
        print(c.error(_("Erreur: {e}").format(e=e)))
        import traceback
        traceback.print_exc()
        input(_("\nAppuyez sur Entrée..."))

    return None
