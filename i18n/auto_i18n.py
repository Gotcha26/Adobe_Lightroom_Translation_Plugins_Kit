#!/usr/bin/env python3
"""
Script avancé pour automatiquement enrober les chaînes de _() en utilisant l'AST.

Gère les cas complexes :
- f-strings
- Chaînes multilignes
- Chaînes dans les appels de fonctions
- Préservation du formatage

Usage:
    python i18n/auto_i18n.py --scan
    python i18n/auto_i18n.py --file tools/translator/compare_langs.py --preview
    python i18n/auto_i18n.py --file tools/translator/compare_langs.py --apply
    python i18n/auto_i18n.py --all --apply
"""

import ast
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.colors import Colors

c = Colors()

PROJECT_ROOT = Path(__file__).parent.parent
SCAN_DIRS = [
    PROJECT_ROOT / "tools",
    PROJECT_ROOT / "core",
]

# Fichiers à exclure du traitement i18n
EXCLUDED_FILES = [
    "core/colors.py",
    "core/config.py",
]

def should_process_file(filepath: Path) -> bool:
    """Vérifie si un fichier doit être traité."""
    relative = filepath.relative_to(PROJECT_ROOT)
    relative_str = str(relative).replace("\\", "/")

    for excluded in EXCLUDED_FILES:
        if relative_str == excluded or relative_str.endswith(excluded):
            return False
    return True


def is_user_facing_string(text: str, parent_context: str = "") -> bool:
    """Détermine si une chaîne doit être traduite."""

    # Trop courte
    if len(text.strip()) < 3:
        return False

    # Patterns techniques à ignorer
    technical_patterns = [
        r'^[A-Z_]+$',  # CONSTANTES
        r'^[a-z_]+$',  # identifiants_techniques
        r'^\.',        # .txt, .json
        r'^/',         # /path/
        r'\\\\',       # chemins Windows
        r'^[A-Z]:\\\\', # chemins Windows absolus C:\\...
        r'^\d+$',      # nombres seuls
        r'^[\s\-=_*#:;,.!?]+$',  # séparateurs seuls
        r'^[=\-*#]{2,}$',  # séparateurs répétés
        r'^utf-8$',    # encodings
        r'^LC_MESSAGES$',
        r'messages\.po',
        r'messages\.pot',
        r'messages\.mo',
        r'TranslatedStrings_',
        r'^%[YmdHMS\-:% ]+$',  # formats de date strftime
        r'^\$\$\$/',            # clés SDK Lightroom $$$/Key=Value
        r'^<plugin>',           # templates chemins <plugin>/...
        r'^<temp_dir>',         # templates chemins <temp_dir>/...
        r'^\{DOMAIN\}',         # {DOMAIN}.mo, {DOMAIN}.po
        r'^\.lrplugin$',        # extension seule
        r'^\./\w+\.',           # chemins relatifs ./xxx.ext
        r'^\.\.\./\{',          # templates .../{var}
        r'^  python\s',         # commandes shell
        r'^python\s+\w+',       # commandes python xxx
        r'^\(auto\)$',          # marqueur (auto)
        r're\.escape',          # regex Python
        r'\[\^[^\]]*\]',        # character classes regex [^=]+
    ]

    for pattern in technical_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    # Si contient seulement des caractères spéciaux
    if not any(c.isalnum() for c in text):
        return False

    # Ignorer si c'est juste un séparateur répété
    if text.strip() and all(c == text.strip()[0] for c in text.strip()):
        return False

    # Mots-clés indiquant des messages utilisateur (UI console uniquement)
    # Note: 'write' est exclu — les f.write() dans les fichiers sont gérés par check_reports.py
    user_indicators = ['print', 'input', 'error', 'warning', 'message', 'prompt']
    if any(ind in parent_context.lower() for ind in user_indicators):
        return True

    # Si texte long et contient des espaces = probablement un message
    if len(text) > 20 and ' ' in text:
        return True

    return False


def should_translate_node(node, source_lines: List[str]) -> bool:
    """Vérifie si un nœud AST doit être traduit."""

    # Récupérer le texte
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        text = node.value
    else:
        return False

    # Récupérer le contexte
    line_num = node.lineno - 1
    if line_num < len(source_lines):
        line_context = source_lines[line_num]
    else:
        line_context = ""

    # Vérifier si déjà traduit
    if '_(' in line_context[:node.col_offset]:
        return False

    # Vérifier si c'est une chaîne utilisateur
    return is_user_facing_string(text, line_context)


def wrap_with_underscore(original_code: str, string_start: int, string_end: int) -> str:
    """Enrobe une chaîne de _() dans le code source."""

    # Insérer _( avant la chaîne
    before = original_code[:string_start]
    string_part = original_code[string_start:string_end]
    after = original_code[string_end:]

    # Vérifier qu'on n'est pas déjà dans un _()
    if before.rstrip().endswith('_('):
        return original_code

    return f"{before}_({string_part}){after}"


def extract_static_parts_from_fstring(line: str) -> List[Tuple[str, int, int]]:
    """
    Extrait les parties statiques d'une f-string pour les traduire.

    Exemple: f"Texte {var} suite" -> [("Texte ", start, end), (" suite", start, end)]
    """
    parts = []

    # Trouver les f-strings
    fstring_pattern = r'f"([^"]*)"'
    for match in re.finditer(fstring_pattern, line):
        fstring_content = match.group(1)

        # Extraire les parties statiques (hors {})
        static_parts = re.split(r'\{[^}]+\}', fstring_content)

        for part in static_parts:
            if part and len(part.strip()) >= 3:
                parts.append((part, match.start(), match.end()))

    return parts


def transform_fstring_to_translatable(line: str) -> str:
    """
    Transforme une f-string en format traduisible.

    Avant: f"CLÉS PRÉSENTES SEULEMENT DANS {lang1_upper} ({len(result['only_in_lang1'])})"
    Après: _("CLÉS PRÉSENTES SEULEMENT DANS {lang1_upper} ({count})").format(lang1_upper=lang1_upper, count=len(result['only_in_lang1']))
    """

    # Pattern pour f-strings
    fstring_pattern = r'f"([^"]+)"'

    def replace_fstring(match):
        content = match.group(1)

        # Si pas de {} dedans, c'est une chaîne simple
        if '{' not in content:
            if is_user_facing_string(content, line):
                return f'_("{content}")'
            return match.group(0)

        # Extraire les expressions {} (y compris formatage)
        # Pattern: {expression:format}
        expressions = re.findall(r'\{([^}]+)\}', content)

        # Si pas de parties statiques significatives, ignorer
        static_parts = re.split(r'\{[^}]+\}', content)
        has_significant_text = any(
            len(part.strip()) >= 3 and is_user_facing_string(part.strip(), line)
            for part in static_parts
        )

        if not has_significant_text:
            return match.group(0)

        # Créer des noms de variables simples
        template = content
        format_args = []

        for i, expr in enumerate(expressions):
            # Séparer expression et format (ex: stats['total']:4d)
            format_spec = ''

            if ':' in expr:
                # Détecter si : fait partie d'un formatage ou d'un appel de fonction
                # Formatage : :4d, :<20s, :6.2f (caractères après :)
                # Appel fonction : datetime.now().strftime('%H:%M') (guillemets après :)

                colon_pos = expr.rfind(':')  # Dernier :
                after_colon = expr[colon_pos+1:].strip()

                # Si après : il y a des guillemets ou des parenthèses, c'est un appel de fonction
                if "'" in after_colon or '"' in after_colon or '(' in after_colon:
                    return match.group(0)

                # Sinon c'est du formatage
                expr_part = expr[:colon_pos]
                format_spec = ':' + after_colon
            else:
                expr_part = expr

            # Nettoyer l'expression
            expr_clean = expr_part.strip()

            # Si l'expression contient des guillemets imbriqués (hors crochets), ignorer cette f-string
            # Autoriser stats['key'] mais pas function('text')
            temp_clean = re.sub(r'\[[^\]]*\]', '', expr_clean)  # Retirer le contenu des []
            if "'" in temp_clean or '"' in temp_clean:
                return match.group(0)

            # Créer un nom de variable simple
            if '[' in expr_clean or '(' in expr_clean or '.' in expr_clean:
                var_name = f"var{i}"
            else:
                # Utiliser le nom de la variable directement (nettoyer les formatages)
                var_name = expr_clean.replace('<', '').replace('>', '')

            # Remplacer dans le template (garder le format)
            template = template.replace('{' + expr + '}', '{' + var_name + format_spec + '}', 1)
            format_args.append(f"{var_name}={expr_clean}")

        # Générer la version traduisible
        if format_args:
            return f'_("{template}").format({", ".join(format_args)})'
        else:
            return f'_("{template}")'

    return re.sub(fstring_pattern, replace_fstring, line)


def process_file_smart(filepath: Path, apply: bool = False) -> Tuple[int, List[dict]]:
    """
    Traite un fichier de manière intelligente (gère les f-strings).

    Returns:
        (nombre_modifications, liste_changements)
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modifications = []
    modified_lines = []

    # Détecter les blocs "with open(...) as f:" pour ignorer les f.write()
    in_write_block = False
    write_block_indent = 0

    for i, line in enumerate(lines, 1):
        original_line = line
        modified_line = line
        modified = False

        stripped = line.strip()

        # Tracking des blocs with open() — les .write() dedans ne sont pas de l'UI
        current_indent = len(line) - len(line.lstrip())
        if re.search(r'with\s+open\s*\(', line):
            in_write_block = True
            write_block_indent = current_indent
        elif in_write_block and current_indent <= write_block_indent and stripped:
            in_write_block = False

        # Ignorer les lignes .write() dans un bloc fichier
        if in_write_block and '.write(' in line:
            modified_lines.append(line)
            continue

        # Ignorer les lignes .write() même hors contexte détecté (sécurité)
        if re.search(r'\.\s*write\s*\(', stripped):
            modified_lines.append(line)
            continue

        # Ignorer les commentaires et docstrings
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            modified_lines.append(line)
            continue

        # Ignorer si déjà traduit
        if '_(' in line and '"' in line:
            quote_pos = line.find('"')
            underscore_pos = line.find('_(')
            if underscore_pos < quote_pos and underscore_pos != -1:
                modified_lines.append(line)
                continue

        # Ignorer les lignes avec séparateurs répétés (ex: "=" * 80)
        if re.search(r'["\'][=\-*#]{1,3}["\'] \* \d+', line):
            modified_lines.append(line)
            continue

        # Ignorer les lignes avec strftime (formatage de date)
        if 'strftime(' in line:
            modified_lines.append(line)
            continue

        # Ignorer les noms de fichiers/dossiers avec timestamp ou variables
        if re.search(r'f["\'][a-z_]+_\{', line):  # ex: f"compare_langs_{timestamp}"
            modified_lines.append(line)
            continue

        # Ignorer les lignes json.dump / json.load
        if 'json.dump' in line or 'json.load' in line:
            modified_lines.append(line)
            continue

        # Traiter les f-strings
        if 'f"' in line or "f'" in line:
            try:
                modified_line = transform_fstring_to_translatable(line)
                if modified_line != line and '{' in modified_line:
                    # Vérifier que la transformation est valide (pas de guillemets cassés)
                    if modified_line.count('"') % 2 == 0 and modified_line.count("'") % 2 == 0:
                        modified = True
                    else:
                        modified_line = line  # Annuler si transformation invalide
            except Exception:
                modified_line = line  # En cas d'erreur, garder l'original
        else:
            # Traiter les chaînes simples
            # Pattern: "texte" (au moins 3 caractères, pas déjà dans _())

            # Chaînes doubles uniquement dans certains contextes
            if '"' in line and not line.strip().startswith('"""'):
                # Trouver toutes les chaînes
                for match in re.finditer(r'"([^"]{3,})"', line):
                    text = match.group(1)

                    # Vérifier si c'est une chaîne utilisateur
                    if is_user_facing_string(text, line):
                        # Vérifier qu'elle n'est pas déjà dans _()
                        before_quote = line[:match.start()]
                        if not before_quote.rstrip().endswith('_('):
                            modified_line = modified_line.replace(f'"{text}"', f'_("{text}")', 1)
                            modified = True

        if modified:
            modifications.append({
                'line': i,
                'before': original_line.rstrip(),
                'after': modified_line.rstrip()
            })

        modified_lines.append(modified_line)

    if apply and modifications:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(modified_lines)

    return len(modifications), modifications


def main():
    """Point d'entrée."""
    import argparse

    parser = argparse.ArgumentParser(description="Automatise l'ajout de _() pour i18n")
    parser.add_argument('--scan', action='store_true', help="Scanner tous les fichiers")
    parser.add_argument('--file', help="Fichier spécifique à traiter")
    parser.add_argument('--all', action='store_true', help="Traiter tous les fichiers")
    parser.add_argument('--preview', action='store_true', help="Aperçu des modifications")
    parser.add_argument('--apply', action='store_true', help="Appliquer les modifications")
    args = parser.parse_args()

    if not any([args.scan, args.file, args.all]):
        parser.print_help()
        return 1

    print()
    print(c.box_header("AUTO I18N - ENROBAGE AUTOMATIQUE"))
    print()

    # Mode scan
    if args.scan:
        print(f"{c.INFO}[i] Scan des fichiers nécessitant i18n...{c.RESET}")
        print()

        # Importer l'outil de scan
        from check_ui import scan_directory

        all_strings = {}
        for directory in SCAN_DIRS:
            if directory.exists():
                results = scan_directory(directory)
                all_strings.update(results)

        # Afficher résumé
        total_files = len(all_strings)
        total_strings = sum(len(strings) for strings in all_strings.values())

        print(f"{c.KEY}Fichiers avec chaînes non traduites:{c.RESET} {c.VALUE}{total_files}{c.RESET}")
        print(f"{c.KEY}Total de chaînes:{c.RESET} {c.VALUE}{total_strings}{c.RESET}")
        print()

        # Top 10
        sorted_files = sorted(all_strings.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        print(f"{c.TITLE}Top 10 fichiers:{c.RESET}")
        for filepath, strings in sorted_files:
            high_count = sum(1 for s in strings if s.confidence == "HIGH")
            print(f"  {filepath}: {c.VALUE}{len(strings)}{c.RESET} ({c.ERROR}{high_count} HIGH{c.RESET})")

        print()
        print(f"{c.DIM}Utilisez --file <path> --preview pour voir les modifications proposées{c.RESET}")
        return 0

    # Mode fichier unique
    if args.file:
        filepath = PROJECT_ROOT / args.file
        if not filepath.exists():
            print(f"{c.ERROR}[ERROR] Fichier introuvable: {filepath}{c.RESET}")
            return 1

        mode = "APPLICATION" if args.apply else "APERÇU"
        print(f"{c.KEY}Fichier:{c.RESET} {args.file}")
        print(f"{c.KEY}Mode:{c.RESET} {mode}")
        print()

        count, changes = process_file_smart(filepath, apply=args.apply)

        if count == 0:
            print(f"{c.SUCCESS}[OK] Aucune modification nécessaire{c.RESET}")
            return 0

        print(f"{c.INFO}[i] {count} modification(s) détectée(s){c.RESET}")
        print()

        # Afficher les modifications
        if args.preview or args.apply:
            for change in changes[:20]:  # Limiter à 20
                print(f"{c.CYAN}Ligne {change['line']}:{c.RESET}")
                print(f"  {c.DIM}Avant:{c.RESET} {change['before']}")
                print(f"  {c.GREEN}Après:{c.RESET} {change['after']}")
                print()

            if len(changes) > 20:
                print(f"{c.DIM}... et {len(changes) - 20} autres modifications{c.RESET}")
                print()

        if args.apply:
            print(f"{c.SUCCESS}[OK] Modifications appliquées!{c.RESET}")
            print()
            print(f"{c.KEY}Prochaines étapes:{c.RESET}")
            print(f"  1. Vérifier: git diff {args.file}")
            print(f"  2. Ajuster manuellement si nécessaire")
            print(f"  3. Synchroniser: python i18n/sync_translations.py")
        else:
            print(f"{c.DIM}Pour appliquer, ajoutez --apply{c.RESET}")

        return 0

    # Mode tous les fichiers
    if args.all:
        if not args.apply:
            print(f"{c.WARNING}[!] Mode --all nécessite --apply pour confirmer{c.RESET}")
            print(f"{c.DIM}Utilisez: python i18n/auto_i18n.py --all --apply{c.RESET}")
            return 1

        print(f"{c.WARNING}[!] Traitement de TOUS les fichiers...{c.RESET}")
        print()

        total_modifications = 0
        files_modified = 0

        for directory in SCAN_DIRS:
            if not directory.exists():
                continue

            for py_file in directory.rglob("*.py"):
                if "__pycache__" in str(py_file):
                    continue
                if not should_process_file(py_file):
                    continue

                count, _ = process_file_smart(py_file, apply=True)
                if count > 0:
                    files_modified += 1
                    total_modifications += count
                    print(f"  {c.GREEN}[OK]{c.RESET} {py_file.relative_to(PROJECT_ROOT)}: {count} modification(s)")

        print()
        print(f"{c.SUCCESS}[OK] Traitement terminé!{c.RESET}")
        print(f"  Fichiers modifiés: {files_modified}")
        print(f"  Total modifications: {total_modifications}")
        print()
        print(f"{c.KEY}Prochaines étapes:{c.RESET}")
        print(f"  1. Vérifier: git diff")
        print(f"  2. Synchroniser: python i18n/sync_translations.py")

        return 0


if __name__ == "__main__":
    sys.exit(main())
