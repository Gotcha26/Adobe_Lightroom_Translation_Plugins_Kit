#!/usr/bin/env python3
"""
Nom du fichier : check_ui.py

Description :
Détecte les chaînes non traduites dans l'interface console (print, input, prompts, erreurs).
Les chaînes dans les fichiers générés (f.write) sont gérées par check_reports.py.

Usage:
    python i18n/check_ui.py
    python i18n/check_ui.py --file tools/translator/compare_langs.py
    python i18n/check_ui.py --verbose
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Set
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

IGNORE_DIRS = {"__pycache__", ".git", "venv", ".venv", "locale"}

# Patterns à ignorer (chaînes techniques, pas des messages utilisateur)
IGNORE_PATTERNS = [
    # Extensions et chemins
    r'^\.',  # .txt, .po, etc.
    r'^/',   # /path/to/
    r'\\',   # chemins Windows

    # Formats techniques
    r'^\d+$',  # nombres seuls
    r'^[A-Z_]+$',  # CONSTANTES
    r'^[a-z_]+$',  # identifiants_techniques

    # Caractères spéciaux seuls
    r'^[\s\-=_*#]+$',  # séparateurs
    r'^[,;:.!?]+$',

    # Formats
    r'%[sd]',  # old-style formatting
    r'\{[^}]*\}',  # {format}
]

# Longueur minimale pour considérer une chaîne
MIN_STRING_LENGTH = 3

# Mots-clés indiquant des messages utilisateur (UI console uniquement)
# Note : 'write' et 'append' sont gérés par check_reports.py
USER_MESSAGE_INDICATORS = [
    'print', 'input', 'error', 'warning', 'info', 'message',
    'prompt', 'label', 'title', 'description', 'help',
]


@dataclass
class UntranslatedString:
    """Représente une chaîne potentiellement non traduite."""
    filepath: str
    line: int
    text: str
    context: str  # contexte (fonction parent, etc.)
    confidence: str  # HIGH, MEDIUM, LOW


class StringExtractor(ast.NodeVisitor):
    """Visiteur AST pour extraire les chaînes littérales (UI console uniquement)."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.strings: List[UntranslatedString] = []
        self.current_function = None
        self.source_lines = []
        self._file_write_vars: Set[str] = set()  # variables fichier (with open() as f)
        self._in_file_write = False  # True quand on est dans un f.write()

        # Charger le contenu source
        with open(filepath, 'r', encoding='utf-8') as f:
            self.source_lines = f.readlines()

    def visit_FunctionDef(self, node):
        """Suivre la fonction courante."""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_With(self, node):
        """Détecter les blocs with open(...) as f: pour exclure f.write()."""
        old_vars = self._file_write_vars.copy()
        for item in node.items:
            # Détecter: with open(...) as <var>
            if (isinstance(item.context_expr, ast.Call) and
                isinstance(item.context_expr.func, ast.Name) and
                item.context_expr.func.id == 'open' and
                item.optional_vars and isinstance(item.optional_vars, ast.Name)):
                self._file_write_vars.add(item.optional_vars.id)
        self.generic_visit(node)
        self._file_write_vars = old_vars

    def visit_Str(self, node):
        """Visiter les chaînes (Python < 3.8)."""
        self._process_string(node, node.s)
        self.generic_visit(node)

    def visit_Constant(self, node):
        """Visiter les constantes (Python >= 3.8)."""
        if isinstance(node.value, str):
            self._process_string(node, node.value)
        self.generic_visit(node)

    def _process_string(self, node, text: str):
        """Traite une chaîne découverte."""
        # Ignorer les chaînes vides ou trop courtes
        if not text or len(text.strip()) < MIN_STRING_LENGTH:
            return

        # Ignorer les chaînes dans un contexte f.write() (géré par check_reports.py)
        if self._is_in_file_write_context(node):
            return

        # Ignorer les chaînes purement techniques
        if self._is_technical_string(text):
            return

        # Vérifier si déjà enrobée de _()
        if self._is_already_translated(node):
            return

        # Déterminer la confiance (HIGH/MEDIUM/LOW)
        confidence = self._calculate_confidence(node, text)

        # Extraire le contexte
        context = self._get_context(node)

        # Ajouter à la liste
        self.strings.append(UntranslatedString(
            filepath=str(self.filepath.relative_to(PROJECT_ROOT)),
            line=node.lineno,
            text=text[:100],  # Limiter à 100 chars pour l'affichage
            context=context,
            confidence=confidence
        ))

    def _is_technical_string(self, text: str) -> bool:
        """Détermine si une chaîne est technique (pas un message utilisateur)."""
        import re

        # Ignorer patterns techniques
        for pattern in IGNORE_PATTERNS:
            if re.search(pattern, text):
                return True

        # Ignorer si contient seulement des caractères spéciaux
        if not any(c.isalnum() for c in text):
            return True

        return False

    def _is_already_translated(self, node) -> bool:
        """Vérifie si la chaîne est déjà dans _()."""
        # Remonter dans l'AST pour voir si le parent est un Call à _()
        # Note: cette approche simple peut manquer certains cas
        # mais évite les faux positifs évidents

        # On regarde si la ligne contient _( avant la chaîne
        line_content = self.source_lines[node.lineno - 1] if node.lineno <= len(self.source_lines) else ""
        col = node.col_offset

        # Chercher _( avant la position de la chaîne
        before = line_content[:col]
        if '_(' in before and before.rstrip().endswith('_('):
            return True

        return False

    def _is_in_file_write_context(self, node) -> bool:
        """Vérifie si la chaîne est dans un appel f.write() d'un fichier ouvert."""
        if not self._file_write_vars:
            return False
        # Vérifier si la ligne contient <var>.write( où <var> est une variable fichier
        if node.lineno <= len(self.source_lines):
            line = self.source_lines[node.lineno - 1]
            for var in self._file_write_vars:
                if f'{var}.write(' in line or f'{var}.writelines(' in line:
                    return True
        return False

    def _calculate_confidence(self, node, text: str) -> str:
        """Calcule le niveau de confiance que c'est un message utilisateur."""
        # HIGH: dans print(), input() avec texte long
        # MEDIUM: dans assignments, f-strings
        # LOW: autres cas

        parent_context = self._get_context(node).lower()

        # HIGH confidence
        if any(indicator in parent_context for indicator in USER_MESSAGE_INDICATORS):
            if len(text) > 15:  # Message substantiel
                return "HIGH"
            return "MEDIUM"

        # MEDIUM confidence
        if len(text) > 30:  # Texte long = probablement un message
            return "MEDIUM"

        # LOW confidence
        return "LOW"

    def _get_context(self, node) -> str:
        """Extrait le contexte (appel de fonction parent, etc.)."""
        # Récupérer la ligne de code
        if node.lineno <= len(self.source_lines):
            line = self.source_lines[node.lineno - 1].strip()
            # Extraire le début (avant la chaîne)
            return line[:50]

        return self.current_function or "unknown"


def scan_file(filepath: Path) -> List[UntranslatedString]:
    """Scanne un fichier Python pour les chaînes non traduites."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        extractor = StringExtractor(filepath)
        extractor.visit(tree)
        return extractor.strings

    except SyntaxError as e:
        print(f"{c.WARNING}[!] Erreur de syntaxe dans {filepath}: {e}{c.RESET}")
        return []
    except Exception as e:
        print(f"{c.WARNING}[!] Erreur lors du scan de {filepath}: {e}{c.RESET}")
        return []


def scan_directory(directory: Path) -> Dict[str, List[UntranslatedString]]:
    """Scanne un répertoire récursivement."""
    results = {}

    for root, dirs, files in os.walk(directory):
        # Filtrer les dossiers à ignorer
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

    parser = argparse.ArgumentParser(description="Trouve les chaînes non traduites")
    parser.add_argument('--file', help="Fichier spécifique à analyser")
    parser.add_argument('--verbose', '-v', action='store_true', help="Affichage détaillé")
    parser.add_argument('--confidence', choices=['HIGH', 'MEDIUM', 'LOW'],
                       help="Filtrer par niveau de confiance minimum")
    args = parser.parse_args()

    print()
    print(c.box_header("RECHERCHE DE CHAÎNES NON TRADUITES"))
    print()

    # Scanner
    all_strings: Dict[str, List[UntranslatedString]] = {}

    if args.file:
        # Fichier spécifique
        filepath = PROJECT_ROOT / args.file
        if not filepath.exists():
            print(f"{c.ERROR}[ERROR] Fichier non trouvé: {filepath}{c.RESET}")
            return 1

        strings = scan_file(filepath)
        if strings:
            all_strings[args.file] = strings
    else:
        # Scanner tous les répertoires
        print(f"{c.INFO}[i] Scan des répertoires...{c.RESET}")
        for directory in SCAN_DIRS:
            if directory.exists():
                results = scan_directory(directory)
                all_strings.update(results)

    # Filtrer par confiance si demandé
    confidence_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    min_confidence = confidence_order.get(args.confidence, 0)

    # Statistiques
    total_files = len(all_strings)
    total_strings = sum(len(strings) for strings in all_strings.values())

    if min_confidence > 0:
        # Filtrer
        filtered = {}
        for filepath, strings in all_strings.items():
            filtered_strings = [s for s in strings if confidence_order[s.confidence] >= min_confidence]
            if filtered_strings:
                filtered[filepath] = filtered_strings
        all_strings = filtered
        total_strings = sum(len(strings) for strings in all_strings.values())

    print(f"     Fichiers analysés: {c.VALUE}{total_files}{c.RESET}")
    print(f"     Chaînes trouvées:  {c.VALUE}{total_strings}{c.RESET}")

    if total_strings == 0:
        print()
        print(f"{c.SUCCESS}[OK] Aucune chaîne non traduite détectée!{c.RESET}")
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
                print(f"  {color}[{s.confidence}]{c.RESET} L{s.line:4d}: {text_preview}")
                if s.context:
                    print(f"         {c.DIM}Context: {s.context}{c.RESET}")
    else:
        print()
        print(f"{c.DIM}Utilisez --verbose pour voir les détails{c.RESET}")

    # Recommandations
    print()
    print(c.separator())
    print(f"{c.TITLE}RECOMMANDATIONS{c.RESET}")
    print(c.separator())
    print()
    print(f"1. Examiner les chaînes {c.ERROR}HIGH{c.RESET} en priorité:")
    print(f"   python i18n/check_ui.py --confidence HIGH --verbose")
    print()
    print(f"2. Pour chaque chaîne, enrober de _():")
    print(f"   {c.DIM}Avant:{c.RESET} print(\"Message\")")
    print(f"   {c.DIM}Après:{c.RESET} print(_(\"Message\"))")
    print()
    print(f"3. Puis synchroniser:")
    print(f"   python i18n/sync_translations.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
