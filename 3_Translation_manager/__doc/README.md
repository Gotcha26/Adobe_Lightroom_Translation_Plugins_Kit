# TranslationManager - Documentation technique

**Version 5.0 | Janvier 2026**

## Vue d'ensemble

TranslationManager est le troisième outil de la chaîne de localisation. Son rôle est de gérer l'évolution des traductions au fil du temps : comparer différentes versions, isoler les nouvelles clés à traduire, injecter les traductions et synchroniser tous les fichiers de langue.

## Architecture du projet

```
3_Translation_manager/
├── TranslationManager.py     ← Point d'entrée (menu + CLI)
├── TM_common.py             ← Fonctions communes (parser, utils, UI)
├── TM_compare.py            ← Commande COMPARE (diff entre 2 versions EN)
├── TM_extract.py            ← Commande EXTRACT (génère TRANSLATE_xx.txt)
├── TM_inject.py             ← Commande INJECT (réinjecte les traductions)
├── TM_sync.py               ← Commande SYNC (synchronise les langues)
└── __doc/
    └── README.md            ← Ce fichier
```

L'architecture est modulaire avec une commande par module. Chaque commande peut être utilisée indépendamment ou via le menu interactif.

## Les 4 commandes

TranslationManager propose 4 commandes principales qui forment un workflow complet.

### 1. COMPARE - Détection des changements

Compare deux versions du fichier anglais (`TranslatedStrings_en.txt`) et génère un fichier de mise à jour.

```
Ancien EN          Nouveau EN
(v1.0)             (v1.1)
    │                  │
    └─────────┬────────┘
              ▼
         COMPARE
              │
              ├── UPDATE_en.json
              │   ├── added: [...]      ← Nouvelles clés
              │   ├── changed: [...]    ← Clés modifiées
              │   ├── deleted: [...]    ← Clés supprimées
              │   └── unchanged: [...]  ← Clés identiques
              │
              └── CHANGELOG.txt
                  ├── Résumé statistique
                  ├── Détail des ajouts
                  ├── Détail des modifications
                  └── Détail des suppressions
```

**Fichiers générés :**

- **UPDATE_en.json** : Fichier structuré avec toutes les différences
- **CHANGELOG.txt** : Rapport lisible pour humains

### 2. EXTRACT - Isolation des nouvelles clés

Génère de petits fichiers contenant uniquement les clés à traduire (nouvelles ou modifiées).

```
UPDATE_en.json
    │
    ├── added: 15 clés
    ├── changed: 5 clés
    │
    └────────┬──────────────────────────────────┐
             ▼                                  ▼
     TRANSLATE_fr.txt                  TRANSLATE_de.txt
     ├── [NEW] Clé1=                   ├── [NEW] Clé1=
     ├── [NEW] Clé2=                   ├── [NEW] Clé2=
     ├── [NEEDS_REVIEW] Clé3=...       ├── [NEEDS_REVIEW] Clé3=...
     └── ...                           └── ...
```

**Avantages :**
- Fichiers légers (quelques Ko vs plusieurs Mo)
- Faciles à envoyer à des traducteurs
- Focus uniquement sur le nouveau contenu

### 3. INJECT - Fusion des traductions

Réinjecte les traductions depuis les fichiers `TRANSLATE_xx.txt` dans les fichiers complets `TranslatedStrings_xx.txt`.

```
TRANSLATE_fr.txt              TranslatedStrings_fr.txt
(nouvelles traductions)       (fichier complet)
    │                              │
    ├── Clé1=Bonjour               ├── Clé0=Ancien texte
    ├── Clé2=Monde                 ├── ...
    └── Clé3=(vide)                └── ...
          │                              │
          └──────────┬───────────────────┘
                     ▼
                  INJECT
                     │
                     ├── Clé traduite → utilise la traduction
                     ├── Clé vide → utilise la valeur EN par défaut
                     └── Clé absente → reste inchangée
                     │
                     ▼
          TranslatedStrings_fr.txt (mis à jour)
          ├── Clé0=Ancien texte
          ├── Clé1=Bonjour          ← Ajoutée
          ├── Clé2=Monde            ← Ajoutée
          ├── Clé3=Default EN       ← Fallback EN
          └── ...
```

**Mécanisme de fallback :**
Si une clé est vide dans `TRANSLATE_xx.txt`, INJECT utilise la valeur anglaise par défaut depuis `UPDATE_en.json`. Cela garantit qu'aucun texte n'est perdu.

### 4. SYNC - Synchronisation finale

Synchronise tous les fichiers de langue avec la version anglaise de référence.

```
UPDATE_en.json              TranslatedStrings_fr.txt
TranslatedStrings_en.txt    TranslatedStrings_de.txt
(référence)                 (langues étrangères)
    │                            │
    └──────────┬─────────────────┘
               ▼
             SYNC
               │
               ├── Ajoute [NEW] pour nouvelles clés
               ├── Marque [NEEDS_REVIEW] pour clés modifiées
               ├── Supprime les clés obsolètes
               └── Préserve les traductions existantes
               │
               ▼
    TranslatedStrings_fr.txt (synchronisé)
    ├── "$$$/App/NewKey=[NEW]"
    ├── "$$$/App/Changed=[NEEDS_REVIEW] Old Translation"
    ├── "$$$/App/Existing=Traduction existante"
    └── (clé obsolète supprimée)
```

**Marqueurs ajoutés :**
- `[NEW]` : Nouvelle clé, pas encore traduite
- `[NEEDS_REVIEW]` : Valeur anglaise modifiée, revoir la traduction

## Workflow complet

Voici le workflow typique lors d'une mise à jour du plugin :

```
┌─────────────────────────────────────────────────────────┐
│ Étape 1 : Développement                                 │
│ - Ajout de nouvelles fonctionnalités au plugin         │
│ - Modification de textes existants                     │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Étape 2 : Extraction (Extractor)                       │
│ - Lance Extractor sur le code modifié                  │
│ - Génère nouveau TranslatedStrings_en.txt              │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Étape 3 : Comparaison (TranslationManager COMPARE)     │
│ - Compare ancien vs nouveau EN                         │
│ - Génère UPDATE_en.json + CHANGELOG.txt               │
│ - Résultat : 10 nouvelles clés, 3 modifiées, 2 supprimées │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Étape 4 : Extraction ciblée (EXTRACT)                  │
│ - Génère TRANSLATE_fr.txt (13 clés à traduire)        │
│ - Génère TRANSLATE_de.txt (13 clés à traduire)        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Étape 5 : Traduction                                    │
│ - Envoi des fichiers TRANSLATE_xx.txt aux traducteurs │
│ - Ou traduction manuelle                               │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Étape 6 : Injection (INJECT)                           │
│ - Réinjecte les traductions dans les fichiers complets│
│ - Fallback EN pour clés non traduites                 │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Étape 7 : Synchronisation (SYNC)                       │
│ - Ajoute [NEW] et [NEEDS_REVIEW]                      │
│ - Supprime les clés obsolètes                         │
│ - Finalise tous les fichiers de langue                │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│ Étape 8 : Test                                          │
│ - Redémarrer Lightroom                                 │
│ - Vérifier les traductions dans l'interface           │
└─────────────────────────────────────────────────────────┘
```

## Options de configuration

### Mode interactif

Lancez `TranslationManager.py` pour accéder au menu :

```
==================================================
     TRANSLATION MANAGER v5.0
==================================================

Options:
  1. COMPARE
     Compare ancien EN vs nouveau EN
     → Génère UPDATE_en.json + CHANGELOG.txt

  2. EXTRACT (optionnel)
     Génère mini fichiers TRANSLATE_xx.txt pour traduction

  3. INJECT (optionnel)
     Réinjecte les traductions (EN par défaut si vide)

  4. SYNC
     Met à jour les langues avec EN
     → Ajoute [NEW], marque [NEEDS_REVIEW], supprime obsolètes

  5. Aide

  0. Quitter
```

### Mode CLI

Chaque commande peut être lancée indépendamment :

**COMPARE :**
```bash
python TranslationManager.py compare \
  --old ancien_en.txt \
  --new nouveau_en.txt \
  --plugin-path ./plugin.lrplugin
```

**EXTRACT :**
```bash
python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

**INJECT :**
```bash
python TranslationManager.py inject \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

**SYNC :**
```bash
python TranslationManager.py sync \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

### Options détaillées

#### Commande COMPARE

| Option | Description | Requis | Exemple |
|--------|-------------|--------|---------|
| `--old` | Ancien fichier EN | Oui | `./v1/TranslatedStrings_en.txt` |
| `--new` | Nouveau fichier EN | Oui | `./v2/TranslatedStrings_en.txt` |
| `--plugin-path` | Chemin plugin (sortie dans `__i18n_tmp__/`) | Non | `./plugin.lrplugin` |
| `--output` | Répertoire de sortie personnalisé | Non | `./output` |

#### Commande EXTRACT

| Option | Description | Requis | Exemple |
|--------|-------------|--------|---------|
| `--update` | Dossier UPDATE (ou auto-détection si `--plugin-path`) | Non* | `./20260129_143000` |
| `--plugin-path` | Chemin plugin (auto-détection dans `__i18n_tmp__/`) | Non* | `./plugin.lrplugin` |
| `--locales` | Répertoire des traductions existantes | Non | `./plugin.lrplugin` |
| `--lang` | Langue spécifique à extraire | Non | `fr`, `de`, `es` |
| `--output` | Répertoire de sortie personnalisé | Non | `./output` |

\* Au moins une de ces options est requise

#### Commande INJECT

| Option | Description | Requis | Exemple |
|--------|-------------|--------|---------|
| `--translate` | Fichier TRANSLATE_xx.txt individuel | Non* | `./TRANSLATE_fr.txt` |
| `--target` | Fichier TranslatedStrings_xx.txt cible | Non* | `./TranslatedStrings_fr.txt` |
| `--translate-dir` | Dossier contenant plusieurs TRANSLATE_*.txt | Non* | `./translations/` |
| `--plugin-path` | Chemin plugin (auto-détection) | Non* | `./plugin.lrplugin` |
| `--locales` | Dossier des fichiers de langue | Non* | `./plugin.lrplugin` |
| `--update` | Dossier UPDATE (valeurs EN de fallback) | Non | `./20260129_143000` |

\* Spécifiez soit (`--translate` + `--target`) OU (`--translate-dir` + `--locales`) OU (`--plugin-path` + `--locales`)

#### Commande SYNC

| Option | Description | Requis | Exemple |
|--------|-------------|--------|---------|
| `--ref` | Fichier EN de référence | Non* | `./TranslatedStrings_en.txt` |
| `--plugin-path` | Chemin plugin (auto-détection) | Non* | `./plugin.lrplugin` |
| `--locales` | Répertoire des fichiers de langues | Oui | `./plugin.lrplugin` |
| `--update` | Dossier UPDATE (avec UPDATE_en.json) | Non | `./20260129_143000` |

\* Au moins une de ces options est requise

## Exemples d'utilisation

### Workflow complet avec --plugin-path

```bash
# 1. Comparer deux versions
python TranslationManager.py compare \
  --old ./backup/TranslatedStrings_en.txt \
  --new ./plugin.lrplugin/__i18n_tmp__/Extractor/20260129_143022/TranslatedStrings_en.txt \
  --plugin-path ./plugin.lrplugin

# 2. Extraire les clés à traduire (auto-détection de UPDATE_en.json)
python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin

# 3. Traduire manuellement les fichiers TRANSLATE_xx.txt
# (édition dans votre éditeur préféré)

# 4. Injecter les traductions (auto-détection)
python TranslationManager.py inject \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin

# 5. Synchroniser tous les fichiers de langue
python TranslationManager.py sync \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

### Extraction et injection pour une seule langue

```bash
# Extraire uniquement pour le français
python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin \
  --lang fr

# Injecter uniquement le français
python TranslationManager.py inject \
  --translate ./plugin.lrplugin/__i18n_tmp__/TranslationManager/<timestamp>/TRANSLATE_fr.txt \
  --target ./plugin.lrplugin/TranslatedStrings_fr.txt \
  --update ./plugin.lrplugin/__i18n_tmp__/TranslationManager/<timestamp>/
```

### Mode legacy (sans --plugin-path)

```bash
# Comparer avec sortie manuelle
python TranslationManager.py compare \
  --old ./v1/en.txt \
  --new ./v2/en.txt \
  --output ./comparison_output/

# Extraire depuis un dossier UPDATE spécifique
python TranslationManager.py extract \
  --update ./comparison_output/20260129_143000/ \
  --locales ./plugin.lrplugin/

# Injecter depuis un dossier TRANSLATE spécifique
python TranslationManager.py inject \
  --translate-dir ./comparison_output/20260129_143000/ \
  --locales ./plugin.lrplugin/ \
  --update ./comparison_output/20260129_143000/

# Synchroniser
python TranslationManager.py sync \
  --update ./comparison_output/20260129_143000/ \
  --locales ./plugin.lrplugin/
```

## Structure des fichiers générés

### UPDATE_en.json

Fichier JSON structuré contenant toutes les différences :

```json
{
  "metadata": {
    "old_file": "./v1/TranslatedStrings_en.txt",
    "new_file": "./v2/TranslatedStrings_en.txt",
    "timestamp": "2026-01-29 14:30:00",
    "total_keys_old": 120,
    "total_keys_new": 133
  },
  "summary": {
    "added": 15,
    "changed": 5,
    "deleted": 2,
    "unchanged": 113
  },
  "added": {
    "$$$/Piwigo/NewFeature_Title": "New Feature Title",
    "$$$/Piwigo/NewFeature_Description": "Description of the new feature",
    ...
  },
  "changed": {
    "$$$/Piwigo/Upload_Status": {
      "old": "Uploading...",
      "new": "Upload in progress..."
    },
    ...
  },
  "deleted": {
    "$$$/Piwigo/OldFeature_Title": "Old Feature Title",
    ...
  },
  "unchanged": {
    "$$$/Piwigo/Submit": "Submit",
    "$$$/Piwigo/Cancel": "Cancel",
    ...
  }
}
```

### CHANGELOG.txt

Rapport lisible pour humains :

```
================================================================================
CHANGELOG - Comparaison des traductions
================================================================================

Fichier ancien : ./v1/TranslatedStrings_en.txt (120 clés)
Fichier nouveau : ./v2/TranslatedStrings_en.txt (133 clés)
Date : 2026-01-29 14:30:00

================================================================================
RÉSUMÉ
================================================================================

Clés ajoutées    : 15
Clés modifiées   : 5
Clés supprimées  : 2
Clés inchangées  : 113

================================================================================
CLÉS AJOUTÉES (15)
================================================================================

"$$$/Piwigo/NewFeature_Title"
  → "New Feature Title"

"$$$/Piwigo/NewFeature_Description"
  → "Description of the new feature"

...

================================================================================
CLÉS MODIFIÉES (5)
================================================================================

"$$$/Piwigo/Upload_Status"
  ANCIEN : "Uploading..."
  NOUVEAU : "Upload in progress..."

...

================================================================================
CLÉS SUPPRIMÉES (2)
================================================================================

"$$$/Piwigo/OldFeature_Title"
  ← "Old Feature Title"

...
```

### TRANSLATE_xx.txt

Fichiers légers pour traduction :

```
# Fichier de traduction pour : fr
# Généré le : 2026-01-29 14:35:00
#
# Instructions :
# - Traduisez les valeurs après le signe =
# - [NEW] = Nouvelle clé
# - [NEEDS_REVIEW] = Valeur anglaise modifiée, revoir la traduction
# - Laissez vide pour utiliser la valeur anglaise par défaut

"$$$/Piwigo/NewFeature_Title=[NEW]"
"$$$/Piwigo/NewFeature_Description=[NEW]"
"$$$/Piwigo/Upload_Status=[NEEDS_REVIEW] Téléchargement..."
```

Après traduction :

```
"$$$/Piwigo/NewFeature_Title=Nouvelle fonctionnalité"
"$$$/Piwigo/NewFeature_Description=Description de la nouvelle fonctionnalité"
"$$$/Piwigo/Upload_Status=Téléchargement en cours..."
```

## Gestion des marqueurs

### Marqueur [NEW]

Indique une clé complètement nouvelle, absente de la version précédente.

```
# Avant traduction
"$$$/App/NewKey=[NEW]"

# Après traduction
"$$$/App/NewKey=Ma traduction"

# Non traduit (fallback EN via INJECT)
"$$$/App/NewKey=Default English Value"
```

### Marqueur [NEEDS_REVIEW]

Indique que la valeur anglaise a changé et que la traduction doit être revue.

```
# Valeur EN ancienne : "Uploading..."
# Valeur EN nouvelle : "Upload in progress..."

# Dans TRANSLATE_fr.txt
"$$$/App/Upload=[NEEDS_REVIEW] Téléchargement..."

# Après révision
"$$$/App/Upload=Téléchargement en cours..."
```

Le marqueur `[NEEDS_REVIEW]` est suivi de l'ancienne traduction pour faciliter la mise à jour.

## Cas d'usage avancés

### Comparaison de deux extractions Extractor

Comparez deux exécutions d'Extractor pour voir ce qui a changé dans le code :

```bash
python TranslationManager.py compare \
  --old ./plugin/__i18n_tmp__/Extractor/20260120_100000/TranslatedStrings_en.txt \
  --new ./plugin/__i18n_tmp__/Extractor/20260129_143022/TranslatedStrings_en.txt \
  --plugin-path ./plugin.lrplugin
```

### Extraction sélective par langue

Si vous ne gérez que quelques langues :

```bash
# Extraire uniquement français et allemand
python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin \
  --lang fr

python TranslationManager.py extract \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin \
  --lang de
```

### Injection sans traduction (fallback EN)

Si vous voulez ajouter les nouvelles clés avec valeurs anglaises par défaut :

```bash
# Ne traduisez pas les fichiers TRANSLATE_xx.txt, laissez-les vides
# Puis injectez : les valeurs EN seront utilisées

python TranslationManager.py inject \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

Cela ajoute les nouvelles clés en anglais, ce qui est mieux que des textes manquants.

### Synchronisation après édition manuelle

Si vous avez édité directement `TranslatedStrings_xx.txt` :

```bash
# Synchroniser pour ajouter les marqueurs [NEW] et [NEEDS_REVIEW]
python TranslationManager.py sync \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

SYNC détectera les clés manquantes et les ajoutera avec `[NEW]`.

### Workflow sans EXTRACT/INJECT (édition directe)

Si vous préférez éditer directement les fichiers complets :

```bash
# 1. Comparer
python TranslationManager.py compare \
  --old ancien_en.txt \
  --new nouveau_en.txt \
  --plugin-path ./plugin.lrplugin

# 2. Consulter CHANGELOG.txt pour savoir quoi traduire
cat ./plugin/__i18n_tmp__/TranslationManager/<timestamp>/CHANGELOG.txt

# 3. Éditer manuellement TranslatedStrings_fr.txt, TranslatedStrings_de.txt, etc.
# (ajoutez les nouvelles clés, mettez à jour les modifiées)

# 4. Synchroniser pour nettoyer et finaliser
python TranslationManager.py sync \
  --plugin-path ./plugin.lrplugin \
  --locales ./plugin.lrplugin
```

## Dépannage

### Erreur : "Aucun dossier TranslationManager trouvé"

**Cause :** Pas de dossier `__i18n_tmp__/TranslationManager/` avec `UPDATE_en.json`.

**Solution :**
```bash
# Lancer d'abord COMPARE
python TranslationManager.py compare \
  --old ancien.txt \
  --new nouveau.txt \
  --plugin-path ./plugin.lrplugin
```

### EXTRACT ne génère aucun fichier

**Causes possibles :**
1. Aucune langue étrangère détectée dans `--locales`
2. Aucune différence dans `UPDATE_en.json` (rien à traduire)
3. Le dossier `--locales` ne contient pas de `TranslatedStrings_xx.txt`

**Solutions :**
```bash
# Vérifier les fichiers de langue
ls ./plugin.lrplugin/TranslatedStrings_*.txt

# Vérifier UPDATE_en.json
cat ./plugin/__i18n_tmp__/TranslationManager/<timestamp>/UPDATE_en.json
```

### INJECT n'ajoute rien

**Causes possibles :**
1. Les fichiers `TRANSLATE_xx.txt` sont vides
2. Les clés sont déjà présentes dans `TranslatedStrings_xx.txt`
3. Le dossier `--update` est incorrect (valeurs EN introuvables)

**Solutions :**
```bash
# Vérifier TRANSLATE_fr.txt
cat ./plugin/__i18n_tmp__/TranslationManager/<timestamp>/TRANSLATE_fr.txt

# Vérifier UPDATE_en.json
cat ./plugin/__i18n_tmp__/TranslationManager/<timestamp>/UPDATE_en.json
```

### SYNC supprime des traductions

SYNC supprime uniquement les clés obsolètes (présentes dans "deleted" de `UPDATE_en.json`). C'est normal.

Si vous voulez les conserver :

1. Éditez `UPDATE_en.json` et retirez les clés de "deleted"
2. Relancez SYNC

### Encodage incorrect

Tous les fichiers sont en UTF-8. Si vous voyez des caractères mal encodés :

```bash
# Vérifier l'encodage
file --mime-encoding TranslatedStrings_fr.txt

# Convertir si nécessaire
iconv -f ISO-8859-1 -t UTF-8 TranslatedStrings_fr.txt > TranslatedStrings_fr_utf8.txt
```

## FAQ technique

### Puis-je utiliser EXTRACT sans COMPARE ?

Non, EXTRACT a besoin de `UPDATE_en.json` généré par COMPARE pour savoir quelles clés extraire.

### Puis-je sauter INJECT et éditer directement les fichiers ?

Oui, c'est possible. INJECT est une commodité pour fusionner facilement les petits fichiers `TRANSLATE_xx.txt` dans les fichiers complets.

### SYNC est-il obligatoire ?

Non, mais c'est fortement recommandé. SYNC nettoie les fichiers (supprime les clés obsolètes) et ajoute les marqueurs `[NEW]` et `[NEEDS_REVIEW]` pour faciliter les révisions futures.

### Que se passe-t-il si je ne traduis pas une clé ?

INJECT utilisera la valeur anglaise par défaut depuis `UPDATE_en.json`. L'utilisateur verra le texte en anglais au lieu d'un texte vide ou une clé brute.

### Puis-je réutiliser un ancien UPDATE_en.json ?

Oui, tant qu'il correspond aux fichiers que vous voulez synchroniser. Mais il est préférable de faire un nouveau COMPARE avec les versions actuelles.

### Comment gérer plusieurs branches Git ?

```bash
# Branche dev
git checkout dev
python TranslationManager.py compare --old main_en.txt --new dev_en.txt --output ./dev_update/

# Branche feature
git checkout feature
python TranslationManager.py compare --old main_en.txt --new feature_en.txt --output ./feature_update/
```

Chaque branche peut avoir son propre dossier de mise à jour.

## Performances

### Temps d'exécution typiques

- **COMPARE** (120 vs 133 clés) : < 1 seconde
- **EXTRACT** (3 langues, 15 clés) : < 1 seconde
- **INJECT** (3 langues, 15 clés) : < 1 seconde
- **SYNC** (3 langues, 133 clés) : 1-2 secondes

TranslationManager est très rapide car il manipule uniquement des fichiers texte.

### Optimisations possibles

Si vous avez beaucoup de langues (10+) ou de clés (1000+) :

1. Utilisez EXTRACT avec `--lang` pour traiter une langue à la fois
2. Lancez les commandes hors heures de développement actif
3. Excluez les langues non maintenues de `--locales`

## Intégration dans un workflow automatisé

### Script bash complet

```bash
#!/bin/bash
# update_translations.sh

PLUGIN_PATH="./plugin.lrplugin"
OLD_EN="./backup/TranslatedStrings_en.txt"
NEW_EN="$PLUGIN_PATH/__i18n_tmp__/Extractor/latest/TranslatedStrings_en.txt"

echo "=== Étape 1 : Comparaison ==="
python TranslationManager.py compare \
  --old "$OLD_EN" \
  --new "$NEW_EN" \
  --plugin-path "$PLUGIN_PATH"

if [ $? -ne 0 ]; then
  echo "Erreur lors de la comparaison"
  exit 1
fi

echo ""
echo "=== Étape 2 : Extraction ==="
python TranslationManager.py extract \
  --plugin-path "$PLUGIN_PATH" \
  --locales "$PLUGIN_PATH"

echo ""
echo "=== Étape 3 : Traduction ==="
echo "Veuillez traduire les fichiers TRANSLATE_xx.txt dans:"
echo "$PLUGIN_PATH/__i18n_tmp__/TranslationManager/<timestamp>/"
read -p "Appuyez sur Entrée quand les traductions sont prêtes..."

echo ""
echo "=== Étape 4 : Injection ==="
python TranslationManager.py inject \
  --plugin-path "$PLUGIN_PATH" \
  --locales "$PLUGIN_PATH"

echo ""
echo "=== Étape 5 : Synchronisation ==="
python TranslationManager.py sync \
  --plugin-path "$PLUGIN_PATH" \
  --locales "$PLUGIN_PATH"

echo ""
echo "✓ Traductions mises à jour avec succès"
echo "  Redémarrez Lightroom pour tester"
```

### Script Python avec API

```python
#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def run_tm_command(command, args):
    """Exécute une commande TranslationManager."""
    cmd = [sys.executable, "TranslationManager.py", command] + args
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Erreur : {result.stderr}")
        return False

    print(result.stdout)
    return True

def main():
    plugin_path = "./plugin.lrplugin"
    old_en = "./backup/TranslatedStrings_en.txt"
    new_en = f"{plugin_path}/__i18n_tmp__/Extractor/latest/TranslatedStrings_en.txt"

    # 1. COMPARE
    print("=== Comparaison ===")
    if not run_tm_command("compare", [
        "--old", old_en,
        "--new", new_en,
        "--plugin-path", plugin_path
    ]):
        return 1

    # 2. EXTRACT
    print("\n=== Extraction ===")
    if not run_tm_command("extract", [
        "--plugin-path", plugin_path,
        "--locales", plugin_path
    ]):
        return 1

    # 3. Attendre traduction (interactif ou automatisé)
    input("\nTraduisez les fichiers TRANSLATE_xx.txt puis appuyez sur Entrée...")

    # 4. INJECT
    print("\n=== Injection ===")
    if not run_tm_command("inject", [
        "--plugin-path", plugin_path,
        "--locales", plugin_path
    ]):
        return 1

    # 5. SYNC
    print("\n=== Synchronisation ===")
    if not run_tm_command("sync", [
        "--plugin-path", plugin_path,
        "--locales", plugin_path
    ]):
        return 1

    print("\n✓ Traductions mises à jour avec succès")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Checklist de mise à jour des traductions

- [ ] Sauvegarder l'ancien `TranslatedStrings_en.txt`
- [ ] Lancer Extractor sur le code modifié
- [ ] Lancer COMPARE (ancien vs nouveau EN)
- [ ] Consulter `CHANGELOG.txt` pour comprendre les changements
- [ ] Lancer EXTRACT pour générer `TRANSLATE_xx.txt`
- [ ] Traduire les fichiers `TRANSLATE_xx.txt`
- [ ] Lancer INJECT pour fusionner les traductions
- [ ] Lancer SYNC pour finaliser et nettoyer
- [ ] Vérifier les fichiers `TranslatedStrings_xx.txt`
- [ ] Commit des modifications dans Git
- [ ] Redémarrer Lightroom et tester
- [ ] Supprimer `__i18n_tmp__/` si désiré (nettoyage)

## Ressources complémentaires

- **SDK Lightroom** : [Adobe Developer Console](https://developer.adobe.com/console)
- **Format de fichiers de traduction** : Format texte simple `"Clé=Valeur"`
- **JSON Python** : [Documentation json](https://docs.python.org/3/library/json.html)
- **difflib Python** : Utilisé en interne pour comparer les fichiers

## Contributions

Pour améliorer TranslationManager, vous pouvez :
- Ajouter de nouveaux formats de sortie (CSV, XLSX, etc.)
- Améliorer la détection des changements (fuzzy matching)
- Ajouter une interface graphique
- Support de nouveaux types de marqueurs

N'hésitez pas à proposer vos modifications !

---

**Développé par Julien MOREAU avec l'aide de Claude (Anthropic)**

Pour toute question ou problème, consultez le README principal ou ouvrez une issue sur le dépôt GitHub.
