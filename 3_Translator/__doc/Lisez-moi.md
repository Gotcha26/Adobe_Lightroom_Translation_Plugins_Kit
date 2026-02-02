# Translator - Documentation technique

**Version 7.0 | Janvier 2026**

## Vue d'ensemble

Translator est le troisième outil de la chaîne de localisation. Son rôle est de gérer l'évolution des traductions au fil du temps.

**Nouveauté v7.0** : Ajout de INSTALL et AUTO-SYNC pour simplifier drastiquement le workflow quotidien.

## Architecture du projet

```
3_Translator/
├── Translator_main.py     ← Point d'entrée (menu + CLI)
├── TM_common.py             ← Fonctions communes (parser, utils, UI)
├── TM_install.py            ← Commande INSTALL (nouvelle v7.0)
├── TM_autosync.py           ← Commande AUTO-SYNC (nouvelle v7.0) ⭐
├── TM_compare.py            ← Commande COMPARE (diff entre 2 versions EN)
├── TM_extract.py            ← Commande EXTRACT (génère TRANSLATE_xx.txt)
├── TM_inject.py             ← Commande INJECT (réinjecte les traductions)
├── TM_sync.py               ← Commande SYNC (synchronise les langues)
└── __doc/
    └── Lisez-moi.md         ← Ce fichier
```

L'architecture est modulaire avec une commande par module. Chaque commande peut être utilisée indépendamment ou via le menu interactif.

---

## 🎯 Les commandes principales (Recommandées)

### 1. INSTALL - Installation initiale

**Cas d'usage** : Première installation des fichiers de traduction dans le plugin.

Copie les fichiers `TranslatedStrings_xx.txt` depuis la dernière extraction Extractor vers la racine du plugin.

```
Extractor output:
  __i18n_tmp__/1_Extractor/20260131_120000/
    └── TranslatedStrings_en.txt

          │
          ▼
       INSTALL
          │
          ▼

Plugin root:
  plugin.lrplugin/
    └── TranslatedStrings_en.txt  ← Copié ici
```

**Fichiers installés** :
- `TranslatedStrings_en.txt` (référence anglaise)
- Autres fichiers de langue si présents dans l'extraction

**Quand l'utiliser** :
- ✅ Première initialisation du plugin multilingue
- ⚠️ Des fichiers existent déjà ? Utilisez AUTO-SYNC à la place

**Commande CLI** :
```bash
python Translator_main.py install --plugin-path ./plugin.lrplugin
```

---

### 2. AUTO-SYNC - Synchronisation automatique ⭐

**Cas d'usage** : Maintenance courante après modification du code.

**C'est la commande à utiliser 99% du temps !**

Détecte automatiquement la dernière extraction et synchronise tous les fichiers de langue existants.

```
Dernière extraction détectée:
  __i18n_tmp__/1_Extractor/20260131_150000/
    └── TranslatedStrings_en.txt (nouvelle version)

          │
          ▼
      AUTO-SYNC ⭐
          │
          ├─→ Synchronise TranslatedStrings_fr.txt
          ├─→ Synchronise TranslatedStrings_de.txt
          └─→ Synchronise TranslatedStrings_es.txt
          │
          ▼

Output:
  __i18n_tmp__/3_Translator/20260131_151000/
    ├── TranslatedStrings_fr.txt  ← Synchronisé (nouvelles clés ajoutées)
    ├── TranslatedStrings_de.txt  ← Synchronisé (nouvelles clés ajoutées)
    └── TranslatedStrings_es.txt  ← Synchronisé (nouvelles clés ajoutées)
```

**Ce que fait AUTO-SYNC** :
1. Détecte la dernière extraction Extractor
2. Trouve tous les fichiers `TranslatedStrings_xx.txt` existants dans le plugin
3. Pour chaque fichier de langue :
   - Ajoute les nouvelles clés avec la valeur EN par défaut
   - Met à jour les clés existantes (conserve les traductions)
   - Supprime les clés obsolètes
   - Préserve toutes les traductions existantes
4. Génère les fichiers synchronisés dans `__i18n_tmp__/3_Translator/`

**Note** : AUTO-SYNC ne génère PAS de marqueurs `[NEW]` ou `[NEEDS_REVIEW]`. C'est un workflow simple et rapide pour la maintenance quotidienne.

**Marqueurs (workflow COMPARE uniquement)** :
- `-- [NEW]` : Nouvelle clé, pas encore traduite
- `-- [NEEDS_REVIEW]` : Valeur anglaise modifiée, revoir la traduction

**IMPORTANT** : AUTO-SYNC ne génère PAS ces marqueurs. Ils sont réservés au workflow avancé COMPARE → SYNC.

**Quand l'utiliser** :
- ✅ Après avoir ajouté de nouvelles fonctionnalités au code
- ✅ Après avoir modifié des textes existants
- ✅ Pour synchroniser tous les fichiers de langue d'un coup

**Avantages** :
- ⚡ Ultra rapide : Une seule commande
- 🎯 Automatique : Détecte tout seul
- 🔒 Sûr : Préserve les traductions existantes
- 📊 Rapport : Affiche le résumé des changements

**Commande CLI** :
```bash
python Translator_main.py autosync --plugin-path ./plugin.lrplugin
```

**Exemple de sortie** :
```
► Langue: fr
  ✓ 15 ajoutées, 3 modifiées, 2 supprimées

► Langue: de
  ✓ 15 ajoutées, 3 modifiées, 2 supprimées

✓ 2 fichier(s) synchronisé(s)
```

---

## 🔧 Les commandes avancées (Usage spécifique)

Ces commandes sont conservées pour des cas d'usage avancés mais ne sont généralement pas nécessaires avec AUTO-SYNC.

### 3. COMPARE - Détection des changements

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

**Quand l'utiliser** :
- ⚠️ Workflow avancé avec EXTRACT/INJECT
- ⚠️ Besoin de changelog détaillé

**Note** : AUTO-SYNC rend cette commande optionnelle dans la plupart des cas.

---

### 4. EXTRACT - Isolation des nouvelles clés

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

**Quand l'utiliser** :
- ⚠️ Workflow avancé avec traducteurs externes sans GitHub
- ⚠️ Besoin de fichiers partiels

**Note** : AUTO-SYNC rend cette commande optionnelle pour les workflows GitHub.

---

### 5. INJECT - Fusion des traductions

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
Si une clé est vide dans `TRANSLATE_xx.txt`, INJECT utilise la valeur anglaise par défaut depuis `UPDATE_en.json`.

**Quand l'utiliser** :
- ⚠️ Workflow avancé avec EXTRACT
- ⚠️ Traducteurs travaillent sur fichiers partiels

**Note** : AUTO-SYNC rend cette commande optionnelle.

---

### 6. SYNC - Synchronisation manuelle

Synchronise un fichier de langue avec la version anglaise de référence.

```
UPDATE_en.json              TranslatedStrings_fr.txt
TranslatedStrings_en.txt    (langue étrangère)
(référence)
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
    ├── -- [NEW] To translate
    ├── "$$$/App/NewKey=New Key"
    ├── -- [NEEDS_REVIEW] English text was modified
    ├── "$$$/App/Changed=Old Translation"
    ├── "$$$/App/Existing=Traduction existante"
    └── (clé obsolète supprimée)
```

**Marqueurs ajoutés :**
- `[NEW]` : Nouvelle clé, pas encore traduite
- `[NEEDS_REVIEW]` : Valeur anglaise modifiée, revoir la traduction

**Quand l'utiliser** :
- ⚠️ Synchroniser UN SEUL fichier de langue manuellement
- ⚠️ Workflow avancé avec contrôle fin

**Note** : AUTO-SYNC fait la même chose mais pour TOUS les fichiers d'un coup.

---

## 🚀 Workflows recommandés

### Workflow 1 : Initialisation (Première fois)

**Situation** : Plugin jamais localisé, première installation.

```bash
# 1. Extraire les chaînes du code
[Option 1] Extractor

# 2. Installer les fichiers de traduction
[Option 3] Translation Manager → [1] INSTALL

# 3. Appliquer dans le code
[Option 2] Applicator

# 4. Tester dans Lightroom
```

**Durée** : 15-30 minutes

---

### Workflow 2 : Maintenance (Quotidien) ⭐

**Situation** : Plugin déjà localisé, nouvelles fonctionnalités ajoutées.

```bash
# 1. Développer normalement

# 2. Extraire les nouvelles chaînes
[Option 1] Extractor

# 3. Synchroniser AUTOMATIQUEMENT tous les fichiers
[Option 3] Translation Manager → [2] AUTO-SYNC

# 4. Copier dans le plugin
cp __i18n_tmp__/3_Translator/<timestamp>/TranslatedStrings_*.txt ./plugin.lrplugin/

# 5. Commit sur GitHub
git add .
git commit -m "i18n: Add new translation keys"
git push
```

**Durée** : 5 minutes

**C'est le workflow à utiliser 99% du temps !**

---

### Workflow 3 : Avancé (Cas spécifiques)

**Situation** : Workflow établi avec COMPARE/EXTRACT/INJECT.

```bash
# 1. Extraire
[Option 1] Extractor

# 2. Comparer
[Option 3] Translation Manager → [3] COMPARE

# 3. Extraire les clés partielles
[4] EXTRACT

# 4. Envoyer TRANSLATE_xx.txt aux traducteurs

# 5. Recevoir les traductions

# 6. Injecter
[5] INJECT

# 7. Finaliser
[6] SYNC
```

**Durée** : 15-30 minutes

**Note** : Ce workflow est conservé pour compatibilité mais AUTO-SYNC le remplace dans la plupart des cas.

---

## 📊 Comparaison des workflows

| Critère | AUTO-SYNC ⭐ | COMPARE+EXTRACT+INJECT+SYNC |
|---------|-------------|----------------------------|
| **Étapes** | 1 commande | 4 commandes |
| **Détection automatique** | ✅ Oui | ❌ Non (manuel) |
| **Fichiers intermédiaires** | ❌ Non | ✅ TRANSLATE_xx.txt |
| **Complexité** | ✅ Simple | ⚠️ Complexe |
| **Durée** | 1 minute | 10-15 minutes |
| **Cas d'usage** | 99% des cas | Workflows établis |

---

## 🎓 Format des fichiers générés

### TranslatedStrings_xx.txt (synchronisés)

```
"$$$/Prefix/Category/Key=Default value"
-- [NEW] To translate
"$$$/Prefix/Category/NewKey=New value"
-- [NEEDS_REVIEW] English text was modified
"$$$/Prefix/Category/ModifiedKey=Old translation"
```

**Structure :**
- Clés existantes : Préservées telles quelles
- Nouvelles clés : Marqueur `-- [NEW]` en début de ligne
- Clés modifiées : Marqueur `-- [NEEDS_REVIEW]` en début de ligne
- Clés obsolètes : Supprimées automatiquement

**Avantage du nouveau format :**
- Les marqueurs sont HORS de la chaîne de traduction
- Visuellement propre même en production
- Faciles à repérer pour les traducteurs
- Ne polluent pas l'affichage dans Lightroom

### UPDATE_en.json (COMPARE)

```json
{
  "metadata": {
    "timestamp": "20260131_151000",
    "old_file": "TranslatedStrings_en_v1.txt",
    "new_file": "TranslatedStrings_en_v2.txt"
  },
  "added": [
    {"key": "$$$/App/NewFeature", "value": "New feature text"}
  ],
  "changed": [
    {
      "key": "$$$/App/Modified",
      "old_value": "Old text",
      "new_value": "New text"
    }
  ],
  "deleted": [
    {"key": "$$$/App/Obsolete", "value": "Removed feature"}
  ],
  "unchanged": [...]
}
```

### TRANSLATE_xx.txt (EXTRACT)

```
"$$$/Prefix/NewKey1=[NEW] "
"$$$/Prefix/NewKey2=[NEW] "
"$$$/Prefix/ModifiedKey=[NEEDS_REVIEW] Old translation here"
```

Fichiers légers contenant uniquement les clés à traduire.

---

## ⚙️ Configuration

Translator utilise la structure `__i18n_tmp__` automatiquement si le plugin est configuré.

**Chemins par défaut :**
```
plugin.lrplugin/
└── __i18n_tmp__/
    ├── 1_Extractor/          ← Source de TranslatedStrings_en.txt
    └── 3_Translator/ ← Sortie INSTALL/AUTO-SYNC/SYNC
```

---

## 💡 Conseils d'utilisation

### Pour les développeurs

1. **Utilisez AUTO-SYNC** pour 99% des cas
2. **INSTALL** uniquement pour la première initialisation
3. **Outils avancés** uniquement si workflow établi
4. **Committez sur GitHub** pour permettre les Pull Requests

### Pour les traducteurs

1. Cherchez les marqueurs `[NEW]` et `[NEEDS_REVIEW]`
2. Traduisez les valeurs
3. Supprimez les marqueurs après traduction
4. Créez une Pull Request sur GitHub

---

## ❓ FAQ

### Quand utiliser AUTO-SYNC vs SYNC ?

**AUTO-SYNC** :
- Synchronise TOUS les fichiers de langue d'un coup
- Détecte automatiquement la dernière extraction
- Recommandé pour la maintenance quotidienne

**SYNC** :
- Synchronise UN SEUL fichier de langue
- Nécessite de spécifier les fichiers manuellement
- Pour workflows avancés avec contrôle fin

### Les commandes COMPARE/EXTRACT/INJECT sont-elles obsolètes ?

**Non**, elles sont conservées pour :
- Workflows établis en entreprise
- Cas d'usage spécifiques (traducteurs sans GitHub)
- Génération de changelogs détaillés

Mais **AUTO-SYNC les remplace** dans 99% des cas.

### Puis-je combiner AUTO-SYNC avec les outils avancés ?

**Oui !**

Exemple :
1. AUTO-SYNC pour synchroniser rapidement
2. COMPARE pour générer un changelog détaillé
3. EXTRACT pour envoyer des fichiers partiels à un traducteur externe

---

## 📚 Ressources

- [Documentation principale](../../Lisez-moi.md)
- [Documentation Extractor](../../1_Extractor/__doc/)
- [Documentation Applicator](../../2_Applicator/__doc/)

---

**Version** : 7.0
**Dernière mise à jour** : 2026-01-31
**Nouveautés v7.0** : INSTALL et AUTO-SYNC
