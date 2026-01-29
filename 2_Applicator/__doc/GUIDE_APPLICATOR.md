# 🔧 GUIDE - Applicator v5.1

## 📊 Vue d'ensemble

**Applicator v5.1** applique les localisations générées par Extractor au plugin Lightroom.

### ✨ Nouvelles fonctionnalités
- **Menu interactif** - Configuration guidée comme Extractor
- **Détection automatique** - Trouve les fichiers Extractor générés
- **Support nouvelle structure** - Compatible dossiers YYYYMMDD_hhmmss
- **Mode Dry-Run** - Simuler avant de modifier

---

## 🎮 Utilisation

### Mode 1: Menu Interactif (RECOMMANDÉ)
```bash
python Applicator_main.py
```

**Advantages:**
- ✓ Détection automatique dossier Extractor
- ✓ Validation en temps réel
- ✓ Mode dry-run avant modifications
- ✓ Idéal pour les débutants

### Mode 2: CLI Classique
```bash
python Applicator_main.py \
  --plugin-path ./plugin \
  --extraction-dir ./output/20260127_091234 \
  --dry-run
```

**Avantages:**
- ✓ Exécution rapide
- ✓ Intégrable dans scripts
- ✓ Pour l'automation

---

## 📖 Guide Pas à Pas

### Étape 1: Lancer Applicator
```bash
python Applicator_main.py
```

Output:
```
================================================================================
  APPLICATOR - Configuration Interactive
================================================================================

Configurer les paramètres d'application des localisations.
```

### Étape 2: Spécifier le plugin
```
1️⃣  Chemin du plugin Lightroom
────────────────────────────────────────────────────────────────────────────────

Chemin du plugin (obligatoire): ./piwigoPublish.lrplugin
✓ Plugin trouvé: piwigoPublish.lrplugin
```

### Étape 3: Sélectionner dossier Extractor
```
2️⃣  Dossier contenant les fichiers Extractor
────────────────────────────────────────────────────────────────────────────────

Dossier détecté automatiquement:
  ./output/20260127_091234

Options:
  1. Utiliser ce dossier
  2. Spécifier un autre dossier
  3. Annuler

Votre choix (1-3): 1
✓ Dossier Extractor: ./output/20260127_091234
```

### Étape 4: Choisir mode
```
3️⃣  Mode de fonctionnement
────────────────────────────────────────────────────────────────────────────────

Dry-run (simulation)  : Affiche ce qui sera fait SANS modifier les fichiers
Modification réelle    : Applique les changements au plugin

Mode dry-run? [O/n]: o
✓ Mode simulation (DRY-RUN) - Aucun fichier ne sera modifié
```

### Étape 5: Confirmation
```
Configuration actuelle:
  1. Chemin du plugin           : piwigoPublish.lrplugin
  2. Dossier Extractor          : ./output/20260127_091234
  3. Mode dry-run               : ✓ Oui (simulation)

Options:
  1. Démarrer l'application
  2. Modifier les paramètres
  3. Quitter

Votre choix (1-3): 1
```

### Étape 6: Vérifier résultats
```
================================================================================
RÉSUMÉ
================================================================================
Fichiers traités       : 10
Fichiers modifiés      : 8
Remplacements effectués: 35
Espaces réinjectés     : 3 ⚠️
Chaînes ignorées       : 2

Rapport détaillé: ./localization_report.txt

IMPORTANT: Redémarrez Lightroom après les modifications!
```

---

## 🗂️ Structure de Fichiers

### Avant (v5.0)
```
plugin/
├─ PW_*.lua
├─ TranslatedStrings_en.txt
├─ spacing_metadata.json
└─ replacements.json
```

### Après (v5.1)
```
output/
├─ 20260127_091234/          ← Premier extraction
│  ├─ TranslatedStrings_en.txt
│  ├─ spacing_metadata.json
│  ├─ replacements.json
│  └─ extraction_report.txt
│
└─ 20260127_092015/          ← Deuxième extraction
   ├─ TranslatedStrings_en.txt
   ├─ spacing_metadata.json
   ├─ replacements.json
   └─ extraction_report.txt

plugin/
├─ PW_*.lua                  ← À localiser
└─ PW_*.lua.bak             ← Sauvegarde après modif
```

---

## 🔄 Workflow Complet

### Étape 1: Extraire les chaînes
```bash
python Extractor_main.py
→ Génère: output/20260127_091234/
   ├─ TranslatedStrings_en.txt
   ├─ spacing_metadata.json
   └─ replacements.json
```

### Étape 2: Appliquer les localisations
```bash
python Applicator_main.py
→ Utilise: output/20260127_091234/
→ Modifie: plugin/*.lua
→ Crée: plugin/*.lua.bak
```

### Étape 3: Vérifier et traduire
```bash
# Éditer TranslatedStrings_fr.txt
# Créer translations
```

### Étape 4: Redémarrer Lightroom
```
✓ Fermer Lightroom complètement
✓ Relancer Lightroom
✓ Vérifier les textes localisés
```

---

## 🧪 Mode Dry-Run vs Real

### DRY-RUN (Recommandé d'abord)
```bash
python Applicator_main.py
→ Mode: dry-run (simulation)
→ Résultat: Affiche changements sans modifier
→ Fichiers .bak: NON créés
→ Rapport: Généré
```

**Usage:**
- Vérifier avant de vraiment modifier
- Tester les chemins
- Valider la configuration

### MODIFICATION RÉELLE
```bash
# Relancer sans dry-run
Mode: Modification réelle
→ Résultat: Fichiers modifiés
→ Fichiers .bak: Créés avant modif
→ Rapport: Généré
```

**Warning:**
- ⚠️ Modifie les fichiers Lua
- ✓ Crée des sauvegardes .bak
- ✓ Recommandé après dry-run

---

## 📁 Détection Automatique

Applicator détecte automatiquement:

✓ Dossiers avec format `YYYYMMDD_HHMMSS`  
✓ Présence de `spacing_metadata.json`  
✓ Dossier d'extraction le plus récent  

```bash
Dossier détecté automatiquement:
  ./output/20260127_091234
```

---

## ⚠️ Important

### Après modification
1. **Redémarrer Lightroom**
   - ❌ Ne pas utiliser "Reload"
   - ✓ Fermer + Relancer complètement

2. **Vérifier les fichiers .bak**
   - Sauvegardes créées automatiquement
   - Format: `filename.lua.bak`

3. **Consulter le rapport**
   - `localization_report.txt`
   - Liste les changements
   - Note les espaces réinjectés ⚠️

---

## 🎯 Cas d'Usage

### Windows - Débutant
```
1. Lancer: python Applicator_main.py
2. Menu: Sélectionner plugin et dossier
3. Mode: Choisir simulation
4. Résultat: Vérifier rapport
5. Relancer: Mode réel
```

### Linux - Automation
```bash
#!/bin/bash
python Applicator_main.py \
  --plugin-path "$PLUGIN" \
  --extraction-dir "$EXTRACTOR_OUTPUT"
```

### Script Batch
```batch
@echo off
python Applicator_main.py ^
  --plugin-path "C:\Lightroom\plugin" ^
  --extraction-dir "D:\Extractions\20260127_091234"
pause
```

---

## 🔗 Intégration Workflow

### Étape 1: Extractor genère
```
plugin/
output/
├─ 20260127_091234/
│  ├─ TranslatedStrings_en.txt
│  ├─ spacing_metadata.json
│  └─ replacements.json
```

### Étape 2: Applicator applique
```
python Applicator_main.py
→ Lit fichiers Extractor
→ Modifie plugin
→ Crée plugin/*.bak
→ Génère rapport
```

### Étape 3: Traduction
```
Éditer TranslatedStrings_fr.txt
avec valeurs traduites
```

---

## 📊 Options CLI Complètes

```bash
python Applicator_main.py --help

Options:
  --plugin-path PATH         Chemin du plugin (OBLIGATOIRE)
  --extraction-dir PATH      Dossier Extractor (OBLIGATOIRE)
  --dry-run                  Mode simulation (optionnel)
```

---

## ✨ Fichiers Extractor Requis

Applicator nécessite (générés par Extractor):

| Fichier | Contenu |
|---------|---------|
| `TranslatedStrings_en.txt` | Clés LOC + valeurs par défaut |
| `spacing_metadata.json` | Métadonnées d'espaces |
| `replacements.json` | Instructions de remplacement |

⚠️ Si manquant: Applicator refusera de continuer

---

## 🆘 Troubleshooting

### "Dossier Extractor introuvable"
```
❌ Répertoire Extractor introuvable: ./output

→ Solution:
  1. Lancer Extractor d'abord
  2. Vérifier le chemin YYYYMMDD_hhmmss
  3. Utiliser le menu pour auto-détection
```

### "Aucune clé LOC trouvée"
```
❌ ERREUR: Aucune clé LOC trouvée dans le fichier

→ Solution:
  1. Vérifier TranslatedStrings_*.txt existe
  2. Vérifier format: "$$$/Key=Value"
  3. Relancer Extractor
```

### "Fichiers .bak non créés"
```
⚠️ Mode dry-run → pas de sauvegarde

→ Solution:
  1. Relancer en mode réel (sans dry-run)
  2. Créera automatiquement .bak
```

---

## 📋 Checklist

Avant de lancer:
- [ ] Extractor exécuté (fichiers générés)
- [ ] Dossier YYYYMMDD_hhmmss créé
- [ ] `spacing_metadata.json` présent
- [ ] `TranslatedStrings_en.txt` présent
- [ ] Plugin Lua accessible

Après application:
- [ ] Rapport généré (vérifier)
- [ ] Fichiers .bak créés
- [ ] Lightroom redémarré
- [ ] Textes localisés vérifiés
- [ ] Fichiers changements acceptés

---

## 🚀 Prochaines Étapes

1. **Traduire** les chaînes dans TranslatedStrings_fr.txt
2. **Tester** dans Lightroom
3. **Valider** les changements
4. **Commit** dans version control
5. **Distribuer** le plugin localisé

---

Version: 5.1  
Date: 2026-01-27  
Auteur: Claude (Anthropic)
