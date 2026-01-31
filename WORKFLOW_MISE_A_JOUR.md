# Workflow de Mise à Jour des Traductions

## Cas d'usage : Plugin existant avec traductions à mettre à jour

Vous avez développé un plugin Lightroom qui possède déjà des fichiers de traduction (`TranslatedStrings_en.txt`, `TranslatedStrings_fr.txt`, etc.), et vous venez de modifier le code du plugin (nouvelles fonctionnalités, textes modifiés).

**Question** : Comment mettre à jour les traductions et permettre aux traducteurs de contribuer ?

Ce document présente **deux workflows disponibles** :
1. **Workflow classique** ✅ : Les traducteurs éditent directement les fichiers `.txt` (pour traducteurs techniques)
2. **Workflow moderne (WebBridge)** ✅ : Les traducteurs utilisent un outil web visuel (RECOMMANDÉ)

---

## 📋 Situation de départ

```
monPlugin.lrplugin/
├── Info.lua
├── MonModule.lua                    ← Code modifié (nouvelles chaînes)
├── TranslatedStrings_en.txt         ← Ancien (270 clés)
├── TranslatedStrings_fr.txt         ← Ancien (268 clés)
└── TranslatedStrings_de.txt         ← Ancien (250 clés)
```

**Modifications apportées au code** :
- Ajout de 13 nouvelles chaînes (nouvelles fonctionnalités)
- Modification de 2 chaînes existantes (texte amélioré)
- Suppression de 9 chaînes obsolètes (fonctionnalités retirées)

---

# Workflow 1 : Édition Directe (Classique) ✅

## Vue d'ensemble

Les traducteurs éditent directement les fichiers `TranslatedStrings_xx.txt` après que vous ayez identifié les changements.

### Avantages
- ✅ Simple et direct
- ✅ Pas d'outil externe requis
- ✅ Contrôle total sur le format
- ✅ **Disponible maintenant**

### Inconvénients
- ❌ Format propriétaire peu convivial
- ❌ Risque d'erreurs de formatage
- ❌ Difficile de voir les changements
- ❌ Pas de contexte visuel

---

## Étapes détaillées

### Étape 1 : Extraire les nouvelles chaînes

**Outil** : `1_Extractor`

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [1] Extractor
```

**Paramètres** :
- Plugin path : `D:\mon\plugin.lrplugin`
- Prefix LOC : `$$$/MonPlugin`
- Langue : `en`

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── Extractor/
        └── 20260131_150000/
            ├── TranslatedStrings_en.txt     ← Nouveau (283 clés)
            ├── spacing_metadata.json
            ├── replacements.json
            └── extraction_report.txt
```

**Sortie console** :
```
✓ Extraction réussie !

Statistiques :
- Fichiers analysés : 15
- Chaînes extraites : 283
- Clés LOC générées : 283
- Clés avec espaces/suffixes : 85

Fichiers générés dans : __i18n_tmp__/Extractor/20260131_150000/
```

---

### Étape 2 : Comparer avec la version précédente

**Outil** : `3_Translation_manager` → **COMPARE**

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [3] Translation
# Sélectionner [1] COMPARE
```

**Sélection des fichiers** :
```
Version ancienne : __i18n_tmp__/Extractor/20260129_143000/TranslatedStrings_en.txt
Version nouvelle : __i18n_tmp__/Extractor/20260131_150000/TranslatedStrings_en.txt
```

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── TranslationManager/
        └── 20260131_150500/
            ├── UPDATE_en.json               ← Diff détaillé
            └── CHANGELOG.txt                ← Résumé lisible
```

**Contenu de UPDATE_en.json** :
```json
{
  "summary": {
    "added": 13,
    "changed": 2,
    "deleted": 9,
    "unchanged": 270
  },
  "added": {
    "$$$/MonPlugin/NewFeature/Title": "New Feature Settings",
    "$$$/MonPlugin/NewFeature/Description": "Configure the new feature",
    ...
  },
  "changed": {
    "$$$/MonPlugin/Settings/Label": {
      "old": "Settings Panel",
      "new": "Plugin Settings"
    },
    ...
  },
  "deleted": [
    "$$$/MonPlugin/OldFeature/Removed1",
    ...
  ]
}
```

**Contenu de CHANGELOG.txt** :
```
═══════════════════════════════════════════════════════════
CHANGELOG - Comparaison des traductions
═══════════════════════════════════════════════════════════

13 clés AJOUTÉES :
  $$$/MonPlugin/NewFeature/Title
  $$$/MonPlugin/NewFeature/Description
  ...

2 clés MODIFIÉES :
  $$$/MonPlugin/Settings/Label
    AVANT : "Settings Panel"
    APRÈS : "Plugin Settings"
  ...

9 clés SUPPRIMÉES :
  $$$/MonPlugin/OldFeature/Removed1
  ...
```

---

### Étape 3 : Générer les mini-fichiers de traduction

**Outil** : `3_Translation_manager` → **EXTRACT**

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [3] Translation
# Sélectionner [2] EXTRACT
```

**Paramètres** :
- Fichier UPDATE_en.json : `__i18n_tmp__/TranslationManager/20260131_150500/UPDATE_en.json`
- Fichiers TranslatedStrings existants :
  - `TranslatedStrings_fr.txt`
  - `TranslatedStrings_de.txt`

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── TranslationManager/
        └── 20260131_151000/
            ├── TRANSLATE_fr.txt             ← À traduire en français
            └── TRANSLATE_de.txt             ← À traduire en allemand
```

**Contenu de TRANSLATE_fr.txt** :
```
-- =============================================================================
-- Traductions à ajouter - FR
-- Générées : 2026-01-31 15:10:00
-- Clés à traduire : 13
-- =============================================================================

-- INSTRUCTIONS :
-- 1. Traduisez uniquement les valeurs (après le =)
-- 2. NE PAS traduire : %s, %d, \n, \t, etc.
-- 3. Préservez les espaces autour du texte

-- NewFeature
"$$$/MonPlugin/NewFeature/Title=New Feature Settings"
"$$$/MonPlugin/NewFeature/Description=Configure the new feature"
"$$$/MonPlugin/NewFeature/Enable=Enable new feature"
...

-- Dialogs
"$$$/MonPlugin/Dialogs/Confirm=Are you sure?"
...
```

**Sortie console** :
```
✓ Extraction réussie !

Fichiers générés :
- TRANSLATE_fr.txt : 13 clés à traduire
- TRANSLATE_de.txt : 13 clés à traduire

Envoyez ces fichiers à vos traducteurs.
```

---

### Étape 4 : Envoyer aux traducteurs

**Action** : Envoyer les fichiers `TRANSLATE_xx.txt` aux traducteurs

**Méthode** :
- Email
- Google Drive / Dropbox
- GitHub issue
- Slack / Discord

**Instructions pour le traducteur** :

> Bonjour,
>
> J'ai ajouté de nouvelles fonctionnalités au plugin.
> Pouvez-vous traduire les 13 nouvelles chaînes dans le fichier ci-joint ?
>
> **Fichier** : `TRANSLATE_fr.txt`
>
> **Instructions** :
> 1. Traduisez uniquement le texte après le `=`
> 2. Ne modifiez PAS les clés (avant le `=`)
> 3. Ne traduisez PAS les placeholders : `%s`, `%d`, `\n`, etc.
> 4. Préservez les espaces autour du texte
>
> Exemple :
> ```
> AVANT : "$$$/MonPlugin/NewFeature/Title=New Feature Settings"
> APRÈS : "$$$/MonPlugin/NewFeature/Title=Paramètres de la nouvelle fonctionnalité"
> ```
>
> Merci !

---

### Étape 5 : Réception des traductions

**Le traducteur renvoie** : `TRANSLATE_fr.txt` (complété)

**Contenu du fichier retourné** :
```
-- NewFeature
"$$$/MonPlugin/NewFeature/Title=Paramètres de la nouvelle fonctionnalité"
"$$$/MonPlugin/NewFeature/Description=Configurer la nouvelle fonctionnalité"
"$$$/MonPlugin/NewFeature/Enable=Activer la nouvelle fonctionnalité"
...

-- Dialogs
"$$$/MonPlugin/Dialogs/Confirm=Êtes-vous sûr ?"
...
```

---

### Étape 6 : Injecter les traductions

**Outil** : `3_Translation_manager` → **INJECT**

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [3] Translation
# Sélectionner [3] INJECT
```

**Paramètres** :
- Fichier TRANSLATE_fr.txt : `__i18n_tmp__/TranslationManager/20260131_151000/TRANSLATE_fr.txt` (complété)
- Fichier TranslatedStrings_fr.txt existant : `TranslatedStrings_fr.txt`

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── TranslationManager/
        └── 20260131_152000/
            └── TranslatedStrings_fr.txt     ← Fusionné (281 clés)
```

**Sortie console** :
```
✓ Injection réussie !

Fusion effectuée :
- Anciennes traductions : 268 clés
- Nouvelles traductions : 13 clés
- Total après fusion : 281 clés

Fichier généré : __i18n_tmp__/TranslationManager/20260131_152000/TranslatedStrings_fr.txt
```

---

### Étape 7 : Synchroniser tous les fichiers de langues

**Outil** : `3_Translation_manager` → **SYNC**

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [3] Translation
# Sélectionner [4] SYNC
```

**Paramètres** :
- Référence EN : `__i18n_tmp__/Extractor/20260131_150000/TranslatedStrings_en.txt` (nouvelle version)
- Fichiers existants :
  - `TranslatedStrings_fr.txt` (fusionné à l'étape 6)
  - `TranslatedStrings_de.txt` (ancien)

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── TranslationManager/
        └── 20260131_152500/
            ├── TranslatedStrings_en.txt     ← 283 clés (à jour)
            ├── TranslatedStrings_fr.txt     ← 283 clés (281 traduites, 2 [NEW])
            └── TranslatedStrings_de.txt     ← 283 clés (250 traduites, 33 [NEW])
```

**Contenu de TranslatedStrings_fr.txt** :
```
-- NewFeature
"$$$/MonPlugin/NewFeature/Title=Paramètres de la nouvelle fonctionnalité"
"$$$/MonPlugin/NewFeature/Description=Configurer la nouvelle fonctionnalité"
...

-- Clés non encore traduites (utiliseront valeur EN)
"$$$/MonPlugin/Settings/Label=[NEW] Plugin Settings"
```

**Sortie console** :
```
✓ Synchronisation réussie !

[EN] Anglais (référence)
  - 283 clés (100%)

[FR] Français
  - 281 clés traduites (99.3%)
  - 2 clés manquantes [NEW]
  - 9 clés obsolètes supprimées

[DE] Allemand
  - 250 clés traduites (88.3%)
  - 33 clés manquantes [NEW]
  - 9 clés obsolètes supprimées
```

---

### Étape 8 : Copier dans le plugin

**Action manuelle** :

```bash
# Copier les fichiers finaux dans le plugin
cp __i18n_tmp__/TranslationManager/20260131_152500/TranslatedStrings_*.txt .

# Vérifier
ls -l TranslatedStrings_*.txt
```

**Résultat** :
```
monPlugin.lrplugin/
├── TranslatedStrings_en.txt         ← Mis à jour (283 clés)
├── TranslatedStrings_fr.txt         ← Mis à jour (283 clés, 99.3% traduit)
└── TranslatedStrings_de.txt         ← Mis à jour (283 clés, 88.3% traduit)
```

---

### Étape 9 : Tester dans Lightroom

**Action** :
1. Recharger le plugin dans Lightroom
2. Changer la langue du système en français
3. Vérifier que les nouvelles chaînes s'affichent correctement
4. Vérifier que les clés `[NEW]` utilisent bien la valeur anglaise par défaut

---

### Étape 10 : (Optionnel) Appliquer les LOC dans le code

Si vous avez modifié le code et ajouté de nouvelles chaînes hardcodées :

**Outil** : `2_Applicator`

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [2] Applicator
```

**Paramètres** :
- Plugin path : `D:\mon\plugin.lrplugin`
- Extraction dir : `__i18n_tmp__/Extractor/20260131_150000/`

**Résultat** :
- Les chaînes hardcodées sont remplacées par des appels `LOC "$$$/..."`
- Backups créés dans `__i18n_tmp__/Applicator/20260131_153000/backups/`

---

## Résumé Workflow 1 (Classique)

```
┌─────────────────────────────────────────────────────────────┐
│ DÉVELOPPEUR                                                 │
├─────────────────────────────────────────────────────────────┤
│ 1. Modifier le code (nouvelles fonctionnalités)             │
│ 2. Extractor → TranslatedStrings_en.txt (nouveau)           │
│ 3. COMPARE → UPDATE_en.json (diff)                          │
│ 4. EXTRACT → TRANSLATE_fr.txt, TRANSLATE_de.txt             │
│ 5. Envoyer fichiers TRANSLATE_xx.txt aux traducteurs        │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ TRADUCTEUR                                                  │
├─────────────────────────────────────────────────────────────┤
│ 6. Éditer TRANSLATE_fr.txt (ajouter traductions)            │
│ 7. Renvoyer TRANSLATE_fr.txt au développeur                 │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ DÉVELOPPEUR                                                 │
├─────────────────────────────────────────────────────────────┤
│ 8. INJECT → TranslatedStrings_fr.txt (fusion)               │
│ 9. SYNC → Tous fichiers mis à jour et synchronisés          │
│ 10. Copier dans plugin.lrplugin/                            │
│ 11. Tester dans Lightroom                                   │
│ 12. (Optionnel) Applicator → Remplacer hardcodés par LOC    │
└─────────────────────────────────────────────────────────────┘
```

**Durée estimée** : 15-30 minutes (hors traduction)

---

---

# Workflow 2 : WebBridge (Moderne) ✅ DISPONIBLE

> ✅ **MODULE OPÉRATIONNEL** : Le module **4_WebBridge** est **pleinement fonctionnel** et prêt à l'emploi.
>
> **Statut** : Complet et testé
>
> **Disponibilité** : Maintenant
>
> **Recommandation** : **Utilisez ce workflow pour une meilleure expérience traducteur**

## Vue d'ensemble

Les traducteurs utilisent un outil web moderne ([quicki18n.studio](https://www.quicki18n.studio/)) pour traduire visuellement dans leur navigateur. Le développeur n'a qu'à exporter/importer un fichier JSON.

### Avantages
- ✅ Interface visuelle intuitive pour les traducteurs
- ✅ Édition multi-langues côte-à-côte
- ✅ Contexte visible pour chaque clé (fichier:ligne)
- ✅ Validation automatique des placeholders (%s, %d, \n)
- ✅ Pas de risque d'erreur de formatage
- ✅ 100% local dans le navigateur (pas de serveur)
- ✅ Traducteurs non-techniques peuvent contribuer facilement
- ✅ Workflow beaucoup plus rapide que le Workflow 1

### Inconvénients
- ⚠️ Nécessite conversion .txt ↔ .json (mais automatique)
- ⚠️ Dépendance à un outil externe (mais gratuit et browser-based)

---

## Étapes détaillées

Le workflow WebBridge est **beaucoup plus simple** que le Workflow 1 car il automatise toute la gestion des traductions.

### Étape 1 : Extraire les chaînes du code

**Outil** : `1_Extractor`

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [1] Extractor
```

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── 1_Extractor/
        └── 20260131_150000/
            ├── TranslatedStrings_en.txt     ← Fichier de référence EN
            ├── spacing_metadata.json
            ├── replacements.json
            └── extraction_report.txt
```

---

### Étape 2 : Exporter vers format JSON i18n

**Outil** : `4_WebBridge` → **EXPORT**

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [8] Export Web (WebBridge)
```

**Configuration** :
- Dossier Extractor : `__i18n_tmp__/1_Extractor/20260131_150000/` (auto-détecté)
- Langues : Toutes les langues détectées (ou spécifier : `en, fr, de`)
- **Option [4]** : Inclure contexte (fichier:ligne) → **Oui** (recommandé)
- **Option [5]** : Inclure champ 'default' (texte EN) → **Non** (par défaut, suffisant)

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── 4_WebBridge/
        └── 20260131_154000/
            └── translations.json       ← Fichier JSON prêt pour le traducteur
```

**Sortie console** :
```
✓ Export réussi !

Fichier créé : __i18n_tmp__/4_WebBridge/20260131_154000/translations.json

Statistiques :
- Clés exportées : 278
- Langues : en
- Clés avec contexte : 278

Instructions :
1. Envoyez translations.json à votre traducteur
2. Le traducteur utilisera https://www.quicki18n.studio/
3. Une fois traduit, récupérez le fichier et lancez l'import
```

**Exemple du fichier JSON généré** (extrait de PiwigoPublish) :
```json
{
  "_meta": {
    "version": "1.0",
    "generated": "2026-01-31T16:43:18",
    "plugin_name": "piwigoPublish.lrplugin",
    "prefix": "$$$/Piwigo",
    "source_extraction": "Extractor/20260130_181147",
    "total_keys": 278,
    "languages": ["en"],
    "translator_notes": "DO NOT translate: %s, %d, \\n. PRESERVE spaces around text.",
    "webbridge_version": "1.0.0"
  },
  "translations": {
    "en": {
      "API": {
        "CannotLogPiwigo": {
          "text": "Cannot log in to Piwigo",
          "context": "PiwigoAPI.lua:1352"
        },
        "AlbumsCreatedPiwigoS": {
          "text": "Albums created on Piwigo: %s, Piwigo links updated: %s",
          "context": "PiwigoAPI.lua:1046"
        }
      }
    }
  }
}
```

**Points clés** :
- `context` : Indique où la chaîne est utilisée dans le code (fichier:ligne)
- Placeholders (`%s`, `%d`, `\n`) : À préserver absolument lors de la traduction
- Organisation par catégories (API, Dialogs, etc.)

---

### Étape 3 : Envoyer le fichier JSON au traducteur

**Action développeur** : Envoyer `translations.json` au traducteur (email, GitHub, Dropbox, etc.)

**Instructions à fournir au traducteur** :

> Bonjour,
>
> Voici le fichier de traduction du plugin : **translations.json**
>
> **Comment traduire** :
>
> 1. Ouvrez https://www.quicki18n.studio/ dans votre navigateur
> 2. Cliquez sur "**Import JSON**" et sélectionnez `translations.json`
> 3. Sélectionnez la langue **FR** (ou votre langue)
> 4. Traduisez les textes dans la colonne de droite
>    - La colonne EN à gauche montre le texte original
>    - Le contexte (fichier:ligne) aide à comprendre l'usage
> 5. **Important** : Ne traduisez PAS les codes spéciaux : `%s`, `%d`, `\n`
> 6. Une fois terminé, cliquez sur "**Export JSON**"
> 7. Renvoyez-moi le fichier `translations.json`
>
> Merci !

---

### Étape 4 : Le traducteur traduit visuellement

**Côté traducteur** (utilise quicki18n.studio) :

1. Ouvre https://www.quicki18n.studio/ dans le navigateur
2. Importe `translations.json`
3. Sélectionne la langue FR (ou autre)
4. Voit l'interface visuelle :
   - Texte EN original à gauche (référence)
   - Champ de traduction FR à droite (éditable)
   - Contexte visible : `PiwigoAPI.lua:1352`
5. Traduit clé par clé avec validation automatique
6. Exporte le JSON traduit
7. Renvoie `translations.json` au développeur

**Important** : Le traducteur n'installe AUCUN outil, tout se passe dans le navigateur.

---

### Étape 5 : Importer le fichier JSON traduit

**Outil développeur** : `4_WebBridge` → **IMPORT**

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [9] Import Web (WebBridge)
```

**Configuration** :
- Fichier JSON : `translations.json` (celui renvoyé par le traducteur)
- Plugin : `D:\mon\plugin.lrplugin`
- Langues : Toutes (ou spécifier : `en, fr`)
- Validation : **Oui** (recommandé)

**Validation automatique** :
```
═══════════════════════════════════════════════════════════
RAPPORT DE VALIDATION
═══════════════════════════════════════════════════════════

✓ Structure JSON valide
✓ Langue de référence (en) présente
✓ 278 clés validées

[FR] Statut :
  ✓ 278 clés traduites
  ✓ Placeholders préservés (%s, %d, \n)

═══════════════════════════════════════════════════════════
AUCUNE ERREUR CRITIQUE - Import autorisé
═══════════════════════════════════════════════════════════
```

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── 4_WebBridge/
        └── 20260131_155000/
            ├── TranslatedStrings_en.txt     ← Généré (278 clés)
            ├── TranslatedStrings_fr.txt     ← Généré (278 clés)
            └── import_report.txt            ← Rapport détaillé
```

---

### Étape 6 : Copier dans le plugin et tester

**Action développeur** :

```bash
# Copier les fichiers finaux dans le plugin
cd D:\mon\plugin.lrplugin
cp __i18n_tmp__/4_WebBridge/20260131_155000/TranslatedStrings_*.txt .
```

**Puis tester dans Lightroom** :
1. Recharger le plugin (ou redémarrer Lightroom)
2. Changer la langue du système en français
3. Vérifier que les traductions s'affichent correctement
4. Tester toutes les fonctionnalités traduites

---

## Résumé Workflow 2 (WebBridge) ✅

```
┌─────────────────────────────────────────────────────────────┐
│ DÉVELOPPEUR                                                 │
├─────────────────────────────────────────────────────────────┤
│ 1. Extraire → TranslatedStrings_en.txt                      │
│ 2. WebBridge EXPORT → translations.json                     │
│ 3. Envoyer translations.json au traducteur                  │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ TRADUCTEUR (pas d'outil à installer)                        │
├─────────────────────────────────────────────────────────────┤
│ 4. Ouvrir https://www.quicki18n.studio/                    │
│ 5. Importer translations.json                               │
│ 6. Traduire visuellement dans le navigateur                 │
│    ✓ Contexte visible (fichier:ligne)                       │
│    ✓ Validation automatique                                 │
│    ✓ Interface intuitive                                    │
│ 7. Exporter translations.json                               │
│ 8. Renvoyer au développeur                                  │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ DÉVELOPPEUR                                                 │
├─────────────────────────────────────────────────────────────┤
│ 9. WebBridge IMPORT → Validation automatique                │
│ 10. TranslatedStrings_xx.txt générés automatiquement        │
│ 11. Copier dans plugin.lrplugin/                            │
│ 12. Tester dans Lightroom                                   │
└─────────────────────────────────────────────────────────────┘
```

**Durée développeur** : 5-10 minutes (hors traduction) - **Beaucoup plus rapide que Workflow 1**

**Avantage clé** : Aucun outil complexe pour le traducteur, juste un navigateur web.

---

---

# Comparaison des Workflows

## Tableau comparatif

| Critère | Workflow 1 (Classique) ✅ | Workflow 2 (WebBridge) ✅ |
|---------|---------------------------|---------------------------|
| **Disponibilité** | ✅ Disponible | ✅ Disponible |
| **Interface traducteur** | Fichier .txt brut | Interface web visuelle |
| **Convivialité** | ⚠️ Moyen (format propriétaire) | ✅ Excellent (éditeur moderne) |
| **Risque d'erreur** | ⚠️ Moyen (erreurs de formatage possibles) | ✅ Faible (validation automatique) |
| **Contexte visible** | ❌ Non (sauf commentaires manuels) | ✅ Oui (fichier:ligne automatique) |
| **Édition multi-langues** | ❌ Non (1 fichier à la fois) | ✅ Oui (côte-à-côte) |
| **Validation temps réel** | ❌ Non | ✅ Oui (placeholders, formatage) |
| **Étapes développeur** | 10 étapes | 6 étapes (plus simple) |
| **Outils requis traducteur** | Éditeur texte + connaissance format | Navigateur web uniquement |
| **Dépendance externe** | ❌ Aucune | ⚠️ quicki18n.studio (gratuit, local) |
| **Courbe d'apprentissage** | ⚠️ Moyenne (format technique) | ✅ Faible (interface intuitive) |
| **Préservation métadonnées** | ✅ Oui (via INJECT + SYNC) | ✅ Oui (automatique) |
| **Validation placeholders** | ⚠️ Manuelle (risque d'oubli) | ✅ Automatique (garantie) |
| **Temps développeur** | 15-30 min | 5-10 min (**beaucoup plus rapide**) |

---

## Recommandations

### Utilisez le Workflow 2 (WebBridge) ✅ RECOMMANDÉ

**Le Workflow 2 est l'option recommandée pour la plupart des cas.**

Idéal pour :
- ✅ **Traducteurs non-techniques** (interface visuelle simple)
- ✅ **Plusieurs langues à gérer** (édition côte-à-côte)
- ✅ **Minimiser les erreurs** (validation automatique)
- ✅ **Contexte nécessaire** (fichier:ligne visible)
- ✅ **Mises à jour fréquentes** (workflow rapide)
- ✅ **Collaboration avec traducteurs externes** (fichier JSON facile à échanger)

### Utilisez le Workflow 1 (Classique) ✅ ALTERNATIF

**Le Workflow 1 reste disponible pour des cas spécifiques.**

Idéal pour :
- ✅ **Traducteurs très techniques** (à l'aise avec formats propriétaires)
- ✅ **Une seule langue** (moins d'avantages avec WebBridge)
- ✅ **Aucun outil externe souhaité** (workflow 100% interne)
- ✅ **Petites corrections** (modifier 1-2 clés directement dans le .txt)
- ✅ **Workflow déjà établi** (équipe habituée au format .txt)

---

## Workflow hybride ✅ DISPONIBLE

Vous pouvez **combiner les deux approches** selon la situation :

1. **Traductions complètes / mises à jour majeures** → Workflow 2 (WebBridge)
   - Traduction de 10+ nouvelles clés
   - Interface visuelle aide à comprendre le contexte
   - Validation automatique garantit la qualité
   - **Exemple** : Nouvelle fonctionnalité avec 50 chaînes à traduire

2. **Petites corrections rapides** → Édition directe du .txt
   - Corriger 1-3 clés rapidement
   - Pas besoin d'export/import pour un typo
   - **Exemple** : Corriger "Se connecte" → "Se connecter"

3. **Première traduction complète d'un plugin** → Workflow 2 (WebBridge)
   - Traduction de 200+ clés depuis zéro
   - Interface facilite la traduction de masse
   - **Exemple** : Traduire tout PiwigoPublish en français (278 clés)

---

# Cas d'usage spécifiques

## Cas 1 : Première traduction complète d'un plugin

**Situation** : Plugin avec 278 clés en anglais (ex: PiwigoPublish), aucune traduction existante.

**Workflow recommandé** : **Workflow 2 (WebBridge)** ✅

**Raison** : Interface visuelle + contexte facilitent grandement la traduction de masse pour des traducteurs non-techniques.

**Étapes** :
1. Extractor → TranslatedStrings_en.txt (278 clés)
2. WebBridge Export → translations.json
3. Envoyer à traducteur → quicki18n.studio
4. WebBridge Import → TranslatedStrings_fr.txt généré
5. Copier dans plugin → Tester

**Durée** : 5-10 minutes développeur + temps traduction

---

## Cas 2 : Correction d'une typo dans une traduction

**Situation** : 1 clé a une faute de frappe en français.

**Workflow recommandé** : **Édition directe** ✅

**Raison** : Trop simple pour nécessiter le workflow complet.

**Étapes** :
1. Ouvrir `TranslatedStrings_fr.txt`
2. Chercher la clé (Ctrl+F)
3. Corriger la valeur
4. Sauvegarder
5. Tester dans Lightroom

---

## Cas 3 : Ajout d'une petite fonctionnalité (5 nouvelles clés)

**Situation** : Nouvelle fonctionnalité avec 5 nouvelles chaînes.

**Workflow recommandé** : **Workflow 1 (Classique)** ✅

**Raison** : Nombre limité de clés, workflow classique adapté.

**Étapes** :
1. Extractor → TranslatedStrings_en.txt (nouveau)
2. COMPARE → UPDATE_en.json
3. EXTRACT → TRANSLATE_fr.txt (5 clés)
4. Traducteur édite TRANSLATE_fr.txt
5. INJECT + SYNC → Fichiers finaux

---

## Cas 4 : Refonte majeure de l'interface (50+ nouvelles clés)

**Situation** : Refonte UI complète, 50+ nouvelles clés, plusieurs langues.

**Workflow recommandé** : **Workflow 2 (WebBridge)** ✅

**Raison** : Nombre élevé de clés + multi-langues → interface web beaucoup plus efficace et moins d'erreurs.

**Étapes** :
1. Extractor → TranslatedStrings_en.txt (avec 50 nouvelles clés)
2. WebBridge Export → translations.json (toutes langues)
3. Envoyer à traducteurs FR, DE, ES
4. Chaque traducteur utilise quicki18n.studio
5. WebBridge Import → Génère tous les TranslatedStrings_xx.txt
6. Copier dans plugin → Tester

**Avantage** : Traduction parallèle possible, validation automatique, aucune erreur de formatage

---

# État du développement WebBridge

## Statut actuel ✅ COMPLET

| Composant | Statut | Description |
|-----------|--------|-------------|
| **Infrastructure** | ✅ Complète | Auto-conditionnement, documentation |
| **Structure module** | ✅ Créée | Dossiers, fichiers de base |
| **Documentation** | ✅ Complète | 250+ pages de spécifications |
| **WebBridge_models.py** | ✅ Opérationnel | Classes de données |
| **WebBridge_utils.py** | ✅ Opérationnel | Parsing .txt ↔ JSON |
| **WebBridge_export.py** | ✅ Opérationnel | Export .txt → .json |
| **WebBridge_import.py** | ✅ Opérationnel | Import .json → .txt |
| **WebBridge_validator.py** | ✅ Opérationnel | Validation stricte |
| **WebBridge_menu.py** | ✅ Opérationnel | Menu interactif |
| **WebBridge_main.py** | ✅ Opérationnel | Point d'entrée CLI |
| **Intégration toolkit** | ✅ Complète | Menu [8] Export Web et [9] Import Web |

## Preuve d'utilisation réelle

Le module a été testé avec succès sur le plugin **PiwigoPublish** :

```
D:\...\piwigoPublish.lrplugin\__i18n_tmp__\4_WebBridge\
├── 20260131_132306/
│   └── translations.json     (278 clés exportées)
├── 20260131_141217/
│   └── translations.json
├── 20260131_153654/
│   └── translations.json
├── 20260131_163041/
│   └── translations.json
└── 20260131_164318/
    └── translations.json     (dernier export réussi)
```

**Le module WebBridge est prêt pour la production.**

---

# Annexe : Commandes rapides

## Workflow 1 (Classique) ✅ DISPONIBLE

```bash
# Étape 1-2 : Extraction
python LocalizationToolkit.py
# [1] Extractor

# Étape 3 : Comparaison
python LocalizationToolkit.py
# [3] Translation → [1] COMPARE

# Étape 4 : Générer mini-fichiers
python LocalizationToolkit.py
# [3] Translation → [2] EXTRACT

# Étape 6 : Injecter traductions
python LocalizationToolkit.py
# [3] Translation → [3] INJECT

# Étape 7 : Synchroniser
python LocalizationToolkit.py
# [3] Translation → [4] SYNC

# Étape 8 : Copier
cp __i18n_tmp__/TranslationManager/<timestamp>/TranslatedStrings_*.txt .
```

---

## Workflow 2 (WebBridge) ✅ DISPONIBLE

```bash
# Étape 1 : Extraction
python LocalizationToolkit.py
# [1] Extractor

# Étape 2 : Export JSON
python LocalizationToolkit.py
# [8] Export Web (WebBridge)

# Étape 3-4 : Traducteur utilise quicki18n.studio
# (pas de commande côté développeur)

# Étape 5 : Import JSON
python LocalizationToolkit.py
# [9] Import Web (WebBridge)

# Étape 6 : Copier dans le plugin
cp __i18n_tmp__/4_WebBridge/<timestamp>/TranslatedStrings_*.txt .
```

**Alternative CLI directe** :
```bash
# Export
python 4_WebBridge/WebBridge_main.py export --plugin-path ./plugin.lrplugin

# Import
python 4_WebBridge/WebBridge_main.py import --json translations.json --plugin-path ./plugin.lrplugin
```

---

# Conclusion

## Deux workflows disponibles ✅

### Workflow 2 (WebBridge) - RECOMMANDÉ ✅

Le **Workflow 2 (WebBridge)** est **pleinement opérationnel** et offre :
- ✅ Une interface web moderne pour les traducteurs (quicki18n.studio)
- ✅ Une expérience utilisateur grandement améliorée
- ✅ Une validation automatique des traductions (placeholders, formatage)
- ✅ Un gain de temps significatif (5-10 min au lieu de 15-30 min)
- ✅ Pas d'outil à installer pour les traducteurs (navigateur uniquement)

**Utilisez-le** pour la plupart des cas, surtout avec des traducteurs non-techniques.

### Workflow 1 (Classique) - ALTERNATIF ✅

Le **Workflow 1 (Classique)** reste **disponible** pour :
- Traducteurs très techniques
- Petites corrections rapides (1-3 clés)
- Workflow interne établi
- Préférence pour l'édition directe de fichiers

---

## Preuve d'utilisation réelle

Le module WebBridge a été **testé avec succès** sur le plugin **PiwigoPublish** :
- 278 clés exportées/importées sans erreur
- Validation automatique opérationnelle
- Fichiers générés dans `__i18n_tmp__/4_WebBridge/`

**Dans tous les cas**, les fichiers `TranslatedStrings_xx.txt` restent la **source de vérité finale** compatible avec le SDK Adobe Lightroom.

---

**Date de mise à jour** : 2026-01-31
**Version** : 2.2 (WebBridge opérationnel)
