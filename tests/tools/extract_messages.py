#!/usr/bin/env python3
"""
Nom du fichier : extract_messages.py

Dépendances : Aucune (bibliothèque standard : ast)

Description :
Extracteur de messages traduisibles de secours, sans GNU gettext. Parcourt les
fichiers Python indiqués (fichiers ou dossiers, récursivement) et collecte les
littéraux de chaîne passés en premier argument à _() et aux deux premiers
arguments de ngettext(). Utilisé par tests/test_i18n_catalog.py pour vérifier
que chaque msgid du code existe dans le catalogue, sans dépendre de xgettext en CI.

Usage CLI :
    python tests/tools/extract_messages.py LocalizationToolKit.py core tools

Date : 2026-11-08
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import ast
import os
import sys


def _iter_python_files(paths):
    """Énumère les fichiers .py des chemins donnés (fichiers ou dossiers)."""
    for path in paths:
        if os.path.isfile(path):
            if path.endswith(".py"):
                yield path
            continue
        for root, dirs, files in os.walk(path):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for name in sorted(files):
                if name.endswith(".py"):
                    yield os.path.join(root, name)


def _literal(node):
    """Renvoie la valeur d'un littéral str (concaténations implicites incluses), sinon None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _call_name(node):
    """Nom simple de la fonction appelée (_ / ngettext), sinon None."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    return None


def extract_from_source(source: str, filename: str = "<string>") -> set:
    """Collecte les msgids d'un code source Python."""
    messages = set()
    tree = ast.parse(source, filename=filename)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node)
        if name == "_" and node.args:
            value = _literal(node.args[0])
            if value:
                messages.add(value)
        elif name == "ngettext" and len(node.args) >= 2:
            for arg in node.args[:2]:
                value = _literal(arg)
                if value:
                    messages.add(value)
    return messages


def extract_messages(paths) -> set:
    """Collecte les msgids de tous les fichiers Python des chemins donnés."""
    messages = set()
    for file_path in _iter_python_files(paths):
        with open(file_path, encoding="utf-8") as f:
            messages |= extract_from_source(f.read(), file_path)
    return messages


def main(argv=None) -> int:
    """Affiche les msgids trouvés, un par ligne (forme repr)."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:] if argv is None else argv
    for message in sorted(extract_messages(args or ["."])):
        print(repr(message))
    return 0


if __name__ == "__main__":
    sys.exit(main())
