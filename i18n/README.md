# Guide i18n - Gestion des Traductions

Ce dossier contient les outils pour gérer automatiquement les traductions du projet.

## Structure

```
i18n/
├── README.md                 # Ce fichier
├── extract_strings.py        # Extrait les chaînes du code
├── update_po.py             # Met à jour les traductions
├── compile_po.py            # Compile en fichiers binaires
└── init_language.py         # Initialise une nouvelle langue
```

## Fichiers de traduction

```
locale/
├── messages.pot             # Template maître (source de vérité)
├── en/LC_MESSAGES/
│   ├── messages.po          # Traduction anglaise
│   └── messages.mo          # Version compilée (binaire)
├── fr/LC_MESSAGES/          # Autres langues...
│   ├── messages.po
│   └── messages.mo
└── ...
```

---

## 📋 Cas d'usage courants

### Cas 1️⃣ : J'ajoute une nouvelle chaîne dans le code

**Avant (❌ Ne pas faire) :**
```python
print("Bonjour le monde")  # Chaîne en dur, pas traduite
```

**Après (✅ Correct) :**
```python
print(_("Bonjour le monde"))  # Utiliser _()
```

**Puis exécuter :**
```bash
python i18n/extract_strings.py
python i18n/update_po.py
python i18n/compile_po.py
```

**Ce qui se passe :**
1. La chaîne est extraite dans `locale/messages.pot`
2. Elle est ajoutée aux `.po` existants (marquée `fuzzy`)
3. Elle est compilée en `.mo`

---

### Cas 2️⃣ : Je modifie une chaîne existante

**Avant :**
```python
print(_("Erreur : fichier introuvable"))
```

**Après :**
```python
print(_("ERREUR : Le fichier n'existe pas"))
```

**Puis exécuter :**
```bash
python i18n/extract_strings.py
python i18n/update_po.py
python i18n/compile_po.py
```

**Ce qui se passe :**
- L'ancienne chaîne est supprimée des `.po`
- La nouvelle chaîne est ajoutée (marquée `fuzzy`)
- Les traductions sont préservées pour les autres chaînes

⚠️ **Important** : Les traductions existantes pour cette chaîne sont perdues (c'est normal, elle a changé). Les traducteurs devront la retraduire.

---

### Cas 3️⃣ : Je supprime une chaîne du code

**Avant :**
```python
print(_("Cette chaîne ne sert plus"))
```

**Après :**
```python
# Chaîne supprimée
```

**Puis exécuter :**
```bash
python i18n/extract_strings.py
python i18n/update_po.py
python i18n/compile_po.py
```

**Ce qui se passe :**
- La chaîne est supprimée de `messages.pot`
- Elle est supprimée des `.po` (comme "obsolète")
- Les autres traductions sont conservées

---

### Cas 4️⃣ : J'ajoute une nouvelle langue

**Exécuter :**
```bash
python i18n/init_language.py fr
```

**Ce qui se passe :**
- Crée `locale/fr/LC_MESSAGES/messages.po`
- Copie toutes les chaînes du `.pot`
- Prête à être traduite

Ensuite, utilisez un éditeur `.po` (ex: [Poedit](https://poedit.net/)) pour traduire.

---

## 🚀 Workflow complet et rapide

### **Option 1️⃣ : Le plus facile (clic unique) 🎯**

#### Windows :
```bash
# Double-clic sur le fichier
sync_translations.bat

# Ou en ligne de commande
python i18n/sync_translations.py
```

#### Linux/Mac :
```bash
# Rendre exécutable (une seule fois)
chmod +x i18n/sync_translations.sh

# Puis lancer
./i18n/sync_translations.sh
```

### **Option 2️⃣ : Ligne de commande**

```bash
# Toutes les langues
python i18n/sync_translations.py

# Ou uniquement une langue
python i18n/sync_translations.py en     # Anglais
python i18n/sync_translations.py fr     # Français
```

### **Option 3️⃣ : Commande complète manuelle**

```bash
python i18n/extract_strings.py && python i18n/update_po.py && python i18n/compile_po.py
```

Ou sur Windows (PowerShell) :
```powershell
python i18n/extract_strings.py; python i18n/update_po.py; python i18n/compile_po.py
```

### **Mettre à jour UNE SEULE langue :**

```bash
# Avec le script automatisé
python i18n/sync_translations.py en    # Anglais uniquement
python i18n/sync_translations.py fr    # Français uniquement
```

---

## 📤 Transmettre pour traduction (Traducteurs externes)

### Fichier à envoyer

**Le SEUL fichier à transmettre** : `locale/messages.pot`

C'est le template maître qui contient **toutes les chaînes** à traduire.

**Pourquoi le `.pot` et pas le `.po` ?**
- ✅ `.pot` = template vierge (source de vérité)
- ❌ `.po` = traduction spécifique à une langue (déjà partiellement traduite)

### Procédure complète

**Toi (Développeur) :**
1. Tu modifies le code
2. Tu lances : `python i18n/sync_translations.py`
3. Tu envoies : `locale/messages.pot` au traducteur

**Traducteur externe :**
1. Reçoit : `locale/messages.pot`
2. Crée/met à jour : `messages_xx.po` avec [Poedit](https://poedit.net/) (où `xx` = code langue)
3. Envoie : `messages_xx.po`

**Toi (Développeur) - Application :**
1. Reçois : `messages_xx.po`
2. Places dans : `locale/xx/LC_MESSAGES/messages.po`
3. Lances : `python i18n/compile_po.py xx`
4. C'est appliqué ! ✨

---

## 📥 Appliquer une traduction reçue

### Cas 1️⃣ : Première traduction pour une nouvelle langue

**Reçu du traducteur :**
```
messages_fr.po (nouvelle traduction française)
```

**À faire :**

```bash
# 1. S'assurer que le répertoire existe
mkdir -p locale/fr/LC_MESSAGES

# 2. Placer le fichier
cp messages_fr.po locale/fr/LC_MESSAGES/messages.po

# 3. Compiler
python i18n/compile_po.py fr

# 4. Vérifier que messages.mo est généré
ls locale/fr/LC_MESSAGES/
```

### Cas 2️⃣ : Mise à jour d'une traduction existante

**Reçu du traducteur :**
```
messages_fr.po (mise à jour de la traduction)
```

**À faire :**

```bash
# 1. Remplacer le fichier
cp messages_fr.po locale/fr/LC_MESSAGES/messages.po

# 2. Compiler
python i18n/compile_po.py fr

# 3. Optionnel : Synchroniser avec les dernières chaînes du code
python i18n/sync_translations.py fr
```

### Cas 3️⃣ : Traduction partiellement complétée

**Reçu du traducteur :**
```
messages_fr.po (50% traduit, nécessite complétion)
```

**À faire :**

```bash
# 1. Placer le fichier
cp messages_fr.po locale/fr/LC_MESSAGES/messages.po

# 2. Synchroniser avec le .pot actuel
python i18n/sync_translations.py fr

# 3. Le traducteur peut continuer avec Poedit
# (les nouvelles chaînes seront marquées fuzzy)
```

---

## ✅ Checklist pour intégrer une traduction

- [ ] Fichier reçu s'appelle bien `messages.po` (ou à renommer de `messages_xx.po`)
- [ ] Répertoire `locale/xx/LC_MESSAGES/` existe (créer sinon)
- [ ] Fichier placé au bon endroit : `locale/xx/LC_MESSAGES/messages.po`
- [ ] Lancer : `python i18n/compile_po.py xx` (où `xx` = code langue)
- [ ] Vérifier que `messages.mo` est généré
- [ ] Tester l'application pour vérifier les traductions affichées

---

## 📋 Structure des fichiers par langue

```
locale/
├── messages.pot                    # Template maître (à envoyer pour traduction)
├── en/LC_MESSAGES/                 # Anglais (par défaut)
│   ├── messages.po                 # Traduction anglaise
│   └── messages.mo                 # Version compilée (ne pas toucher)
├── fr/LC_MESSAGES/                 # Français (reçu du traducteur)
│   ├── messages.po                 # Traduction française
│   └── messages.mo                 # Version compilée (ne pas toucher)
├── de/LC_MESSAGES/                 # Allemand (reçu du traducteur)
│   ├── messages.po                 # Traduction allemande
│   └── messages.mo                 # Version compilée (ne pas toucher)
└── ...
```

**Note importante :** Le traducteur doit **toujours** envoyer le fichier nommé `messages.po`, pas `messages_fr.po` ou autre variante.

---

## 🔄 Exemple complet : Recevoir et appliquer une traduction

### **Scénario :**
Tu développes, tu envoies le `.pot`, et une semaine après tu reçois la traduction française.

### **Étape 1 - Préparation (avant d'envoyer)**

```bash
# Tu modifies le code
# Puis tu synchronises
python i18n/sync_translations.py

# Tu envoies ce fichier au traducteur
📧 Pièce jointe: locale/messages.pot
```

### **Étape 2 - Traducteur travaille**

Le traducteur utilise [Poedit](https://poedit.net/) pour :
1. Ouvrir le `.pot`
2. Traduire les chaînes en français
3. Envoyer le `.po` généré

### **Étape 3 - Tu intègres la traduction**

```bash
# 1. Tu reçois le fichier
📧 Pièce jointe: messages.po

# 2. Tu places le fichier au bon endroit
# (Si nécessaire, renommer de messages_fr.po en messages.po)
cp messages.po locale/fr/LC_MESSAGES/messages.po

# 3. Tu compiles
python i18n/compile_po.py fr

# 4. Les traductions s'affichent automatiquement ! ✨
```

---

## 💡 Conseils pour les traducteurs

**À communiquer au traducteur :**

1. **Format requis** : Fichier `.po` au format gettext
2. **Outil recommandé** : [Poedit](https://poedit.net/) (gratuit)
3. **Format du fichier** :
   - Le fichier doit s'appeler **`messages.po`**
   - Avec l'en-tête i18n standard (Poedit le fait automatiquement)
4. **Chaînes vides** : Les chaînes vierges (`msgstr ""`) ne sont pas traduites
5. **Fuzzy** : Les entrées marquées `#, fuzzy` sont "non finalisées"

**Exemple d'en-tête valide :**
```
msgid ""
msgstr ""
"Language: fr\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
```

---

## 📝 Exemple complet : Modifier le code ET les traductions anglaises

### Scénario courant : Modifier une chaîne ET sa traduction anglaise

Tu modifies le code, une chaîne est marquée `fuzzy`, et tu veux directement corriger la traduction anglaise sans passer par Poedit.

### Workflow complet

**Étape 1 - Modifier le code :**

Dans `tools/applicator/main.py` ligne 182 :
```python
# AVANT
print(_("ERREUR: Fichier replacements.json introuvable dans {dir}").format(dir=extraction_dir))

# APRÈS
print(_("ERREUR: Le fichier replacements.json est introuvable dans {dir}").format(dir=extraction_dir))
```

**Étape 2 - Synchroniser (crée les fuzzy) :**

```bash
# Lance les 3 étapes automatiquement
python i18n/sync_translations.py
```

**Étape 3 - Vérifier l'état :**

```bash
# Voir quelles chaînes sont fuzzy
python i18n/check_translations.py en -v
```

Sortie :
```
...
Marquées fuzzy       : 1

⚠️  CHAÎNES MARQUÉES FUZZY (à revoir) :
   ERREUR: Le fichier replacements.json est introuvable dans {dir}
```

**Étape 4 - Ouvrir et corriger le `.po` :**

Ouvre `locale/en/LC_MESSAGES/messages.po` avec un éditeur texte et trouve :

```po
#, fuzzy
msgid "ERREUR: Le fichier replacements.json est introuvable dans {dir}"
msgstr ""
```

Modifie-le en :

```po
msgid "ERREUR: Le fichier replacements.json est introuvable dans {dir}"
msgstr "ERROR: The replacements.json file is not found in {dir}"
```

**Important :**
- ✅ **Enlève le `#, fuzzy`** (la ligne du commentaire)
- ✅ **Remplis le `msgstr`** avec la traduction anglaise
- ✅ **Enregistre le fichier**

**Étape 5 - Recompiler :**

```bash
python i18n/compile_po.py en
```

**Étape 6 - Vérifier que c'est bon :**

```bash
python i18n/check_translations.py en -v
```

Résultat : La chaîne n'apparaît plus dans les fuzzy ! ✨

---

## 🎯 Résumé du workflow pour l'anglais

| Étape | Action | Commande |
|-------|--------|----------|
| 1 | Modifier le code | Éditer `.py` |
| 2 | Synchroniser | `python i18n/sync_translations.py` |
| 3 | Vérifier fuzzy | `python i18n/check_translations.py en -v` |
| 4 | Corriger `.po` | Éditer `locale/en/LC_MESSAGES/messages.po` |
| 5 | Recompiler | `python i18n/compile_po.py en` |
| 6 | Vérifier OK | `python i18n/check_translations.py en` |

**Temps total :** 2-3 minutes pour une chaîne ! ⚡

---

## 💡 Raccourci rapide (si tu es seul dev)

Si tu es le seul développeur sur l'anglais, tu peux faire directement :

```bash
# 1. Modifier le code
# 2. Lancer tout en une fois
python i18n/sync_translations.py

# 3. Éditer rapidement le .po avec ton éditeur
# (ou Poedit si tu préfères)
code locale/en/LC_MESSAGES/messages.po

# 4. Recompiler
python i18n/compile_po.py en
```

Et voilà ! Les modifications anglaises sont appliquées. 🚀

---

## 📊 Vérifier l'état des traductions (sans Poedit !)

### Voir rapidement si des chaînes ne sont pas traduites

```bash
# Vérifier toutes les langues
python i18n/check_translations.py

# Vérifier une langue spécifique
python i18n/check_translations.py fr

# Affichage détaillé (liste les chaînes non traduites)
python i18n/check_translations.py fr -v
```

### Exemple de sortie

```
──────────────────────────────────────────────────────────────────────
LANGUE: FR
──────────────────────────────────────────────────────────────────────

████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░

Total chaînes        : 156
Traduites            : 120 (76.9%)
Non traduites        : 36
Marquées fuzzy       : 5
```

### Interpréter les résultats

| Statut | Signification |
|--------|---------------|
| **Traduites** | Chaînes avec `msgstr` complétée |
| **Non traduites** | `msgstr ""` vide (à traduire) |
| **Fuzzy** | Marquées `#, fuzzy` (à revoir/finaliser) |

### Avec `-v` (verbose)

Affiche aussi :
- ✅ Liste des chaînes non traduites
- ⚠️ Liste des chaînes fuzzy
- 💡 Conseil d'utiliser Poedit

---

## ⚠️ Pièges courants

### ❌ Ne pas faire :

```python
# Mauvais - chaînes concaténées
msg = "Erreur: " + variable

# Mauvais - pas d'appel _()
print("Message hardcodé")

# Mauvais - modifier directement les fichiers .po
# (ils seront écrasés à la prochaine mise à jour)
```

### ✅ Faire :

```python
# Bon - utiliser format avec _()
msg = _("Erreur: {var}").format(var=variable)

# Bon - enrober la chaîne
print(_("Message"));

# Bon - utiliser les scripts pour modifier
# (modifier le code source, puis relancer extract_strings.py)
```

---

## 🔄 Ordre d'exécution important

**TOUJOURS respecter cet ordre :**

1. **Modifier le code source** (ajouter/modifier/supprimer `_("...")`)
2. **`extract_strings.py`** (crée/met à jour le `.pot`)
3. **`update_po.py`** (synchronise les `.po` avec le `.pot`)
4. **`compile_po.py`** (génère les `.mo`)

Ne jamais sauter une étape !

---

## 📚 Fichiers générés

### `messages.pot` (Template)
- **Source de vérité** du projet
- Contient toutes les chaînes à traduire
- Généré automatiquement par `extract_strings.py`
- **Ne pas éditer manuellement** (il sera écrasé)

### `messages.po` (Traduction)
- Fichier de traduction pour chaque langue
- Contient `msgid` (chaîne anglaise) et `msgstr` (traduction)
- Peut être édité avec Poedit ou un éditeur texte
- **Mis à jour automatiquement** par `update_po.py`
- Contient les backups automatiques (`.po.bak`)

### `messages.mo` (Compilé)
- Format binaire utilisé par gettext à l'exécution
- **Ne pas éditer** (fichier binaire)
- Généré automatiquement par `compile_po.py`
- C'est lui qui est utilisé par l'application

---

## 🐛 Dépannage

### Le fichier `.pot` ne change pas après modification du code

**Cause** : Les chaînes ne sont pas entourées de `_()`.

**Solution** : Ajouter `_()` autour des chaînes à traduire.

```python
# ❌ Avant
msg = "Bonjour"

# ✅ Après
msg = _("Bonjour")
```

### Les traductions ne sont pas à jour dans l'application

**Cause** : Vous avez modifié les `.po` mais oublié de compiler en `.mo`.

**Solution** :
```bash
python i18n/compile_po.py
```

### Un fichier `.po` semble corrompu

**Solution** : Il y a un backup automatique !
```bash
cp locale/en/LC_MESSAGES/messages.po.bak locale/en/LC_MESSAGES/messages.po
python i18n/compile_po.py
```

---

## 📖 Ressources

- [Format .po/.pot (gettext)](https://www.gnu.org/software/gettext/manual/gettext.html)
- [Poedit - Éditeur .po](https://poedit.net/)
- [Python i18n / gettext](https://docs.python.org/3/library/gettext.html)

---

## 💡 Conseils

1. **Rester en anglais dans le code** - Les commentaires et noms de variables restent en anglais
2. **Seules les chaînes affichées à l'utilisateur** sont à traduire (utiliser `_()`)
3. **Tester régulièrement** - Lancez les 3 commandes souvent pour éviter les accumulations
4. **Utiliser Poedit** - C'est beaucoup plus simple que d'éditer directement les fichiers `.po`
5. **Commiter régulièrement** - Committez les fichiers `.po` et `.mo` avec votre code

---

**Dernière mise à jour** : 2026-02-04
**Auteur** : Claude (Anthropic) pour Julien Moreau
