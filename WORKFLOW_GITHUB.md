# Workflow de Traduction via GitHub

## Vue d'ensemble

Ce workflow est **recommandé pour les plugins open-source hébergés sur GitHub**. Il est simple, naturel et utilise les outils que les contributeurs connaissent déjà : Git et GitHub.

### Pourquoi ce workflow ?

- ✅ **Simple** : Édition directe des fichiers `.txt` dans GitHub
- ✅ **Traçable** : Historique Git complet de toutes les modifications
- ✅ **Collaboratif** : Review du développeur avant merge
- ✅ **Standard** : Workflow classique de contribution open-source
- ✅ **Aucun outil externe** : Juste GitHub et Git
- ✅ **Transparent** : Tout le monde voit qui a traduit quoi

### Cas d'usage idéal

- Plugin hébergé sur GitHub (public ou privé)
- Traducteurs techniques (à l'aise avec Git/GitHub)
- Traductions incrémentales (quelques clés à la fois)
- Besoin de review et validation avant intégration

---

## Pour le développeur

### Initialisation : Première localisation du plugin

Si votre plugin n'a jamais été localisé, suivez d'abord ces étapes :

#### 1. Extraire les chaînes du code

```bash
python LocalizationToolkit.py
# Sélectionner [1] Extractor
```

**Résultat** : Fichier `TranslatedStrings_en.txt` généré dans `__i18n_tmp__/1_Extractor/<timestamp>/`

#### 2. Appliquer les clés LOC dans le code

```bash
python LocalizationToolkit.py
# Sélectionner [2] Applicator
```

**Résultat** : Code Lua modifié avec des appels `LOC "$$$/Key=Default"`

#### 3. Tester dans Lightroom

Rechargez le plugin et vérifiez que tout fonctionne.

#### 4. Commit initial

```bash
# Copier le fichier EN dans le plugin
cp __i18n_tmp__/1_Extractor/<timestamp>/TranslatedStrings_en.txt ./plugin.lrplugin/

# Commit
git add .
git commit -m "i18n: Add localization support

- Extract all hardcoded strings
- Add TranslatedStrings_en.txt
- Replace hardcoded strings with LOC calls

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push
```

✅ **Votre plugin est maintenant prêt pour les traductions !**

---

### Maintenance : Ajout de nouvelles fonctionnalités

#### 1. Développer normalement

Ajoutez votre nouvelle fonctionnalité avec des chaînes en dur (comme d'habitude).

```lua
-- Nouveau code
local dialog = LrDialogs.confirm(
    "Do you want to delete this album?",
    "This action cannot be undone."
)
```

#### 2. Extraire les nouvelles chaînes

```bash
python LocalizationToolkit.py
# [1] Extractor
```

**Résultat** : Nouveau `TranslatedStrings_en.txt` avec les nouvelles clés

#### 3. Appliquer les LOC

```bash
# [2] Applicator
```

**Résultat** : Code modifié :

```lua
-- Code localisé
local dialog = LrDialogs.confirm(
    LOC "$$$/MyPlugin/Dialogs/DeleteConfirm=Do you want to delete this album?",
    LOC "$$$/MyPlugin/Dialogs/DeleteWarning=This action cannot be undone."
)
```

#### 4. Propager les nouvelles clés dans toutes les langues

**Option A : Manuellement (si 1-2 clés)**

Ouvrez chaque fichier `TranslatedStrings_xx.txt` et ajoutez les nouvelles lignes avec `[NEW]`.

**Option B : Avec SYNC (si 5+ clés)**

```bash
python LocalizationToolkit.py
# [3] Translation Manager
# [4] SYNC

# Sélectionner :
# - Référence EN : __i18n_tmp__/1_Extractor/<nouveau_timestamp>/TranslatedStrings_en.txt
# - Fichiers existants : plugin.lrplugin/TranslatedStrings_*.txt
```

**Résultat** : Tous les fichiers de langue mis à jour avec les nouvelles clés marquées `[NEW]`.

#### 5. Copier dans le plugin

```bash
# Copier la nouvelle version EN
cp __i18n_tmp__/1_Extractor/<timestamp>/TranslatedStrings_en.txt ./plugin.lrplugin/

# Si vous avez utilisé SYNC, copier aussi les autres langues
cp __i18n_tmp__/3_TranslationManager/<timestamp>/TranslatedStrings_*.txt ./plugin.lrplugin/
```

#### 6. Commit et push

```bash
git add .
git commit -m "feat: Add album deletion confirmation dialog

- Add new confirmation dialog for album deletion
- Extract new strings: DeleteConfirm, DeleteWarning
- Mark new keys with [NEW] for translators

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push
```

✅ **Les traducteurs peuvent maintenant voir les nouvelles clés à traduire !**

---

### Réception d'une Pull Request de traduction

#### 1. Review de la PR

Vérifiez :
- ✅ Les placeholders (`%s`, `%d`, `\n`) sont préservés
- ✅ Le format du fichier est correct
- ✅ Pas de clés manquantes
- ✅ Les traductions ont du sens (si vous connaissez la langue)

**Exemple de diff à reviewer** :

```diff
# TranslatedStrings_fr.txt

- "$$$/Piwigo/Dialogs/DeleteConfirm=[NEW] Do you want to delete this album?"
+ "$$$/Piwigo/Dialogs/DeleteConfirm=Voulez-vous supprimer cet album ?"

- "$$$/Piwigo/Dialogs/DeleteWarning=[NEW] This action cannot be undone."
+ "$$$/Piwigo/Dialogs/DeleteWarning=Cette action ne peut pas être annulée."

- "$$$/Piwigo/API/AlbumsCreated=[NEW] Albums created: %s"
+ "$$$/Piwigo/API/AlbumsCreated=Albums créés : %s"
```

✅ **Tout est correct** : Les placeholders sont préservés, le format est bon.

#### 2. Commenter si nécessaire

Si quelque chose ne va pas :

```markdown
@traducteur Merci pour la traduction !

Petite remarque ligne 42 :
- Le placeholder `%s` a été oublié
- Il faut : `Albums créés : %s` (pas `Albums créés`)

Peux-tu corriger ? Merci !
```

#### 3. Merge

```bash
git merge pr/123
git push
```

#### 4. Tester

Changez la langue de votre système et testez dans Lightroom.

---

## Pour le traducteur

### Contribuer une nouvelle traduction

#### 1. Fork du repository

Sur GitHub, cliquez sur **Fork** en haut à droite.

#### 2. Cloner votre fork (optionnel, peut être fait directement sur GitHub)

```bash
git clone https://github.com/VOTRE_USERNAME/nom-du-plugin.git
cd nom-du-plugin/plugin.lrplugin
```

#### 3. Identifier les clés à traduire

**Option A : Chercher les marqueurs `[NEW]`**

Ouvrez le fichier `TranslatedStrings_fr.txt` et cherchez les lignes avec `[NEW]` :

```
"$$$/Piwigo/Dialogs/DeleteConfirm=[NEW] Do you want to delete this album?"
```

**Option B : Comparer avec la version EN**

Si le fichier n'existe pas encore :

```bash
# Créer le fichier FR en copiant EN
cp TranslatedStrings_en.txt TranslatedStrings_fr.txt
```

Puis traduisez toutes les valeurs après le `=`.

#### 4. Traduire les clés

**Important** :
- ✅ Traduisez UNIQUEMENT le texte après le `=`
- ✅ Préservez les placeholders : `%s`, `%d`, `\n`, `\t`
- ✅ Gardez les espaces autour des placeholders
- ❌ Ne modifiez PAS la clé (avant le `=`)

**Exemple** :

```diff
# Avant
"$$$/Piwigo/Dialogs/DeleteConfirm=[NEW] Do you want to delete this album?"
"$$$/Piwigo/API/AlbumsCreated=[NEW] Albums created: %s, updated: %s"

# Après
"$$$/Piwigo/Dialogs/DeleteConfirm=Voulez-vous supprimer cet album ?"
"$$$/Piwigo/API/AlbumsCreated=Albums créés : %s, mis à jour : %s"
```

#### 5. Commit et Push

```bash
# Si vous travaillez localement
git add TranslatedStrings_fr.txt
git commit -m "i18n(fr): Add French translations for album deletion"
git push origin main

# Ou directement dans GitHub (bouton "Edit this file")
```

#### 6. Créer une Pull Request

Sur GitHub :
1. Cliquez sur **Pull Request**
2. Titre : `i18n(fr): Add French translations for album deletion`
3. Description :
   ```markdown
   Translated 15 new keys added in commit abc123:
   - DeleteConfirm
   - DeleteWarning
   - AlbumsCreated
   - ...

   All placeholders preserved (%s, %d).
   ```
4. Cliquez sur **Create Pull Request**

✅ **C'est fait !** Le développeur va review et merger votre contribution.

---

### Traduire un plugin depuis zéro

Si aucune traduction n'existe encore pour votre langue :

#### 1. Fork et clone

```bash
git clone https://github.com/VOTRE_USERNAME/nom-du-plugin.git
cd nom-du-plugin/plugin.lrplugin
```

#### 2. Créer le fichier de langue

```bash
cp TranslatedStrings_en.txt TranslatedStrings_fr.txt
```

#### 3. Traduire progressivement

Vous n'êtes **pas obligé de tout traduire** d'un coup !

**Workflow recommandé** :
1. Traduisez les clés les plus visibles (dialogs, menus)
2. Commit et PR
3. Puis traduisez les messages d'erreur
4. Commit et PR
5. Etc.

**Exemple de commit incrémental** :

```bash
# Première session : Traduire les dialogs (20 clés)
git commit -m "i18n(fr): Translate main dialogs (20 keys)"

# Deuxième session : Traduire les erreurs API (15 clés)
git commit -m "i18n(fr): Translate API error messages (15 keys)"

# Etc.
```

✅ **Avantage** : Petites PRs faciles à review, progression visible.

---

## Exemples concrets

### Exemple 1 : Ajout d'une nouvelle fonctionnalité (développeur)

**Contexte** : Vous ajoutez un bouton "Export to CSV".

**Workflow** :

```bash
# 1. Développer la fonctionnalité (avec textes en dur)
# ... code ...

# 2. Extraire et appliquer
python LocalizationToolkit.py
# [1] Extractor
# [2] Applicator

# 3. Propager dans toutes les langues
# [3] Translation Manager → [4] SYNC

# 4. Copier les fichiers
cp __i18n_tmp__/1_Extractor/20260131_120000/TranslatedStrings_en.txt ./
cp __i18n_tmp__/3_TranslationManager/20260131_120100/TranslatedStrings_*.txt ./

# 5. Commit
git add .
git commit -m "feat: Add CSV export functionality

- New export button in main dialog
- Extract 3 new strings: ExportCSV, ExportSuccess, ExportFailed
- Mark as [NEW] for translators

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
git push
```

**Durée** : 5 minutes

---

### Exemple 2 : Correction d'une typo (traducteur)

**Contexte** : Vous trouvez une faute dans une traduction française.

**Workflow** :

```bash
# 1. Directement sur GitHub, cliquer "Edit this file"
# 2. Corriger la ligne 42 :
# Avant : "Imposible de se connecter"
# Après : "Impossible de se connecter"

# 3. Commit message : "i18n(fr): Fix typo in login error message"
# 4. Create Pull Request
```

**Durée** : 1 minute

---

### Exemple 3 : Première traduction complète (traducteur)

**Contexte** : Plugin avec 278 clés, aucune traduction française.

**Workflow recommandé (progressif)** :

```bash
# Session 1 : Dialogs principaux (30 clés)
git commit -m "i18n(fr): Translate main dialogs (30 keys)"

# Session 2 : Messages d'erreur API (50 clés)
git commit -m "i18n(fr): Translate API errors (50 keys)"

# Session 3 : Settings et configuration (40 clés)
git commit -m "i18n(fr): Translate settings (40 keys)"

# Session 4 : Messages info et logs (80 clés)
git commit -m "i18n(fr): Translate info messages (80 keys)"

# Session 5 : Clés restantes (78 clés)
git commit -m "i18n(fr): Complete French translation (78 remaining keys)"
```

**Durée** : 5 sessions de 1-2h chacune (réparties sur plusieurs jours)

**Avantage** : Le développeur peut merger progressivement, et vous pouvez prendre des pauses.

---

## Avantages de ce workflow

### Pour le développeur

1. **Traçabilité complète** : Git log montre qui a traduit quoi et quand
2. **Review facile** : GitHub diff montre clairement les changements
3. **Pas d'outil externe** : Tout dans GitHub
4. **Automatisation possible** : GitHub Actions peut valider les placeholders
5. **Historique** : Facile de retrouver une ancienne traduction

### Pour le traducteur

1. **Familier** : Workflow standard de contribution open-source
2. **Progressif** : Pas besoin de tout traduire d'un coup
3. **Visible** : Tout le monde voit votre contribution
4. **Collaboratif** : Plusieurs traducteurs peuvent travailler ensemble
5. **Validation** : Le développeur review avant merge

---

## Outils complémentaires

### TranslationManager SYNC

Utile pour le développeur pour propager rapidement les nouvelles clés :

```bash
python LocalizationToolkit.py
# [3] Translation Manager → [4] SYNC
```

**Quand l'utiliser** :
- Vous avez ajouté 5+ nouvelles clés
- Vous voulez marquer les nouvelles clés avec `[NEW]` dans tous les fichiers
- Vous voulez synchroniser l'ordre des clés

### WebBridge (optionnel)

Si un traducteur n'est **vraiment pas** à l'aise avec GitHub, vous pouvez utiliser WebBridge :

1. Développeur exporte vers JSON
2. Traducteur utilise quicki18n.studio
3. Développeur importe et commit

**Mais** : Pour la plupart des contributeurs GitHub, l'édition directe du `.txt` est plus simple.

---

## Comparaison avec les autres workflows

| Critère | GitHub (ce workflow) | WebBridge | TranslationManager classique |
|---------|----------------------|-----------|------------------------------|
| **Simplicité** | ✅ Excellent | ⚠️ Moyen | ⚠️ Moyen |
| **Traçabilité** | ✅ Git log complet | ❌ Aucune | ⚠️ Limitée |
| **Review** | ✅ GitHub PR | ❌ Manuelle | ❌ Manuelle |
| **Collaboration** | ✅ Native GitHub | ⚠️ Fichier unique | ⚠️ Difficile |
| **Courbe d'apprentissage** | ✅ Standard Git | ⚠️ Nouvel outil | ⚠️ Format propriétaire |
| **Outils externes** | ❌ Aucun | ⚠️ quicki18n.studio | ❌ Aucun |
| **Historique** | ✅ Git blame | ❌ Non | ❌ Non |

---

## FAQ

### Dois-je utiliser SYNC à chaque fois ?

**Non**. SYNC est utile si vous avez ajouté beaucoup de nouvelles clés (5+) et que vous voulez les propager automatiquement dans tous les fichiers.

Pour 1-2 clés, vous pouvez les ajouter manuellement dans chaque fichier.

### Comment savoir quelles clés sont nouvelles ?

Cherchez le marqueur `[NEW]` dans les fichiers de langue :

```bash
grep "\[NEW\]" TranslatedStrings_fr.txt
```

Ou regardez le dernier commit du développeur sur GitHub.

### Puis-je traduire plusieurs langues en même temps ?

Oui ! Créez des fichiers pour chaque langue et faites une seule PR :

```
TranslatedStrings_fr.txt
TranslatedStrings_de.txt
TranslatedStrings_es.txt
```

### Le développeur peut-il modifier mes traductions ?

Oui, c'est normal dans un projet open-source. Si le développeur modifie une traduction, vous verrez le changement dans Git et pourrez discuter via GitHub issues si nécessaire.

### Comment tester mes traductions ?

Demandez au développeur de merger votre PR, puis :
1. Téléchargez le plugin
2. Changez la langue de votre système
3. Testez dans Lightroom

---

## Ressources

- [Comment faire une Pull Request sur GitHub](https://docs.github.com/en/pull-requests)
- [Git basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)
- [Format TranslatedStrings SDK Lightroom](https://developer.adobe.com/console)

---

**Date de création** : 2026-01-31
**Version** : 1.0
