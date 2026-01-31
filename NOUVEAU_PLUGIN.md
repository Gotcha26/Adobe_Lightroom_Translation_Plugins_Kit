# Workflow pour un Nouveau Plugin Lightroom

## Cas d'usage : Plugin tout neuf avec traductions à initialiser

Vous venez de créer un plugin Lightroom flambant neuf. Il ne contient actuellement que le fichier `TranslatedStrings_en.txt` à la racine avec vos chaînes anglaises. Vous souhaitez maintenant structurer les traductions et collaborer avec des traducteurs.

**Questions** :
- **Je suis développeur** : Comment initialiser correctement mes traductions ?
- **Je suis traducteur** : Comment contribuer à la traduction d'un nouveau plugin ?

Ce document présente **le workflow complet pour un plugin neuf**, du simple fichier unique à un système multilingue organisé.

---

## 📋 Situation de départ

```
monPlugin.lrplugin/
├── Info.lua
├── MonModule.lua
└── TranslatedStrings_en.txt      ← Fichier unique (langue source)
```

**Caractéristiques** :
- Plugin nouveau, structure fraîche
- Une seule langue disponible : anglais
- Pas de traductions existantes
- Aucun historique de versions précédentes

---

# Workflow pour Développeur

## Vue d'ensemble

En tant que développeur d'un plugin neuf, vous devez :
1. Valider la structure de vos chaînes anglaises
2. Identifier les chaînes à traduire
3. Créer les fichiers pour les traducteurs
4. Collaborer avec les traducteurs pour les autres langues

### Objectif final
```
monPlugin.lrplugin/
├── Info.lua
├── MonModule.lua
├── TranslatedStrings_en.txt      ← Référence (300 clés)
├── TranslatedStrings_fr.txt      ← Français (300 clés, 100% traduit)
├── TranslatedStrings_de.txt      ← Allemand (300 clés, 100% traduit)
└── TranslatedStrings_es.txt      ← Espagnol (300 clés, 100% traduit)
```

---

## Étapes détaillées

### Étape 1 : Valider et extraire les chaînes anglaises

**Outil** : `1_Extractor`

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [1] Extractor
```

**Paramètres** :
- Plugin path : `D:\mon\nouveau\plugin.lrplugin`
- Prefix LOC : `$$$/MonPlugin`
- Langue : `en`

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── Extractor/
        └── 20260131_100000/
            ├── TranslatedStrings_en.txt     ← Extraction validée (300 clés)
            ├── spacing_metadata.json        ← Métadonnées de formatage
            ├── replacements.json            ← Substitutions de texte
            └── extraction_report.txt        ← Rapport de validation
```

**Sortie console** :
```
✓ Extraction réussie !

Statistiques :
- Fichiers analysés : 8
- Chaînes extraites : 300
- Clés LOC générées : 300
- Clés avec espaces/suffixes : 42

Fichiers générés dans : __i18n_tmp__/Extractor/20260131_100000/
```

**À noter** : Si votre `TranslatedStrings_en.txt` existe déjà, l'Extractor valide sa structure et détecte les éventuelles anomalies (clés orphelines, formatage incorrect, etc.).

---

### Étape 2 : Préparer les langues cibles

Décidez quelles langues vous souhaitez supporter. Pour chaque langue :

| Langue | Code | Effort initial | Communauté |
|--------|------|-----------------|------------|
| Français | `fr` | Moyen | Bonne (Europe) |
| Allemand | `de` | Moyen | Bonne (Europe) |
| Espagnol | `es` | Moyen | Excellente (Amérique Latine) |
| Néerlandais | `nl` | Faible | Petite |
| Portugais (Brésil) | `pt-BR` | Moyen | Bonne (Amérique Latine) |
| Japonais | `ja` | Fort | Très bonne (Asie) |
| Chinois simplifié | `zh-CN` | Fort | Excellente (Asie) |

**Conseil** : Commencez par 2-3 langues, vous pourrez en ajouter plus tard.

---

### Étape 3 : Générer les fichiers de traduction

**Outil** : `3_Translation_manager` → **EXTRACT**

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [3] Translation
# Sélectionner [2] EXTRACT
```

**Paramètres** :
- Mode : `NEW_PLUGIN` (nouveau plugin)
- Extraction de référence : `__i18n_tmp__/Extractor/20260131_100000/TranslatedStrings_en.txt`
- Langues cibles : `fr, de, es` (saisir une par une)

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── TranslationManager/
        └── 20260131_101000/
            ├── TRANSLATE_fr.txt             ← À traduire en français
            ├── TRANSLATE_de.txt             ← À traduire en allemand
            ├── TRANSLATE_es.txt             ← À traduire en espagnol
            ├── extraction_report.txt        ← Statistiques
            └── instructions.txt             ← Instructions pour traducteurs
```

**Contenu de TRANSLATE_fr.txt** :
```
-- =============================================================================
-- TRADUCTION COMPLÈTE - FR
-- Générées : 2026-01-31 10:10:00
-- Plugin : monPlugin.lrplugin
-- Total clés : 300
-- =============================================================================

-- INSTRUCTIONS :
-- 1. Traduisez la VALEUR après le = uniquement
-- 2. Ne modifiez PAS les clés (avant le =)
-- 3. Ne traduisez PAS : %s, %d, \n, \t, etc.
-- 4. Préservez les espaces autour du texte
-- 5. Testez dans Lightroom après traduction

-- ============= SECTION 1 : Menus =============
"$$$/MonPlugin/Menu/File=File"
"$$$/MonPlugin/Menu/Edit=Edit"
"$$$/MonPlugin/Menu/View=View"
...

-- ============= SECTION 2 : Dialogues =============
"$$$/MonPlugin/Dialog/Title=Settings"
"$$$/MonPlugin/Dialog/OK=OK"
"$$$/MonPlugin/Dialog/Cancel=Cancel"
...

-- ============= SECTION 3 : Messages =============
"$$$/MonPlugin/Message/Success=Success"
"$$$/MonPlugin/Message/Error=Error"
...
```

**Sortie console** :
```
✓ Extraction réussie !

Fichiers générés :
- TRANSLATE_fr.txt : 300 clés à traduire
- TRANSLATE_de.txt : 300 clés à traduire
- TRANSLATE_es.txt : 300 clés à traduire

Organisez votre équipe de traducteurs et envoyez les fichiers.
```

---

### Étape 4 : Documenter et envoyer aux traducteurs

**Fichiers à préparer** :

1. **instructions.txt** (généré automatiquement)
2. **TRANSLATE_xx.txt** (pour chaque langue)
3. **context_guide.txt** (optionnel mais recommandé)

**Email type pour les traducteurs** :

```
Objet : Traduction du plugin MonPlugin (Nouveau Plugin)

Bonjour,

Nous lançons un nouveau plugin Lightroom et recherchons des traducteurs
pour les langues suivantes :
- Français
- Allemand
- Espagnol

Le plugin contient 300 chaînes à traduire.

TÂCHE :
1. Téléchargez le fichier TRANSLATE_<langue>.txt ci-joint
2. Traduisez chaque ligne (voir instructions ci-dessous)
3. Renvoyez-moi le fichier complété

INSTRUCTIONS IMPORTANTES :
1. Traduisez uniquement après le = (exemple ci-dessous)
2. NE modifiez PAS les clés (avant le =)
3. NE traduisez PAS les placeholders : %s, %d, \n, \t, etc.
4. Préservez les espaces autour du texte

EXEMPLE :
AVANT  : "$$$/MonPlugin/Menu/File=File"
APRÈS  : "$$$/MonPlugin/Menu/File=Fichier"

CONTEXTE :
- Plugin : Gestion de photos Lightroom
- Domaine : Photographie
- Public : Photographes amateurs et professionnels
- Style : Formel mais accessible

Les fichiers comportent 300 clés organisées par section :
- Menus (50 clés)
- Dialogues (100 clés)
- Messages (80 clés)
- Paramètres (70 clés)

Délai proposé : [À définir selon vos besoins]

Merci de votre aide !

Cordialement,
[Votre nom]
```

---

### Étape 5 : Réception des traductions

**Le traducteur renvoie** : `TRANSLATE_xx.txt` (complété)

**Vérifications à faire** :
- ✓ Toutes les 300 clés sont traduites
- ✓ Les clés n'ont pas été modifiées
- ✓ Les placeholders n'ont pas été traduits
- ✓ Le formatage est correct

**Exemple de fichier reçu** (TRANSLATE_fr.txt) :
```
-- ============= SECTION 1 : Menus =============
"$$$/MonPlugin/Menu/File=Fichier"
"$$$/MonPlugin/Menu/Edit=Édition"
"$$$/MonPlugin/Menu/View=Affichage"
...

-- ============= SECTION 2 : Dialogues =============
"$$$/MonPlugin/Dialog/Title=Paramètres du Plugin"
"$$$/MonPlugin/Dialog/OK=Valider"
"$$$/MonPlugin/Dialog/Cancel=Annuler"
...
```

---

### Étape 6 : Créer les fichiers finaux (mode NEW_PLUGIN)

**Outil** : `3_Translation_manager` → **BUILD**

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [3] Translation
# Sélectionner [5] BUILD (nouveau pour les nouveaux plugins)
```

**Paramètres** :
- Mode : `NEW_PLUGIN`
- Référence EN : `__i18n_tmp__/Extractor/20260131_100000/TranslatedStrings_en.txt`
- Fichiers traduits :
  - `TRANSLATE_fr.txt` (complété)
  - `TRANSLATE_de.txt` (complété)
  - `TRANSLATE_es.txt` (complété)

**Résultat** :
```
monPlugin.lrplugin/
└── __i18n_tmp__/
    └── TranslationManager/
        └── 20260131_102000/
            ├── TranslatedStrings_en.txt     ← Référence (300 clés, 100%)
            ├── TranslatedStrings_fr.txt     ← Français (300 clés, 100%)
            ├── TranslatedStrings_de.txt     ← Allemand (300 clés, 100%)
            ├── TranslatedStrings_es.txt     ← Espagnol (300 clés, 100%)
            └── build_report.txt             ← Rapport de qualité
```

**Contenu de build_report.txt** :
```
═══════════════════════════════════════════════════════════
BUILD REPORT - Nouveau Plugin
═══════════════════════════════════════════════════════════

[EN] Anglais (référence)
  ✓ 300 clés (100%)
  ✓ Format valide

[FR] Français
  ✓ 300 clés (100%)
  ✓ Format valide
  ✓ Placeholders préservés
  ✓ Qualité : Excellente

[DE] Allemand
  ✓ 300 clés (100%)
  ✓ Format valide
  ✓ Placeholders préservés
  ✓ Qualité : Excellente

[ES] Espagnol
  ✓ 300 clés (100%)
  ✓ Format valide
  ✓ Placeholders préservés
  ✓ Qualité : Excellente

═══════════════════════════════════════════════════════════
✓ TOUS LES FICHIERS SONT PRÊTS
═══════════════════════════════════════════════════════════

Statistiques globales :
- Total clés : 300
- Langues complètes : 4 (en, fr, de, es)
- Taux de complétude : 100%
- Erreurs détectées : 0
```

---

### Étape 7 : Copier dans le plugin

**Action manuelle** :

```bash
# Copier les fichiers finaux dans le plugin
cp __i18n_tmp__/TranslationManager/20260131_102000/TranslatedStrings_*.txt .

# Vérifier
ls -l TranslatedStrings_*.txt
```

**Résultat** :
```
monPlugin.lrplugin/
├── Info.lua
├── MonModule.lua
├── TranslatedStrings_en.txt     ← Référence (300 clés)
├── TranslatedStrings_fr.txt     ← Français (300 clés, 100% traduit)
├── TranslatedStrings_de.txt     ← Allemand (300 clés, 100% traduit)
└── TranslatedStrings_es.txt     ← Espagnol (300 clés, 100% traduit)
```

---

### Étape 8 : Tester dans Lightroom

**Actions** :

1. **Recharger le plugin** dans Lightroom
   - Ouvrir Lightroom
   - File → Plug-in Manager
   - Reload plugins

2. **Tester chaque langue** :
   - Langues anglaise, française, allemande, espagnole
   - Vérifier que tous les textes s'affichent correctement
   - Chercher les [NEW] ou valeurs manquantes

3. **Tester les placeholders** :
   - Confirmer que `%s`, `%d`, `\n`, etc. ne sont pas présents dans les traductions affichées
   - Vérifier que les paramètres dynamiques fonctionnent

4. **Documenter les résultats** :
   ```
   ✓ Version EN : OK (300/300 clés)
   ✓ Version FR : OK (300/300 clés)
   ✓ Version DE : OK (300/300 clés)
   ✓ Version ES : OK (300/300 clés)
   ✓ Tous les textes s'affichent correctement
   ✓ Pas d'erreurs détectées
   ```

---

### Étape 9 : (Optionnel) Appliquer les LOC dans le code

Si votre code contient encore des chaînes **hardcodées** au lieu d'utiliser des appels `LOC` :

**Outil** : `2_Applicator`

**Commande** :
```bash
python LocalizationToolkit.py
# Sélectionner [2] Applicator
```

**Paramètres** :
- Plugin path : `D:\mon\plugin.lrplugin`
- Extraction dir : `__i18n_tmp__/Extractor/20260131_100000/`

**Avant (hardcodé)** :
```lua
LrDialogs.showMessage("Success", "Operation completed successfully")
```

**Après (localisé)** :
```lua
LrDialogs.showMessage(LOC "$$$/MonPlugin/Message/Success",
                      LOC "$$$/MonPlugin/Message/Success/Description")
```

**Résultat** :
- Les chaînes hardcodées sont remplacées par des appels `LOC`
- Backups créés dans `__i18n_tmp__/Applicator/<timestamp>/backups/`
- Verification que les clés existent dans `TranslatedStrings_en.txt`

---

## Résumé Workflow Développeur (Nouveau Plugin)

```
┌─────────────────────────────────────────────────────────────┐
│ DÉVELOPPEUR - NOUVEAU PLUGIN                                │
├─────────────────────────────────────────────────────────────┤
│ 1. Extractor → TranslatedStrings_en.txt (validation)         │
│ 2. Choisir les langues cibles (fr, de, es, etc.)             │
│ 3. EXTRACT → TRANSLATE_xx.txt pour chaque langue             │
│ 4. Envoyer fichiers TRANSLATE_xx.txt aux traducteurs         │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ TRADUCTEURS (1 par langue)                                  │
├─────────────────────────────────────────────────────────────┤
│ 5. Éditer TRANSLATE_xx.txt (traduire 300 clés)              │
│ 6. Renvoyer fichier complété au développeur                 │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ DÉVELOPPEUR - FINITION                                      │
├─────────────────────────────────────────────────────────────┤
│ 7. BUILD → Générer TranslatedStrings_xx.txt finaux          │
│ 8. Copier dans plugin.lrplugin/                             │
│ 9. Tester dans Lightroom (toutes les langues)               │
│ 10. (Optionnel) Applicator → Remplacer hardcodés par LOC    │
└─────────────────────────────────────────────────────────────┘
```

**Durée estimée** : 2-4 semaines (dépend des traducteurs)

---

---

# Workflow pour Traducteur

## Vue d'ensemble

Vous êtes intéressé pour traduire le nouveau plugin en français (ou autre langue). Voici comment procéder.

### Objectif
Traduire **300 chaînes de texte** du plugin pour la langue cible.

---

## Prérequis

### Outils requis
- ✓ Éditeur de texte brut : Notepad++, VS Code, Sublime Text, etc.
  - **PAS** Microsoft Word (qui ajoute des formatage cachés)
  - **PAS** Google Docs
- ✓ UTF-8 encoding supporté (important pour les caractères accentués)
- ✓ Environ 4-6 heures disponibles (300 clés)

### Compétences requises
- Bonne maîtrise de la langue cible (français, allemand, espagnol, etc.)
- Compréhension des interfaces logicielles
- Attention au détail (formatage, placeholders, espaces)
- Aucune connaissance technique requise

### Exemple : Traduction en français

Si vous parlez français, vous pouvez contribuer à la traduction du plugin.

---

## Étapes détaillées

### Étape 1 : Recevoir le fichier de traduction

**Le développeur vous envoie** :
- Fichier : `TRANSLATE_fr.txt` (ou votre langue)
- Email avec instructions
- Contexte du plugin (optionnel mais utile)

**Fichier reçu (exemple)** :
```
-- =============================================================================
-- TRADUCTION COMPLÈTE - FR
-- Générées : 2026-01-31 10:10:00
-- Plugin : monPlugin.lrplugin
-- Total clés : 300
-- =============================================================================

-- INSTRUCTIONS :
-- 1. Traduisez la VALEUR après le = uniquement
-- 2. Ne modifiez PAS les clés (avant le =)
-- 3. Ne traduisez PAS : %s, %d, \n, \t, etc.
-- 4. Préservez les espaces autour du texte
-- 5. Testez dans Lightroom après traduction

-- ============= SECTION 1 : Menus =============
"$$$/MonPlugin/Menu/File=File"
"$$$/MonPlugin/Menu/Edit=Edit"
"$$$/MonPlugin/Menu/View=View"
...
```

---

### Étape 2 : Préparer votre environnement de travail

**Préparation** :

1. **Télécharger un bon éditeur** (si vous n'en avez pas)
   - **Recommandé** : VS Code (gratuit, multiplateforme)
   - **Alternatif** : Notepad++ (Windows), Sublime Text

2. **Ouvrir le fichier TRANSLATE_fr.txt** :
   - Clic droit → Ouvrir avec → Votre éditeur
   - **Vérifier** : UTF-8 encoding
   - **Vérifier** : Pas de formatage Word

3. **Préparer votre environnement** :
   - Ouvrir un dictionnaire/traducteur en ligne (Google Translate, DeepL) pour référence
   - Préparer une liste d'abréviations et termes métier (exemple : "Settings" = "Paramètres")

---

### Étape 3 : Comprendre la structure du fichier

**Format du fichier** :

```
"$$$/MonPlugin/Menu/File=File"
   │          │      │    │
   │          │      │    └─ VALEUR À TRADUIRE (remplacer)
   │          │      └────── Clé (NE PAS TOUCHER)
   │          └───────────── Catégorie
   └──────────────────────── Clé LOC (NE PAS TOUCHER)
```

**Règles** :

| Règle | Exemple | ✗ Incorrect | ✓ Correct |
|-------|---------|------------|-----------|
| Garder la clé | `$$$/MonPlugin/Menu/File=File` | `$$$/MonPlugin/Menu/Fichier=Fichier` | `$$$/MonPlugin/Menu/File=Fichier` |
| Ne pas traduire `%s` | `"Label=%s items"` | `"Label=%s éléments"` ❌ | `"Label=%s items"` ✓ puis remplacer par traduction anglaise |
| Garder les espaces | `" = Value "` | `"=Value"` | `" = Valeur "` |
| UTF-8 encoding | Français avec accents | Caractères cassés | Chaîne lisible |

---

### Étape 4 : Traduire les chaînes

**Approche recommandée** :

#### A. Lecture complète (5-10 min)
Parcourir le fichier pour comprendre le contexte global du plugin.

#### B. Traduction par section (2-3 heures)

```
-- ============= SECTION 1 : Menus =============
"$$$/MonPlugin/Menu/File=File"               → "Fichier"
"$$$/MonPlugin/Menu/Edit=Edit"               → "Édition"
"$$$/MonPlugin/Menu/View=View"               → "Affichage"
"$$$/MonPlugin/Menu/Tools=Tools"             → "Outils"

-- ============= SECTION 2 : Dialogues =============
"$$$/MonPlugin/Dialog/Title=Settings"        → "Paramètres"
"$$$/MonPlugin/Dialog/OK=OK"                 → "Valider"
"$$$/MonPlugin/Dialog/Cancel=Cancel"         → "Annuler"
"$$$/MonPlugin/Dialog/Help=Help"             → "Aide"

-- ============= SECTION 3 : Messages =============
"$$$/MonPlugin/Message/Success=Success"      → "Succès"
"$$$/MonPlugin/Message/Error=Error"          → "Erreur"
```

**Conseils de traduction** :

1. **Soyez cohérent** : Utilisez le même mot pour le même concept
   - "Settings" = "Paramètres" (toujours)
   - "Cancel" = "Annuler" (toujours)

2. **Respectez la tonalité** : Formel ou amical
   - Photographe professionnel ? → Langage professionnel
   - Public amateur ? → Langage accessible

3. **Testez avec le contexte** :
   - Imaginez le texte dans l'interface
   - Le texte traduit est-il clair ?
   - N'est-il pas trop long pour un bouton ?

4. **Cas spéciaux** :
   - `%s`, `%d`, `\n` → À **NE PAS traduire**, à laisser comme-is
   - `...` (ellipsis) → Garder dans la traduction
   - `&` (accélérateur) → Garder et adapter si possible

#### C. Relecture (30-60 min)

Relire votre traduction :
- ✓ Cohérence des termes
- ✓ Pas de caractères cassés
- ✓ Placeholders intacts (`%s`, `%d`, `\n`)
- ✓ Longueur raisonnable pour l'interface

---

### Étape 5 : Format et validation

**Avant de renvoyer, vérifier** :

1. **Encodage UTF-8**
   - Dans VS Code : En bas à droite, vérifier "UTF-8"
   - Dans Notepad++ : Encoding → Encode in UTF-8 without BOM

2. **Fins de ligne Unix (LF)**
   - Ne pas utiliser Windows (CRLF)
   - VS Code : Sélectionner "LF" en bas à droite

3. **Aucune ligne vide supplémentaire**
   - Sauvegarder le fichier

4. **Vérifier quelques clés aléatoires**
   ```
   -- AVANT traduction
   "$$$/MonPlugin/Menu/File=File"

   -- APRÈS traduction
   "$$$/MonPlugin/Menu/File=Fichier"

   -- À VÉRIFIER
   - Format préservé ✓
   - Clé intacte ✓
   - Traduction cohérente ✓
   ```

---

### Étape 6 : Soumettre votre traduction

**Préparer votre soumission** :

1. **Renommer le fichier** :
   ```
   TRANSLATE_fr.txt  →  TRANSLATE_fr_[VotreNom].txt
   ```
   (Exemple : `TRANSLATE_fr_Jean_Dupont.txt`)

2. **Vérifier le fichier une dernière fois** :
   - Ouvrir dans l'éditeur
   - Compter les lignes non-vides (doit correspondre au nombre original)
   - Vérifier qu'aucune clé ne manque

3. **Envoyer au développeur** :
   - Email avec fichier en pièce jointe
   - Indiquer votre statut
   - Mentionner si vous avez rencontré des difficultés

**Email de soumission** :

```
Objet : Traduction MonPlugin - Français (Complétée)

Bonjour,

Vous trouverez en pièce jointe le fichier TRANSLATE_fr.txt
que j'ai traduit entièrement en français.

STATISTIQUES :
- 300 clés traduites ✓
- Encodage UTF-8 ✓
- Aucune clé manquante ✓
- Format préservé ✓

NOTES (optionnel) :
- Termes métier utilisés : Paramètres, Réglages, etc.
- Quelques notes sur les traductions difficiles
- Suggestions pour les versions futures

Cordialement,
[Votre nom]
```

---

## Résumé Workflow Traducteur (Nouveau Plugin)

```
┌─────────────────────────────────────────────────────────────┐
│ TRADUCTEUR - PRÉPARATION                                    │
├─────────────────────────────────────────────────────────────┤
│ 1. Recevoir TRANSLATE_xx.txt du développeur                 │
│ 2. Télécharger un éditeur de texte (VS Code, Notepad++)     │
│ 3. Vérifier l'encodage UTF-8                                │
│ 4. Lire le fichier pour comprendre le contexte (5-10 min)   │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ TRADUCTEUR - TRADUCTION                                     │
├─────────────────────────────────────────────────────────────┤
│ 5. Traduire les 300 chaînes par section (2-3 heures)        │
│ 6. Respecter les règles (clés, placeholders, espaces)       │
│ 7. Assurer la cohérence des termes                          │
│ 8. Relire votre traduction (30-60 min)                      │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ TRADUCTEUR - FINALISATION                                   │
├─────────────────────────────────────────────────────────────┤
│ 9. Vérifier l'encodage UTF-8 et fins de ligne (LF)          │
│ 10. Valider qu'aucune clé ne manque                         │
│ 11. Renvoyer TRANSLATE_xx.txt au développeur                │
└─────────────────────────────────────────────────────────────┘
```

**Durée estimée** : 4-6 heures (selon expérience)

---

## Conseils pratiques pour traducteurs

### Créer un glossaire personnel

```
TERME ANGLAIS       → TERME FRANÇAIS    → UTILISÉ DANS
File                → Fichier           → Menu, Dialogues
Edit                → Édition           → Menu
View                → Affichage         → Menu
Settings            → Paramètres        → Dialogues, Menu
OK                  → Valider           → Dialogues
Cancel              → Annuler           → Dialogues
Save                → Enregistrer       → Dialogues
Open                → Ouvrir            → Menu
Close               → Fermer            → Menu
Delete              → Supprimer         → Menu, Dialogues
Export              → Exporter          → Menu
Import              → Importer          → Menu
Search              → Rechercher        → Menu
Replace             → Remplacer         → Menu
```

### Outils recommandés

| Outil | Usage | Gratuit |
|-------|-------|---------|
| [Google Translate](https://translate.google.com/) | Traduction rapide de référence | ✓ |
| [DeepL](https://www.deepl.com/) | Traduction professionnelle plus précise | ✓ (limité) |
| [VS Code](https://code.visualstudio.com/) | Édition du fichier | ✓ |
| [Reverso Context](https://context.reverso.net/) | Vérifier comment les termes sont utilisés | ✓ |
| [French Dictionary](https://www.cnrtl.fr/) | Vérifier l'orthographe et usage | ✓ |

### Cas difficiles

#### Cas 1 : Texte trop long pour l'interface
```
Anglais  : "Do you want to save your changes before closing?"
Français : "Voulez-vous enregistrer vos modifications avant de fermer ?"
Problème : Texte trop long pour un dialogue

Solution : "Enregistrer les modifications ?"
ou         "Enregistrer avant de fermer ?"
```

#### Cas 2 : Placeholders
```
Anglais  : "$$$/MonPlugin/Message/Items=%d items selected"
Réception : "Enregistrer %d éléments sélectionnés"
Problème : Le %d doit rester inchangé

Solution : "%d éléments sélectionnés"
           (le %d sera remplacé par le nombre)
```

#### Cas 3 : Abréviations
```
Anglais   : "Mon %s %d"  (Monday, 3)
Français  : "Lun %s %d"  (Lundi, 3)
Solution  : Garder le format mais adapter la langue
```

---

---

# Comparaison des deux rôles

| Aspect | Développeur | Traducteur |
|--------|-------------|-----------|
| **Objectif** | Initialiser et structurer les traductions | Traduire les chaînes anglaises |
| **Outils requis** | Adobe_Lightroom_Translation_Plugins_Kit | Simple éditeur de texte |
| **Prérequis techniques** | Python, en ligne de commande | Aucun requis |
| **Durée estimée** | 2-4 semaines (total avec traducteurs) | 4-6 heures par langue |
| **Expertise requise** | Toolkit, infrastructure | Langue cible uniquement |
| **Nombre de participants** | 1 développeur | 1+ traducteur par langue |
| **Responsabilité** | Validation, intégration, test | Qualité de la traduction |

---

# Cas d'usage spécifiques

## Cas 1 : Je suis développeur et je veux tout gérer seul

**Situation** : Vous avez créé un plugin neuf et vous parlez couramment français, allemand et espagnol.

**Approche** :
1. Utiliser le Workflow Développeur (Étapes 1-3)
2. Vous-même faire le travail de traducteur (Étape 4-6)
3. Finaliser le plugin (Étapes 7-9)

**Durée** : 2-3 semaines pour 3 langues + 300 clés

---

## Cas 2 : Je suis traducteur et je veux aider

**Situation** : Un développeur cherche des traducteurs pour son nouveau plugin.

**Approche** :
1. Contacter le développeur
2. Manifester votre intérêt pour une ou plusieurs langues
3. Recevoir le fichier `TRANSLATE_xx.txt`
4. Suivre le Workflow Traducteur (Étapes 1-6)
5. Renvoyer le fichier traduit

**Durée** : 4-6 heures par langue

---

## Cas 3 : Plugin neuf avec 10+ langues

**Situation** : Vous avez développé un plugin ambitieux et visez le marché mondial.

**Approche** :
1. Commencer par 2-3 langues prioritaires (développeur)
2. Utiliser le Workflow Développeur complet
3. Chercher des traducteurs natives pour chaque langue
4. Utiliser un système de tracking (Google Sheet, Trello, Github Issues)
5. Ajouter les autres langues progressivement

**Exemple de tracking** :
```
| Langue | Traducteur | Statut | Date renvoi |
|--------|-----------|--------|------------|
| FR | Jean Dupont | ✓ Complétée | 2026-02-15 |
| DE | Hans Mueller | ⏳ En cours | - |
| ES | Maria Garcia | ⏳ En attente | - |
| IT | Marco Rossi | ✓ Complétée | 2026-02-18 |
| PT-BR | João Silva | ⏳ En cours | - |
```

---

# Ressources utiles

## Pour les développeurs

- [README.md](README.md) - Documentation principale
- [WORKFLOW_MISE_A_JOUR.md](WORKFLOW_MISE_A_JOUR.md) - Mise à jour des traductions existantes
- [LocalizationToolkit.py](LocalizationToolkit.py) - Script principal

## Pour les traducteurs

- [Editeurs de texte recommandés](#outils-recommandés)
- [Ressources de traduction](#outils-recommandés)
- [Conseils de traduction](#conseils-pratiques-pour-traducteurs)

## Outils en ligne

- [Google Translate](https://translate.google.com/)
- [DeepL](https://www.deepl.com/)
- [Reverso Context](https://context.reverso.net/)

---

# Conclusion

## Pour les développeurs ✓

Le workflow d'initialisation d'un nouveau plugin est simple :
1. Extraire vos chaînes anglaises
2. Générer les fichiers de traduction
3. Envoyer aux traducteurs
4. Intégrer et tester

**Durée** : 2-4 semaines avec traducteurs, moins d'une semaine en solo.

## Pour les traducteurs ✓

Contribuer à la traduction d'un nouveau plugin est accessible :
1. Recevoir le fichier `TRANSLATE_xx.txt`
2. Traduire les 300 chaînes
3. Vérifier et soumettre

**Durée** : 4-6 heures par langue.

---

**Date de création** : 2026-01-31
**Version** : 1.0
**Statut** : ✓ Complet
