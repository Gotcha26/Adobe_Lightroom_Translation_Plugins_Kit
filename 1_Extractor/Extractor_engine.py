#!/usr/bin/env python3
"""
Extractor_engine.py

Moteur principal d'extraction des chaînes localisables.
Analyse les fichiers Lua et extrait les chaînes UI.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional

from Extractor_config import (
    LOG_LINE_REGEX, UI_CONTEXT_PATTERNS, ALL_STRINGS_PATTERN,
    IGNORE_LOC_KEY_PATTERNS, IGNORE_LOC_VALUES
)
from Extractor_models import ExtractedString, ExtractionStats
from Extractor_utils import (
    extract_spacing, extract_all_string_literals, is_line_concatenated,
    extract_suffix, is_technical_string, generate_loc_key, generate_replacement_code,
    is_in_technical_context
)


class MultiLineContext:
    """
    Gère le contexte pour les appels multi-lignes (LrDialogs, LrErrors, statusMsg, etc.).

    Détecte quand un appel de fonction ou une assignation s'étale sur plusieurs lignes
    et accumule le contenu jusqu'à ce que les parenthèses soient équilibrées ou que
    la chaîne concaténée soit complète.

    Stocke chaque ligne avec son numéro pour pouvoir retrouver la ligne exacte
    d'une chaîne extraite.
    """

    def __init__(self):
        self.active = False
        self.pattern_name = ""
        self.start_line = 0
        self.paren_depth = 0
        self.lines_with_numbers = []  # Liste de tuples (line_num, line_content)
        self.is_concatenation = False

    def start(self, pattern_name: str, line_num: int, line: str):
        """Démarre un nouveau contexte multi-ligne."""
        self.active = True
        self.pattern_name = pattern_name
        self.start_line = line_num
        self.paren_depth = line.count('(') - line.count(')')
        self.lines_with_numbers = [(line_num, line)]
        self.is_concatenation = line.rstrip().endswith('..')

    def add_line(self, line_num: int, line: str) -> bool:
        """
        Ajoute une ligne au contexte.

        Args:
            line_num: Numéro de la ligne
            line: Contenu de la ligne

        Returns:
            True si le contexte est maintenant complet
        """
        if not self.active:
            return False

        self.lines_with_numbers.append((line_num, line))
        self.paren_depth += line.count('(') - line.count(')')

        line_stripped = line.rstrip()
        self.is_concatenation = line_stripped.endswith('..')

        if self.paren_depth <= 0 and not self.is_concatenation:
            return True

        return False

    def reset(self):
        """Réinitialise le contexte."""
        self.active = False
        self.pattern_name = ""
        self.start_line = 0
        self.paren_depth = 0
        self.lines_with_numbers = []
        self.is_concatenation = False

    def get_combined_content(self) -> str:
        """Retourne le contenu combiné de toutes les lignes."""
        return ' '.join(line.strip() for _, line in self.lines_with_numbers)

    def find_line_for_string(self, search_text: str) -> int:
        """
        Trouve le numéro de ligne réel où se trouve une chaîne.

        Args:
            search_text: La chaîne à rechercher

        Returns:
            Le numéro de ligne où la chaîne a été trouvée, ou start_line par défaut
        """
        # Chercher la chaîne exacte (avec guillemets) dans chaque ligne
        search_quoted = f'"{search_text}"'

        for line_num, line_content in self.lines_with_numbers:
            if search_quoted in line_content:
                return line_num

        # Si pas trouvé avec guillemets doubles, essayer sans (cas des concaténations)
        for line_num, line_content in self.lines_with_numbers:
            if search_text in line_content:
                return line_num

        # Par défaut, retourner la première ligne
        return self.start_line


class LocalizableStringExtractor:
    """Moteur d'extraction des chaînes localisables."""

    def __init__(self, plugin_path: str, prefix: str = "$$$/Piwigo",
                 min_length: int = 3, exclude_files: List[str] = None,
                 ignore_log: bool = True):
        self.plugin_path = plugin_path
        self.prefix = prefix
        self.min_length = min_length
        self.ignore_log = ignore_log
        self.exclude_files = set(exclude_files or [])
        self.exclude_files.add('JSON.lua')

        self.extracted: List[ExtractedString] = []
        self.stats = ExtractionStats()
        self.seen_texts: Dict[str, ExtractedString] = {}
        self.text_to_key: Dict[str, str] = {}
        self.spacing_metadata: Dict[str, Dict] = {}
        self.used_keys: set = set()

        # Contexte multi-ligne
        self.multi_line_ctx = MultiLineContext()

    def _is_already_localized(self, text: str, line: str) -> bool:
        """
        Vérifie si une chaîne spécifique est déjà localisée dans la ligne.

        Cherche si le texte est précédé de 'LOC "$$$/...'
        """
        # Chercher toutes les occurrences du texte
        search_pattern = re.compile(r'LOC\s*["\'](\$\$\$/[^=]+=)' + re.escape(text) + r'["\']')
        return search_pattern.search(line) is not None

    def _find_non_localized_strings(self, line: str) -> List[Tuple[str, int, int]]:
        """
        Trouve les chaînes qui ne sont PAS encore localisées dans une ligne.

        Gère les lignes mixtes avec certaines chaînes déjà localisées.

        Returns:
            Liste de (texte, start_pos, end_pos) pour les chaînes non localisées
        """
        all_strings = extract_all_string_literals(line)
        non_localized = []

        for text, start_pos, end_pos in all_strings:
            if not text.strip():
                continue

            # Vérifier si cette chaîne est dans un appel LOC
            # Regarder ce qui précède la position de la chaîne
            before = line[:start_pos]

            # Pattern: LOC "$$$/Key= juste avant le texte
            if re.search(r'LOC\s*"(\$\$\$/[^=]+=)\s*$', before):
                # C'est la valeur par défaut d'un LOC existant
                continue

            # Pattern: "$$$/Key= au début de la chaîne (l'utilisateur a mis le LOC dans la chaîne)
            if text.startswith('$$$/'):
                continue

            non_localized.append((text, start_pos, end_pos))

        return non_localized

    def extract_from_file(self, file_path: str):
        """Extrait les chaînes d'un fichier Lua, y compris les chaînes concaténées et multi-lignes."""
        self.stats.files_processed += 1
        file_name = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, self.plugin_path)

        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Erreur lecture {file_path}: {e}")
            return

        file_has_strings = False
        self.multi_line_ctx.reset()

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Ignorer les commentaires Lua
            if line_stripped.startswith('--'):
                continue

            # Gestion du contexte multi-ligne en cours
            if self.multi_line_ctx.active:
                is_complete = self.multi_line_ctx.add_line(line_num, line)
                if is_complete:
                    # Traiter le bloc complet
                    # Extraire les chaînes du bloc combiné avec le contexte pour retrouver les lignes
                    extracted_from_block = self._extract_from_combined_block(
                        self.multi_line_ctx, rel_path, file_name
                    )
                    self.multi_line_ctx.reset()
                    if extracted_from_block:
                        file_has_strings = True
                continue

            # CONTRAINTE 1: Ignorer les lignes de log
            if self.ignore_log and LOG_LINE_REGEX.search(line):
                self.stats.log_lines_ignored += 1
                continue

            # Vérifier si la ligne contient un contexte UI
            matched_pattern = None
            for pattern_name, pattern_re in UI_CONTEXT_PATTERNS:
                if pattern_re.search(line):
                    matched_pattern = pattern_name
                    break

            if not matched_pattern:
                continue

            # Calculer l'équilibre des parenthèses et détecter les concaténations
            paren_balance = line.count('(') - line.count(')')
            ends_with_concat = line_stripped.endswith('..')

            # Détecter si c'est un appel/assignation multi-ligne
            # Cas 1: Parenthèses non fermées (paren_balance > 0)
            # Cas 2: Ligne se terminant par ".." (concaténation qui continue)
            if paren_balance > 0 or ends_with_concat:
                # Début d'un bloc multi-ligne
                self.multi_line_ctx.start(matched_pattern, line_num, line)
                continue

            # Traitement standard (ligne simple complète)
            extracted_from_line = self._process_single_line(
                line, line_stripped, rel_path, file_name, line_num, matched_pattern
            )
            if extracted_from_line:
                file_has_strings = True

        # Gérer le cas où le fichier se termine avec un contexte multi-ligne non fermé
        if self.multi_line_ctx.active:
            extracted_from_block = self._extract_from_combined_block(
                self.multi_line_ctx, rel_path, file_name
            )
            self.multi_line_ctx.reset()
            if extracted_from_block:
                file_has_strings = True

        if file_has_strings:
            self.stats.files_with_strings += 1

    def _extract_from_combined_block(self, ctx: MultiLineContext, rel_path: str,
                                      file_name: str) -> bool:
        """
        Extrait les chaînes d'un bloc combiné multi-ligne.

        Args:
            ctx: Le contexte multi-ligne contenant les lignes avec leurs numéros
            rel_path: Chemin relatif du fichier
            file_name: Nom du fichier

        Returns:
            True si des chaînes ont été extraites
        """
        combined = ctx.get_combined_content()
        pattern_name = ctx.pattern_name

        # Utiliser _find_non_localized_strings pour ne pas re-localiser
        non_localized = self._find_non_localized_strings(combined)

        if not non_localized:
            return False

        extracted_any = False

        for original_text, start_pos, end_pos in non_localized:
            if len(original_text.strip()) < self.min_length:
                continue

            if is_technical_string(original_text, combined):
                self.stats.technical_ignored += 1
                continue

            # Trouver le numéro de ligne réel pour cette chaîne
            actual_line_num = ctx.find_line_for_string(original_text)

            # Trouver le contenu de la ligne réelle pour line_content
            actual_line_content = combined  # Par défaut
            for ln, lc in ctx.lines_with_numbers:
                if ln == actual_line_num:
                    actual_line_content = lc.strip()
                    break

            entry = self._create_entry(
                original_text, actual_line_content, rel_path, file_name,
                actual_line_num, pattern_name, is_concat=False
            )

            if entry:
                extracted_any = True

        return extracted_any

    def _process_single_line(self, line: str, line_stripped: str,
                             rel_path: str, file_name: str,
                             line_num: int, matched_pattern: str) -> bool:
        """
        Traite une ligne simple (non multi-ligne).

        Returns:
            True si des chaînes ont été extraites
        """
        # TRAITEMENT SPÉCIAL: Lignes avec LOC existants - extraire UNIQUEMENT les chaînes non localisées
        has_existing_loc = 'LOC "$$$/' in line

        if has_existing_loc:
            # Extraire les clés LOC existantes pour référence
            self._extract_existing_loc(line, rel_path, file_name, line_num)

            # Puis chercher les chaînes NON localisées
            non_localized = self._find_non_localized_strings(line)

            if not non_localized:
                return False
        else:
            # Pas de LOC existant - extraire tout
            non_localized = extract_all_string_literals(line)

        if not non_localized:
            return False

        # Vérifier le contexte technique (pour filtrer les headers HTTP etc.)
        is_tech_context = is_in_technical_context(line)

        # Déterminer si c'est une ligne concaténée
        is_concat = is_line_concatenated(line) and len(non_localized) > 1

        # Filtrer les chaînes valides
        valid_members = []
        for original_text, start_pos, end_pos in non_localized:
            if len(original_text.strip()) < self.min_length:
                continue

            if is_technical_string(original_text, line if is_tech_context else None):
                self.stats.technical_ignored += 1
                continue

            valid_members.append((original_text, start_pos, end_pos))

        if not valid_members:
            return False

        # Mettre à jour les stats de concaténation
        if is_concat and len(valid_members) > 1:
            self.stats.concatenated_lines += 1
            self.stats.concat_members_total += len(valid_members)

        # Traiter chaque membre valide
        for member_idx, (original_text, start_pos, end_pos) in enumerate(valid_members):
            entry = self._create_entry(
                original_text, line_stripped, rel_path, file_name,
                line_num, matched_pattern,
                is_concat=(is_concat and len(valid_members) > 1),
                member_idx=member_idx,
                total_members=len(valid_members)
            )

        return len(valid_members) > 0

    def _create_entry(self, original_text: str, line_content: str,
                      rel_path: str, file_name: str, line_num: int,
                      pattern_name: str, is_concat: bool = False,
                      member_idx: int = 0, total_members: int = 1) -> Optional[ExtractedString]:
        """
        Crée une entrée ExtractedString pour une chaîne.

        Returns:
            L'entrée créée ou None si déjà vue/invalide
        """
        # ÉTAPE 1: Extraire les espaces de formatage
        clean_text, leading, trailing = extract_spacing(original_text)

        if len(clean_text) < self.min_length:
            return None

        # ÉTAPE 2: Extraire les suffixes communs
        base_text, suffix = extract_suffix(clean_text)

        if suffix:
            trailing = 0

        # Vérifier si ce TEXTE DE BASE a déjà une clé assignée
        text_key = base_text

        if text_key in self.text_to_key:
            loc_key = self.text_to_key[text_key]
        else:
            loc_key = generate_loc_key(base_text, file_name, self.prefix, self.used_keys)
            if not loc_key:
                return None

            self.used_keys.add(loc_key)
            self.text_to_key[text_key] = loc_key

        # Générer le code de remplacement
        replacement = generate_replacement_code(
            pattern_name, loc_key, leading, trailing, suffix, original_text, base_text
        )

        # Créer l'entrée
        entry = ExtractedString(
            original_text=original_text,
            clean_text=clean_text,
            base_text=base_text,
            file_path=rel_path,
            file_name=file_name,
            line_num=line_num,
            line_content=line_content,
            pattern_name=pattern_name,
            suggested_key=loc_key,
            leading_spaces=leading,
            trailing_spaces=trailing,
            suffix=suffix,
            replacement_code=replacement,
            match_context=line_content[:100],
            is_concat_member=is_concat,
            concat_member_index=member_idx,
            concat_total_members=total_members
        )

        self.extracted.append(entry)
        self.stats.total_strings += 1

        # Stats par pattern
        self.stats.patterns_found[pattern_name] = \
            self.stats.patterns_found.get(pattern_name, 0) + 1

        # Stats espaces et suffixes
        if entry.has_spacing():
            self.stats.strings_with_spacing += 1
        if entry.has_suffix():
            self.stats.strings_with_suffix += 1

        # Déduplication
        dedup_key = f"{rel_path}:{line_num}:{clean_text}"
        if dedup_key not in self.seen_texts:
            self.seen_texts[dedup_key] = entry

            # Métadonnées d'espaces et suffixes
            if entry.has_spacing() or entry.has_suffix() or entry.is_concat_member:
                self.spacing_metadata[loc_key] = {
                    'original_text': original_text,
                    'clean_text': clean_text,
                    'base_text': base_text,
                    'leading_spaces': leading,
                    'trailing_spaces': trailing,
                    'suffix': suffix,
                    'is_concat_member': entry.is_concat_member,
                    'concat_index': member_idx,
                    'file': rel_path,
                    'line': line_num,
                    'pattern': pattern_name
                }

        return entry

    def _extract_existing_loc(self, line: str, rel_path: str, file_name: str, line_num: int):
        """Extrait les clés LOC existantes d'une ligne déjà localisée."""
        loc_pattern = re.compile(r'LOC\s*["\'](\$\$\$/[^=]+)=([^"\']+)["\']')

        for match in loc_pattern.finditer(line):
            existing_key = match.group(1)
            existing_value = match.group(2)

            # Ignorer les clés techniques (headers HTTP, identifiants, etc.)
            is_technical_key = any(
                pattern.search(existing_key) for pattern in IGNORE_LOC_KEY_PATTERNS
            )
            if is_technical_key:
                self.stats.technical_ignored += 1
                continue

            # Ignorer les valeurs techniques
            if existing_value in IGNORE_LOC_VALUES:
                self.stats.technical_ignored += 1
                continue

            entry = ExtractedString(
                original_text=existing_value,
                clean_text=existing_value,
                base_text=existing_value,
                file_path=rel_path,
                file_name=file_name,
                line_num=line_num,
                line_content=line,
                pattern_name="existing_loc",
                suggested_key=existing_key,
                leading_spaces=0,
                trailing_spaces=0,
                suffix="",
                replacement_code="",
                match_context=f'LOC "{existing_key}={existing_value}"',
                is_concat_member=False,
                concat_member_index=0,
                concat_total_members=1
            )

            self.extracted.append(entry)
            self.used_keys.add(existing_key)
            self.text_to_key[existing_value] = existing_key
            self.stats.total_strings += 1
            self.stats.patterns_found["existing_loc"] = \
                self.stats.patterns_found.get("existing_loc", 0) + 1

    def extract_all(self):
        """Extrait les chaînes de tous les fichiers Lua."""
        lua_files = list(Path(self.plugin_path).rglob('*.lua'))

        for lua_file in sorted(lua_files):
            if lua_file.name in self.exclude_files:
                continue
            self.extract_from_file(str(lua_file))

        self.stats.unique_strings = len(self.used_keys)

    def print_summary(self):
        """Affiche le résumé dans la console."""
        print("\n" + "=" * 80)
        print("RÉSUMÉ DE L'EXTRACTION")
        print("=" * 80)
        print(f"Fichiers analysés          : {self.stats.files_processed}")
        print(f"Fichiers avec chaînes      : {self.stats.files_with_strings}")
        print(f"Total chaînes trouvées     : {self.stats.total_strings}")
        print(f"Clés uniques               : {self.stats.unique_strings}")
        print(f"Lignes de log ignorées     : {self.stats.log_lines_ignored}")
        print(f"Chaînes techniques ignorées: {self.stats.technical_ignored}")
        print(f"Chaînes avec espaces       : {self.stats.strings_with_spacing}")
        print(f"Chaînes avec suffixes      : {self.stats.strings_with_suffix}")
        print(f"Lignes concaténées         : {self.stats.concatenated_lines}")
        print(f"Membres de concaténation   : {self.stats.concat_members_total}")
        print("=" * 80)
