# Comparaison des Workflows de Traduction

## Vue d'ensemble

Ce toolkit propose **3 workflows** selon votre situation et vos besoins.

```
┌─────────────────────────────────────────────────────────────┐
│ NOUVEAU PLUGIN                                              │
│ → Duplication simple (NOUVEAU_PLUGIN.md)                    │
│ ✓ Pour débutants                                            │
│ ✓ Plugin sans traductions existantes                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ MAINTENANCE STANDARD                                        │
│ → AUTO-SYNC (Lisez-moi.md / WORKFLOW_MISE_A_JOUR.md)        │
│ ✓ Pour usage quotidien                                     │
│ ✓ Nouvelles/modifiées clés en anglais dans fichier complet │
│ ✗ Pas de marqueurs [NEW]/[NEEDS_REVIEW]                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ CONTRÔLE AVANCÉ                                             │
│ → COMPARE → EXTRACT → INJECT (WORKFLOW_AVANCE.md)           │
│ ✓ Pour traducteurs professionnels                          │
│ ✓ Isolation des changements dans TRANSLATE_xx.txt          │
│ ✓ Marqueurs [NEW]/[NEEDS_REVIEW] si COMPARE → SYNC         │
└─────────────────────────────────────────────────────────────┘
```

---

## Comparaison détaillée

| Critère | Nouveau Plugin LrC | AUTO-SYNC | COMPARE → EXTRACT → INJECT |
|---------|---------------|-----------|----------------------------|
| **Commandes** | ***Extractor*** → *Dupliquer* | ***Extractor*** → **AUTO-SYNC** | **COMPARE** → **EXTRACT** → **INJECT** |
| **Fichier traducteur** | `TranslatedStrings_xx.txt` (tout en anglais) | `TranslatedStrings_xx.txt` (nouvelles clés en EN) | `TRANSLATE_xx.txt` (seulement changements) |
| **Marqueurs** | ❌ Non | ❌ Non | ✅ Oui (si **COMPARE** → **SYNC**) |
| **Taille fichier** | 300 lignes (tout) | 300 lignes (complet) | 62 lignes (changements) |
| **Identification changements** | Tout est à traduire | Chercher clés en anglais | Fichier `TRANSLATE-xx.txt` isolé |
| **Complexité** | Simple | Simple | Avancé |
| **Cas d'usage** | Nouveau plugin LrC | Maintenance courante | Gros volumes, contrôle fin |

---

## Exemples visuels

### Workflow 1 : **Nouveau Plugin LrC**

**Fichier `TranslatedStrings_fr.txt` après duplication** :
```
"$$$/MonPlugin/Menu/File=File"                    ← Tout en anglais
"$$$/MonPlugin/Menu/Edit=Edit"                    ← À traduire
"$$$/MonPlugin/Dialog/OK=OK"                      ← À traduire
```

**Action pour le traducteur** : Traduire toutes les lignes.

---

### Workflow 2 : **AUTO-SYNC**

**Avant AUTO-SYNC** (278 clés, 100% traduites) :
```
"$$$/MonPlugin/Menu/File=Fichier"
"$$$/MonPlugin/Menu/Edit=Édition"
"$$$/MonPlugin/Dialog/OK=Valider"
```

**Après AUTO-SYNC** (330 clés, nouvelles en anglais) :
```
"$$$/MonPlugin/Menu/File=Fichier"                 ← Conservé
"$$$/MonPlugin/Menu/Edit=Édition"                 ← Conservé
"$$$/MonPlugin/Dialog/OK=Valider"                 ← Conservé
"$$$/MonPlugin/NewFeature=Export to Cloud"        ← NOUVEAU (en anglais)
"$$$/MonPlugin/Modified=New text here"            ← MODIFIÉ (en anglais)
```

**Action traducteur** : Chercher les clés en anglais et les traduire.

---

### Workflow 3 : **COMPARE** → **EXTRACT** → **INJECT**

**Étape 1 : EXTRACT génère TRANSLATE_fr.txt** :
```
# ======================================================================
# NOUVELLES CLÉS (50)
# ======================================================================

[KEY] $$$/MonPlugin/NewFeature
[EN]  Export to Cloud
[FR] →

# ======================================================================
# CLÉS MODIFIÉES (12)
# ======================================================================

[KEY] $$$/MonPlugin/Modified
[EN AVANT]  Old text
[EN APRÈS]  New text here
[FR ACTUEL] Ancien texte
[FR] →
```

**Étape 2 : Traducteur édite `TRANSLATE_fr.txt`** :
```
[FR] → Exporter vers le Cloud

[FR] → Nouveau texte ici
```

**Étape 3 : **INJECT** fusionne dans `TranslatedStrings_fr.txt`** :
```
"$$$/MonPlugin/Menu/File=Fichier"                 ← Conservé
"$$$/MonPlugin/NewFeature=Exporter vers le Cloud" ← Fusionné
"$$$/MonPlugin/Modified=Nouveau texte ici"        ← Fusionné
```

**Bonus : **SYNC** avec `UPDATE_xx.json` ajoute marqueurs** :
```
"$$$/MonPlugin/Menu/File=Fichier"
-- [NEW] To translate
"$$$/MonPlugin/NewFeature=Exporter vers le Cloud"
-- [NEEDS_REVIEW] English text was modified
"$$$/MonPlugin/Modified=Nouveau texte ici"
```

#### Les marqueurs [NEW] et [NEEDS_REVIEW]

> ℹ️ Ces marqueurs n'apparaissent que dans le cadre du [Workflow 3](#Workflow-3--COMPARE-→-EXTRACT-→-INJECT).

##### ❌ N'apparaissent PAS avec :
- Workflow nouveau plugin (duplication simple)
- **AUTO-SYNC** (workflow standard)

##### ✅ Apparaissent UNIQUEMENT avec :
- **COMPARE** → **SYNC** (avec `UPDATE_xx.json`)

##### A quoi servent-ils ?
Dans un flux spécifique de traduction de grande ampleur, permet de mettre l'accent sur les clés qui requiert une attention particulière car elles sont "noyées dans la masse" au sein du fichier `TranslatedString_xx.txt`.
Sachant qu'il est préférable d'utiliser un autre fichier spécialisé pour cette tâche... Plus d'infos : [SYNC.md](../../3_Translator/__doc/fr/commandes/SYNC.md)

##### Code source responsable

```python
# TR_sync.py ligne 131-141
# UNIQUEMENT si update_data fourni via COMPARE
if update_data and key in changed_keys:
    markers[key] = "-- [NEEDS_REVIEW] English text was modified"

if update_data:
    markers[key] = "-- [NEW] To translate"
```

---

## Quel workflow choisir ?

### Nouveau plugin LrC (première localisation)
→ **Workflow 1 : Extractor → Applicator**
- ***Extractor***
- ***Applicator***
- Dupliquer `TranslatedStrings_xx.txt` pour chaque langue
- Envoyer aux traducteurs

**Pourquoi** : Simple, direct, pas besoin de complexité.

---

### Plugin Lrc existant avec quelques changements
→ **Workflow 2 : Extractor → Translator → AUTO-SYNC**
- ***Extractor***
- ***Translator***
- **AUTO-SYNC**
- Les traducteurs recherchent visuellement les clés en anglais dans le fichier complet.

**Pourquoi** : Rapide, automatique, pas de fichiers intermédiaires.

---

### Plugin avec gros changements + traducteurs pro
→ **Workflow 3 : COMPARE → EXTRACT → INJECT**
- **COMPARE** (analyse des différences)
- **EXTRACT** (génère `TRANSLATE_xx.txt` avec uniquement changements)
- Traducteurs éditent `TRANSLATE_xx.txt`
- **INJECT** (fusionne dans `TranslatedStrings_xx.txt`)
- **SYNC** avec `UPDATE_en.json` (ajoute marqueurs optionnels)

**Pourquoi** : Isolation complète, contrôle fin, marqueurs pour traducteurs pro.

---

## Résumé technique

| Workflow | Utilise UPDATE_en.json | Marqueurs [NEW]/[NEEDS_REVIEW] | Fichier traducteur |
|----------|------------------------|--------------------------------|--------------------|
| **Nouveau plugin** | ❌ Non | ❌ Non | `TranslatedStrings_xx.txt` (complet) |
| **AUTO-SYNC** | ❌ Non | ❌ Non | `TranslatedStrings_xx.txt` (complet) |
| **COMPARE** → **EXTRACT** → **INJECT** | ✅ Oui | ❌ Non (sauf si SYNC après) | `TRANSLATE_xx.txt` (partiel) |
| **COMPARE** → **SYNC** | ✅ Oui | ✅ Oui | `TranslatedStrings_xx.txt` (avec marqueurs) |

---

## Documentation associée

### Guides pour les développeurs

| Ressource | Description |
| --- | --- |
| 🗒 [Installation nouveau plugin](dev/01_Installation.md) | *Première mise en place* |
| 🗒 [Maintenance](dev/02_Maintenance.md) | *Workflow AUTO-SYNC quotidien* |
| 🗒 [Workflows avancés](dev/03_Avance.md) | *COMPARE/EXTRACT/INJECT* |

### Guides pour les traducteurs

| Ressource | Description |
| --- | --- |
| 🗒 [Contributeur simple](trad/01_Contributeur_simple.md) | *Fichier existant, prêt à traduire* |
| 🗒 [Contributeur débrouillard](trad/02_Contributeur_debrouillard.md) | *Créer le fichier soi-même* |
| 🗒 [Contributeur professionnel](trad/03_Contributeur_pro.md) | *Outils CAT et gros volumes* |

### Documentation technique
- [Lisez-moi.md](Lisez-moi.md) — Documentation technique complète

---

| 📜 | Traçabilité |  |  |
|--|--|--|--|
| **Nom** | *WORKFLOWS_COMPARAISON.md* | **Version** | 1.1 |
| **Type** | Aide - choix - compréhension | **Langue** | FR - *[EN](../en/WORKFLOWS_COMPARAISON.md)* |
| **Projet GitHub** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-02 |
| **Licence** | Open source | | |
