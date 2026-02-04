# Guide i18n - Gestion des Traductions

Ce dossier contient les outils pour gérer automatiquement les traductions du projet.

## 📋 Table des matières

1. [Structure rapide](#structure-rapide)
2. [Démarrage rapide](#démarrage-rapide)
3. [Cas d'usage courants](#cas-dusage-courants)
4. [Workflow complet](#workflow-complet)
5. [Traductions externes](#traductions-externes)
6. [Vérifier l'état](#vérifier-létat-des-traductions)
7. [Dépannage](#dépannage)

---

## Structure rapide

### Outils disponibles

```
i18n/
├── extract_strings.py        # Extrait les chaînes du code
├── update_po.py              # Met à jour les traductions
├── compile_po.py             # Compile en fichiers binaires
├── init_language.py          # Initialise une nouvelle langue
├── sync_translations.py       # Fait tout en une seule commande
└── check_translations.py      # Vérifie l'état des traductions
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

**Vous modifiez le code ?** C'est simple en 3 étapes :

```bash
# 1. Modifiez votre code (enrobez les chaînes de _())
# 2. Synchronisez tout en une commande
python i18n/sync_translations.py

# 3. C'est fait ! ✨
```

Ou sur Windows, double-clic sur `sync_translations.bat`.

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

## Workflow complet

### Les 3 commandes de base

```bash
# 1. Extraire les chaînes du code dans messages.pot
python i18n/extract_strings.py

# 2. Mettre à jour les fichiers .po avec les nouvelles chaînes
python i18n/update_po.py

# 3. Compiler en fichiers .mo (utilisés à l'exécution)
python i18n/compile_po.py
```

Ou tous en une fois (recommandé) :

```bash
python i18n/sync_translations.py
```

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

---

## Points importants

### Bonnes pratiques

```python
# ✅ Bon
print(_("Bienvenue"))
msg = _("Erreur: {var}").format(var=variable)

# ❌ Mauvais
print("Bienvenue")                          # Pas de _()
msg = "Erreur: " + variable                 # Pas de _()
```

### Ordre d'exécution

1. Modifiez le code (ajouter/modifier/supprimer des chaînes `_()`)
2. Lancez `python i18n/sync_translations.py`

C'est tout ! Les trois étapes (extract → update → compile) se font automatiquement.

### Fichiers à ne pas toucher

- `locale/messages.pot` - Régénéré automatiquement
- `locale/*/LC_MESSAGES/messages.mo` - Fichiers binaires, générés automatiquement
- Fichiers `.po.bak` - Backups automatiques

---

## Dépannage

| Problème | Cause | Solution |
|----------|-------|----------|
| Le `.pot` ne change pas | Chaînes non enrobées de `_()` | Ajouter `_()` autour des chaînes |
| Traductions non à jour dans l'appli | `.po` modifiés mais pas compilés | Lancer `python i18n/compile_po.py` |
| Fichier `.po` corrompu | Édition incorrecte | Restaurer depuis `.po.bak` |

---

## Ressources utiles

- [Poedit](https://poedit.net/) - Éditeur graphique pour `.po` (gratuit et recommandé)
- [Format gettext](https://www.gnu.org/software/gettext/manual/gettext.html)
- [Python gettext](https://docs.python.org/3/library/gettext.html)

---
