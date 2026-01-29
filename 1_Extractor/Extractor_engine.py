#!/usr/bin/env python3
"""
Extractor_engine.py

Moteur principal d'extraction des chaînes localisables.
Analyse les fichiers Lua et extrait les chaînes UI.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set

from Extractor_config import LOG_LINE_REGEX, UI_CONTEXT_PATTERNS, ALL_STRINGS_PATTERN
from Extractor_models import ExtractedString, ExtractionStats
from Extractor_utils import (
    extract_spacing, extract_all_string_literals, is_line_concatenated,
    extract_suffix, is_technical_string, generate_loc_key, generate_replacement_code
)


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
    
    def extract_from_file(self, file_path: str):
        """Extrait les chaînes d'un fichier Lua, y compris les chaînes concaténées."""
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
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Ignorer les commentaires Lua
            if line_stripped.startswith('--'):
                continue
            
            # TRAITEMENT SPÉCIAL: Lignes déjà localisées avec LOC "$$$/Key=Value"
            if 'LOC "$$$/' in line or "LOC '$$$/'" in line:
                self._extract_existing_loc(line, rel_path, file_name, line_num)
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
            
            # Extraire TOUTES les chaînes littérales de la ligne
            all_strings = extract_all_string_literals(line)
            
            if not all_strings:
                continue
            
            # Déterminer si c'est une ligne concaténée
            is_concat = is_line_concatenated(line) and len(all_strings) > 1
            
            # Filtrer les chaînes valides
            valid_members = []
            for original_text, start_pos, end_pos in all_strings:
                if len(original_text.strip()) < self.min_length:
                    continue
                
                if is_technical_string(original_text):
                    self.stats.technical_ignored += 1
                    continue
                
                valid_members.append((original_text, start_pos, end_pos))
            
            if not valid_members:
                continue
            
            # Mettre à jour les stats de concaténation
            if is_concat and len(valid_members) > 1:
                self.stats.concatenated_lines += 1
                self.stats.concat_members_total += len(valid_members)
            
            # Traiter chaque membre valide
            for member_idx, (original_text, start_pos, end_pos) in enumerate(valid_members):
                # ÉTAPE 1: Extraire les espaces de formatage
                clean_text, leading, trailing = extract_spacing(original_text)
                
                if len(clean_text) < self.min_length:
                    continue
                
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
                        continue
                    
                    self.used_keys.add(loc_key)
                    self.text_to_key[text_key] = loc_key
                
                # Générer le code de remplacement
                replacement = generate_replacement_code(
                    matched_pattern, loc_key, leading, trailing, suffix, original_text, base_text
                )
                
                # Créer l'entrée
                entry = ExtractedString(
                    original_text=original_text,
                    clean_text=clean_text,
                    base_text=base_text,
                    file_path=rel_path,
                    file_name=file_name,
                    line_num=line_num,
                    line_content=line_stripped,
                    pattern_name=matched_pattern,
                    suggested_key=loc_key,
                    leading_spaces=leading,
                    trailing_spaces=trailing,
                    suffix=suffix,
                    replacement_code=replacement,
                    match_context=line_stripped[:100],
                    is_concat_member=is_concat and len(valid_members) > 1,
                    concat_member_index=member_idx,
                    concat_total_members=len(valid_members) if is_concat else 1
                )
                
                self.extracted.append(entry)
                self.stats.total_strings += 1
                
                # Stats par pattern
                self.stats.patterns_found[matched_pattern] = \
                    self.stats.patterns_found.get(matched_pattern, 0) + 1
                
                # Stats espaces et suffixes
                if entry.has_spacing():
                    self.stats.strings_with_spacing += 1
                if entry.has_suffix():
                    self.stats.strings_with_suffix += 1
                
                # Déduplication
                dedup_key = f"{rel_path}:{line_num}:{clean_text}"
                if dedup_key not in self.seen_texts:
                    self.seen_texts[dedup_key] = entry
                    file_has_strings = True
                    
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
                            'pattern': matched_pattern
                        }
        
        if file_has_strings:
            self.stats.files_with_strings += 1
    
    def _extract_existing_loc(self, line: str, rel_path: str, file_name: str, line_num: int):
        """Extrait les clés LOC existantes d'une ligne déjà localisée."""
        loc_pattern = re.compile(r'LOC\s*["\'](\$\$\$/[^=]+)=([^"\']+)["\']')
        
        for match in loc_pattern.finditer(line):
            existing_key = match.group(1)
            existing_value = match.group(2)
            
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