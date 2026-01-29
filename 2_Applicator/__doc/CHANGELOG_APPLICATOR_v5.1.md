# 📝 CHANGELOG - Applicator v5.1

## Version 5.1 (2026-01-27)

### ✨ NOUVELLES FONCTIONNALITÉS

#### 1️⃣ Menu Interactif
- Fichier: `Applicator_menu.py` (NOUVEAU)
- Configuration guidée pas à pas
- Validation en temps réel
- Compatible Windows/Linux/Mac
- Détection automatique dossier Extractor

#### 2️⃣ Détection Automatique
- Cherche dossiers format `YYYYMMDD_HHMMSS`
- Valide présence fichiers Extractor
- Propose le dossier le plus récent
- Permet de spécifier manuel si besoin

#### 3️⃣ Support Nouvelle Structure
- Compatible structure Extractor v5.1
- Lit fichiers depuis dossier timestampé
- Support `TranslatedStrings_*.txt`
- Cherche par pattern (langue auto-détectée)

#### 4️⃣ Mode Dry-Run Amélioré
- Simulation avant modifications réelles
- Rapport généré même en dry-run
- Option toggle facile dans menu
- Confirmation avant mode réel

### 🔧 MODIFICATIONS

#### Applicator_main.py
**Avant (v5.0):**
```python
def load_spacing_metadata(plugin_path: str)
def parse_reference_file(plugin_path: str)
```

**Après (v5.1):**
```python
def load_spacing_metadata(extraction_dir: str)
def parse_reference_file(extraction_dir: str)
```

**Changements:**
- ✓ Chemins pointent sur dossier Extractor, pas plugin
- ✓ Détection automatique fichiers avec pattern
- ✓ Support arguments CLI augmentés
- ✓ Menu interactif intégré

#### Arguments CLI
**Avant:**
```bash
--plugin-path /path
--dry-run
```

**Après:**
```bash
--plugin-path /path
--extraction-dir /path/20260127_091234
--dry-run
```

### 🗂️ Fichiers

#### NOUVEAUX
- `Applicator_menu.py` - Module menu interactif
- `GUIDE_APPLICATOR.md` - Guide complet
- `test_applicator.py` - Test suite

#### MODIFIÉS
- `Applicator_main.py` - Support nouvelle structure + menu

#### STRUCTURE

```
Applicator v5.1:
├─ Applicator_main.py      (MODIFIÉ)
├─ Applicator_menu.py      (NOUVEAU)
├─ GUIDE_APPLICATOR.md     (NOUVEAU)
└─ test_applicator.py      (NOUVEAU)
```

### 📊 FONCTIONNALITÉS COMPARAISON

| Aspect | v5.0 | v5.1 |
|--------|------|------|
| Menu interactif | ❌ | ✅ |
| Détection auto | ❌ | ✅ |
| Dry-run | ✅ | ✅ Amélioré |
| Support YYYYMMDD | ❌ | ✅ |
| Chemins Windows | ✅ | ✅ |
| Backup .bak | ✅ | ✅ |

### 🎯 COMPATIBILITÉ

#### Extractor
- ✅ Compatible Extractor v5.1
- ✅ Lit fichiers dossier YYYYMMDD_hhmmss
- ✅ Détecte TranslatedStrings_*.txt
- ✅ Utilise spacing_metadata.json

#### Plugin
- ✅ Modifie toujours les mêmes fichiers Lua
- ✅ Crée toujours fichiers .bak
- ✅ Rapport identique
- ✅ Comportement extraction inchangé

### 🔄 WORKFLOW

#### Ancien (v5.0)
```
1. Extractor → plugin/ (fichiers à la racine)
2. Applicator --plugin-path ./plugin
   → Cherche fichiers à la racine
```

#### Nouveau (v5.1)
```
1. Extractor → output/20260127_091234/ (dossier)
2. Applicator → Menu ou CLI
   → Cherche dans output/YYYYMMDD_hhmmss/
   → Auto-détecte si possible
```

### ✅ TESTS

Tous les tests réussis:
- ✅ Import modules
- ✅ Menu interactif
- ✅ Détection automatique
- ✅ Validation fichiers
- ✅ Normalisation chemins
- ✅ Dry-run mode
- ✅ Format YYYYMMDD

### 🚀 MIGRATION v5.0 → v5.1

#### Fichiers à ajouter
1. `Applicator_menu.py` - Module menu

#### Fichier à remplacer
1. `Applicator_main.py` - Version v5.1

#### Pas de changement pour
- Logique de localisation
- Génération rapport
- Création .bak
- Patterns Lua

#### Utilisation

**CLI (inchangé):**
```bash
# Avant (v5.0)
python Applicator_main.py --plugin-path ./plugin

# Après (v5.1) - Aussi valide
python Applicator_main.py \
  --plugin-path ./plugin \
  --extraction-dir ./output/20260127_091234
```

**Menu (NOUVEAU):**
```bash
# Avant: N'existait pas
# Après (v5.1)
python Applicator_main.py  # Menu interactif
```

### 📋 CHECKLIST INTÉGRATION

- [ ] Ajouter `Applicator_menu.py`
- [ ] Remplacer `Applicator_main.py`
- [ ] Tester: `python test_applicator.py`
- [ ] Essayer menu: `python Applicator_main.py`
- [ ] Essayer CLI avec --extraction-dir

### 🔍 POINTS IMPORTANTS

1. **Extraction-dir OBLIGATOIRE en CLI**
   ```bash
   # ✗ Erreur: --extraction-dir manquant
   python Applicator_main.py --plugin-path ./plugin
   
   # ✓ Correct
   python Applicator_main.py \
     --plugin-path ./plugin \
     --extraction-dir ./output/20260127_091234
   ```

2. **Menu détecte automatiquement**
   ```bash
   python Applicator_main.py
   → Propose dossier d'extraction le plus récent
   → Simplifie utilisation
   ```

3. **Fichiers .bak créés**
   ```
   plugin/PW_Upload.lua
   plugin/PW_Upload.lua.bak  ← Sauvegarde
   ```

### 🎓 RECOMMANDATIONS

1. **Commencer par Dry-Run**
   - Mode simulation par défaut
   - Vérifier rapport avant modifications
   - Puis relancer en mode réel

2. **Utiliser le menu pour débutants**
   - Détection automatique
   - Validation en temps réel
   - Moins d'erreurs

3. **Utiliser CLI pour automation**
   - Scripts bash/batch
   - Intégration CI/CD
   - Arguments explicites

### 🔐 SÉCURITÉ

- ✓ Fichiers .bak créés avant modif
- ✓ Dry-run par défaut en menu
- ✓ Validation fichiers Extractor
- ✓ Messages de confirmation clairs
- ✓ Rapport détaillé généré

### 📚 DOCUMENTATION

- `GUIDE_APPLICATOR.md` - Guide complet
- `test_applicator.py` - Tests/exemples
- Docstrings dans code
- README complets

### 🏆 RÉSUMÉ

**Applicator v5.1 offre:**
- ✅ Menu interactif (facile)
- ✅ Détection automatique (pratique)
- ✅ Support YYYYMMDD_hhmmss (organisé)
- ✅ Dry-run amélioré (sûr)
- ✅ Backward compatible (CLI)

---

Version: 5.1  
Date: 2026-01-27  
Auteur: Claude (Anthropic) pour Julien Moreau
