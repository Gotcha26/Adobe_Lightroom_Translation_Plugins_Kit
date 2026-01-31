# Adobe Lightroom Translation Plugins Kit

**Version 2.1 | Janvier 2026**

## Qu'est-ce que c'est ?

Un ensemble d'outils Python pour faciliter la traduction et la maintenance des traductions de plugins Adobe Lightroom Classic. Si vous développez un plugin Lightroom en Lua et que vous souhaitez le rendre multilingue, ce kit est fait pour vous.

## Le problème

Développer un plugin Lightroom multilingue, c'est comme essayer de jongler avec plusieurs balles en même temps :
- Vous avez des textes en dur dans votre code Lua ("Submit", "Cancel", "Please wait...")
- Vous devez les extraire et les remplacer par des clés de localisation
- Vous devez maintenir les traductions à jour à chaque modification du code
- Vous devez gérer plusieurs langues sans perdre les traductions existantes

Sans outil, c'est un travail fastidieux et source d'erreurs.

## La solution

Ce kit automatise tout le processus en 5 modules complémentaires :

```
┌─────────────────────────────────────────────────────────────┐
│                 LocalisationToolKit.py                      │
│           🎯 Point d'entrée principal (recommandé)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
     ┌──────────────┬─────────────────┬──────────────┬──────────────┐
     │              │                 │              │              │
     ▼              ▼                 ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌─────────┐
│Extractor│  │Applicator│  │Translation   │  │WebBridge │  │  Tools  │
│         │  │          │  │Manager       │  │   ⭐     │  │         │
└─────────┘  └──────────┘  └──────────────┘  └──────────┘  └─────────┘
```

### 0. LocalisationToolKit.py - Le chef d'orchestre

C'est votre point d'entrée unique. Un menu interactif qui vous guide et lance les bons outils au bon moment. Plus besoin de se perdre dans les commandes !

**Utilisez-le en priorité**, c'est le moyen le plus simple de travailler avec ce kit.

### 1. Extractor - L'extracteur intelligent

Il analyse vos fichiers Lua et trouve automatiquement toutes les chaînes de texte qui devraient être traduites.

**Ce qu'il fait :**
- Scanne tous vos fichiers `.lua`
- Détecte les textes en dur (`"Submit"`, `"Cancel"`, etc.)
- Ignore intelligemment les logs, les valeurs techniques, les clés déjà localisées
- Génère un fichier `TranslatedStrings_en.txt` conforme au SDK Lightroom
- Crée des métadonnées pour préserver les espaces et la mise en forme
- Produit un fichier `replacements.json` pour l'Applicator

**Exemple d'utilisation :**
```bash
# Via le menu principal (recommandé)
python LocalisationToolKit.py

# Ou directement en CLI
python 1_Extractor/Extractor_main.py --plugin-path ./monPlugin.lrplugin
```

### 2. Applicator - L'applicateur précis

Il prend les chaînes extraites et remplace automatiquement le texte en dur dans votre code par des appels à la fonction de localisation `LOC`.

**Ce qu'il fait :**
- Lit le fichier `replacements.json` généré par Extractor
- Remplace `"Submit"` par `LOC "$$$/MonPlugin/Submit=Submit"`
- Crée des backups automatiques de vos fichiers (dans `__i18n_tmp__/2_Applicator/backups/`)
- Préserve les espaces, les concaténations et la mise en forme
- Génère un rapport détaillé des modifications

**Format SDK Lightroom :**
Le format `LOC "$$$/Key=Default"` est obligatoire. La valeur par défaut après `=` permet à Lightroom d'afficher quelque chose même si la traduction n'existe pas encore.

**Exemple d'utilisation :**
```bash
# Via le menu principal (recommandé)
python LocalisationToolKit.py

# Ou directement en CLI
python 2_Applicator/Applicator_main.py --plugin-path ./monPlugin.lrplugin
```

### 3. TranslationManager - Le gestionnaire de versions

C'est le pivot pour maintenir vos traductions à jour au fil du temps. Il compare deux versions de vos extractions et identifie ce qui a changé.

**Ce qu'il fait :**
- **COMPARE** : Compare une ancienne et une nouvelle extraction
  - Identifie les clés ajoutées, modifiées, supprimées
  - Génère `UPDATE_en.json` et `CHANGELOG.txt`
- **EXTRACT** : Crée de petits fichiers `TRANSLATE_xx.txt` avec uniquement les nouvelles clés à traduire
- **INJECT** : Réinjecte les traductions dans les fichiers de langue complets
- **SYNC** : Synchronise tous les fichiers de langue avec la version anglaise de référence
  - Ajoute `[NEW]` pour les nouvelles clés
  - Marque `[NEEDS_REVIEW]` pour les clés modifiées
  - Supprime les clés obsolètes

**Workflow typique :**
```
Code modifié
    │
    ▼
Extractor → nouveau TranslatedStrings_en.txt
    │
    ▼
COMPARE (ancien vs nouveau)
    │
    ▼
EXTRACT (génère TRANSLATE_fr.txt, TRANSLATE_de.txt, etc.)
    │
    ▼
[Vous traduisez les fichiers TRANSLATE_xx.txt]
    │
    ▼
INJECT (fusionne dans TranslatedStrings_xx.txt)
    │
    ▼
SYNC (finalise tous les fichiers de langue)
```

**Exemple d'utilisation :**
```bash
# Via le menu principal (recommandé)
python LocalisationToolKit.py

# Ou directement en CLI
python 3_Translation_manager/TranslationManager.py compare --old ancien.txt --new nouveau.txt --plugin-path ./monPlugin.lrplugin
python 3_Translation_manager/TranslationManager.py extract --plugin-path ./monPlugin.lrplugin --locales ./monPlugin.lrplugin
python 3_Translation_manager/TranslationManager.py sync --plugin-path ./monPlugin.lrplugin --locales ./monPlugin.lrplugin
```

### 4. WebBridge - Le pont web pour traducteurs ⭐

C'est le module moderne qui permet aux traducteurs non-techniques de contribuer facilement via une interface web visuelle.

**Ce qu'il fait :**
- **EXPORT** : Convertit `TranslatedStrings_xx.txt` vers `translations.json` (format i18n standard)
- **IMPORT** : Convertit `translations.json` vers `TranslatedStrings_xx.txt` (format Lightroom)
- Validation automatique des placeholders (`%s`, `%d`, `\n`)
- Compatible avec [quicki18n.studio](https://www.quicki18n.studio/) (gratuit, browser-based)
- Contexte visible pour chaque clé (fichier:ligne)

**Workflow typique :**
```
Développeur:
  Extractor → TranslatedStrings_en.txt
  WebBridge Export → translations.json
  Envoyer à traducteur

Traducteur (navigateur web uniquement):
  Ouvrir quicki18n.studio
  Importer translations.json
  Traduire visuellement
  Exporter translations.json
  Renvoyer au développeur

Développeur:
  WebBridge Import → TranslatedStrings_fr.txt
  Copier dans plugin
  Tester
```

**Avantages :**
- ✅ Interface intuitive pour traducteurs non-techniques
- ✅ Pas d'outil à installer (tout dans le navigateur)
- ✅ Validation automatique (aucune erreur de formatage)
- ✅ Contexte visible (fichier:ligne)
- ✅ Beaucoup plus rapide que l'édition manuelle

**Exemple d'utilisation :**
```bash
# Via le menu principal (recommandé)
python LocalizationToolkit.py
# [8] Export Web → Génère translations.json
# [9] Import Web → Génère TranslatedStrings_xx.txt

# Ou directement en CLI
python 4_WebBridge/WebBridge_main.py export --plugin-path ./monPlugin.lrplugin
python 4_WebBridge/WebBridge_main.py import --json translations.json --plugin-path ./monPlugin.lrplugin
```

**Testé avec succès** : Plugin PiwigoPublish (278 clés)

### 5. Tools - La boîte à outils

Deux petits utilitaires pratiques :

- **Delete_temp_dir.py** : Supprime le dossier temporaire `__i18n_tmp__` (nettoie l'espace)
- **Restore_backup.py** : Restaure les fichiers depuis les backups créés par Applicator (annule les modifications)

**Exemple d'utilisation :**
```bash
# Via le menu principal (recommandé)
python LocalisationToolKit.py

# Ou directement en CLI
python 9_Tools/Delete_temp_dir.py
python 9_Tools/Restore_backup.py
```

## Organisation des fichiers générés

Tous les outils génèrent leurs sorties dans un dossier temporaire `__i18n_tmp__` (configurable) à la racine de votre plugin :

```
monPlugin.lrplugin/
├── Info.lua
├── *.lua
├── TranslatedStrings_en.txt
├── TranslatedStrings_fr.txt
└── __i18n_tmp__/                    ← Dossier temporaire
    ├── 1_Extractor/
    │   ├── 20260129_143022/         ← Timestamp de l'exécution
    │   │   ├── TranslatedStrings_en.txt
    │   │   ├── spacing_metadata.json
    │   │   ├── replacements.json
    │   │   └── extraction_report.txt
    │   └── 20260129_151500/         ← Autre exécution
    │       └── ...
    ├── 2_Applicator/
    │   └── 20260129_143530/
    │       ├── application_report.txt
    │       └── backups/
    │           └── *.bak
    ├── 3_TranslationManager/
    │   └── 20260129_144000/
    │       ├── UPDATE_en.json
    │       ├── CHANGELOG.txt
    │       ├── TRANSLATE_fr.txt
    │       └── ...
    └── 9_Tools/
        └── 20260129_145000/
            └── restore_log.txt
```

Chaque exécution crée un sous-dossier horodaté pour conserver l'historique. Les rapports et fichiers intermédiaires sont organisés par outil.

## Workflows disponibles

Ce toolkit supporte **3 workflows** selon votre situation :

1. **[Workflow GitHub](WORKFLOW_GITHUB.md)** 🌟 **RECOMMANDÉ pour plugins open-source**
   - Collaboration via Pull Requests GitHub
   - Simple, traçable, standard
   - Idéal pour traducteurs techniques

2. **[Workflow WebBridge](WORKFLOW_MISE_A_JOUR.md#workflow-2--webbridge-moderne--disponible)**
   - Interface web visuelle (quicki18n.studio)
   - Idéal pour traducteurs non-techniques
   - Validation automatique

3. **[Workflow Classique](WORKFLOW_MISE_A_JOUR.md#workflow-1--classique--disponible)**
   - Édition directe des fichiers .txt
   - Pour cas spécifiques

### 🤔 Pas sûr de quel workflow choisir ?

Consultez le **[Guide de choix](CHOIX_WORKFLOW.md)** qui compare les 3 workflows et vous aide à choisir selon votre situation.

**Recommandation rapide** :
- Plugin sur GitHub ? → [Workflow GitHub](WORKFLOW_GITHUB.md)
- Traducteur non technique ? → [Workflow WebBridge](WORKFLOW_MISE_A_JOUR.md#workflow-2--webbridge-moderne--disponible)
- Workflow établi ? → [Workflow Classique](WORKFLOW_MISE_A_JOUR.md#workflow-1--classique--disponible)

---

## Cas concrets d'utilisation

### Cas 1 : Premier plugin multilingue

Vous avez développé un plugin entièrement en anglais avec du texte en dur. Vous voulez le rendre multilingue.

1. Lancez `LocalisationToolKit.py`
2. Configurez le chemin de votre plugin (option 6)
3. Lancez **Extractor** (option 1) pour extraire toutes les chaînes
4. Lancez **Applicator** (option 2) pour remplacer le texte en dur par des appels LOC
5. Redémarrez Lightroom et testez
6. Copiez `TranslatedStrings_en.txt` et renommez-le en `TranslatedStrings_fr.txt`, `TranslatedStrings_de.txt`, etc.
7. Traduisez les valeurs dans ces fichiers

### Cas 2 : Mise à jour d'un plugin existant

Vous avez déjà un plugin multilingue et vous venez d'ajouter de nouvelles fonctionnalités avec du nouveau texte.

1. Lancez **Extractor** pour créer une nouvelle extraction
2. Lancez **TranslationManager** (option 3) → **COMPARE**
   - Sélectionnez l'ancienne extraction
   - Sélectionnez la nouvelle extraction
3. Lancez **EXTRACT** pour générer les fichiers `TRANSLATE_xx.txt` avec uniquement les nouvelles clés
4. Traduisez ces petits fichiers (beaucoup plus rapide que de tout retraduire !)
5. Lancez **INJECT** pour fusionner les traductions dans les fichiers complets
6. Lancez **SYNC** pour finaliser et marquer les clés à revoir
7. Lancez **Applicator** pour appliquer les nouvelles localisations au code
8. Redémarrez Lightroom et testez

### Cas 3 : Correction d'une traduction existante

Vous avez trouvé une erreur dans une traduction ou vous voulez améliorer un texte.

1. Ouvrez directement le fichier `TranslatedStrings_xx.txt` dans votre éditeur
2. Modifiez la valeur de la clé concernée
3. Redémarrez Lightroom (un simple reload ne suffit pas)
4. Testez

Pas besoin d'outils pour ce cas simple !

### Cas 4 : Collaboration avec un traducteur externe

Vous avez un traducteur qui ne connaît pas les outils de développement. WebBridge rend tout simple !

1. Lancez **Extractor** pour extraire les chaînes
2. Lancez **WebBridge Export** (option 8) pour générer `translations.json`
3. Envoyez `translations.json` à votre traducteur par email
4. Le traducteur ouvre https://www.quicki18n.studio/ dans son navigateur
5. Il importe le JSON, traduit visuellement, et exporte le JSON
6. Il vous renvoie `translations.json` (traduit)
7. Lancez **WebBridge Import** (option 9) pour générer les fichiers `.txt`
8. Copiez les fichiers dans votre plugin et testez

**Temps développeur** : 5-10 minutes
**Outils requis pour le traducteur** : Navigateur web uniquement

### Cas 5 : Restauration après une erreur

Vous avez lancé Applicator mais le résultat ne vous convient pas.

1. Lancez `LocalisationToolKit.py`
2. Choisissez **Restore** (option 4)
3. Sélectionnez le backup à restaurer
4. Vos fichiers sont restaurés à leur état initial

## Prérequis

- Python 3.7 ou supérieur
- Un plugin Adobe Lightroom Classic (fichiers `.lua`)
- Système Windows (principalement testé, mais compatible Linux/Mac)

## Installation

1. Clonez ou téléchargez ce dépôt
2. Assurez-vous que Python est installé
3. Lancez `python LocalisationToolKit.py`

Aucune dépendance externe requise, uniquement la bibliothèque standard Python.

## Configuration

Le fichier `config.json` (créé automatiquement) stocke vos préférences :
- Chemin du plugin
- Préfixe des clés LOC (ex: `$$$/MonPlugin`)
- Langue par défaut (généralement `en`)
- Nom du dossier temporaire (par défaut `__i18n_tmp__`)

Vous pouvez modifier ces paramètres via le menu ou éditer directement le fichier JSON.

## FAQ

### Dois-je traduire toutes les clés ?

Non ! Le système de fallback du SDK Lightroom affiche la valeur par défaut (en anglais) si une traduction est manquante. Vous pouvez traduire progressivement.

### Puis-je utiliser les outils en ligne de commande ?

Oui ! Tous les outils supportent un mode CLI complet. Le `LocalisationToolKit.py` propose aussi des commandes rapides :
```bash
python LocalisationToolKit.py extract
python LocalisationToolKit.py apply
python LocalisationToolKit.py translate
```

### Que faire si Lightroom n'affiche pas mes traductions ?

1. Vérifiez que le fichier `TranslatedStrings_xx.txt` est à la racine du plugin
2. Le nom du fichier doit correspondre à la langue système (ex: `TranslatedStrings_fr.txt` pour le français)
3. Redémarrez complètement Lightroom (pas juste "Reload Plugin")
4. Vérifiez que les clés dans le fichier correspondent à celles dans le code

### Puis-je modifier manuellement les fichiers générés ?

Oui ! Les fichiers `TranslatedStrings_xx.txt` sont de simples fichiers texte. Vous pouvez les éditer à la main. Les fichiers JSON sont aussi éditables mais faites attention à la syntaxe.

### Que signifie `[NEW]` ou `[NEEDS_REVIEW]` dans mes fichiers ?

Ce sont des marqueurs ajoutés par la commande **SYNC** du TranslationManager :
- `[NEW]` : Nouvelle clé à traduire
- `[NEEDS_REVIEW]` : Valeur anglaise modifiée, la traduction doit être revue

Traduisez ces entrées puis supprimez le marqueur.

### Le dossier `__i18n_tmp__` prend beaucoup de place

Vous pouvez le supprimer sans risque via l'option 5 du menu principal ou manuellement. Il sera recréé automatiquement à la prochaine exécution. Pensez à le faire régulièrement pour économiser de l'espace.

### Comment faire traduire mon plugin par quelqu'un qui n'est pas développeur ?

Utilisez **WebBridge** ! C'est exactement son but.

1. Lancez **[8] Export Web** pour générer un fichier JSON
2. Envoyez le JSON à votre traducteur
3. Le traducteur utilise https://www.quicki18n.studio/ (gratuit, dans le navigateur)
4. Il vous renvoie le JSON traduit
5. Lancez **[9] Import Web** pour générer les fichiers `.txt`

Aucun outil de développement requis côté traducteur, juste un navigateur !

### Puis-je contribuer ou signaler un bug ?

Absolument ! Ce projet est ouvert aux contributions. Utilisez les issues GitHub pour signaler des bugs ou proposer des améliorations.

## Crédits

**Développé par Julien MOREAU** avec l'aide de **Claude (Anthropic)**.

Ce projet est né d'un besoin personnel pour un tout petit usage initial. Sans connaissances pointues dans le domaine et grâce à l'assistance de Claude, j'ai réussi à créer un outil performant capable de servir à d'autres développeurs de plugins Lightroom.

Les contributions sont grandement acceptées et les retours sont encouragés. N'hésitez pas à partager vos expériences et suggestions !

Fais avec

## Ressources

- [SDK Adobe Lightroom Classic](https://developer.adobe.com/console) - Documentation officielle
- [Format de localisation](https://developer.adobe.com/console/servicesandapis) - `LOC "$$$/Key=Default"`
- [Timestamps Python](https://docs.python.org/3/library/datetime.html) - Format strict `YYYYMMDD_HHMMSS`

## Licence

Ce projet est open source. Utilisez-le librement pour vos plugins Lightroom !

---

**Besoin d'aide ?** Consultez les documentations techniques dans les sous-dossiers `__doc` de chaque outil pour plus de détails.
