#!/usr/bin/env python3
"""
common/colors.py

Module pour gérer les couleurs dans le terminal.
Compatible Windows (Git Bash, PowerShell, CMD) et Linux/Mac.

Usage:
    from common.colors import Colors, c

    print(c.OK + "Succès!" + c.RESET)
    print(c.error("Erreur!"))
    print(c.success("OK!"))
    print(c.warning("Attention!"))
    print(c.info("Info"))
    print(c.header("=== TITRE ==="))

Auteur : Claude (Anthropic) pour Julien Moreau
Date : 2026-01-30
Version : 1.0
"""

import os
import sys


def supports_color() -> bool:
    """
    Détecte si le terminal supporte les couleurs ANSI.

    Returns:
        True si les couleurs sont supportées
    """
    # Forcer les couleurs si FORCE_COLOR est defini
    if os.environ.get('FORCE_COLOR'):
        return True

    # Desactiver si NO_COLOR est defini
    if os.environ.get('NO_COLOR'):
        return False

    # Verifier si stdout est un terminal
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False

    # Windows: activer le support ANSI si possible
    if os.name == 'nt':
        # Git Bash, MSYS, Cygwin supportent les couleurs
        if os.environ.get('TERM'):
            return True
        # Windows Terminal et PowerShell Core supportent les couleurs
        if os.environ.get('WT_SESSION') or os.environ.get('ConEmuANSI') == 'ON':
            return True
        # Essayer d'activer le mode ANSI sur Windows 10+
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            pass
        return False

    # Unix/Linux/Mac: supporter par defaut
    return True


class Colors:
    """
    Classe pour les codes couleur ANSI.

    Attributs:
        RESET: Réinitialise les couleurs
        BOLD: Texte en gras
        DIM: Texte atténué

        OK, SUCCESS, GREEN: Vert pour les succès
        ERROR, RED: Rouge pour les erreurs
        WARNING, YELLOW: Jaune pour les avertissements
        INFO, BLUE: Bleu pour les informations
        CYAN: Cyan pour les valeurs/chemins
        MAGENTA: Magenta pour les titres
        WHITE: Blanc
    """

    def __init__(self, force_color: bool = None):
        """
        Initialise les couleurs.

        Args:
            force_color: Forcer l'activation (True) ou désactivation (False) des couleurs.
                        None = auto-détection.
        """
        if force_color is not None:
            self._enabled = force_color
        else:
            self._enabled = supports_color()

        self._init_colors()

    def _init_colors(self):
        """Initialise les codes couleurs."""
        if self._enabled:
            # Codes de base
            self.RESET = '\033[0m'
            self.BOLD = '\033[1m'
            self.DIM = '\033[2m'
            self.UNDERLINE = '\033[4m'

            # Couleurs de base
            self.BLACK = '\033[30m'
            self.RED = '\033[31m'
            self.GREEN = '\033[32m'
            self.YELLOW = '\033[33m'
            self.BLUE = '\033[34m'
            self.MAGENTA = '\033[35m'
            self.CYAN = '\033[36m'
            self.WHITE = '\033[37m'

            # Couleurs claires
            self.LIGHT_RED = '\033[91m'
            self.LIGHT_GREEN = '\033[92m'
            self.LIGHT_YELLOW = '\033[93m'
            self.LIGHT_BLUE = '\033[94m'
            self.LIGHT_MAGENTA = '\033[95m'
            self.LIGHT_CYAN = '\033[96m'

            # Alias semantiques
            self.OK = self.GREEN
            self.SUCCESS = self.GREEN
            self.ERROR = self.RED
            self.WARNING = self.YELLOW
            self.INFO = self.BLUE
            self.HEADER = self.BOLD + self.CYAN
            self.TITLE = self.BOLD + self.WHITE
            self.VALUE = self.CYAN
            self.KEY = self.WHITE
            self.PROMPT = self.YELLOW
        else:
            # Mode sans couleur
            self.RESET = ''
            self.BOLD = ''
            self.DIM = ''
            self.UNDERLINE = ''
            self.BLACK = ''
            self.RED = ''
            self.GREEN = ''
            self.YELLOW = ''
            self.BLUE = ''
            self.MAGENTA = ''
            self.CYAN = ''
            self.WHITE = ''
            self.LIGHT_RED = ''
            self.LIGHT_GREEN = ''
            self.LIGHT_YELLOW = ''
            self.LIGHT_BLUE = ''
            self.LIGHT_MAGENTA = ''
            self.LIGHT_CYAN = ''
            self.OK = ''
            self.SUCCESS = ''
            self.ERROR = ''
            self.WARNING = ''
            self.INFO = ''
            self.HEADER = ''
            self.TITLE = ''
            self.VALUE = ''
            self.KEY = ''
            self.PROMPT = ''

    @property
    def enabled(self) -> bool:
        """Retourne True si les couleurs sont activées."""
        return self._enabled

    def enable(self):
        """Active les couleurs."""
        self._enabled = True
        self._init_colors()

    def disable(self):
        """Désactive les couleurs."""
        self._enabled = False
        self._init_colors()

    # Méthodes pour formater du texte
    def success(self, text: str) -> str:
        """Formate un texte de succès (vert)."""
        return f"{self.OK}[OK]{self.RESET} {text}"

    def error(self, text: str) -> str:
        """Formate un texte d'erreur (rouge)."""
        return f"{self.ERROR}[ERREUR]{self.RESET} {text}"

    def warning(self, text: str) -> str:
        """Formate un texte d'avertissement (jaune)."""
        return f"{self.WARNING}[ATTENTION]{self.RESET} {text}"

    def info(self, text: str) -> str:
        """Formate un texte d'information (bleu)."""
        return f"{self.INFO}[INFO]{self.RESET} {text}"

    def header(self, text: str) -> str:
        """Formate un titre/header (cyan gras)."""
        return f"{self.HEADER}{text}{self.RESET}"

    def title(self, text: str) -> str:
        """Formate un titre (blanc gras)."""
        return f"{self.TITLE}{text}{self.RESET}"

    def value(self, text: str) -> str:
        """Formate une valeur (cyan)."""
        return f"{self.VALUE}{text}{self.RESET}"

    def key(self, text: str) -> str:
        """Formate une cle (blanc)."""
        return f"{self.KEY}{text}{self.RESET}"

    def prompt(self, text: str) -> str:
        """Formate un prompt (jaune)."""
        return f"{self.PROMPT}{text}{self.RESET}"

    def ok_marker(self) -> str:
        """Retourne un marqueur OK vert."""
        return f"{self.OK}[OK]{self.RESET}"

    def error_marker(self) -> str:
        """Retourne un marqueur ERREUR rouge."""
        return f"{self.ERROR}[ERREUR]{self.RESET}"

    def warn_marker(self) -> str:
        """Retourne un marqueur ATTENTION jaune."""
        return f"{self.WARNING}[ATTENTION]{self.RESET}"

    def menu_option(self, number: str, text: str) -> str:
        """Formate une option de menu."""
        return f"  {self.YELLOW}{number}{self.RESET}. {text}"

    def config_line(self, key: str, value: str, key_width: int = 25) -> str:
        """Formate une ligne de configuration."""
        return f"  {self.KEY}{key:<{key_width}}{self.RESET}: {self.VALUE}{value}{self.RESET}"

    def separator(self, char: str = "-", width: int = 60) -> str:
        """Retourne une ligne de séparation."""
        return f"{self.DIM}{char * width}{self.RESET}"

    def box_header(self, text: str, width: int = 70) -> str:
        """Formate un header de boîte."""
        line = "=" * width
        return f"{self.HEADER}{line}\n  {text.center(width - 4)}\n{line}{self.RESET}"


# Instance globale pour import facile
c = Colors()
