"""
Nom du fichier : flip_anim.py

Dépendances : Aucune

Description :
Animation de style panneau aéroport avec flip progressif des caractères. Affiche un texte
avec un effet de révélation progressif et une extinction finale en style "airport flip clock".
Supporte les couleurs ANSI et les fonds personnalisés.

Usage CLI :
    python flip_anim.py

    Exemples d'exécution directe (à partir de ce fichier):
    - Éditer les paramètres TEXT, DURATION, FADE_DURATION, etc. en haut du fichier
    - Lancer le script pour voir l'animation

Date : 2026-02-04
GitHub : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit
Auteur : Julien Moreau https://julien-moreau.fr contact@julien-moreau.fr

"""

import time
import random
import sys

# ============================================================================
# PARAMÈTRES À ÉDITER
# ============================================================================
TEXT = "GOTCHA Solutions"
DURATION = 4.0              # Durée animation principale (secondes)
FADE_DURATION = 1.0         # Durée extinction symboles (secondes)
FINAL_PAUSE = 2.0           # Pause sur frame finale (secondes)
LINE_WIDTH = 80             # Largeur totale
LINE_SYMBOL = "▁"           # Symbole de part et d'autre du texte
TEXT_COLOR = "yellow"       # yellow, red, green, blue, magenta, cyan, white
BG_COLOR = "default"        # default, black, red, green, yellow, blue, magenta, cyan, white
FRAMERATE = 25              # FPS (8-15 pour ralentir)
# ============================================================================

# Codes ANSI
RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"

# Couleurs disponibles (foreground)
COLORS = {
    "yellow": "\033[93m",
    "red": "\033[91m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
}

# Couleurs de fond disponibles
BG_COLORS = {
    "black": "\033[40m",
    "red": "\033[41m",
    "green": "\033[42m",
    "yellow": "\033[43m",
    "blue": "\033[44m",
    "magenta": "\033[45m",
    "cyan": "\033[46m",
    "white": "\033[47m",
}

def airport_display_intro(text="GOTCHA Solutions", duration=5.0, line_width=80, color="yellow", bg_color="default", fade_duration=1.0, framerate=20, line_symbol="_", final_pause=1.0):
    """
    Animation style panneau aéroport avec flip progressif des caractères.

    Args:
        text: Texte à afficher (défaut: "GOTCHA Solutions")
        duration: Durée de l'animation principale en secondes (défaut: 5)
        line_width: Largeur totale de la ligne (défaut: 80)
        color: Couleur du texte - yellow, red, green, blue, magenta, cyan, white (défaut: yellow)
        bg_color: Couleur de fond - default, black, red, green, yellow, blue, magenta, cyan, white (défaut: default)
        fade_duration: Durée de l'extinction des symboles en secondes (défaut: 1.0)
        framerate: FPS (défaut: 20). Utiliser 10-15 pour ralentir.
        line_symbol: Symbole pour la ligne de part et d'autre du texte (défaut: "_")
        final_pause: Durée de la pause sur la frame finale avant clear en secondes (défaut: 1.0)
    """
    color_code = COLORS.get(color.lower(), COLORS["yellow"])
    bg_code = BG_COLORS.get(bg_color.lower(), "") if bg_color.lower() != "default" else ""
    frame_delay = 1.0 / framerate
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    symbols = "_#*-+="
    text_length = len(text)
    padding = (line_width - text_length) // 2
    left_line = line_symbol * padding
    right_line = line_symbol * (line_width - padding - text_length)
    
    start_time = time.time()
    revealed = [False] * text_length
    
    # Générer les lignes statiques de remplissage (5 au-dessus et en-dessous)
    def generate_messy_line():
        return "".join(random.choice(symbols + " ") for _ in range(line_width))
    
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        progress = elapsed / duration
        
        # Nombre de caractères à révéler basé sur le temps écoulé
        chars_to_reveal = int(text_length * progress)
        
        # Marquer les caractères comme révélés progressivement
        for i in range(chars_to_reveal):
            revealed[i] = True
        
        # Animation des underscores (flipping aléatoire)
        left_display = "".join(random.choice("_ ") for _ in range(len(left_line)))
        right_display = "".join(random.choice("_ ") for _ in range(len(right_line)))
        
        # Construire la ligne d'affichage avec texte formaté
        text_display = ""
        for i, char in enumerate(text):
            if revealed[i]:
                text_display += f"{color_code}{BOLD}{ITALIC}{char}{RESET}"
            else:
                text_display += f"{color_code}{BOLD}{ITALIC}{random.choice(chars)}{RESET}"
        
        display = left_display + text_display + right_display
        
        # Effacer et afficher les 11 lignes (5 au-dessus + 1 texte + 5 au-dessous)
        sys.stdout.write("\033[2J\033[H")  # Nettoyer l'écran
        for _ in range(5):
            sys.stdout.write(f"{bg_code}{generate_messy_line()}\033[0m\n")
        sys.stdout.write(f"{bg_code}{display}\033[0m\n")
        for _ in range(5):
            sys.stdout.write(f"{bg_code}{generate_messy_line()}\033[0m\n")
        sys.stdout.flush()
        
        time.sleep(frame_delay)
    
    # Phase finale : extinction progressive
    fade_duration = fade_duration
    fade_start = time.time()
    
    # Générer les positions aléatoires à éteindre
    positions_to_fade = list(range(line_width))
    random.shuffle(positions_to_fade)
    
    while time.time() - fade_start < fade_duration:
        fade_progress = (time.time() - fade_start) / fade_duration
        num_to_clear = int(len(positions_to_fade) * fade_progress)
        positions_cleared = set(positions_to_fade[:num_to_clear])
        
        # Construire le texte final
        text_final = f"{color_code}{BOLD}{ITALIC}{text}{RESET}"
        left_final = left_line
        right_final = right_line
        
        sys.stdout.write("\033[2J\033[H")  # Nettoyer l'écran
        
        # 5 lignes du haut avec extinction progressive
        for _ in range(5):
            line = ""
            for pos in range(line_width):
                if pos in positions_cleared:
                    line += " "
                else:
                    line += random.choice(symbols + " ")
            sys.stdout.write(f"{bg_code}{line}\033[0m\n")
        
        # Ligne du texte
        sys.stdout.write(f"{bg_code}{left_final}{text_final}{right_final}\033[0m\n")
        
        # 5 lignes du bas avec extinction progressive
        for _ in range(5):
            line = ""
            for pos in range(line_width):
                if pos in positions_cleared:
                    line += " "
                else:
                    line += random.choice(symbols + " ")
            sys.stdout.write(f"{bg_code}{line}\033[0m\n")
        
        sys.stdout.flush()
        time.sleep(frame_delay)
    
    # Frame finale statique
    left_final = left_line
    right_final = right_line
    text_final = f"{color_code}{BOLD}{ITALIC}{text}{RESET}"
    empty_line = " " * line_width

    sys.stdout.write("\033[2J\033[H")  # Nettoyer l'écran
    for _ in range(5):
        sys.stdout.write(f"{empty_line}\n")
    sys.stdout.write(f"{left_final}{text_final}{right_final}\n")
    for _ in range(5):
        sys.stdout.write(f"{empty_line}\n")
    sys.stdout.flush()
    
    # Pause sur la frame finale
    time.sleep(final_pause)
    
    # Clear l'écran
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


if __name__ == "__main__":
    airport_display_intro(
        text=TEXT,
        duration=DURATION,
        line_width=LINE_WIDTH,
        color=TEXT_COLOR,
        bg_color=BG_COLOR,
        fade_duration=FADE_DURATION,
        framerate=FRAMERATE,
        line_symbol=LINE_SYMBOL,
        final_pause=FINAL_PAUSE
    )