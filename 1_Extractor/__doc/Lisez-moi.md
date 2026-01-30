# Extractor - Documentation technique

**Version 5.1 | Janvier 2026**

## Vue d'ensemble

Extractor est le premier outil de la chaîne de localisation. Son rôle est d'analyser les fichiers Lua d'un plugin Lightroom et d'extraire automatiquement toutes les chaînes de texte qui devraient être localisées.

## Architecture du projet

```
1_Extractor/
├── Extractor_main.py         ← Point d'entrée, orchestration
├── Extractor_config.py       ← Patterns regex et constantes
├── Extractor_models.py       ← Classes de données (StringMember, ExtractedString, etc.)
├── Extractor_utils.py        ← Fonctions utilitaires (espaces, clés, filtres)
├── Extractor_engine.py       ← Moteur d'extraction principal
├── Extractor_output.py       ← Génération des fichiers de sortie
├── Extractor_report.py       ← Génération des rapports
├── Extractor_menu.py         ← Interface interactive
└── __doc/
    └── README.md             ← Ce fichier
```
```
┌─────────────────────────────────────────────────────────────┐
│                    Extractor_main.py                        │
│                    (orchestrateur)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│ LocalizableString│ │Output        │ │Report            │
│Extractor         │ │Generator     │ │Generator         │
│(engine.py)       │ │(output.py)   │ │(report.py)       │
└────────┬─────────┘ └──────┬───────┘ └──────┬───────────┘
         │                  │                │
         ├─ Utilise:        ├─ Utilise:      └─ Utilise:
         │  • config.py     │  • models.py      • models.py
         │  • models.py     │  • utils.py       • output.py
         │  • utils.py      │
         │
```

L'architecture est modulaire pour faciliter la maintenance et l'évolution. Chaque module a une responsabilité claire.

## Fonctionnement détaillé

### Phase 1 : Analyse des fichiers

```
Plugin Lightroom (.lrplugin)
    │
    ├── Scan récursif des fichiers .lua
    │   │
    │   ├── Lecture ligne par ligne
    │   │
    │   └── Détection des patterns
    │       │
    │       ├── Chaînes UI (title = "Submit")
    │       ├── Concaténations (a .. "text" .. b)
    │       └── Contextes UI (bind_to_object, f:static_text, etc.)
    │
    └── Filtrage intelligent
        │
        ├── Ignorer les clés LOC existantes
        ├── Ignorer les logs (logInfo, logError)
        ├── Ignorer les valeurs techniques
        └── Ignorer les chaînes trop courtes
```

### Phase 2 : Extraction et métadonnées

Pour chaque chaîne détectée :

```
"  Hello World  :  "
    │
    ├── Texte de base : "Hello World"
    ├── Espaces avant : 2
    ├── Espaces après : 2
    ├── Suffixe : " : "
    │
    └── Génération clé LOC
        │
        ├── Normalisation (alphanumériques + underscores)
        ├── Camel case (HelloWorld)
        ├── Ajout contexte fichier (MyDialog_HelloWorld)
        └── Unicité (HelloWorld_2 si collision)
```

Toutes ces métadonnées sont conservées pour que l'Applicator puisse reconstruire exactement la chaîne originale.

### Phase 3 : Génération des fichiers

#### TranslatedStrings_en.txt

Format SDK Lightroom, utilisable directement dans le plugin :

```
-- =============================================================================
-- Plugin Localization - EN
-- Generated: 2026-01-30 15:00:00
-- Total keys: 124
-- =============================================================================

-- -----------------------------------------------------------------------------
-- IMPORTANT NOTES FOR TRANSLATORS:
-- -----------------------------------------------------------------------------
-- 1. DO NOT translate the following patterns (keep them exactly as-is):
--    - %s, %d, %f, %i, %u, %x, %X, %o, %c, %e, %E, %g, %G (format specifiers)
--    - %1, %2, %3... (numbered placeholders)
--    - \n (newline character)
--    - \t (tab character)
--    - \" (escaped quote)
--    - \\ (escaped backslash)
--    - ... (ellipsis used as placeholder)
--    - Technical terms in UPPERCASE (API, URL, HTTP, JSON, etc.)
--
-- 2. PRESERVE spaces around text exactly as they appear:
--    - Leading spaces (before text) are used for layout/alignment
--    - Trailing spaces (after text) are used for concatenation
--    - Example: "  Hello  " must keep both leading and trailing spaces
--
-- 3. Keep the same punctuation style (colons, periods, etc.)
-- -----------------------------------------------------------------------------

"$$$/Piwigo/Submit=Submit"
"$$$/Piwigo/Cancel=Cancel"
"$$$/Piwigo/Dialog_PleaseWait=Please wait..."
```

Chaque ligne contient :
- La clé LOC complète avec le préfixe
- Le symbole `=`
- La valeur par défaut en anglais (ou autre langue de base)

L'en-tête inclut des notes importantes pour les traducteurs concernant les motifs à ne pas traduire et la préservation des espaces.

#### spacing_metadata.json

Métadonnées pour reconstituer les espaces et suffixes :

```json
{
  "$$$/Piwigo/Submit": {
    "leading_spaces": 0,
    "trailing_spaces": 0,
    "suffix": ""
  },
  "$$$/Piwigo/Dialog_PleaseWait": {
    "leading_spaces": 2,
    "trailing_spaces": 3,
    "suffix": "..."
  }
}
```

#### replacements.json

Instructions précises pour l'Applicator :

```json
{
  "files": {
    "MyDialog.lua": {
      "total_replacements": 15,
      "replacements": [
        {
          "line_num": 42,
          "original_line": "title = \"Submit\",",
          "members": [
            {
              "original_text": "Submit",
              "base_text": "Submit",
              "loc_key": "$$$/Piwigo/Submit",
              "leading_spaces": 0,
              "trailing_spaces": 0,
              "suffix": ""
            }
          ]
        }
      ]
    }
  }
}
```

#### extraction_report.txt

Rapport détaillé avec statistiques :

```
================================================================================
RAPPORT D'EXTRACTION - Plugin PiwigoPublish
================================================================================

STATISTIQUES GLOBALES
--------------------------------------------------------------------------------
Fichiers analysés        : 12
Fichiers avec extractions: 8
Lignes UI détectées      : 156
Chaînes uniques          : 124
Chaînes ignorées         : 32
Clés LOC existantes      : 18

DÉTAIL PAR FICHIER
--------------------------------------------------------------------------------

MyDialog.lua
  Lignes UI : 42
  Chaînes   : 35
  Clés LOC  : 7 (déjà localisé)

  $$$/Piwigo/Submit          → "Submit"
  $$$/Piwigo/Cancel          → "Cancel"
  ...
```

## Options de configuration

### Mode interactif

Lancez simplement `Extractor_main.py` pour accéder au menu interactif :

```
==================================================
        EXTRACTOR - Configuration
==================================================

Options actuelles:
  Plugin path    : ./monPlugin.lrplugin
  Préfixe LOC    : $$$/MonPlugin
  Langue         : en
  Longueur min   : 3
  Ignorer logs   : Oui

[1] Modifier le chemin du plugin
[2] Modifier le préfixe LOC
[3] Modifier la langue
[4] Options avancées
[5] Lancer l'extraction
[0] Quitter
```

### Mode CLI

```bash
python Extractor_main.py --plugin-path ./plugin.lrplugin [OPTIONS]
```

**Options disponibles :**

| Option | Description | Défaut | Exemple |
|--------|-------------|--------|---------|
| `--plugin-path` | Chemin du plugin (OBLIGATOIRE) | - | `./monPlugin.lrplugin` |
| `--output-dir` | Répertoire de sortie personnalisé | `<plugin>/__i18n_tmp__/Extractor/` | `./output` |
| `--prefix` | Préfixe des clés LOC | `$$$/Piwigo` | `$$$/MonApp` |
| `--lang` | Code langue de base | `en` | `fr`, `de`, `es` |
| `--exclude` | Fichiers à exclure (répétable) | - | `--exclude test.lua --exclude debug.lua` |
| `--min-length` | Longueur minimale des chaînes | `3` | `5` |
| `--no-ignore-log` | Ne pas ignorer les logs | false | - |

### Exemples d'utilisation

**Extraction standard :**
```bash
python Extractor_main.py --plugin-path ./piwigoPublish.lrplugin
```

**Extraction avec préfixe personnalisé :**
```bash
python Extractor_main.py --plugin-path ./myPlugin.lrplugin --prefix $$$/MyApp
```

**Extraction avec exclusions :**
```bash
python Extractor_main.py \
  --plugin-path ./plugin.lrplugin \
  --exclude test.lua \
  --exclude deprecated.lua \
  --min-length 5
```

**Extraction en français comme langue de base :**
```bash
python Extractor_main.py \
  --plugin-path ./plugin.lrplugin \
  --lang fr \
  --prefix $$$/MonApp
```

## Patterns d'extraction

Extractor détecte automatiquement plusieurs contextes UI dans le code Lua.

### Contextes UI reconnus

```lua
-- 1. Titres et labels de widgets
f:static_text {
    title = "Hello World",      -- ✓ Extrait
}

-- 2. bind_to_object (composants liés)
f:edit_field {
    bind_to_object = propertyTable,
    value = LrBinding.keyToProp("apiKey"),
    title = "API Key:",         -- ✓ Extrait
}

-- 3. Items de menu
f:popup_menu {
    items = {
        { title = "Option 1", value = "opt1" },  -- ✓ Extrait "Option 1"
        { title = "Option 2", value = "opt2" },  -- ✓ Extrait "Option 2"
    }
}

-- 4. Concaténations de chaînes
local message = "Upload " .. count .. " photos"  -- ✓ Extrait "Upload " et " photos"

-- 5. Retours de fonction
function getTitle()
    return "My Title"           -- ✓ Extrait
end

-- 6. Chaînes dans tableaux
local messages = {
    "First message",            -- ✓ Extrait
    "Second message",           -- ✓ Extrait
}
```

### Patterns ignorés

```lua
-- Logs (si --no-ignore-log non spécifié)
logInfo("Debug message")        -- ✗ Ignoré
log:trace("Trace info")         -- ✗ Ignoré

-- Valeurs techniques
color = "red"                   -- ✗ Ignoré (valeur technique)
format = "jpg"                  -- ✗ Ignoré (format)

-- Clés LOC existantes
title = LOC "$$$/App/Title=Title"  -- ✗ Ignoré (déjà localisé)

-- Chaînes trop courtes (< min_length)
x = "OK"                        -- ✗ Ignoré si min_length > 2
```

## Gestion des espaces et suffixes

Extractor préserve intelligemment les espaces et suffixes pour garantir un rendu identique après application.

### Espaces

```lua
-- Avant
title = "  Hello World  "

-- Extraction
{
  "base_text": "Hello World",
  "leading_spaces": 2,
  "trailing_spaces": 2
}

-- Après Applicator
title = "  " .. LOC "$$$/App/HelloWorld=Hello World" .. "  "
```

### Suffixes

```lua
-- Avant
label = "Username:"

-- Extraction
{
  "base_text": "Username",
  "suffix": ":"
}

-- Après Applicator
label = LOC "$$$/App/Username=Username" .. ":"
```

### Concaténations complexes

```lua
-- Avant
message = "  Processing " .. count .. " files...  "

-- Extraction (2 membres)
[
  {
    "base_text": "Processing ",
    "leading_spaces": 2
  },
  {
    "base_text": " files",
    "suffix": "...",
    "trailing_spaces": 2
  }
]

-- Après Applicator
message = "  " .. LOC "$$$/App/Processing=Processing " .. count .. LOC "$$$/App/Files=files" .. "..." .. "  "
```

## Génération des clés LOC

Les clés LOC sont générées selon un algorithme strict pour garantir leur unicité et leur lisibilité.

### Étapes de génération

```
Texte original : "Please wait..."
    │
    ├── 1. Nettoyage (alphanumériques + espaces)
    │   └── "Please wait"
    │
    ├── 2. Camel case
    │   └── "PleaseWait"
    │
    ├── 3. Contexte fichier (nom sans extension)
    │   └── "MyDialog_PleaseWait"
    │
    ├── 4. Vérification unicité
    │   └── Si existe : "MyDialog_PleaseWait_2"
    │
    └── 5. Préfixe
        └── "$$$/Piwigo/MyDialog_PleaseWait"
```

### Exemples de génération

| Texte original | Fichier | Clé générée |
|----------------|---------|-------------|
| `"Submit"` | `Dialog.lua` | `$$$/Piwigo/Dialog_Submit` |
| `"Please wait..."` | `Upload.lua` | `$$$/Piwigo/Upload_PleaseWait` |
| `"API Key:"` | `Settings.lua` | `$$$/Piwigo/Settings_APIKey` |
| `"Photo(s)"` | `Main.lua` | `$$$/Piwigo/Main_Photos` |

### Gestion des collisions

Si une clé existe déjà, un suffixe numérique est ajouté :

```
$$$/Piwigo/Submit       → Première occurrence
$$$/Piwigo/Submit_2     → Deuxième occurrence
$$$/Piwigo/Submit_3     → Troisième occurrence
```

## Statistiques et rapports

Le rapport d'extraction fournit des informations détaillées sur le processus.

### Métriques globales

- **Fichiers analysés** : Nombre total de fichiers `.lua` scannés
- **Fichiers avec extractions** : Fichiers contenant au moins une chaîne à extraire
- **Lignes UI détectées** : Nombre de lignes contenant des patterns UI
- **Chaînes uniques** : Nombre de clés LOC générées
- **Chaînes ignorées** : Chaînes filtrées (logs, techniques, trop courtes)
- **Clés LOC existantes** : Clés déjà localisées dans le code

### Détails par fichier

Pour chaque fichier :
- Liste des clés LOC générées
- Valeur par défaut de chaque clé
- Métadonnées (espaces, suffixes)
- Contexte d'extraction

## Cas d'usage avancés

### Extraction multilingue de base

Si votre plugin est initialement en français et que vous voulez l'angliciser :

```bash
python Extractor_main.py \
  --plugin-path ./monPlugin.lrplugin \
  --lang fr \
  --prefix $$$/MonApp
```

Cela génère `TranslatedStrings_fr.txt` au lieu de `TranslatedStrings_en.txt`. Vous pouvez ensuite créer `TranslatedStrings_en.txt` en dupliquant et traduisant.

### Réexécution sur un projet partiellement localisé

Extractor détecte automatiquement les clés LOC existantes et ne les réextrait pas. Vous pouvez donc relancer l'extraction après avoir ajouté du nouveau code.

```bash
# Première extraction
python Extractor_main.py --plugin-path ./plugin.lrplugin

# ... développement, nouvelles fonctionnalités ...

# Nouvelle extraction (ne touche pas aux clés existantes)
python Extractor_main.py --plugin-path ./plugin.lrplugin
```

Les clés déjà localisées sont listées dans le rapport mais ne sont pas ajoutées au fichier de sortie.

### Extraction ciblée avec exclusions

Pour extraire uniquement certains fichiers :

```bash
python Extractor_main.py \
  --plugin-path ./plugin.lrplugin \
  --exclude test.lua \
  --exclude debug.lua \
  --exclude vendor/external.lua
```

### Personnalisation du préfixe par plugin

Chaque plugin devrait avoir son propre préfixe pour éviter les conflits :

```bash
# Plugin 1
python Extractor_main.py --plugin-path ./pluginA.lrplugin --prefix $$$/PluginA

# Plugin 2
python Extractor_main.py --plugin-path ./pluginB.lrplugin --prefix $$$/PluginB
```

## Dépannage

### Aucune chaîne extraite

**Causes possibles :**
- Le paramètre `--min-length` est trop élevé
- Les chaînes sont déjà localisées
- Les patterns ne correspondent pas à votre code
- Le chemin du plugin est incorrect

**Solutions :**
```bash
# Réduire la longueur minimale
python Extractor_main.py --plugin-path ./plugin.lrplugin --min-length 1

# Vérifier le chemin
ls ./plugin.lrplugin/*.lua

# Consulter le rapport pour comprendre ce qui a été ignoré
```

### Trop de chaînes extraites (logs inclus)

Si les messages de logs sont extraits par erreur :

```bash
# S'assurer que l'option par défaut est active
python Extractor_main.py --plugin-path ./plugin.lrplugin
```

Les logs sont ignorés par défaut. Si vous avez utilisé `--no-ignore-log`, retirez cette option.

### Clés LOC générées illisibles

Si les clés générées sont trop longues ou complexes :

1. Raccourcissez les textes originaux dans le code
2. Ou éditez manuellement le fichier `TranslatedStrings_xx.txt` après extraction
3. **Important** : Si vous changez les clés, mettez à jour aussi `replacements.json` pour Applicator

### Encodage incorrect (caractères spéciaux)

Tous les fichiers sont lus et écrits en UTF-8. Si vous voyez des caractères mal encodés :

```bash
# Vérifier l'encodage de vos fichiers .lua
file --mime-encoding *.lua

# Convertir si nécessaire (exemple Linux/Mac)
iconv -f ISO-8859-1 -t UTF-8 fichier.lua > fichier_utf8.lua
```

## FAQ technique

### Puis-je modifier les patterns de détection ?

Oui, éditez le fichier [Extractor_config.py:1](1_Extractor/Extractor_config.py#L1). Les patterns sont définis dans les constantes `UI_CONTEXT_PATTERNS`, `UI_KEYWORDS`, etc.

### Les métadonnées sont-elles vraiment nécessaires ?

Oui, elles garantissent que l'Applicator reconstruit exactement les chaînes originales avec espaces et suffixes. Sans elles, le rendu serait différent.

### Comment ajouter un nouveau type de widget à détecter ?

Ajoutez le pattern dans [Extractor_config.py:1](1_Extractor/Extractor_config.py#L1) :

```python
UI_KEYWORDS = [
    "title", "label", "value", "placeholder",
    "mon_nouveau_widget",  # Ajoutez ici
]
```

### Puis-je utiliser Extractor sur d'autres types de projets ?

Extractor est spécifique au format Lua et au SDK Lightroom. Pour d'autres langages ou frameworks, il faudrait adapter les patterns dans `Extractor_config.py` et potentiellement le moteur dans `Extractor_engine.py`.

### Les fichiers générés peuvent-ils être versionnés (Git) ?

- **TranslatedStrings_xx.txt** : Oui, à la racine du plugin
- **__i18n_tmp__/** : Non, ajoutez-le au `.gitignore` (fichiers temporaires)

## Performances

### Temps d'exécution typiques

- Petit plugin (5-10 fichiers, < 1000 lignes) : < 1 seconde
- Plugin moyen (20-30 fichiers, ~5000 lignes) : 2-3 secondes
- Gros plugin (50+ fichiers, > 10000 lignes) : 5-10 secondes

### Optimisations possibles

Extractor est déjà optimisé, mais si vous travaillez sur de très gros projets :

1. Utilisez `--exclude` pour ignorer les fichiers volumineux non pertinents
2. Augmentez `--min-length` pour filtrer plus de chaînes
3. Lancez l'extraction hors heures de développement actif

## Intégration dans un workflow automatisé

Extractor peut être intégré dans un script de build ou un pipeline CI/CD.

### Exemple de script bash

```bash
#!/bin/bash
# extract_and_check.sh

PLUGIN_PATH="./monPlugin.lrplugin"
OUTPUT_DIR="./extraction_output"

# Lancer l'extraction
python 1_Extractor/Extractor_main.py \
  --plugin-path "$PLUGIN_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --prefix '$$$/MonApp'

# Vérifier le succès
if [ $? -eq 0 ]; then
  echo "✓ Extraction réussie"
  # Copier le fichier de langue à la racine du plugin
  cp "$OUTPUT_DIR/TranslatedStrings_en.txt" "$PLUGIN_PATH/"
else
  echo "✗ Échec de l'extraction"
  exit 1
fi
```

### Exemple de script Python

```python
#!/usr/bin/env python3
import subprocess
import sys

def run_extraction(plugin_path, prefix="$$$/MyApp"):
    """Lance Extractor via subprocess."""
    cmd = [
        sys.executable,
        "1_Extractor/Extractor_main.py",
        "--plugin-path", plugin_path,
        "--prefix", prefix
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ Extraction réussie")
        print(result.stdout)
        return True
    else:
        print("✗ Échec")
        print(result.stderr)
        return False

if __name__ == "__main__":
    success = run_extraction("./monPlugin.lrplugin")
    sys.exit(0 if success else 1)
```

## Ressources complémentaires

- **SDK Lightroom** : [Adobe Developer Console](https://developer.adobe.com/console)
- **Format LOC** : `LOC "$$$/Key=Default"` (valeur par défaut obligatoire)
- **Expressions régulières Python** : [Documentation re](https://docs.python.org/3/library/re.html)
- **JSON Python** : [Documentation json](https://docs.python.org/3/library/json.html)

## Contributions

Ce projet est ouvert aux contributions. Si vous souhaitez :
- Ajouter de nouveaux patterns de détection
- Améliorer la génération des clés
- Optimiser les performances
- Corriger des bugs

N'hésitez pas à proposer vos modifications !

---

**Développé par Julien MOREAU avec l'aide de Claude (Anthropic)**

Pour toute question ou problème, consultez le README principal ou ouvrez une issue sur le dépôt GitHub.
