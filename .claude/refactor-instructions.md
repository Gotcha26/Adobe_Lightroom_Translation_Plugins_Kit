# 🔧 REFACTORISATION: Structure __i18n_kit__

**Date**: 2026-01-29  
**Objectif**: Réorganiser tous les outils pour écrire dans `<plugin>/__i18n_kit__/<Outil>/<timestamp>/`  
**Branche**: `refactor/i18n-kit-structure`

---

## 📋 RÈGLES STRICTES

### 1. Structure de sortie OBLIGATOIRE
```
<plugin_lightroom>/
├── Info.lua
├── *.lua
└── __i18n_kit__/                    ← NOUVEAU dossier racine
    ├── Extractor/
    │   ├── 20260129_143022/         ← Timestamp
    │   │   ├── TranslatedStrings_en.txt
    │   │   ├── spacing_metadata.json
    │   │   ├── replacements.json
    │   │   └── extraction_report.txt
    │   └── 20260129_151500/         ← Autre exécution
    │       └── ...
    ├── Applicator/
    │   └── 20260129_143530/
    │       ├── application_report.txt
    │       └── backups/
    │           └── *.bak
    ├── TranslationManager/
    │   └── 20260129_144000/
    │       ├── UPDATE_en.json
    │       ├── CHANGELOG.txt
    │       └── ...
    └── Tools/
        └── 20260129_145000/
            └── restore_log.txt
```

### 2. Ce qui DOIT changer
- ❌ **ANCIEN**: Fichiers dans le repo `Adobe_Lightroom_Translation_Plugins_Kit/`
- ✅ **NOUVEAU**: Fichiers dans `<plugin>/__i18n_kit__/<Outil>/<timestamp>/`

### 3. Ce qui NE change PAS
- ✅ SDK Adobe Lightroom (format LOC, structure .lua)
- ✅ Backups .bak dans le plugin (ou dans __i18n_kit__/Applicator/<timestamp>/backups/)
- ✅ Scripts indépendants et utilisables en standalone
- ✅ Menu LocalisationToolKit.py centralise toujours

---

## 🎯 OBJECTIFS DE LA REFACTORISATION

### Phase 1: Module commun de gestion des chemins
**Fichier**: `common/paths.py` (NOUVEAU)

```python
"""
Module commun pour gérer les chemins __i18n_kit__
"""
import os
from datetime import datetime
from pathlib import Path

def get_i18n_kit_path(plugin_path: str) -> str:
    """Retourne le chemin du dossier __i18n_kit__ dans le plugin."""
    return os.path.join(plugin_path, "__i18n_kit__")

def get_tool_output_path(plugin_path: str, tool_name: str, create: bool = True) -> str:
    """
    Retourne le chemin de sortie pour un outil avec timestamp.
    
    Args:
        plugin_path: Chemin vers le plugin Lightroom
        tool_name: Nom de l'outil (Extractor, Applicator, TranslationManager, Tools)
        create: Créer le dossier si True
    
    Returns:
        Chemin complet: <plugin>/__i18n_kit__/<tool_name>/<YYYYMMDD_HHMMSS>/
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(
        get_i18n_kit_path(plugin_path),
        tool_name,
        timestamp
    )
    
    if create:
        os.makedirs(path, exist_ok=True)
    
    return path

def find_latest_tool_output(plugin_path: str, tool_name: str) -> str | None:
    """
    Trouve le dossier le plus récent pour un outil.
    
    Returns:
        Chemin complet du dernier dossier ou None si aucun
    """
    tool_dir = os.path.join(get_i18n_kit_path(plugin_path), tool_name)
    
    if not os.path.exists(tool_dir):
        return None
    
    # Lister dossiers format YYYYMMDD_HHMMSS
    dirs = [
        d for d in os.listdir(tool_dir)
        if os.path.isdir(os.path.join(tool_dir, d)) and len(d) == 15
    ]
    
    if not dirs:
        return None
    
    # Tri décroissant (plus récent en premier)
    dirs.sort(reverse=True)
    return os.path.join(tool_dir, dirs[0])

def normalize_path(path: str) -> str:
    """Normalise un chemin (Windows/Linux)."""
    return os.path.normpath(os.path.abspath(path))
```

**Actions**:
1. Créer dossier `common/` à la racine du repo
2. Créer `common/__init__.py` vide
3. Créer `common/paths.py` avec le contenu ci-dessus

---

### Phase 2: Modifier Extractor

**Fichier**: `1_Extractor/Extractor_main.py`

**Changements**:
```python
# AVANT
output_dir = args.output_dir or os.path.dirname(__file__)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
final_output = os.path.join(output_dir, timestamp)

# APRÈS
from common.paths import get_tool_output_path
final_output = get_tool_output_path(plugin_path, "Extractor")
```

**Actions**:
1. Importer `common.paths`
2. Remplacer logique de création du dossier de sortie
3. Supprimer l'option `--output-dir` (optionnel, peut garder pour override)
4. Mettre à jour `Extractor_menu.py` pour retirer input output_dir

---

### Phase 3: Modifier Applicator

**Fichier**: `2_Applicator/Applicator_main.py`

**Changements**:
```python
# AVANT
def load_spacing_metadata(extraction_dir: str):
    path = os.path.join(extraction_dir, "spacing_metadata.json")

# APRÈS
from common.paths import find_latest_tool_output

# Détection auto du dernier Extractor
if not extraction_dir:
    extraction_dir = find_latest_tool_output(plugin_path, "Extractor")
    if not extraction_dir:
        raise ValueError("Aucune extraction trouvée")

# Créer dossier de sortie pour Applicator
from common.paths import get_tool_output_path
applicator_output = get_tool_output_path(plugin_path, "Applicator")

# Sauvegardes .bak dans applicator_output/backups/
backup_dir = os.path.join(applicator_output, "backups")
```

**Actions**:
1. Ajouter détection auto de la dernière extraction
2. Créer dossier de sortie Applicator avec timestamp
3. Déplacer backups .bak dans `__i18n_kit__/Applicator/<timestamp>/backups/`
4. Mettre à jour rapport pour indiquer le nouveau chemin

---

### Phase 4: Modifier TranslationManager

**Fichier**: `3_TranslationManager/TranslationManager.py`

**Changements**:
```python
# AVANT
output_dir = args.output_dir or "."
timestamp_dir = os.path.join(output_dir, timestamp)

# APRÈS
from common.paths import get_tool_output_path, find_latest_tool_output

# Pour COMPARE
output_dir = get_tool_output_path(plugin_path, "TranslationManager")

# Pour EXTRACT/INJECT/SYNC - chercher dernière version COMPARE
compare_output = find_latest_tool_output(plugin_path, "TranslationManager")
```

**Actions**:
1. Adapter toutes les commandes (COMPARE, EXTRACT, INJECT, SYNC)
2. Utiliser `get_tool_output_path` pour créer nouveau dossier
3. Utiliser `find_latest_tool_output` pour lire résultats précédents
4. Tester workflow complet

---

### Phase 5: Modifier Tools

**Fichier**: `9_Tools/restore_backups.py`

**Changements**:
```python
# AVANT
backup_dir = "./backups"

# APRÈS
from common.paths import find_latest_tool_output

# Chercher backups dans dernier Applicator
applicator_output = find_latest_tool_output(plugin_path, "Applicator")
backup_dir = os.path.join(applicator_output, "backups")
```

---

### Phase 6: Mettre à jour LocalisationToolKit.py

**Changements**:
```python
# Ajouter info sur __i18n_kit__ dans display()
def display(self):
    plugin_path = self.config.get('plugin_path')
    if plugin_path:
        i18n_path = os.path.join(plugin_path, "__i18n_kit__")
        print(f"   __i18n_kit__ path  : {i18n_path}")
```

**Actions**:
1. Afficher chemin `__i18n_kit__` dans la config
2. Option pour nettoyer vieux dossiers timestampés
3. Lister les dernières exécutions de chaque outil

---

## 🧪 TESTS REQUIS

### Test 1: Extractor standalone
```bash
cd 1_Extractor
python Extractor_main.py --plugin-path /path/to/plugin

# Vérifier:
# - Dossier créé: /path/to/plugin/__i18n_kit__/Extractor/YYYYMMDD_HHMMSS/
# - Fichiers présents: TranslatedStrings_en.txt, spacing_metadata.json, etc.
```

### Test 2: Applicator standalone
```bash
cd 2_Applicator
python Applicator_main.py --plugin-path /path/to/plugin

# Vérifier:
# - Détecte automatiquement dernière extraction
# - Crée /path/to/plugin/__i18n_kit__/Applicator/YYYYMMDD_HHMMSS/
# - Backups dans __i18n_kit__/Applicator/<timestamp>/backups/
```

### Test 3: Workflow complet
```bash
python LocalisationToolKit.py
# 1. Extractor
# 2. Applicator
# 3. TranslationManager COMPARE
# 4. TranslationManager EXTRACT
# 5. TranslationManager INJECT
# 6. TranslationManager SYNC

# Vérifier structure complète __i18n_kit__
```

### Test 4: Windows compatibility
```cmd
REM Tester avec chemins Windows (espaces, backslashes)
python Extractor_main.py --plugin-path "C:\Users\Test\Lightroom Plugin\plugin.lrplugin"
```

---

## 📝 CHECKLIST

### Fichiers à créer
- [ ] `common/__init__.py`
- [ ] `common/paths.py`
- [ ] `.vscode/settings.json` (workspace)
- [ ] `tests/test_i18n_structure.py`

### Fichiers à modifier
- [ ] `1_Extractor/Extractor_main.py`
- [ ] `1_Extractor/Extractor_menu.py`
- [ ] `2_Applicator/Applicator_main.py`
- [ ] `2_Applicator/Applicator_menu.py`
- [ ] `3_TranslationManager/TranslationManager.py`
- [ ] `3_TranslationManager/TM_*.py` (tous les modules)
- [ ] `9_Tools/restore_backups.py`
- [ ] `LocalisationToolKit.py`

### Documentation à mettre à jour
- [ ] `README.md` principal
- [ ] `1_Extractor/__doc/GUIDE_MENU.md`
- [ ] `2_Applicator/__doc/GUIDE_APPLICATOR.md`
- [ ] `3_TranslationManager/__doc/README.md`

### Tests à exécuter
- [ ] Test 1: Extractor standalone
- [ ] Test 2: Applicator standalone
- [ ] Test 3: TranslationManager workflow
- [ ] Test 4: Windows paths
- [ ] Test 5: Workflow LocalisationToolKit.py complet

---

## ⚠️ POINTS D'ATTENTION

1. **Rétrocompatibilité**: Garder option `--output-dir` en override pour anciens scripts
2. **Erreurs claires**: Si plugin_path manquant, message explicite
3. **Windows**: Toujours utiliser `os.path.normpath()` et `os.path.join()`
4. **Timestamps**: Format strict `YYYYMMDD_HHMMSS` (15 caractères)
5. **Git**: Commits atomiques par outil (1 commit = 1 outil refactorisé)

---

## 🚀 ORDRE D'EXÉCUTION RECOMMANDÉ

1. ✅ Créer `common/paths.py`
2. ✅ Tester `common/paths.py` isolément
3. ✅ Refactoriser Extractor + test
4. ✅ Refactoriser Applicator + test
5. ✅ Refactoriser TranslationManager + test
6. ✅ Refactoriser Tools + test
7. ✅ Mettre à jour LocalisationToolKit.py
8. ✅ Tests complets workflow
9. ✅ Documentation
10. ✅ Merge dans main

---

## 📚 RESSOURCES

- SDK Lightroom: Respecter format `LOC "$$$/Key=Default"`
- Python os.path: https://docs.python.org/3/library/os.path.html
- Timestamps: `datetime.now().strftime("%Y%m%d_%H%M%S")`
