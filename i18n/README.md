# Guide i18n - Gestion des Traductions

Ce dossier contient les outils pour gérer automatiquement les traductions du projet.

## 📋 Table des matières

1. [Structure rapide](#structure-rapide)
2. [Démarrage rapide](#démarrage-rapide)
3. [Cas d'usage courants](#cas-dusage-courants)
4. [Formatage automatique global](#formatage-automatique-global)
5. [Workflow complet](#workflow-complet)
6. [Traductions externes](#traductions-externes)
7. [Vérifier l'état](#vérifier-létat-des-traductions)
8. [Traduction assistée par IA](#traduction-assistée-par-ia-claude-gpt-etc-) ⭐ NOUVEAU
9. [Dépannage](#dépannage)

---

## Structure rapide

### Outils disponibles

**Outils d'automatisation (NOUVEAUX)** ⭐
```
├── check_ui.py                   # Détecte les chaînes UI console sans _()
├── check_reports.py              # Détecte les chaînes fichiers générés sans _()
├── auto_i18n.py                  # Enrobe automatiquement (gère f-strings)
└── auto_wrap_strings.py          # Enrobe simplement (fichier par fichier)
```

**Outils de traduction (essentiels)**
```
├── extract_strings.py           # Extrait les chaînes du code
├── update_po.py                 # Met à jour les traductions
├── compile_po.py                # Compile en fichiers binaires
├── init_language.py             # Initialise une nouvelle langue
├── sync_translations.py         # Fait tout en une seule commande (4 étapes)
├── check_translations.py        # Vérifie l'état des traductions
├── export_untranslated_chains.py  # Exporte fuzzy/non traduites pour IA ⭐ NOUVEAU
└── import_translated_chains.py    # Réimporte traductions depuis IA ⭐ NOUVEAU
```

### Structure des fichiers de traduction

```
locale/
├── messages.pot              # Template maître (à envoyer pour traduction)
├── en/LC_MESSAGES/
│   ├── messages.po           # Traduction anglaise
│   └── messages.mo           # Version compilée (ne pas toucher)
├── fr/LC_MESSAGES/           # Idem pour autres langues...
│   ├── messages.po
│   └── messages.mo
└── ...
```

---

## Démarrage rapide

**Vous modifiez le code ?** C'est simple :

```bash
# 1. Modifiez votre code (enrobez les chaînes de _())
# 2. Synchronisez tout en une commande (4 étapes automatiques)
python i18n/sync_translations.py

# Étape 0: Pré-vérifie les chaînes non traduites (informatif)
# Étape 1: Extrait les chaînes _(...)
# Étape 2: Met à jour les .po
# Étape 3: Compile les .mo

# 3. C'est fait ! ✨
```

Ou sur Windows, double-clic sur `sync_translations.bat`.

> **Note** : L'étape 0 vérifie automatiquement les chaînes non traduites via `check_ui.py` et `check_reports.py`. Si des chaînes HIGH sont détectées, elles sont listées (mais le processus continue).

### 🚀 5 minutes pour traiter TOUT le projet

Vous avez ajouté du code et voulez que tout soit traduit d'un coup ?

```bash
# 1. Scanner pour voir ce qui doit être traduit
python i18n/check_ui.py --confidence HIGH

# 2. Enrober automatiquement tout
python i18n/auto_i18n.py --all --apply

# 3. Synchroniser
python i18n/sync_translations.py

# ✅ C'est fait ! Vérifiez :
python i18n/check_translations.py
```

C'est tout ! Tous les chaînes détectées comme "HIGH confidence" sont maintenant enrobées et prêtes à être traduites.

---

## Cas d'usage courants

### ✏️ J'ajoute une nouvelle chaîne

**Code :**
```python
# ❌ Avant
print("Bienvenue")

# ✅ Après
print(_("Bienvenue"))
```

**Commande :**
```bash
python i18n/sync_translations.py
```

Résultat : La chaîne apparaît dans tous les fichiers `.po` (marquée `fuzzy` pour revoir).

### 🔄 Je modifie une chaîne existante

**Code :**
```python
# ❌ Avant
print(_("Erreur : fichier introuvable"))

# ✅ Après
print(_("ERREUR : Le fichier n'existe pas"))
```

**Commande :**
```bash
python i18n/sync_translations.py
```

Résultat : L'ancienne est supprimée, la nouvelle est ajoutée (marquée `fuzzy`).

### 🗑️ Je supprime une chaîne

**Commande :**
```bash
python i18n/sync_translations.py
```

Résultat : Chaîne supprimée de `messages.pot` et des `.po`.

### 🌍 J'ajoute une nouvelle langue

**Commande :**
```bash
python i18n/init_language.py fr    # Crée locale/fr/LC_MESSAGES/messages.po
python i18n/sync_translations.py   # Remplit avec les chaînes actuelles
```

Ensuite, ouvrez avec [Poedit](https://poedit.net/) pour traduire.

### 💬 Je modifie une chaîne ET je la retraduisis en Français ET Anglais

**Scénario** : Vous changez une chaîne du code ET vous voulez directement corriger les traductions FR et EN.

**Étapes** :

```bash
# 1. Modifiez le code
# Exemple : ligne 182 de tools/applicator/main.py
# print(_("Fichier introuvable"))
# ↓ devient
# print(_("Le fichier n'existe pas"))

# 2. Synchronisez
python i18n/sync_translations.py

# 3. Vérifiez les chaînes marquées fuzzy
python i18n/check_translations.py en -v
python i18n/check_translations.py fr -v
```

**Puis éditez les fichiers `.po`** :

- `locale/en/LC_MESSAGES/messages.po` - Modifiez la traduction anglaise
- `locale/fr/LC_MESSAGES/messages.po` - Modifiez la traduction française

Trouvez la chaîne marquée `#, fuzzy` et remplacez-la comme suit :

```po
# ❌ Avant (fuzzy)
#, fuzzy
msgid "Le fichier n'existe pas"
msgstr ""

# ✅ Après (corrigé et sans fuzzy)
msgid "Le fichier n'existe pas"
msgstr "The file does not exist"    # EN
```

**Important** :
- Supprimez la ligne `#, fuzzy`
- Remplissez le `msgstr` avec la traduction
- Enregistrez le fichier

**Puis recompiler** :

```bash
python i18n/compile_po.py fr
python i18n/compile_po.py en
```

Vous pouvez aussi utiliser [Poedit](https://poedit.net/) pour éditer graphiquement si vous préférez.

---

## Formatage automatique global

**Nouveau !** Trois outils pour automatiser l'ajout de `_()` sur l'ensemble du code.

### 🔍 1. Trouver les chaînes non traduites

Deux outils complémentaires analysent différents scopes du code :

#### `check_ui.py` — Interface console (print, input, erreurs)

```bash
# Scanner global
python i18n/check_ui.py

# Avec détails (liste complète)
python i18n/check_ui.py --verbose

# Fichier spécifique
python i18n/check_ui.py --file tools/translator/compare_langs.py

# Filtrer par confiance (uniquement HIGH)
python i18n/check_ui.py --confidence HIGH
```

**Scope** : Détecte les chaînes dans `print()`, `input()`, `c.error()`, `c.warning()`, etc.

#### `check_reports.py` — Fichiers générés (f.write dans with open)

```bash
# Scanner global
python i18n/check_reports.py

# Avec détails
python i18n/check_reports.py --verbose

# Uniquement HIGH
python i18n/check_reports.py --confidence HIGH
```

**Scope** : Détecte les chaînes dans `f.write()` au sein de blocs `with open(...) as f:` (rapports CHANGELOG, TRANSLATE_xx.txt, etc.).

> **Note** : `sync_translations.py` exécute automatiquement ces deux checks en **étape 0** (pré-vérification).

**Résultat** : Affiche par fichier :
- Nombre de chaînes non traduites
- Niveau de confiance (HIGH/MEDIUM/LOW)
- Contexte et numéro de ligne

### 🤖 2. Enrober automatiquement les chaînes

#### Option A : Auto i18n (recommandé, gère les f-strings)

```bash
# Aperçu avant modification
python i18n/auto_i18n.py --file tools/translator/compare_langs.py --preview

# Appliquer les modifications
python i18n/auto_i18n.py --file tools/translator/compare_langs.py --apply

# Tous les fichiers à la fois
python i18n/auto_i18n.py --all --apply
```

**Avantages :**
- Gère les f-strings complexes : `f"Texte {var}"` → `_("Texte {var}").format(var=var)`
- Ignore automatiquement les patterns techniques
- Mode aperçu avant de modifier
- Préserve le formatage

#### Option B : Auto wrap strings (plus simple, fichier par fichier)

```bash
# Aperçu
python i18n/auto_wrap_strings.py --file tools/translator/compare_langs.py --dry-run

# Appliquer
python i18n/auto_wrap_strings.py --file tools/translator/compare_langs.py

# Avec contrôle de confiance
python i18n/auto_wrap_strings.py --file tools/translator/compare_langs.py --confidence MEDIUM
```

### ✅ Workflow complet automatisé

```bash
# 1. Trouver les chaînes
python i18n/check_ui.py --confidence HIGH

# 2. Aperçu des modifications
python i18n/auto_i18n.py --file tools/translator/compare_langs.py --preview

# 3. Appliquer
python i18n/auto_i18n.py --file tools/translator/compare_langs.py --apply

# 4. Synchroniser les traductions
python i18n/sync_translations.py

# 5. Vérifier
python i18n/check_translations.py --verbose
```

### 📋 Exemple pratique

**Situation :** Vous avez ajouté du code avec des chaînes, et vous voulez les traduire automatiquement.

```bash
# 1. Scanner pour voir ce qui doit être traduit
python i18n/check_ui.py --file tools/new_feature.py --verbose

# 2. Voir les modifications proposées
python i18n/auto_i18n.py --file tools/new_feature.py --preview

# 3. Si ça vous plaît, appliquer
python i18n/auto_i18n.py --file tools/new_feature.py --apply

# 4. Finaliser
python i18n/sync_translations.py fr en
```

---

## Workflow complet

### Les 4 étapes de synchronisation

```bash
# Étape 0: Pré-vérifier les chaînes non traduites (automatique)
python i18n/check_ui.py --confidence HIGH
python i18n/check_reports.py --confidence HIGH

# Étape 1: Extraire les chaînes du code dans messages.pot
python i18n/extract_strings.py

# Étape 2: Mettre à jour les fichiers .po avec les nouvelles chaînes
python i18n/update_po.py

# Étape 3: Compiler en fichiers .mo (utilisés à l'exécution)
python i18n/compile_po.py
```

**Ou tout en une fois (recommandé)** :

```bash
python i18n/sync_translations.py
```

Ce script exécute automatiquement les **4 étapes** dans l'ordre :
- **Étape 0** : Pré-vérification (`check_ui` + `check_reports`) — informatif, ne bloque pas
- **Étape 1** : Extraction des chaînes `_()` → `.pot`
- **Étape 2** : Mise à jour `.po`
- **Étape 3** : Compilation `.mo`

Vous pouvez aussi limiter à une langue :

```bash
python i18n/sync_translations.py fr    # Français uniquement
python i18n/sync_translations.py en    # Anglais uniquement
```

---

## Traductions externes

### Envoyer pour traduction

**Fichier à envoyer** : `locale/messages.pot`

C'est le template maître avec **toutes les chaînes** à traduire.

**Procédure** :

1. **Vous (développeur)** :
   - Modifiez le code
   - Lancez `python i18n/sync_translations.py`
   - Envoyez `locale/messages.pot` au traducteur

2. **Traducteur** (avec [Poedit](https://poedit.net/)) :
   - Ouvre le `.pot`
   - Traduit les chaînes
   - Envoie `messages.po`

3. **Vous (retour)** :
   - Recevez `messages.po`
   - Placez dans `locale/xx/LC_MESSAGES/messages.po` (où `xx` = code langue)
   - Lancez `python i18n/compile_po.py xx`

### Appliquer une traduction reçue

```bash
# 1. Placer le fichier au bon endroit
cp messages_fr.po locale/fr/LC_MESSAGES/messages.po

# 2. Compiler
python i18n/compile_po.py fr

# 3. Optionnel : synchroniser avec les dernières chaînes
python i18n/sync_translations.py fr
```

---

## Vérifier l'état des traductions

```bash
# Toutes les langues
python i18n/check_translations.py

# Une langue spécifique
python i18n/check_translations.py fr

# Affichage détaillé (liste les chaînes non traduites)
python i18n/check_translations.py fr -v
```

Vous obtenez un résumé avec pourcentage de traduction et liste des chaînes `fuzzy` à revoir.

**Mode interactif** : Si chaînes fuzzy ou non traduites détectées, proposition d'export automatique pour traduction par IA.

---

## Traduction assistée par IA (Claude, GPT, etc.) 🤖

**Nouveau !** Workflow interactif pour traduire rapidement via IA (Claude, ChatGPT, DeepL, etc.).

### Workflow complet automatisé

```bash
# 1. Vérifier l'état (propose automatiquement l'export si problèmes)
python i18n/check_translations.py fr -v

# → Répondre "o" pour exporter
# → Fichier généré : tmp_chains_tofrom_translation.txt

# 2. Faire traduire le fichier par Claude/GPT
#    (Instructions incluses dans le fichier)

# 3. Import automatique (mode interactif)
python i18n/import_translated_chains.py

# → Détecte automatiquement la langue
# → Importe les traductions
# → Propose de vérifier

# 4. Vérification automatique
# → Lance check_translations.py avec -v
```

### Export manuel des chaînes à traduire

```bash
# Export tout (fuzzy + non traduites)
python i18n/export_untranslated_chains.py fr

# Seulement les fuzzy
python i18n/export_untranslated_chains.py fr --fuzzy-only

# Seulement les non traduites
python i18n/export_untranslated_chains.py fr --untranslated-only
```

**Résultat** : Génère `tmp_chains_tofrom_translation.txt` formaté avec :
- Instructions complètes pour l'IA
- Blocs msgid/msgstr structurés
- Préservation des codes de formatage ({1}, ^1, \n, etc.)

### Import des traductions

```bash
# Mode interactif (détecte la langue automatiquement)
python i18n/import_translated_chains.py

# Mode CLI classique
python i18n/import_translated_chains.py fr

# Sans backup
python i18n/import_translated_chains.py fr --no-backup

# Garder le fichier tmp
python i18n/import_translated_chains.py fr --keep-tmp
```

**Fonctionnalités** :
- Détection automatique de la langue depuis le fichier tmp
- Backup automatique (.po.backup)
- Recherche par correspondance exacte de msgid
- Suppression automatique des marqueurs fuzzy
- Proposition de vérification après import
- Proposition de suppression du fichier tmp

### Exemple pratique complet

```bash
# Scénario : 50 chaînes fuzzy en français à traduire

# 1. Check (interactif)
python i18n/check_translations.py fr -v
# → "Exporter pour traduction ? (o/n): o"

# 2. Ouvrir tmp_chains_tofrom_translation.txt
#    Copier le contenu dans Claude/GPT avec le prompt :
#    "Traduis ces chaînes .po en français selon les instructions"

# 3. Copier les traductions dans tmp_chains_tofrom_translation.txt

# 4. Import (interactif)
python i18n/import_translated_chains.py
# → Détecte "fr" automatiquement
# → "Lancer la vérification maintenant ? (o/n): o"

# 5. Vérification lancée automatiquement
# → Affiche les nouvelles stats avec -v
```

### Format du fichier tmp_chains_tofrom_translation.txt

```
════════════════════════════════════════════
INSTRUCTIONS POUR IA - TRADUCTION FICHIER .PO (FR)
════════════════════════════════════════════

[Instructions détaillées pour l'IA...]

════════════════════════════════════════════
DÉBUT DES CHAÎNES À TRADUIRE
════════════════════════════════════════════

────────────────────────────────────────────
ENTRÉE 1/50
────────────────────────────────────────────

msgid "Welcome to the application"
msgstr ""

────────────────────────────────────────────
ENTRÉE 2/50
────────────────────────────────────────────

msgid "File not found: {filename}"
msgstr ""

[...]
```

**Important** :
- Ne modifier QUE les lignes msgstr
- Ne PAS toucher aux msgid
- Préserver les codes {1}, ^1, \n, etc.
- Ne pas supprimer les lignes vides

### Chaîne interactive complète

Les trois scripts sont chainés interactivement :

```
check_translations.py
    ↓ (propose export)
export_untranslated_chains.py
    ↓ (propose import)
import_translated_chains.py
    ↓ (propose vérification)
check_translations.py -v
```

Une seule commande pour démarrer :
```bash
python i18n/check_translations.py fr -v
```

Puis répondre "o" à chaque étape pour workflow fluide.

---

## Points importants

### Bonnes pratiques

```python
# ✅ Bon
print(_("Bienvenue"))
msg = _("Erreur: {var}").format(var=variable)
label = _("Nom complet")

# ❌ Mauvais
print("Bienvenue")                          # Pas de _()
msg = "Erreur: " + variable                 # Pas de _()
filename = "data.json"                      # Fichier technique, pas traduire
```

### Ordre d'exécution standard

1. Modifiez le code
2. Lancez `python i18n/check_ui.py` (optionnel, pour vérifier l'UI)
3. Lancez `python i18n/check_reports.py` (optionnel, pour vérifier les fichiers générés)
4. Lancez `python i18n/auto_i18n.py --file <path> --preview` (optionnel, pour aperçu)
5. Lancez `python i18n/auto_i18n.py --file <path> --apply` (automatise les _())
6. Lancez `python i18n/sync_translations.py`

C'est tout ! Les quatre étapes (check → extract → update → compile) se font automatiquement via `sync_translations.py`.

**Note:** Les étapes 2-5 sont optionnelles si vous avez déjà enrobé vos chaînes de `_()` manuellement. `sync_translations.py` exécute toujours l'étape 2+3 (checks) automatiquement en mode informatif.

### Fichiers à ne pas toucher

- `locale/messages.pot` - Régénéré automatiquement
- `locale/*/LC_MESSAGES/messages.mo` - Fichiers binaires, générés automatiquement
- Fichiers `.po.bak` - Backups automatiques

---

## Dépannage

| Problème | Cause | Solution |
|----------|-------|----------|
| Le `.pot` ne change pas | Chaînes non enrobées de `_()` | Lancer `python i18n/auto_i18n.py --file <path> --apply` |
| Trop de chaînes UI détectées | Patterns non reconnus | Ajouter patterns à ignorer dans `check_ui.py` |
| Trop de chaînes reports détectées | Séparateurs ou JSON détectés | Ajouter patterns à `TECHNICAL_PATTERNS` dans `check_reports.py` |
| F-string pas enrobée correctement | Auto i18n ne gère pas ce cas | Modifier manuellement ou signaler l'issue |
| Traductions non à jour dans l'appli | `.po` modifiés mais pas compilés | Lancer `python i18n/compile_po.py` |
| Fichier `.po` corrompu | Édition incorrecte | Restaurer depuis `.po.bak` |
| Auto wrap ne trouve pas la chaîne | Guillemets imbriqués ou f-string | Utiliser `auto_i18n.py` à la place |
| Warnings HIGH dans sync_translations | Chaînes non enrobées de `_()` | Consulter `check_ui.py --confidence HIGH -v` ou `check_reports.py --confidence HIGH -v` |
| Import ne trouve pas le msgid | msgid modifié manuellement | Vérifier correspondance exacte avec `messages.po` |
| Langue non détectée en mode interactif | Fichier tmp corrompu | Lancer `python i18n/import_translated_chains.py <lang>` en mode CLI |
| Traductions IA incorrectes | Prompt ou contexte insuffisant | Ajouter contexte dans instructions du fichier tmp |

---

## Ressources utiles

- [Poedit](https://poedit.net/) - Éditeur graphique pour `.po` (gratuit et recommandé)
- [Format gettext](https://www.gnu.org/software/gettext/manual/gettext.html)
- [Python gettext](https://docs.python.org/3/library/gettext.html)

---
