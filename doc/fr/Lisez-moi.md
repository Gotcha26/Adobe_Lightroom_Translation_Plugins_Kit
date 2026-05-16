# Adobe Lightroom Translation Plugins Kit

Un ensemble d'outils Python pour internationaliser vos plugins **Adobe Lightroom Classic** sans effort.
Développé pour simplifier la gestion du multilingue, ce kit automatise l'extraction, l'application et la synchronisation des traductions.

---

## 📋 Pour qui ?

**Développeurs de plugins Lightroom**
- Vous voulez rendre votre plugin multilingue sans gérer manuellement les clés de traduction.
- Vous préférez coder avec du texte en dur et automatiser la conversion vers le système `LOC()`.
- Vous cherchez à maintenir facilement les traductions lors des évolutions de votre code.
- Vous cherchez à proposer l'internationnalisation sans effort et sans changer vos habitudes de codage.

**Contributeurs de traduction**
- Vous souhaitez traduire un plugin dans votre langue.
- Vous voulez contribuer via GitHub ou simplement partager un fichier traduit.
- Le plugin n'a pas encore de fichiers `TranslatedStrings_xx.txt` ? Ce kit facilitera la création.

---

## 🤚 Limitations

- **Ne modifie pas la langue d'origine** : Le SDK Adobe impose qu'une chaîne par défaut reste hardcodée dans les fichiers `.lua` pour le fallback.
- **Ne traduit pas automatiquement** : La traduction reste manuelle (et c'est mieux ainsi, le contexte compte !).
- **Guillemets `"` vs apostrophe `'`** : Le SDK Adobe autorise les 2 mais pour l'extraction, seuls les chaînes entre guillemets `"` sont ciblées.
- **Ne répare pas la plomberie** : Et ne rend pas riche non plus.

---

## 🎯 Le défi du multilingue

Internationaliser un plugin Lightroom implique :
- Extraire toutes les chaînes de texte du code.
- Créer et gérer des clés uniques pour chaque texte.
- Remplacer les textes en dur par des appels `LOC()` compatibles SDK Adobe.
- Synchroniser les fichiers de langue à chaque modification du code.
- Éviter les doublons, les clés obsolètes et les incohérences.

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

#### AUTO-SYNC ⭐ (pour un usage quotidien)
Synchronise automatiquement toutes les langues présentes :
- Détecte la dernière extraction comme référence.
- Ajoute les nouvelles clés à tous les fichiers de langue.
- Supprime les clés obsolètes.
- Préserve toutes les traductions existantes.
- Utilise la langue d'origine par défaut pour les clés modifiées.

**C'est la commande à utiliser 99% du temps.**

#### COMPARE-LANGS (audit de cohérence)
Compare deux fichiers de traduction pour identifier les clés manquantes, les oublis de traduction et les incohérences entre langues.

#### Commandes avancées
Pour des besoins spécifiques, consultez la [documentation détaillée de Translator](../../3_Translator/__doc/fr/Lisez-moi.md).

---

## 🚀 Guide de démarrage

### Première utilisation (conversion d'un plugin LrC existant)

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
5. Tester dans Lightroom.

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

1. Téléchargez le fichier `TranslatedStrings_XX.txt` depuis le dépôt.
2. Traduisez les lignes.
3. Envoyez le fichier au développeur (email, message).
4. Utilisez immédiatement votre version traduite en local !

### Rien n'est prêt ?!

Glissez-vous dans la peau d'un développeur et reprennez le fichier le présent fichier dès le début pour extraire par vous-même le fichier `TranslatedString_xx.txt` et tester l'application en direct chez vous !

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
            ├── COMPARE_LANGS_data.json
            ├── COMPARE_LANGS_report.txt
```

**À propos du dossier temporaire `__i18n_tmp__/` :**
- Il est créé automatiquement lors de l'exécution.
- Son nom est configurable dans les paramètres.
- Il peut être supprimé sans risque (il sera recréé au besoin).
- Exclusion dans votre fichier `.gitignore` proposée automatiquement.

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
- `$$$/` : Marqueur obligatoire, conforme au SDK Adobe.
- `Prefix` : Identifiant unique de votre plugin (ex: `Piwigo`).
- `Category/Key` : Hiérarchie organisationnelle (ex: `Dialogs/ConfirmDelete`).
- `=Default value` : Texte par défaut (langue d'origine du code).

### Placeholders (à préserver !)

> 🇫🇷 _"Placeholder"_ → Espace réservé

Les chaînes peuvent contenir des variables dynamiques :
- `%s` : Chaîne de texte.
- `%d` : Nombre entier.
- `\n` : Retour à la ligne.
- `\t` : Tabulation.

**⚠️ IMPORTANT : Ne jamais supprimer ni déplacer les placeholders !**

```
✅ Correct :
"$$$/Status=Albums created: %s, updated: %d"
→ "$$$/Status=Albums créés : %s, mis à jour : %d"

❌ Incorrect :
"$$$/Status=Albums créés, mis à jour"  (placeholders manquants)
```

### Conseils directement dans le fichier `TranslatedStrings_xx.txt`

Un bloc de conseils est systématiquement ajouter en en-tête de chaque fichiers `TranslatedStrings_xx.txt` reprennant les bonnes pratiques et les conseils pour bien traduire sans tout casser.

### Marqueurs de workflow avancé

> ℹ️ Uniquement avec la commande **COMPARE** (usage avancé) :
> - `-- [NEW]` : Nouvelle clé à traduire
> - `-- [NEEDS_REVIEW]` : Valeur d'origine modifiée, retraduction nécessaire

Ces marqueurs **ne sont PAS utilisés** avec **AUTO-SYNC** (workflow quotidien).

---

## ⚙️ Configuration

Le fichier `config.json` stocke vos préférences :

```json
{
  "plugin_path": "D:\\Lightroom\\monPlugin.lrplugin",
  "output_base_dir": "",
  "temp_dir": "__i18n_tmp__",
  "auto_add_gitignore": true,
  "enable_flip_anim": false,
  "prefix": "$$$/Piwigo",
  "lang": "en",
  "last_extraction_dir": "",
  "last_used": ""
}
```

### Détail des paramètres

| Paramètre | Description | Valeur par défaut |
|-----------|-------------|-------------------|
| `plugin_path` | Chemin absolu vers le plugin `.lrplugin` | *(vide)* |
| `output_base_dir` | Répertoire de sortie (vide = à côté du script) | *(vide)* |
| `temp_dir` | Nom du dossier temporaire créé dans le plugin | `__i18n_tmp__` |
| `auto_add_gitignore` | Proposer d'ajouter le dossier temporaire au `.gitignore` | `true` |
| `enable_flip_anim` | Afficher l'animation au démarrage du menu | `true` |
| `prefix` | Préfixe des clés de localisation (ex: `$$$/Piwigo`) | `$$$/Piwigo` |
| `lang` | Langue par défaut du code source du plugin LrC cicblé | `en` |
| `last_extraction_dir` | Chemin de la dernière extraction (usage interne) | *(vide)* |
| `last_used` | Horodatage de la dernière utilisation (usage interne) | *(vide)* |

Modifiable via : `[Option 6] Configurer le plugin`

> **Note** : Lorsque `auto_add_gitignore` est activé, le toolkit détecte automatiquement si le plugin est dans un dépôt Git et propose d'ajouter le dossier temporaire au `.gitignore` pour éviter de versionner les fichiers générés qui peuvent être nombreux et non essentiel à versionner.

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

### Le dossier temporaire prend de la place
Les backups de ***Applicator*** peuvent être volumineuses. Vous pouvez :
- Le supprimer via `[Option 5] Supprimer` ou manuellement
- L'exclure de Git en ajoutant `__i18n_tmp__/` dans `.gitignore`
- Il sera recréé automatiquement au besoin

### Comment contribuer ou signaler un bug du toolkit ?
Utilisez les [GitHub Issues](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit/issues).

---

## 🎨 Outils complémentaires (***Tools***)

### Restore (Option 4)
Restaure les fichiers `.lua` originaux mis de coté avant une modification par ***Applicator***.
Les backups sont créés automatiquement avant toute modification.

### Delete temp dir (Option 5)
Supprime `__i18n_tmp__/` pour libérer de l'espace.
Recommandé après chaque version majeure du toolkit.

---

## 📚 Centre de cocumentation enrivhie

### Guides par profil

| Vous êtes... | Commencez par... |
|--------------|------------------|
| Développeur d'un plugin LrC | [Guide Installation](./dev/01_Installation.md) |
| Développeur en maintenance | [Guide Maintenance](./dev/02_Maintenance.md) |
| Développeur avancé | [Workflows avancés](./dev/03_Avance.md) |
| Traducteur débutant | [Contributeur simple](./trad/01_Contributeur_simple.md) |
| Traducteur autonome | [Contributeur débrouillard](./trad/02_Contributeur_debrouillard.md) |
| Traducteur professionnel | [Contributeur pro](./trad/03_Contributeur_pro.md) |

### Documentation technique des outils

Pour approfondir chaque outil :
- ***[Extractor](../../1_Extractor/__doc/fr/Lisez-moi.md)*** — Extraction des chaînes
- ***[Applicator](../../2_Applicator/__doc/fr/Lisez-moi.md)*** — Application des clés LOC()
- ***[Translator](../../3_Translator/__doc/fr/Lisez-moi.md)*** — Gestion des traductions
- ***[Tools](../../9_Tools/__doc/fr/Lisez-moi.md)*** — Utilitaires (restauration, nettoyage)

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

**Mes outils** : Windows11 | VScode + extensions

---

| 📜 | Traçabilité |  |  |
|--|--|--|--|
| **Nom** | *Lisez-moi.md* | **Version** | 3.1 |
| **Type** | Présentation - Vue globale | **Langue** | FR - *[EN](README.md)* |
| **Projet GitHub** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-08 |
| **Licence** | [MIT](../../LICENSE) | | |
