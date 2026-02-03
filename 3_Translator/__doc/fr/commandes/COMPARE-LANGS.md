# Commande COMPARE-LANGS

📚 **Retour à la documentation principale** : [Lisez-moi.md](../Lisez-moi.md)

---

## 🎯 Objectif

**COMPARE-LANGS** analyse les différences entre deux fichiers de traduction (`TranslatedStrings_xx.txt`), qu'ils soient de langues différentes ou de versions différentes d'une même langue.

> Cette commande est utile pour l'audit qualité, la vérification de cohérence et le suivi des traductions.

---

## 📥 Entrées / 📤 Sorties

```mermaid
flowchart LR
    subgraph Input["📂 Entrées"]
        I1["TranslatedStrings_xx.txt<br/>(langue 1 ou version 1)"]
        I2["TranslatedStrings_yy.txt<br/>(langue 2 ou version 2)"]
    end

    subgraph Process["⚙️ Comparaison"]
        P["COMPARE-LANGS"]
    end

    subgraph Output["📂 Sorties"]
        O1["COMPARE_LANGS_data.json"]
        O2["COMPARE_LANGS_report.txt"]
    end

    I1 --> P
    I2 --> P
    P --> O1 & O2

    style P fill:#9C27B0,color:#fff
```

| Type | Fichiers |
|------|----------|
| **Entrée** | `TranslatedStrings_xx.txt` (langue 1 ou version 1) |
| **Entrée** | `TranslatedStrings_yy.txt` (langue 2 ou version 2) |
| **Sortie** | `COMPARE_LANGS_data.json` (données structurées) |
| **Sortie** | `COMPARE_LANGS_report.txt` (rapport détaillé lisible) |

---

## 🔄 Fonctionnement

### Algorithme de comparaison

```mermaid
flowchart TD
    A["Charger fichier 1"] --> B["Parser toutes les clés"]
    C["Charger fichier 2"] --> D["Parser toutes les clés"]

    B --> E["Comparateur de langues"]
    D --> E

    E --> F{"Pour chaque clé"}

    F --> G["Clé dans fichier 1 uniquement"]
    G --> H["→ ONLY_IN_LANG1"]

    F --> I["Clé dans fichier 2 uniquement"]
    I --> J["→ ONLY_IN_LANG2"]

    F --> K["Clé dans les deux fichiers"]
    K --> L{"Valeur identique ?"}
    L -->|Oui| M["→ IDENTICAL_VALUES<br/>(⚠️ possibles oublis)"]
    L -->|Non| N["→ DIFFERENT_VALUES"]

    H & J & M & N --> O["Générer statistiques"]
    O --> P["Générer COMPARE_LANGS_data.json"]
    P --> Q["Générer COMPARE_LANGS_report.txt"]

    style P fill:#FFEB3B,color:#000
    style Q fill:#E8F5E9
```

### Catégories d'analyse

| Catégorie | Description | Utilité |
|-----------|-------------|---------|
| **ONLY_IN_LANG1** | Clés présentes seulement dans le fichier 1 | Identifier clés manquantes dans fichier 2 |
| **ONLY_IN_LANG2** | Clés présentes seulement dans le fichier 2 | Identifier clés manquantes dans fichier 1 |
| **IDENTICAL_VALUES** | Même clé avec même valeur dans les deux | Détecter possibles oublis de traduction |
| **DIFFERENT_VALUES** | Même clé avec valeurs différentes | Vérifier les traductions effectuées |

---

## 💡 Cas d'usage

### 1. Vérifier la complétude d'une traduction

```bash
# Comparer FR vs EN pour voir ce qui manque en français
python Translator_main.py compare-langs --lang1 fr --lang2 en --locales ./plugin.lrplugin
```

**Utilité** : Identifier les clés manquantes et les traductions non faites (valeurs identiques à l'anglais).

### 2. Harmoniser deux traductions

```bash
# Comparer FR vs DE pour voir les différences
python Translator_main.py compare-langs --lang1 fr --lang2 de --locales ./plugin.lrplugin
```

**Utilité** : S'assurer que deux langues ont les mêmes clés.

### 3. Suivre l'évolution d'une traduction

```bash
# Comparer ancienne version FR vs nouvelle version FR
python Translator_main.py compare-langs --file1 ./v1/TranslatedStrings_fr.txt --file2 ./v2/TranslatedStrings_fr.txt
```

**Utilité** : Voir les changements apportés à une langue entre deux versions.

### 4. Audit qualité global

```bash
# Comparer chaque langue vs EN pour générer un rapport de complétude
python Translator_main.py compare-langs --lang1 de --lang2 en --locales ./plugin.lrplugin
python Translator_main.py compare-langs --lang1 es --lang2 en --locales ./plugin.lrplugin
python Translator_main.py compare-langs --lang1 it --lang2 en --locales ./plugin.lrplugin
```

**Utilité** : Audit complet de la qualité des traductions de toutes les langues.

---

## 💻 Utilisation

### Mode interactif

```
┌──────────────────────────────────────────────────────────────────┐
│  TRANSLATION MANAGER v7.0                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  2. COMPARE-LANGS                                                │  ◄── Sélectionner
│     Comparer 2 fichiers de langues                               │
│     → FR vs DE, FR vs EN, ancien FR vs nouveau FR...             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

Le menu propose deux modes :

#### Mode 1 : Par codes langue
1. Répertoire contenant les fichiers de langue
2. Code de la première langue (ex: `fr`, `de`, `en`)
3. Code de la seconde langue (ex: `de`, `en`, `es`)

#### Mode 2 : Par chemins complets
1. Chemin complet du premier fichier
2. Chemin complet du second fichier

### Mode CLI

#### Avec codes langue (cherche dans --locales)

```bash
# Comparer FR vs DE
python Translator_main.py compare-langs --lang1 fr --lang2 de --locales ./plugin.lrplugin

# Comparer FR vs EN pour voir ce qui n'est pas traduit
python Translator_main.py compare-langs --lang1 fr --lang2 en --locales ./plugin.lrplugin

# Avec sortie dans __i18n_tmp__
python Translator_main.py compare-langs --lang1 fr --lang2 de --locales ./plugin.lrplugin --plugin-path ./plugin.lrplugin
```

#### Avec chemins de fichiers complets

```bash
# Comparer deux versions d'un même fichier
python Translator_main.py compare-langs --file1 ./v1/TranslatedStrings_fr.txt --file2 ./v2/TranslatedStrings_fr.txt

# Comparer deux fichiers de langues différentes
python Translator_main.py compare-langs --file1 ./Locales/TranslatedStrings_fr.txt --file2 ./Locales/TranslatedStrings_de.txt

# Sortie personnalisée
python Translator_main.py compare-langs --file1 ./fr.txt --file2 ./de.txt --output ./my_output/
```

### Options CLI

| Option | Description | Requis |
|--------|-------------|--------|
| `--lang1` | Code langue 1 (ex: fr) - cherche dans --locales | Conditionnel |
| `--lang2` | Code langue 2 (ex: de) - cherche dans --locales | Conditionnel |
| `--locales` | Répertoire des traductions | Requis avec --lang1/--lang2 |
| `--file1` | Premier fichier (ou répertoire) | Conditionnel |
| `--file2` | Second fichier (ou répertoire) | Conditionnel |
| `--plugin-path` | Sortie dans `__i18n_tmp__/3_Translator/` | ❌ Non |
| `--output` | Répertoire de sortie personnalisé | ❌ Non |

> **Note** : Spécifiez soit `--lang1` + `--lang2` + `--locales`, soit `--file1` + `--file2`.

---

## 📋 Exemple de session

### Mode interactif - Comparer FR vs EN

```
COMPARE-LANGS: Comparer deux fichiers de traduction
══════════════════════════════════════════════════════════════════

Vous pouvez comparer:
  • Deux langues différentes (ex: FR vs DE)
  • Deux versions d'une même langue (ex: ancien FR vs nouveau FR)
  • Une langue vs EN (pour voir ce qui n'est pas traduit)

Mode de sélection:
  1. Par codes langue (ex: fr, de) - cherche dans un répertoire
  2. Par chemins de fichiers complets

  Votre choix (1-2): 1

Répertoire contenant les fichiers de langue:
  (ex: ./Locales ou chemin vers le plugin)
  > ./plugin.lrplugin

[INFO] Langues disponibles: de, en, es, fr, it

Code de la première langue (ex: fr, en, de):
  > fr

Code de la seconde langue (ex: fr, en, de):
  > en

[INFO] Comparaison en cours...

══════════════════════════════════════════════════════════════════
  RÉSUMÉ DE LA COMPARAISON
══════════════════════════════════════════════════════════════════
  Langue 1: FR  (142 clés)
  Langue 2: EN  (148 clés)

  Total de clés uniques       :  148
  Clés dans les deux langues  :  140
  Seulement dans FR           :    2
  Seulement dans EN           :    8

  Valeurs identiques          :   12
  Valeurs différentes         :  128

  ⚠️  12 traduction(s) identique(s) à EN détectée(s)!

✓ Fichiers générés dans: __i18n_tmp__/3_Translator/20260202_153000/
  • COMPARE_LANGS_report.txt
  • COMPARE_LANGS_data.json
```

### Mode CLI - Comparer deux versions

```bash
$ python Translator_main.py compare-langs --file1 ./v1/TranslatedStrings_fr.txt --file2 ./v2/TranslatedStrings_fr.txt

[INFO] Comparaison de langues...

============================================================
RÉSUMÉ - COMPARAISON DE LANGUES
============================================================
Langue 1: FR (135 clés)
Langue 2: FR (142 clés)

Clés totales uniques    :  145
Clés dans les deux      :  132
Seulement dans FR       :    3
Seulement dans FR       :    7

Valeurs identiques      :  120
Valeurs différentes     :   12

✓ Fichiers générés dans: compare_langs_20260202_153045/
```

---

## 📁 Format des fichiers générés

### COMPARE_LANGS_data.json

```json
{
  "generated": "2026-02-02T15:30:00",
  "file1": "/path/to/TranslatedStrings_fr.txt",
  "file2": "/path/to/TranslatedStrings_en.txt",
  "lang1_name": "FR",
  "lang2_name": "EN",
  "statistics": {
    "total_unique_keys": 148,
    "keys_in_lang1": 142,
    "keys_in_lang2": 148,
    "keys_in_both": 140,
    "only_lang1": 2,
    "only_lang2": 8,
    "identical_values_count": 12,
    "different_values_count": 128,
    "coverage_lang1_pct": 95.95,
    "coverage_lang2_pct": 100.0
  },
  "only_in_lang1": [
    "$$$/Plugin/OldFeature/Title"
  ],
  "only_in_lang2": [
    "$$$/Plugin/NewFeature/Title",
    "$$$/Plugin/NewFeature/Description"
  ],
  "identical_values": {
    "$$$/Plugin/Dialog/OK": "OK",
    "$$$/Plugin/Settings/API": "API"
  },
  "different_values": [
    "$$$/Plugin/Dialog/Cancel",
    "$$$/Plugin/Settings/Help"
  ]
}
```

### COMPARE_LANGS_report.txt

```
================================================================================
RAPPORT DE COMPARAISON DE LANGUES
================================================================================

Date: 2026-02-02 15:30:00
Langue 1: FR
Langue 2: EN
Fichier 1: /path/to/TranslatedStrings_fr.txt
Fichier 2: /path/to/TranslatedStrings_en.txt

--------------------------------------------------------------------------------
STATISTIQUES GLOBALES
--------------------------------------------------------------------------------
  Total de clés uniques            :  148
  Clés dans FR                     :  142  ( 95.95%)
  Clés dans EN                     :  148  (100.00%)
  Clés présentes dans les deux     :  140
  Clés seulement dans FR           :    2
  Clés seulement dans EN           :    8

--------------------------------------------------------------------------------
ANALYSE DES CLÉS COMMUNES
--------------------------------------------------------------------------------
  Valeurs identiques               :   12
  Valeurs différentes              :  128

================================================================================
CLÉS PRÉSENTES SEULEMENT DANS EN (8)
Ces clés existent dans EN mais sont absentes de FR.
================================================================================

  [ONLY-EN] $$$/Plugin/NewFeature/Title
        EN: New Feature

  [ONLY-EN] $$$/Plugin/NewFeature/Description
        EN: This is a new feature

================================================================================
CLÉS AVEC VALEURS IDENTIQUES (12)
Ces clés existent dans les deux langues avec la même valeur.
⚠️  ATTENTION: Valeurs identiques à l'anglais = possibles oublis de traduction!
================================================================================

  [IDENTICAL] $$$/Plugin/Dialog/OK
        Valeur commune: OK

  [IDENTICAL] $$$/Plugin/Settings/API
        Valeur commune: API

================================================================================
CLÉS AVEC VALEURS DIFFÉRENTES (128)
Ces clés existent dans les deux langues avec des valeurs différentes.
(Affichage des 20 premières différences)
================================================================================

  [DIFFERENT] $$$/Plugin/Dialog/Cancel
        FR: Annuler
        EN: Cancel

  [DIFFERENT] $$$/Plugin/Settings/Help
        FR: Aide
        EN: Help

  ... et 108 autres différences
  (voir COMPARE_LANGS_data.json pour la liste complète)

================================================================================
RECOMMANDATIONS
================================================================================
• 8 clé(s) manquante(s) dans FR
  → Ajouter ces traductions dans FR

⚠️  12 traduction(s) identique(s) à l'anglais détectée(s)!
  → Vérifier si ces clés ont bien été traduites
```

---

## 🎯 Interprétation des résultats

### Valeurs identiques avec EN

Si vous comparez une langue avec l'anglais et trouvez des **valeurs identiques**, ce sont probablement :

| Type | Exemple | Action |
|------|---------|--------|
| **Non traduit** | `"$$$/Menu/File=File"` en FR | ❌ À traduire |
| **Nom propre** | `"$$$/Plugin/Name=Adobe Lightroom"` | ✅ Normal |
| **Terme technique** | `"$$$/Settings/API=API"` | ✅ Normal |
| **Acronyme** | `"$$$/Format/JPG=JPG"` | ✅ Normal |

> **Conseil** : Vérifiez manuellement chaque valeur identique pour confirmer qu'il ne s'agit pas d'un oubli.

### Clés manquantes

| Situation | Cause probable | Action |
|-----------|----------------|--------|
| Clés dans EN mais pas dans FR | Nouvelles clés non traduites | Ajouter les traductions |
| Clés dans FR mais pas dans EN | Clés obsolètes | Supprimer si confirmé obsolète |
| Clés dans v1 mais pas v2 | Refactoring du code | Vérifier le code source |

### Statistiques de couverture

```
coverage_lang1_pct: 95.95%  → FR a 95.95% des clés totales
coverage_lang2_pct: 100.0%  → EN a 100% des clés totales (référence)
```

**Interprétation** : Le français manque ~4% de clés par rapport à l'anglais.

---

## 🔗 Commandes liées

| Commande | Lien | Relation |
|----------|------|----------|
| **COMPARE** | [COMPARE.md](COMPARE.md) | Compare versions EN uniquement |
| **SYNC** | [SYNC.md](SYNC.md) | Synchronise après avoir identifié les manques |
| **AUTO-SYNC** | [AUTOSYNC.md](AUTOSYNC.md) | Alternative automatique |

---

## 📚 Ressources

| Élément | Information |
|---------|-------------|
| Module source | `TM_compare_langs.py` |
| Classe principale | `LanguageComparator` |
| Fonction principale | `run_compare_langs()` |
| Menu interactif | `menu_compare_langs()` |

---

## 💡 Astuces

### Script batch pour audit complet

Créez un script pour comparer toutes les langues vs EN :

```bash
#!/bin/bash
# audit_all_langs.sh

LOCALES="./plugin.lrplugin"

for lang in de es fr it; do
    echo "Comparaison de $lang vs EN..."
    python Translator_main.py compare-langs \
        --lang1 $lang \
        --lang2 en \
        --locales $LOCALES \
        --plugin-path $LOCALES
done

echo "✓ Audit terminé. Vérifiez __i18n_tmp__/3_Translator/"
```

### Rechercher les traductions manquantes

Dans `COMPARE_LANGS_report.txt`, cherchez :
- Section **"CLÉS PRÉSENTES SEULEMENT DANS EN"** → à traduire
- Section **"CLÉS AVEC VALEURS IDENTIQUES"** (si comparé avec EN) → possibles oublis

---

| 📜 | Traçabilité |  |  |
|--|--|--|--|
| **Nom** | *COMPARE-LANGS.md* | **Version** | 1.0 |
| **Type** | Guide utilisateur - Avancé | **Langue** | FR - *[EN](../../en/commands/COMPARE-LANGS.md)* |
| **Projet GitHub** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-02 |
| **Licence** | Open source | | |
