# 🎯 GUIDE - Menu Interactif Extractor

## 📊 Vue d'ensemble

À partir de la version 5.1, **Extractor_main.py** propose deux modes d'utilisation:

### 1️⃣ Mode Menu Interactif (nouveau!)
```bash
python Extractor_main.py
```
Lance un menu de configuration interactive compatible Windows/Linux/Mac

### 2️⃣ Mode CLI Classique
```bash
python Extractor_main.py --plugin-path ./plugin
```
Utilisation en ligne de commande (compatible scripts/batch)

---

## 🎮 Menu Interactif - Fonctionnalités

### ✨ Avantages
- ✓ **Facile à utiliser** - Guidance pas à pas
- ✓ **Compatible Windows** - Chemins normalisés automatiquement
- ✓ **Vérification en temps réel** - Validations immédiates
- ✓ **Modifications faciles** - Corriger sans redémarrer
- ✓ **Résumé avant exécution** - Vérifier la config

### 🏗️ Structure du Menu

```
1️⃣  Chemin du plugin         (obligatoire)
2️⃣  Répertoire de sortie     (optionnel)
3️⃣  Préfixe LOC              (par défaut: $$$/Piwigo)
4️⃣  Code langue              (par défaut: en)
5️⃣  Fichiers à exclure       (optionnel)
6️⃣  Longueur min chaînes     (par défaut: 3)
7️⃣  Ignorer logs             (par défaut: oui)
```

---

## 📖 Utilisation Pas à Pas

### Étape 1: Lancer le menu
```bash
python Extractor_main.py
```

Output:
```
================================================================================
  EXTRACTOR - Configuration Interactive
================================================================================

Configurer les paramètres d'extraction.
```

### Étape 2: Configurer le chemin du plugin
```
1️⃣  Chemin du plugin
────────────────────────────────────────────────────────────────────────────────
Exemples Windows:
  C:\Users\User\Documents\Lightroom\piwigoPublish.lrplugin
  .\piwigoPublish.lrplugin

Exemples Linux/Mac:
  /home/user/piwigoPublish.lrplugin
  ./piwigoPublish.lrplugin

Chemin du plugin (obligatoire): ./piwigoPublish.lrplugin
✓ Plugin trouvé: piwigoPublish.lrplugin
```

**Note**: Le menu normalise automatiquement les chemins (Windows/Linux)

### Étape 3: Configurer le répertoire de sortie
```
2️⃣  Répertoire de sortie
────────────────────────────────────────────────────────────────────────────────
Les fichiers seront générés dans un sous-dossier YYYYMMDD_hhmmss

Exemples Windows:
  C:\Users\User\Desktop\Extraction
  .\output

Exemples Linux/Mac:
  /home/user/extraction
  ./output

(Appuyer sur ENTRÉE pour le répertoire du script)

Répertoire de sortie (optionnel): ./output
✓ Répertoire de sortie: ./output
```

### Étape 4-7: Options restantes
Le menu guide pour les options supplémentaires (préfixe, langue, etc.)

### Étape 8: Confirmation
```
Configuration actuelle:
  1. Chemin du plugin      : piwigoPublish.lrplugin
  2. Répertoire de sortie  : ./output
  3. Préfixe LOC           : $$$/Piwigo
  4. Code langue           : en
  5. Fichiers à exclure    : (aucun)
  6. Longueur min chaînes  : 3
  7. Ignorer logs          : ✓ Oui

Options:
  1. Démarrer l'extraction
  2. Modifier les paramètres
  3. Quitter

Votre choix (1-3): 1
```

---

## 🖥️ Compatibilité Chemins

### Windows
```
✓ C:\Users\User\plugin
✓ .\plugin
✓ relative\path\to\plugin
✓ ..\..\..\plugin
```

### Linux/Mac
```
✓ /home/user/plugin
✓ ./plugin
✓ relative/path/to/plugin
✓ ~/plugin (expansion ~)
```

### Auto-normalisation
Le menu normalise automatiquement avec `os.path.normpath()`:
- `C:\Users/User\plugin` → `C:\Users\User\plugin` (Windows)
- `./plugin\subdir` → `plugin/subdir` (Linux)

---

## 📁 Organisation des Fichiers Générés

### Avant (v5.0)
```
./output/
├─ TranslatedStrings_en.txt
├─ spacing_metadata.json
├─ replacements.json
└─ extraction_report_20260127_091234.txt
```

### Après (v5.1)
```
./output/
└─ 20260127_091234/          ← Dossier avec timestamp
   ├─ TranslatedStrings_en.txt
   ├─ spacing_metadata.json
   ├─ replacements.json
   └─ extraction_report.txt
```

### Avantages
- ✓ Historique des extractions préservé
- ✓ Pas de surcharge entre exécutions
- ✓ Facile à organiser par date
- ✓ Compatible avec version control

---

## 🔄 Modifier les Paramètres

### Après configuration initiale
Vous pouvez:
1. **Démarrer** - Exécute avec la config actuelle
2. **Modifier** - Change un ou plusieurs paramètres
3. **Quitter** - Annule l'extraction

### Modifier un seul paramètre
```
Options:
  1. Modifier les paramètres

Sélectionnez le paramètre à modifier:

Configuration actuelle:
  1. Chemin du plugin      : piwigoPublish.lrplugin
  2. Répertoire de sortie  : ./output
  3. Préfixe LOC           : $$$/Piwigo
  ...

Paramètre à modifier (1-7) ou 0 pour revenir: 3
```

---

## 💻 Mode CLI (Ligne de Commande)

Pour utiliser sans menu interactif:

```bash
# Extraction simple
python Extractor_main.py --plugin-path ./plugin

# Avec options
python Extractor_main.py \
  --plugin-path ./plugin \
  --output-dir ./output \
  --prefix $$$/MyApp \
  --lang fr \
  --exclude test.lua \
  --min-length 4 \
  --no-ignore-log
```

---

## 🎯 Cas d'Usage

### Cas 1: Utilisateur Windows novice
```
python Extractor_main.py
→ Menu guidé pas à pas
→ Chemins Windows normalisés
→ Simple et intuitif
```

### Cas 2: Développeur Linux
```
python Extractor_main.py --plugin-path ./plugin --lang fr
→ CLI rapide et directe
→ Intégrable dans scripts
```

### Cas 3: Batch/Script automatisé
```bash
# batch.sh
python Extractor_main.py \
  --plugin-path "$PLUGIN_PATH" \
  --output-dir "$OUTPUT_DIR" \
  --lang "$LANG"
```

---

## ⚙️ Exemples Complets

### Windows - Menu interactif
```
python Extractor_main.py

Plugin: C:\Dev\piwigoPublish.lrplugin
Output: C:\Dev\output
Langue: fr

→ Fichiers générés dans: C:\Dev\output\20260127_091234\
```

### Linux - CLI
```bash
python Extractor_main.py \
  --plugin-path ~/lightroom/plugins/piwigo \
  --output-dir ~/extractions \
  --lang fr

→ Fichiers générés dans: ~/extractions/20260127_091234/
```

### Batch Windows
```batch
@echo off
python Extractor_main.py ^
  --plugin-path "C:\Lightroom\piwigoPublish.lrplugin" ^
  --output-dir "D:\Extractions"

pause
```

---

## 🆘 Troubleshooting

### "Répertoire introuvable"
```
❌ Répertoire introuvable: piwigoPublish.lrplugin

→ Vérifier:
  1. Chemin complet ou relatif
  2. Nom du répertoire exact
  3. Permissions d'accès
```

### "Chemin invalide"
```
❌ Entrez un chemin valide

→ Exemples corrects:
  .\plugin\piwigoPublish.lrplugin
  ../plugins/piwigo
  /home/user/plugin
```

### "Choix invalide"
```
❌ Choix invalide (1-3)

→ Entrez: 1, 2 ou 3
```

---

## 📊 Options Détaillées

### 1️⃣ Chemin du plugin
- **Obligatoire**: Oui
- **Exemples**: `./plugin`, `C:\plugin\piwigo`
- **Validation**: Répertoire doit exister

### 2️⃣ Répertoire de sortie
- **Obligatoire**: Non (défaut: répertoire du script)
- **Exemples**: `./output`, `C:\Extractions`
- **Validation**: Auto-création si nécessaire

### 3️⃣ Préfixe LOC
- **Défaut**: `$$$/Piwigo`
- **Exemples**: `$$$/MyApp`, `$$$/Plugin/Name`
- **Format**: Commence par `$$$/`

### 4️⃣ Code langue
- **Défaut**: `en` (anglais)
- **Exemples**: `fr`, `de`, `es`, `it`
- **Validé**: 2 caractères

### 5️⃣ Fichiers à exclure
- **Optionnel**: Oui
- **Format**: Séparé par virgules
- **Exemple**: `test.lua, debug.lua, JSON.lua`

### 6️⃣ Longueur min chaînes
- **Défaut**: `3`
- **Plage**: ≥ 1
- **Utilité**: Ignorer les chaînes très courtes

### 7️⃣ Ignorer logs
- **Défaut**: Oui (recommandé)
- **Options**: Oui/Non
- **Effet**: Exclut les lignes contenant `log()`, `warn()`, etc.

---

## 📝 Résumé

| Aspect | Menu | CLI |
|--------|------|-----|
| Facilité | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Guidage | Complet | Aide disponible |
| Rapide | ✗ Étapes | ✓ Direct |
| Validation | Immédiate | À la fin |
| Windows | ✓ Optimisé | ✓ Normalisé |
| Automation | ✗ | ✓ Facile |

---

## 🚀 Prochaines Étapes

1. **Lancer l'extraction**
   ```bash
   python Extractor_main.py
   ```

2. **Vérifier les fichiers générés**
   ```
   output/YYYYMMDD_hhmmss/
   ├─ TranslatedStrings_en.txt
   ├─ spacing_metadata.json
   ├─ replacements.json
   └─ extraction_report.txt
   ```

3. **Utiliser avec Applicator**
   ```bash
   python Applicator_main.py --plugin-path ./plugin
   ```

---

Version: 5.1 (Menu interactif)  
Date: 2026-01-27  
Auteur: Claude (Anthropic)
