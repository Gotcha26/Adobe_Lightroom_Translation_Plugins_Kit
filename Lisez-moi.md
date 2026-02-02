# Adobe Lightroom Translation Plugins Kit

Un ensemble d'outils Python pour internationaliser vos plugins **Adobe Lightroom Classic** sans effort.
Développé pour simplifier la gestion du multilingue, ce kit automatise l'extraction, l'application et la synchronisation des traductions.

---

## 📋 Pour qui ?

**Développeurs de plugins Lightroom**
- Vous voulez rendre votre plugin multilingue sans gérer manuellement les clés de traduction
- Vous préférez coder avec du texte en dur et automatiser la conversion vers le système `LOC()`
- Vous cherchez à maintenir facilement les traductions lors des évolutions de votre code

**Contributeurs de traduction**
- Vous souhaitez traduire un plugin dans votre langue
- Vous voulez contribuer via GitHub ou simplement partager un fichier traduit
- Le plugin n'a pas encore de fichiers `TranslatedStrings_xx.txt` ? Ce kit facilitera la création

---

## 🤚 Limitations

- **Ne modifie pas la langue d'origine** : Le SDK Adobe impose qu'une chaîne par défaut reste hardcodée dans les fichiers `.lua` pour le fallback
- **Ne traduit pas automatiquement** : La traduction reste manuelle (et c'est mieux ainsi, le contexte compte !)
- **Ne répare pas la plomberie** : Et ne rend pas riche non plus

---

## 🎯 Le défi du multilingue

Internationaliser un plugin Lightroom implique :
- Extraire toutes les chaînes de texte du code
- Créer et gérer des clés uniques pour chaque texte
- Remplacer les textes en dur par des appels `LOC()` compatibles SDK Adobe
- Synchroniser les fichiers de langue à chaque modification du code
- Éviter les doublons, les clés obsolètes et les incohérences

**Sans outils, c'est chronophage et source d'erreurs.**

---

## ✨ La solution : 3 outils complémentaires

```
┌─────────────────────────────────────────────────────────────┐
│                   LocalisationToolKit.py                    │
│                       Menu principal                        │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
    ┌─────────┐         ┌──────────┐        ┌──────────┐
    │Extractor│         │Applicator│        │Translator│
    └─────────┘         └──────────┘        └──────────┘
```

### 1. ***Extractor*** - Extraction des chaînes

Scanne automatiquement votre code Lua pour en extraire toutes les chaînes de texte.

**Entrée :**
```lua
local dialog = LrDialogs.confirm("Delete this photo?", "This cannot be undone")
```

**Sortie** (`TranslatedStrings_en.txt`) :
```
"$$$/MyPlugin/Dialogs/DeleteConfirm=Delete this photo?"
"$$$/MyPlugin/Dialogs/DeleteWarning=This cannot be undone"
```

Génère des clés uniques selon une *recette* reproductible et cohérente.

### 2. ***Applicator*** - Application dans le code

Remplace automatiquement les chaînes hardcodées par des appels `LOC()`.

**Résultat :**
```lua
local dialog = LrDialogs.confirm(
    LOC "$$$/MyPlugin/Dialogs/DeleteConfirm=Delete this photo?",
    LOC "$$$/MyPlugin/Dialogs/DeleteWarning=This cannot be undone"
)
```

Crée des backups automatiques avec possibilité de restauration.

### 3. ***Translator*** - Synchronisation des traductions

Maintient tous vos fichiers de langue à jour automatiquement.

**Deux modes principaux :**

#### INSTALL (première fois)
Copie les fichiers générés par ***Extractor*** dans votre plugin et lance la conversion initiale.

#### AUTO-SYNC ⭐ (usage quotidien)
Synchronise automatiquement toutes les langues :
- Détecte la dernière extraction comme référence
- Ajoute les nouvelles clés à tous les fichiers de langue
- Supprime les clés obsolètes
- Préserve toutes les traductions existantes
- Met la valeur par défaut (langue d'origine) pour les clés modifiées

**C'est la commande à utiliser 99% du temps.**

#### Commandes avancées
Pour des besoins spécifiques, consultez la [documentation détaillée de Translator](3_Translator/__doc/Lisez-moi.md) :

---

## 🚀 Guide de démarrage

### Première utilisation (conversion d'un plugin existant)

```
Code Lua hardcodé
         │
         ▼  [1] python LocalisationToolKit.py → Extractor
TranslatedStrings_en.txt
         │
         ▼  [2] Translator → INSTALL
Fichiers copiés dans plugin.lrplugin/
         │
         ▼  [3] Applicator
Code avec LOC() + Traductions actives
         │
         ▼  [4] Test dans Lightroom
Validation fonctionnelle
```

**Commandes :**
1. Configurer le chemin du plugin : `[Option 6]`
2. Extraire les chaînes : `[Option 1] Extractor`
3. Installer : `[Option 3] Translator → INSTALL`
4. Appliquer les clés : `[Option 2] Applicator`
5. Tester dans Lightroom

### Maintenance quotidienne (après modifications du code)

```
Développement normal (texte en dur)
         │
         ▼  [1] Extractor
Nouvelle extraction
         │
         ▼  [2] AUTO-SYNC ⭐
Tous les fichiers de langue synchronisés
         │
         ▼  [3] Copie dans plugin + commit
Prêt pour traduction
```

**Workflow recommandé :**
1. Développez normalement avec du texte en dur
2. Lancez ***Extractor*** : `[Option 1]`
3. Synchronisez : `[Option 3] Translator → AUTO-SYNC`
4. Copiez les fichiers synchronisés :
   ```bash
   cp __i18n_tmp__/3_Translator/<timestamp>/TranslatedStrings_*.txt ./plugin.lrplugin/
   ```
5. Committez :
   ```bash
   git add .
   git commit -m "i18n: Update translation keys"
   git push
   ```

---

## 💡 Contribuer aux traductions

### Via GitHub (recommandé)

```
Fork du repo → Clonage → Traduction → Pull Request → Merge
```

**Étapes :**
1. Forkez le repository du plugin
2. Clonez : `git clone https://github.com/VOTRE_USERNAME/plugin.git`
3. Éditez `plugin.lrplugin/TranslatedStrings_XX.txt` (XX = votre langue)
4. Traduisez les clés (comparez avec `TranslatedStrings_en.txt`)
5. Créez une Pull Request :
   ```bash
   git add TranslatedStrings_fr.txt
   git commit -m "i18n(fr): Add French translation"
   git push
   ```

### Sans GitHub

1. Téléchargez le fichier `TranslatedStrings_XX.txt` depuis le dépôt
2. Traduisez les lignes
3. Envoyez le fichier au développeur (email, message)
4. Utilisez immédiatement votre version traduite en local !

### Rien n'est prêt ?!

Glissez-vous dnas la peau d'un développeur et reprennez le fichier `Lisez-moi.md` dès le début pour extraire par vous-même le fichier `TranslatedString_xx.txt` et tester l'application en direct chez vous !

---

## 📁 Structure des fichiers

```
plugin.lrplugin/
├── Info.lua
├── PluginCode.lua
├── TranslatedStrings_en.txt      ← Anglais (référence/origine)
├── TranslatedStrings_fr.txt      ← Français
├── TranslatedStrings_de.txt      ← Allemand
├── TranslatedStrings_es.txt      ← Espagnol
└── __i18n_tmp__/                 ← Dossier temporaire (auto-généré)
    ├── 1_Extractor/
    │   └── 20260131_120000/
    │       ├── TranslatedStrings_en.txt
    │       ├── replacements.json
    |       ├── spacing_metadata.json
    │       └── extraction_report.txt
    ├── 2_Applicator/
    │   └── 20260131_120500/
    │       ├── BACKUP/
    |       |   ├── Fichier1.lua.bak
    |       |   └── Fichier2.lua.bak
    │       └── applicator_report.txt
    └── 3_Translator/
        └── 20260131_121000/
            ├── TranslatedStrings_fr.txt
            ├── TranslatedStrings_de.txt
            ├── sync_report.txt
            ├── TRANSLATE_fr.txt
            ├── UPDATE_en.json
```

**À propos du dossier temporaire `__i18n_tmp__/` :**
- Créé automatiquement lors de l'exécution
- Nom configurable dans les paramètres
- Peut être supprimé sans risque (recréé au besoin)
- Exclusion `.gitignore` proposée automatiquement

---

## 🎓 Format des fichiers de traduction

### Anatomie d'une clé

```
"$$$/Piwigo/Dialogs/ConfirmDelete=Are you sure?"
 │    │       │         │            │
 │    │       │         │            └─ Valeur par défaut
 │    │       │         └────────────── Nom descriptif
 │    │       └──────────────────────── Catégorie
 │    └──────────────────────────────── Préfixe du plugin
 └───────────────────────────────────── Marqueur SDK (obligatoire)
```

**Structure :**
- `$$$/` : Marqueur obligatoire du SDK Lightroom
- `Prefix` : Identifiant unique de votre plugin (ex: `Piwigo`)
- `Category/Key` : Hiérarchie organisationnelle (ex: `Dialogs/ConfirmDelete`)
- `=Default value` : Texte par défaut (langue d'origine du code)

### Placeholders (à préserver !)

> 🇫🇷 _"Placeholder"_ → Espace réservé

Les chaînes peuvent contenir des variables dynamiques :
- `%s` : Chaîne de texte
- `%d` : Nombre entier
- `\n` : Retour à la ligne
- `\t` : Tabulation

**⚠️ IMPORTANT : Ne jamais supprimer ni déplacer les placeholders !**

```
✅ Correct :
"$$$/Status=Albums created: %s, updated: %d"
→ "$$$/Status=Albums créés : %s, mis à jour : %d"

❌ Incorrect :
"$$$/Status=Albums créés, mis à jour"  (placeholders manquants)
```

### Marqueurs de workflow avancé

Uniquement avec la commande **COMPARE** (usage avancé) :
- `-- [NEW]` : Nouvelle clé à traduire
- `-- [NEEDS_REVIEW]` : Valeur d'origine modifiée, retraduction nécessaire

Ces marqueurs **ne sont PAS utilisés** avec **AUTO-SYNC** (workflow quotidien).

---

## ⚙️ Configuration

Le fichier `config.json` stocke vos préférences :

```json
{
  "plugin_path": "D:\\Lightroom\\monPlugin.lrplugin",
  "output_base_dir": "",
  "prefix": "$$$/Piwigo",
  "lang": "en",
  "temp_dir": "__i18n_tmp__",
  "last_extraction_dir": "",
  "last_used": "",
  "enable_flip_anim": false
}
```

Modifiable via : `[Option 6] Configurer le plugin`

---

## 🛠️ Installation du toolkit

### Prérequis
- Python 3.7+
- Un plugin Adobe Lightroom Classic (`.lua`)
- Windows, Linux ou macOS

### Installation
```bash
git clone https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit.git
cd Adobe_Lightroom_Translation_Plugins_Kit
python LocalisationToolKit.py
```

**Aucune dépendance externe requise** (uniquement la bibliothèque standard Python).

---

## ❓ FAQ

### Dois-je traduire toutes les clés d'un coup ?
**Non.** Le SDK Lightroom utilise un système de fallback : si une clé manque, la valeur par défaut (hardcodée) s'affiche. Vous pouvez traduire progressivement.

### Lightroom n'affiche pas mes traductions
Vérifiez :
1. Le fichier `TranslatedStrings_xx.txt` est à la racine du plugin
2. Le nom correspond à votre langue système (ex: `TranslatedStrings_fr.txt` pour français)
3. Redémarrage complet de Lightroom (pas juste "Relancer le plugin")
4. Les clés du fichier correspondent au code (recherche dans les `.lua`)

### Puis-je éditer manuellement les fichiers ?
**Oui !** Les fichiers `TranslatedStrings_xx.txt` sont du texte pur. Éditez-les avec n'importe quel éditeur.

### Le dossier `__i18n_tmp__` prend de la place
Les backups de ***Applicator*** peuvent être volumineux. Vous pouvez :
- Le supprimer via `[Option 5] Supprimer` ou manuellement
- L'exclure de Git en ajoutant `__i18n_tmp__/` dans `.gitignore`
- Il sera recréé automatiquement au besoin

### Comment contribuer ou signaler un bug ?
Utilisez les [GitHub Issues](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit/issues).

---

## 🎨 Outils complémentaires

### Restore (Option 4)
Restaure les fichiers `.lua` originaux avant modification par ***Applicator***.
Les backups sont créés automatiquement avant toute modification.

### Delete temp dir (Option 5)
Supprime `__i18n_tmp__/` pour libérer de l'espace.
Recommandé après chaque version majeure du toolkit.

---

## 📚 Documentation technique détaillée

Pour approfondir chaque outil :
- [Extractor](1_Extractor/__doc/Lisez-moi.md)
- [Applicator](2_Applicator/__doc/Lisez-moi.md)
- [Translator](3_Translator/__doc/Lisez-moi.md)

---

## 🔗 Ressources externes

- [SDK Adobe Lightroom Classic](https://developer.adobe.com/console)
- [Format de localisation SDK](https://developer.adobe.com/console/servicesandapis)
- [Guide des Pull Requests GitHub](https://docs.github.com/en/pull-requests)

**Besoin d'aide ?** Consultez la documentation technique ou ouvrez une [issue GitHub](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit/issues).

---

## 👏 Crédits

**Développé par Julien MOREAU** avec l'aide de **Claude (Anthropic)**.

Né d'un besoin personnel, ce projet a été créé sans connaissances techniques approfondies, grâce à l'assistance de Claude. Il est désormais un outil performant pour la communauté des développeurs de plugins Lightroom.

Les contributions sont bienvenues et les retours encouragés !

**Outils** : Windows11 | VScode + extensions

---

## 📜 Licence & informations

Ce projet est open source. Utilisez-le librement pour vos plugins Lightroom.

**Page GitHub** : https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit

**Version** : 3.0
**Dernière mise à jour** : 2026-02-01

> **Note sur le versioning** : Chaque module (***Extractor, Applicator, Translator, Tools***) possède sa propre version indépendante. La version 3.0 correspond au kit global (***LocalisationToolKit***).
