#!/usr/bin/env python3
"""
TM_compare_langs.py

Module COMPARE-LANGS pour Translator.
Compare deux fichiers TranslatedStrings de langues différentes.

================================================================================
DESCRIPTION
================================================================================

Ce module permet de comparer deux fichiers de traduction (TranslatedStrings)
de langues différentes ou identiques pour :

1. Identifier les clés présentes dans un fichier mais absentes de l'autre
2. Détecter les traductions identiques (possibles oublis de traduction)
3. Comparer deux versions d'une même langue (avant/après révision)
4. Générer des rapports de complétude et de cohérence

================================================================================
CAS D'USAGE
================================================================================

1. Vérifier la cohérence entre langues
   - Comparer FR vs EN pour voir les clés manquantes en français
   - Comparer DE vs FR pour harmoniser deux traductions

2. Audit qualité
   - Identifier les traductions non faites (valeurs identiques à l'anglais)
   - Vérifier qu'une langue a bien toutes les clés d'une autre

3. Suivi de versions
   - Comparer ancienne version FR vs nouvelle version FR
   - Voir l'évolution des traductions

================================================================================
SORTIES GÉNÉRÉES
================================================================================

Le module génère dans le répertoire de sortie :

1. COMPARE_LANGS_report.txt
   - Rapport détaillé lisible avec toutes les différences
   - Statistiques complètes
   - Recommandations

2. COMPARE_LANGS_data.json
   - Données structurées pour traitement automatique
   - Listes des clés par catégorie

================================================================================
USAGE
================================================================================

Mode interactif (recommandé):
    Menu principal > Options avancées > COMPARE-LANGS

Mode CLI:
    python Translator_main.py compare-langs --lang1 fr --lang2 de --locales ./Locales
    python Translator_main.py compare-langs --file1 ./v1/fr.txt --file2 ./v2/fr.txt

Auteur: Claude (Anthropic) pour Julien Moreau
Date: 2026-02-02
Version: 1.0 - Création initiale
"""

import os
import json
from datetime import datetime
from typing import Dict, Set, Tuple, Optional

from TM_common import (
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
                      lang1_name: str = None, lang2_name: str = None,
                      output_dir: str = None) -> str:
    """
    Compare deux fichiers de traduction.

    Args:
        file1_path: Chemin du premier fichier (ou répertoire)
        file2_path: Chemin du second fichier (ou répertoire)
        lang1_name: Nom de la langue 1 (auto-détecté si None)
        lang2_name: Nom de la langue 2 (auto-détecté si None)
        output_dir: Répertoire de sortie (défaut: timestampé local)

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
    _generate_json_output(output_dir, result, file1, file2, lang1_name, lang2_name)
    _generate_text_report(output_dir, result, file1, file2, lang1_name, lang2_name,
                         lang1_strings, lang2_strings)

    return output_dir


def _extract_lang_from_filename(filepath: str) -> str:
    """Extrait le code langue depuis un nom de fichier TranslatedStrings_xx.txt."""
    basename = os.path.basename(filepath)
    if basename.startswith('TranslatedStrings_') and basename.endswith('.txt'):
        return basename.replace('TranslatedStrings_', '').replace('.txt', '')
    return "unknown"


def _generate_json_output(output_dir: str, result: Dict, file1: str, file2: str,
                          lang1_name: str, lang2_name: str):
    """Génère le fichier JSON avec les données structurées."""
    data = {
        'generated': datetime.now().isoformat(),
        'file1': os.path.abspath(file1),
        'file2': os.path.abspath(file2),
        'lang1_name': lang1_name.upper(),
        'lang2_name': lang2_name.upper(),
        'statistics': result['statistics'],
        'only_in_lang1': result['only_in_lang1'],
        'only_in_lang2': result['only_in_lang2'],
        'identical_values': result['identical_values'],
        'different_values': result['different_values']
    }

    output_file = os.path.join(output_dir, 'COMPARE_LANGS_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _generate_text_report(output_dir: str, result: Dict, file1: str, file2: str,
                          lang1_name: str, lang2_name: str,
                          lang1_strings: Dict[str, str], lang2_strings: Dict[str, str]):
    """Génère le rapport texte lisible."""
    stats = result['statistics']
    lang1_upper = lang1_name.upper()
    lang2_upper = lang2_name.upper()

    report_file = os.path.join(output_dir, 'COMPARE_LANGS_report.txt')

    with open(report_file, 'w', encoding='utf-8') as f:
        # En-tête
        f.write("=" * 80 + "\n")
        f.write("RAPPORT DE COMPARAISON DE LANGUES\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Langue 1: {lang1_upper}\n")
        f.write(f"Langue 2: {lang2_upper}\n")
        f.write(f"Fichier 1: {file1}\n")
        f.write(f"Fichier 2: {file2}\n\n")

        # Statistiques globales
        f.write("-" * 80 + "\n")
        f.write("STATISTIQUES GLOBALES\n")
        f.write("-" * 80 + "\n")
        f.write(f"  Total de clés uniques            : {stats['total_unique_keys']:4d}\n")
        f.write(f"  Clés dans {lang1_upper:<20s}     : {stats['keys_in_lang1']:4d}  ({stats['coverage_lang1_pct']:6.2f}%)\n")
        f.write(f"  Clés dans {lang2_upper:<20s}     : {stats['keys_in_lang2']:4d}  ({stats['coverage_lang2_pct']:6.2f}%)\n")
        f.write(f"  Clés présentes dans les deux     : {stats['keys_in_both']:4d}\n")
        f.write(f"  Clés seulement dans {lang1_upper:<12s} : {stats['only_lang1']:4d}\n")
        f.write(f"  Clés seulement dans {lang2_upper:<12s} : {stats['only_lang2']:4d}\n")
        f.write("\n")

        # Analyse des clés communes
        f.write("-" * 80 + "\n")
        f.write("ANALYSE DES CLÉS COMMUNES\n")
        f.write("-" * 80 + "\n")
        f.write(f"  Valeurs identiques               : {stats['identical_values_count']:4d}\n")
        f.write(f"  Valeurs différentes              : {stats['different_values_count']:4d}\n")
        f.write("\n")

        # Section 1: Clés seulement dans Lang1
        if result['only_in_lang1']:
            f.write("=" * 80 + "\n")
            f.write(f"CLÉS PRÉSENTES SEULEMENT DANS {lang1_upper} ({len(result['only_in_lang1'])})\n")
            f.write(f"Ces clés existent dans {lang1_upper} mais sont absentes de {lang2_upper}.\n")
            f.write("=" * 80 + "\n\n")
            for key in result['only_in_lang1']:
                value = lang1_strings[key]
                f.write(f"  [ONLY-{lang1_upper}] {key}\n")
                f.write(f"        {lang1_upper}: {value}\n\n")

        # Section 2: Clés seulement dans Lang2
        if result['only_in_lang2']:
            f.write("=" * 80 + "\n")
            f.write(f"CLÉS PRÉSENTES SEULEMENT DANS {lang2_upper} ({len(result['only_in_lang2'])})\n")
            f.write(f"Ces clés existent dans {lang2_upper} mais sont absentes de {lang1_upper}.\n")
            f.write("=" * 80 + "\n\n")
            for key in result['only_in_lang2']:
                value = lang2_strings[key]
                f.write(f"  [ONLY-{lang2_upper}] {key}\n")
                f.write(f"        {lang2_upper}: {value}\n\n")

        # Section 3: Valeurs identiques (possibles oublis de traduction)
        if result['identical_values']:
            f.write("=" * 80 + "\n")
            f.write(f"CLÉS AVEC VALEURS IDENTIQUES ({len(result['identical_values'])})\n")
            f.write(f"Ces clés existent dans les deux langues avec la même valeur.\n")

            # Avertissement si l'une des langues est EN
            if lang1_name.lower() == 'en' or lang2_name.lower() == 'en':
                f.write("⚠️  ATTENTION: Valeurs identiques à l'anglais = possibles oublis de traduction!\n")

            f.write("=" * 80 + "\n\n")
            for key in sorted(result['identical_values'].keys()):
                value = result['identical_values'][key]
                f.write(f"  [IDENTICAL] {key}\n")
                f.write(f"        Valeur commune: {value}\n\n")

        # Section 4: Exemples de différences (max 20)
        if result['different_values']:
            f.write("=" * 80 + "\n")
            f.write(f"CLÉS AVEC VALEURS DIFFÉRENTES ({len(result['different_values'])})\n")
            f.write(f"Ces clés existent dans les deux langues avec des valeurs différentes.\n")

            display_count = min(20, len(result['different_values']))
            if len(result['different_values']) > 20:
                f.write(f"(Affichage des {display_count} premières différences)\n")

            f.write("=" * 80 + "\n\n")
            for key in result['different_values'][:display_count]:
                val1 = lang1_strings[key]
                val2 = lang2_strings[key]
                f.write(f"  [DIFFERENT] {key}\n")
                f.write(f"        {lang1_upper}: {val1}\n")
                f.write(f"        {lang2_upper}: {val2}\n\n")

            if len(result['different_values']) > 20:
                f.write(f"  ... et {len(result['different_values']) - 20} autres différences\n")
                f.write(f"  (voir COMPARE_LANGS_data.json pour la liste complète)\n\n")

        # Recommandations
        f.write("\n" + "=" * 80 + "\n")
        f.write("RECOMMANDATIONS\n")
        f.write("=" * 80 + "\n")

        if stats['only_lang1'] > 0:
            f.write(f"• {stats['only_lang1']} clé(s) manquante(s) dans {lang2_upper}\n")
            f.write(f"  → Ajouter ces traductions dans {lang2_upper}\n\n")

        if stats['only_lang2'] > 0:
            f.write(f"• {stats['only_lang2']} clé(s) manquante(s) dans {lang1_upper}\n")
            f.write(f"  → Ajouter ces traductions dans {lang1_upper}\n\n")

        if stats['identical_values_count'] > 0:
            # Avertissement spécial si comparaison avec EN
            if lang1_name.lower() == 'en' or lang2_name.lower() == 'en':
                f.write(f"⚠️  {stats['identical_values_count']} traduction(s) identique(s) à l'anglais détectée(s)!\n")
                f.write(f"  → Vérifier si ces clés ont bien été traduites\n\n")
            else:
                f.write(f"• {stats['identical_values_count']} valeur(s) identique(s) entre les deux langues\n")
                f.write(f"  → Vérifier si c'est intentionnel (noms propres, termes techniques)\n\n")

        if stats['different_values_count'] == 0 and stats['only_lang1'] == 0 and stats['only_lang2'] == 0:
            f.write("✓ Les deux fichiers sont parfaitement identiques!\n\n")
        elif stats['only_lang1'] == 0 and stats['only_lang2'] == 0:
            f.write(f"✓ Les deux fichiers contiennent exactement les mêmes clés ({stats['keys_in_both']})\n\n")


# =============================================================================
# MENU INTERACTIF
# =============================================================================

def menu_compare_langs(plugin_path: str = ""):
    """Menu interactif pour COMPARE-LANGS.

    Args:
        plugin_path: Chemin du plugin (optionnel) pour utiliser __i18n_tmp__
    """
    from TM_common import clear_screen, print_header
    from common.paths import get_tool_output_path

    clear_screen()
    print_header()
    print(f"\n{c.INFO}COMPARE-LANGS{c.RESET}: Comparer deux fichiers de traduction")
    print(c.separator())

    print(f"\n{c.DIM}Vous pouvez comparer:{c.RESET}")
    print(f"  {c.DIM}• Deux langues différentes (ex: FR vs DE){c.RESET}")
    print(f"  {c.DIM}• Deux versions d'une même langue (ex: ancien FR vs nouveau FR){c.RESET}")
    print(f"  {c.DIM}• Une langue vs EN (pour voir ce qui n'est pas traduit){c.RESET}")

    print(f"\n{c.KEY}Mode de sélection:{c.RESET}")
    print(f"  {c.YELLOW}1{c.RESET}. Par codes langue (ex: fr, de) - cherche dans un répertoire")
    print(f"  {c.YELLOW}2{c.RESET}. Par chemins de fichiers complets")

    mode = input(f"\n{c.PROMPT}  Votre choix (1-2): {c.RESET}").strip()

    file1 = None
    file2 = None
    lang1_name = None
    lang2_name = None

    if mode == '1':
        # Mode: sélection par codes langue
        print(f"\n{c.KEY}Répertoire contenant les fichiers de langue{c.RESET}:")
        print(f"{c.DIM}  (ex: ./Locales ou chemin vers le plugin){c.RESET}")
        locales_dir = input(f"{c.PROMPT}  > {c.RESET}").strip()

        if not locales_dir or not os.path.isdir(locales_dir):
            print(c.error("Répertoire invalide."))
            input("\nAppuyez sur Entrée...")
            return None

        # Trouver les langues disponibles
        available_langs = find_languages(locales_dir, exclude_en=False)
        if not available_langs:
            print(c.error("Aucun fichier TranslatedStrings trouvé dans ce répertoire."))
            input("\nAppuyez sur Entrée...")
            return None

        print(f"\n{c.INFO}Langues disponibles{c.RESET}: {c.VALUE}{', '.join(available_langs)}{c.RESET}")

        print(f"\n{c.KEY}Code de la première langue{c.RESET} (ex: fr, en, de):")
        lang1_name = input(f"{c.PROMPT}  > {c.RESET}").strip().lower()
        if not lang1_name or lang1_name not in available_langs:
            print(c.error(f"Langue '{lang1_name}' non trouvée."))
            input("\nAppuyez sur Entrée...")
            return None

        print(f"\n{c.KEY}Code de la seconde langue{c.RESET} (ex: fr, en, de):")
        lang2_name = input(f"{c.PROMPT}  > {c.RESET}").strip().lower()
        if not lang2_name or lang2_name not in available_langs:
            print(c.error(f"Langue '{lang2_name}' non trouvée."))
            input("\nAppuyez sur Entrée...")
            return None

        file1 = os.path.join(locales_dir, f'TranslatedStrings_{lang1_name}.txt')
        file2 = os.path.join(locales_dir, f'TranslatedStrings_{lang2_name}.txt')

    elif mode == '2':
        # Mode: chemins complets
        print(f"\n{c.KEY}Chemin du PREMIER fichier{c.RESET} (TranslatedStrings_*.txt ou répertoire):")
        file1 = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not file1:
            print(c.error("Chemin requis."))
            input("\nAppuyez sur Entrée...")
            return None

        print(f"\n{c.KEY}Chemin du SECOND fichier{c.RESET} (TranslatedStrings_*.txt ou répertoire):")
        file2 = input(f"{c.PROMPT}  > {c.RESET}").strip()
        if not file2:
            print(c.error("Chemin requis."))
            input("\nAppuyez sur Entrée...")
            return None

    else:
        print(c.error("Choix invalide."))
        input("\nAppuyez sur Entrée...")
        return None

    # Exécuter la comparaison
    try:
        print(f"\n{c.INFO}[INFO]{c.RESET} Comparaison en cours...")

        # Déterminer le répertoire de sortie
        if plugin_path:
            output_dir = get_tool_output_path(plugin_path, "Translator", create=True)
        else:
            output_dir = None  # run_compare_langs créera un dossier local

        output_dir = run_compare_langs(file1, file2, lang1_name, lang2_name, output_dir)

        # Charger le résultat pour affichage
        with open(os.path.join(output_dir, 'COMPARE_LANGS_data.json'), 'r', encoding='utf-8') as f:
            result = json.load(f)

        stats = result['statistics']
        l1 = result['lang1_name']
        l2 = result['lang2_name']

        # Afficher le résumé
        print(f"\n{c.HEADER}{'=' * 66}{c.RESET}")
        print(f"{c.TITLE}  RÉSUMÉ DE LA COMPARAISON{c.RESET}")
        print(f"{c.HEADER}{'=' * 66}{c.RESET}")
        print(f"  {c.KEY}Langue 1{c.RESET}: {c.CYAN}{l1}{c.RESET}  ({c.VALUE}{stats['keys_in_lang1']}{c.RESET} clés)")
        print(f"  {c.KEY}Langue 2{c.RESET}: {c.CYAN}{l2}{c.RESET}  ({c.VALUE}{stats['keys_in_lang2']}{c.RESET} clés)")
        print()
        print(f"  {c.KEY}Total de clés uniques       {c.RESET}: {c.VALUE}{stats['total_unique_keys']:4d}{c.RESET}")
        print(f"  {c.KEY}Clés dans les deux langues  {c.RESET}: {c.GREEN}{stats['keys_in_both']:4d}{c.RESET}")
        print(f"  {c.KEY}Seulement dans {l1:<12s}{c.RESET}: {c.YELLOW}{stats['only_lang1']:4d}{c.RESET}")
        print(f"  {c.KEY}Seulement dans {l2:<12s}{c.RESET}: {c.YELLOW}{stats['only_lang2']:4d}{c.RESET}")
        print()
        print(f"  {c.KEY}Valeurs identiques          {c.RESET}: {c.DIM}{stats['identical_values_count']:4d}{c.RESET}")
        print(f"  {c.KEY}Valeurs différentes         {c.RESET}: {c.VALUE}{stats['different_values_count']:4d}{c.RESET}")
        print()

        # Avertissements
        if stats['identical_values_count'] > 0 and (l1 == 'EN' or l2 == 'EN'):
            print(f"  {c.WARNING}⚠️  {stats['identical_values_count']} traduction(s) identique(s) à EN détectée(s)!{c.RESET}")

        print(c.success(f"\nFichiers générés dans: {c.VALUE}{output_dir}{c.RESET}"))
        print(f"  {c.DIM}• COMPARE_LANGS_report.txt{c.RESET}")
        print(f"  {c.DIM}• COMPARE_LANGS_data.json{c.RESET}")

        return output_dir

    except FileNotFoundError as e:
        print(c.error(f"Fichier non trouvé: {e}"))
    except Exception as e:
        print(c.error(f"Erreur: {e}"))
        import traceback
        traceback.print_exc()

    return None
