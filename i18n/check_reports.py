#!/usr/bin/env python3
"""
Nom du fichier : check_reports.py

Dépendances : core.colors

Description :
Détecte les chaînes non traduites dans le code de génération de fichiers.
Scope : uniquement les appels f.write() dans les blocs with open(...).
Complémentaire à check_ui.py (qui gère l'UI console).

Usage:
    python i18n/check_reports.py
    python i18n/check_reports.py --file tools/extractor/report.py
    python i18n/check_reports.py --verbose
    python i18n/check_reports.py --confidence HIGH

Date : 2026-02-06
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.colors import Colors

c = Colors()

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent

SCAN_DIRS = [
    PROJECT_ROOT / "tools",
    PROJECT_ROOT / "core",
]

IGNORE_DIRS = {"__pycache__", ".git", "venv", ".venv", "locale", "__doc__"}


def _safe_print(text: str):
    """Print compatible Windows (remplace les caractères non encodables)."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(
            sys.stdout.encoding or 'utf-8', errors='replace'))

# Longueur minimale de texte alphabétique pour considérer une chaîne
MIN_ALPHA_LENGTH = 3

# Mots français courants (indicateurs de chaîne non traduite)
FRENCH_INDICATORS = [
    'é', 'è', 'ê', 'ë', 'à', 'â', 'ù', 'û', 'ô', 'î', 'ï', 'ç', 'œ', 'æ',
]

# Patterns purement techniques à ignorer dans f.write()
TECHNICAL_PATTERNS = [
    re.compile(r'^[\s\-=_*#~`|+><!]+$'),          # séparateurs
    re.compile(r'^[\s\n\r\t]+$'),                  # whitespace
    re.compile(r'^\s*$'),                           # vide
    re.compile(r'^"[^"]*"$'),                       # clés entre guillemets
    re.compile(r'^\{.*\}$'),                        # JSON-like
    re.compile(r'^--\s*$'),                         # commentaire Lua vide
]


@dataclass
class FileOutputString:
    """Représente une chaîne non traduite dans un fichier de sortie."""
    filepath: str
    line: int
    text: str
    context: str
    confidence: str  # HIGH, MEDIUM, LOW
    suggestion: str  # correction suggérée


class FileWriteAnalyzer(ast.NodeVisitor):
    """Visiteur AST spécialisé pour détecter les chaînes non-i18n dans f.write()."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.results: List[FileOutputString] = []
        self._file_vars: Set[str] = set()  # variables fichier ouvertes
        self._in_json_dump = False
        self.source_lines = []

        with open(filepath, 'r', encoding='utf-8') as f:
            self.source_lines = f.readlines()

    def visit_With(self, node):
        """Détecter with open(...) as f: et analyser le bloc."""
        old_vars = self._file_vars.copy()
        for item in node.items:
            if (isinstance(item.context_expr, ast.Call) and
                isinstance(item.context_expr.func, ast.Name) and
                item.context_expr.func.id == 'open' and
                item.optional_vars and isinstance(item.optional_vars, ast.Name)):
                self._file_vars.add(item.optional_vars.id)
        self.generic_visit(node)
        self._file_vars = old_vars

    def visit_Call(self, node):
        """Analyser les appels de méthode, surtout .write()."""
        # Détecter json.dump() pour l'ignorer
        if (isinstance(node.func, ast.Attribute) and
            node.func.attr == 'dump' and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == 'json'):
            return  # Ignorer json.dump()

        # Détecter f.write() où f est une variable fichier
        if (isinstance(node.func, ast.Attribute) and
            node.func.attr == 'write' and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id in self._file_vars):
            # Analyser l'argument de write()
            if node.args:
                self._analyze_write_arg(node.args[0], node.lineno)

        self.generic_visit(node)

    def _analyze_write_arg(self, arg_node, line_num: int):
        """Analyse l'argument passé à f.write()."""

        # Cas 1: String littérale directe — f.write("texte")
        if isinstance(arg_node, ast.Constant) and isinstance(arg_node.value, str):
            text = arg_node.value
            if self._is_localizable_text(text):
                self._add_result(line_num, text, "string literal")

        # Cas 2: f-string — f.write(f"texte {var}")
        elif isinstance(arg_node, ast.JoinedStr):
            self._analyze_fstring(arg_node, line_num)

        # Cas 3: Concaténation — f.write("a" + "b")
        elif isinstance(arg_node, ast.BinOp) and isinstance(arg_node.op, ast.Add):
            self._analyze_write_arg(arg_node.left, line_num)
            self._analyze_write_arg(arg_node.right, line_num)

        # Cas 4: Appel de fonction — f.write(_("texte")) → OK, ignoré
        elif isinstance(arg_node, ast.Call):
            if self._is_gettext_call(arg_node):
                return  # Déjà traduit, OK
            # Appel à .format() sur un _() → OK aussi
            if (isinstance(arg_node.func, ast.Attribute) and
                arg_node.func.attr == 'format'):
                return

    def _analyze_fstring(self, node: ast.JoinedStr, line_num: int):
        """Analyse une f-string pour trouver du texte littéral localisable."""
        text_parts = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                text_parts.append(value.value)

        # Reconstituer le texte littéral de la f-string
        combined_text = ''.join(text_parts)
        if self._is_localizable_text(combined_text):
            # Récupérer la f-string complète depuis la source
            source_line = self.source_lines[line_num - 1].strip() if line_num <= len(self.source_lines) else ""
            self._add_result(line_num, combined_text, "f-string", source_line)

    def _is_gettext_call(self, node: ast.Call) -> bool:
        """Vérifie si c'est un appel à _()."""
        return isinstance(node.func, ast.Name) and node.func.id == '_'

    def _is_localizable_text(self, text: str) -> bool:
        """Détermine si un texte devrait être localisé."""
        if not text:
            return False

        # Compter les caractères alphabétiques
        alpha_chars = sum(1 for ch in text if ch.isalpha())
        if alpha_chars < MIN_ALPHA_LENGTH:
            return False

        # Exclure les patterns techniques
        stripped = text.strip()
        for pattern in TECHNICAL_PATTERNS:
            if pattern.match(stripped):
                return False

        # Exclure les lignes purement de séparateurs avec multiplication
        if stripped in ('', '\n', '\n\n', '\r\n'):
            return False

        return True

    def _calculate_confidence(self, text: str) -> str:
        """Détermine le niveau de confiance."""
        # HIGH : contient des caractères français
        if any(ch in text for ch in FRENCH_INDICATORS):
            return "HIGH"

        # HIGH : texte long avec des mots
        alpha_count = sum(1 for ch in text if ch.isalpha())
        if alpha_count > 20:
            return "HIGH"

        # MEDIUM : texte moyen
        if alpha_count > 8:
            return "MEDIUM"

        return "LOW"

    def _add_result(self, line_num: int, text: str, context: str, source_line: str = ""):
        """Ajoute un résultat détecté."""
        confidence = self._calculate_confidence(text)

        # Construire la suggestion
        display_text = text[:80] + "..." if len(text) > 80 else text
        if context == "f-string":
            suggestion = 'Convertir la f-string en _("...").format(...)'
        else:
            suggestion = f'Enrober de _() : _("{display_text}")'

        # Contexte depuis la source
        if not source_line and line_num <= len(self.source_lines):
            source_line = self.source_lines[line_num - 1].strip()

        self.results.append(FileOutputString(
            filepath=str(self.filepath.relative_to(PROJECT_ROOT)),
            line=line_num,
            text=display_text,
            context=source_line[:80] if source_line else context,
            confidence=confidence,
            suggestion=suggestion,
        ))


def scan_file(filepath: Path) -> List[FileOutputString]:
    """Scanne un fichier Python pour les chaînes non traduites dans f.write()."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        analyzer = FileWriteAnalyzer(filepath)
        analyzer.visit(tree)
        return analyzer.results

    except SyntaxError as e:
        print(f"{c.WARNING}[!] Erreur de syntaxe dans {filepath}: {e}{c.RESET}")
        return []
    except Exception as e:
        print(f"{c.WARNING}[!] Erreur lors du scan de {filepath}: {e}{c.RESET}")
        return []


def scan_directory(directory: Path) -> Dict[str, List[FileOutputString]]:
    """Scanne un répertoire récursivement."""
    results = {}

    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for filename in files:
            if not filename.endswith('.py'):
                continue

            filepath = Path(root) / filename
            strings = scan_file(filepath)

            if strings:
                rel_path = str(filepath.relative_to(PROJECT_ROOT))
                results[rel_path] = strings

    return results


def main():
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Détecte les chaînes non traduites dans les fichiers générés (f.write)")
    parser.add_argument('--file', help="Fichier spécifique à analyser")
    parser.add_argument('--verbose', '-v', action='store_true', help="Affichage détaillé")
    parser.add_argument('--confidence', choices=['HIGH', 'MEDIUM', 'LOW'],
                       help="Filtrer par niveau de confiance minimum")
    args = parser.parse_args()

    print()
    print(c.box_header("CHAÎNES NON TRADUITES DANS LES FICHIERS GÉNÉRÉS"))
    print()
    print(f"{c.DIM}Scope : f.write() dans les blocs with open(...){c.RESET}")
    print()

    # Scanner
    all_strings: Dict[str, List[FileOutputString]] = {}

    if args.file:
        filepath = PROJECT_ROOT / args.file
        if not filepath.exists():
            print(f"{c.ERROR}[ERROR] Fichier non trouvé: {filepath}{c.RESET}")
            return 1

        strings = scan_file(filepath)
        if strings:
            all_strings[args.file] = strings
    else:
        print(f"{c.INFO}[i] Scan des répertoires...{c.RESET}")
        for directory in SCAN_DIRS:
            if directory.exists():
                results = scan_directory(directory)
                all_strings.update(results)

    # Filtrer par confiance
    confidence_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    min_confidence = confidence_order.get(args.confidence, 0)

    if min_confidence > 0:
        filtered = {}
        for filepath, strings in all_strings.items():
            filtered_strings = [s for s in strings if confidence_order[s.confidence] >= min_confidence]
            if filtered_strings:
                filtered[filepath] = filtered_strings
        all_strings = filtered

    # Statistiques
    total_files = len(all_strings)
    total_strings = sum(len(strings) for strings in all_strings.values())

    print(f"     Fichiers avec résultats: {c.VALUE}{total_files}{c.RESET}")
    print(f"     Chaînes détectées:       {c.VALUE}{total_strings}{c.RESET}")

    if total_strings == 0:
        print()
        print(f"{c.SUCCESS}[OK] Aucune chaîne non traduite détectée dans les fichiers générés!{c.RESET}")
        return 0

    # Compter par confiance
    high = sum(1 for strings in all_strings.values() for s in strings if s.confidence == "HIGH")
    medium = sum(1 for strings in all_strings.values() for s in strings if s.confidence == "MEDIUM")
    low = sum(1 for strings in all_strings.values() for s in strings if s.confidence == "LOW")

    print()
    print(f"{c.KEY}Répartition par confiance:{c.RESET}")
    print(f"  {c.ERROR}HIGH{c.RESET}   (très probable): {c.VALUE}{high:4d}{c.RESET}")
    print(f"  {c.WARNING}MEDIUM{c.RESET} (probable):      {c.VALUE}{medium:4d}{c.RESET}")
    print(f"  {c.DIM}LOW{c.RESET}    (incertain):    {c.VALUE}{low:4d}{c.RESET}")

    # Affichage détaillé
    if args.verbose:
        print()
        print(c.separator())
        print(f"{c.TITLE}DÉTAILS PAR FICHIER{c.RESET}")
        print(c.separator())

        for filepath in sorted(all_strings.keys()):
            strings = all_strings[filepath]
            print()
            print(f"{c.CYAN}{filepath}{c.RESET} ({len(strings)} chaîne(s))")

            for s in sorted(strings, key=lambda x: x.line):
                color = c.ERROR if s.confidence == "HIGH" else c.WARNING if s.confidence == "MEDIUM" else c.DIM
                text_preview = s.text if len(s.text) <= 60 else s.text[:57] + "..."
                _safe_print(f"  {color}[{s.confidence}]{c.RESET} L{s.line:4d}: \"{text_preview}\"")
                if s.context:
                    _safe_print(f"         {c.DIM}Source : {s.context}{c.RESET}")
                _safe_print(f"         {c.INFO}Action : {s.suggestion}{c.RESET}")
    else:
        # Affichage compact
        print()
        for filepath in sorted(all_strings.keys()):
            strings = all_strings[filepath]
            for s in sorted(strings, key=lambda x: x.line):
                color = c.ERROR if s.confidence == "HIGH" else c.WARNING if s.confidence == "MEDIUM" else c.DIM
                text_preview = s.text if len(s.text) <= 50 else s.text[:47] + "..."
                _safe_print(f"  {color}[{s.confidence:6s}]{c.RESET} {filepath}:{s.line} \"{text_preview}\"")

    # Recommandations
    print()
    print(c.separator())
    print(f"{c.TITLE}RECOMMANDATIONS{c.RESET}")
    print(c.separator())
    print()
    print(f"1. Examiner les chaînes {c.ERROR}HIGH{c.RESET} en priorité :")
    print(f"   python i18n/check_reports.py --confidence HIGH --verbose")
    print()
    print(f"2. Pour les string literals, enrober de _() :")
    print(f"   {c.DIM}Avant:{c.RESET} f.write(\"Texte en français\")")
    print(f"   {c.DIM}Après:{c.RESET} f.write(_(\"Texte en français\"))")
    print()
    print(f"3. Pour les f-strings, convertir en _().format() :")
    print(f"   {c.DIM}Avant:{c.RESET} f.write(f\"Généré: {{date}}\")")
    print(f"   {c.DIM}Après:{c.RESET} f.write(_(\"Généré: {{var0}}\").format(var0=date))")
    print()
    print(f"4. Puis synchroniser :")
    print(f"   python i18n/sync_translations.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
