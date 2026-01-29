#!/usr/bin/env python3
"""
Extractor_output.py

Génération des fichiers de sortie: PluginStrings.txt, JSON, rapports, etc.
"""

import os
import json
from datetime import datetime
from typing import Dict, List
from collections import defaultdict

from Extractor_models import ExtractedString, ExtractionStats


class OutputGenerator:
    """Gère la génération de tous les fichiers de sortie."""
    
    def __init__(self, plugin_path: str, prefix: str):
        self.plugin_path = plugin_path
        self.prefix = prefix
    
    def generate_plugin_strings(self, extracted: List[ExtractedString], output_path: str, lang: str = "en"):
        """Génère le fichier PluginStrings.txt avec les clés uniques (fichier de référence)."""
        # Construire un dictionnaire clé → entry (première occurrence)
        unique_keys: Dict[str, ExtractedString] = {}
        
        for entry in extracted:
            if entry.suggested_key not in unique_keys:
                unique_keys[entry.suggested_key] = entry
        
        # Grouper par catégorie
        by_category: Dict[str, List[ExtractedString]] = defaultdict(list)
        for entry in unique_keys.values():
            parts = entry.suggested_key.split('/')
            category = parts[2] if len(parts) >= 3 else 'General'
            by_category[category].append(entry)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"-- =============================================================================\n")
            f.write(f"-- Plugin Localization - {lang.upper()}\n")
            f.write(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- Total keys: {len(unique_keys)}\n")
            f.write(f"-- =============================================================================\n\n")
            
            for category in sorted(by_category.keys()):
                entries = by_category[category]
                f.write(f"-- {category}\n")
                
                for entry in sorted(entries, key=lambda e: e.suggested_key):
                    # Fichier propre : uniquement clé=valeur, sans émojis ni métadonnées
                    f.write(f'"{entry.suggested_key}={entry.base_text}"\n')
                
                f.write("\n")
        
        print(f"✓ PluginStrings généré: {output_path} ({len(unique_keys)} clés uniques)")
    
    def generate_spacing_metadata(self, spacing_metadata: Dict[str, Dict], text_to_key: Dict[str, str], 
                                   output_path: str):
        """Génère le fichier spacing_metadata.json (rétrocompatibilité)."""
        data = {
            'generated': datetime.now().isoformat(),
            'total_keys_with_spacing': len(spacing_metadata),
            'metadata': spacing_metadata,
            'text_to_key': text_to_key
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Spacing metadata: {output_path} ({len(spacing_metadata)} clés)")
    
    def generate_replacements_json(self, extracted: List[ExtractedString], output_path: str, 
                                   text_to_key: Dict[str, str]):
        """
        Génère le fichier JSON de remplacement avec avant/après pour chaque ligne.
        
        Structure:
        {
            "generated": "...",
            "plugin_path": "...",
            "stats": { ... },
            "files": {
                "fichier.lua": {
                    "replacements": [
                        {
                            "line_num": 74,
                            "original_line": "title = \"Publishing \" .. nPhotos ...",
                            "replaced_line": "title = LOC \"$$$/...\" .. \" \" .. nPhotos ...",
                            "members": [ ... ]
                        }
                    ]
                }
            }
        }
        """
        # Grouper par fichier puis par ligne
        # EXCLURE les entrées "existing_loc" qui ne doivent pas être modifiées
        by_file: Dict[str, Dict[int, List[ExtractedString]]] = defaultdict(lambda: defaultdict(list))
        for entry in extracted:
            # Ne pas inclure les clés LOC existantes dans les remplacements
            if entry.pattern_name == "existing_loc":
                continue
            by_file[entry.file_path][entry.line_num].append(entry)
        
        # Construire la structure JSON
        files_data = {}
        
        for file_path in sorted(by_file.keys()):
            lines_data = by_file[file_path]
            replacements = []
            
            for line_num in sorted(lines_data.keys()):
                entries = lines_data[line_num]
                if not entries:
                    continue
                
                # Ligne originale
                original_line = entries[0].line_content
                
                # Construire la ligne remplacée
                replaced_line = self._build_replaced_line(original_line, entries)
                
                # Détails des membres
                members = []
                for entry in entries:
                    member_info = {
                        'original_text': entry.original_text,
                        'base_text': entry.base_text,
                        'loc_key': entry.suggested_key,
                        'leading_spaces': entry.leading_spaces,
                        'trailing_spaces': entry.trailing_spaces,
                        'suffix': entry.suffix,
                        'replacement': self._build_loc_call(entry)
                    }
                    members.append(member_info)
                
                replacement_entry = {
                    'line_num': line_num,
                    'pattern': entries[0].pattern_name,
                    'is_concatenated': entries[0].is_concat_member and len(entries) > 1,
                    'original_line': original_line,
                    'replaced_line': replaced_line,
                    'members': members
                }
                replacements.append(replacement_entry)
            
            files_data[file_path] = {
                'total_replacements': len(replacements),
                'replacements': replacements
            }
        
        # Structure finale
        output_data = {
            'generated': datetime.now().isoformat(),
            'plugin_path': self.plugin_path,
            'prefix': self.prefix,
            'stats': {
                'total_strings': len(extracted),
                'unique_keys': len(set(e.suggested_key for e in extracted if e.pattern_name != "existing_loc")),
                'concatenated_lines': sum(1 for e in extracted if e.is_concat_member),
            },
            'text_to_key': text_to_key,
            'files': files_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        total_replacements = sum(f['total_replacements'] for f in files_data.values())
        print(f"✓ Replacements JSON: {output_path} ({total_replacements} lignes à modifier)")
    
    def _build_loc_call(self, entry: ExtractedString) -> str:
        """
        Construit l'appel LOC pour une entrée.
        
        Format ZString du SDK Lightroom: LOC "$$$/Key=Default Value"
        La valeur par défaut EST OBLIGATOIRE sinon Lightroom affiche la clé brute.
        """
        parts = []
        
        # Espaces en début
        if entry.leading_spaces > 0:
            parts.append('"' + ' ' * entry.leading_spaces + '" .. ')
        
        # Appel LOC avec valeur par défaut (base_text)
        parts.append(f'LOC "{entry.suggested_key}={entry.base_text}"')
        
        # Suffixe ou espaces en fin
        if entry.suffix:
            parts.append(f' .. "{entry.suffix}"')
        elif entry.trailing_spaces > 0:
            parts.append(' .. "' + ' ' * entry.trailing_spaces + '"')
        
        return ''.join(parts)
    
    def _build_replaced_line(self, original_line: str, entries: List[ExtractedString]) -> str:
        """
        Construit la ligne avec les remplacements appliqués.
        
        Remplace chaque chaîne originale par son appel LOC correspondant.
        """
        result = original_line
        
        # Trier par position décroissante pour ne pas décaler les indices
        sorted_entries = sorted(entries, key=lambda e: original_line.find(f'"{e.original_text}"'), reverse=True)
        
        for entry in sorted_entries:
            search_str = f'"{entry.original_text}"'
            replace_str = self._build_loc_call(entry)
            
            # Remplacer une seule occurrence (la première trouvée depuis la fin)
            pos = result.rfind(search_str)
            if pos != -1:
                result = result[:pos] + replace_str + result[pos + len(search_str):]
        
        return result
