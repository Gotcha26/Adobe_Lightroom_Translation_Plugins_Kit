# Tools - Documentation technique

**Version 2.0 | Février 2026**

## Vue d'ensemble

Le dossier Tools contient deux utilitaires pour gérer les fichiers temporaires et restaurer les backups. Ces outils s'intègrent avec `LocalisationToolKit.py` et peuvent également être utilisés indépendamment en ligne de commande.

## Architecture du projet

```
9_Tools/
├── Delete_temp_dir.py       ← Nettoyage du dossier temporaire
├── Restore_backup.py        ← Restauration des backups
└── __doc/
    └── Lisez-moi.md         ← Ce fichier
```

Ces deux scripts peuvent être utilisés indépendamment ou via `LocalisationToolKit.py`.

## Delete_temp_dir.py - Nettoyage du dossier temporaire

### Description

Cet outil permet de nettoyer tout ou partie du dossier temporaire `__i18n_tmp__` (ou le nom configuré) d'un plugin Lightroom. Deux options sont disponibles : supprimer uniquement les backups ou supprimer l'intégralité du dossier.

### Quand l'utiliser ?

**Option 1 : Supprimer uniquement les backups**
- Après avoir validé que l'application fonctionne correctement
- Pour libérer de l'espace sans perdre les extractions et traductions
- Quand vous ne prévoyez plus de restaurer les fichiers

**Option 2 : Supprimer tout le dossier temporaire**
- Pour libérer beaucoup d'espace disque
- Après avoir terminé un cycle complet de localisation
- Avant de versionner le plugin (le dossier temporaire ne doit pas être dans Git)
- Pour repartir de zéro

### Comment ça fonctionne ?

```
Plugin Lightroom
    │
    └── __i18n_tmp__/
        ├── 1_Extractor/
        │   ├── 20260120_100000/    (5 fichiers, 120 Ko)
        │   └── 20260129_143022/    (5 fichiers, 135 Ko)
        ├── 2_Applicator/           ← BACKUPS
        │   ├── 20260127_091234/
        │   │   └── backups/        (12 fichiers .bak, 1.1 Mo)
        │   └── 20260129_143530/
        │       └── backups/        (12 fichiers .bak, 1.2 Mo)
        └── 3_Translator/
            └── 20260129_144000/    (8 fichiers, 45 Ko)

        TOTAL: 37 fichiers, 2.6 Mo

        ▼
    NOUVEAU : Choix du mode de suppression
        ▼

Option 1: Supprimer UNIQUEMENT les backups
    → Supprime 2_Applicator/
    → Conserve Extractor/ et Translator/
    → Libère 2.3 Mo

Option 2: Supprimer TOUT
    → Supprime __i18n_tmp__/ entièrement
    → Libère 2.6 Mo
```

### Utilisation

**Via LocalisationToolKit (recommandé) :**
```bash
python LocalisationToolKit.py
# Puis sélectionner l'option 5
```

Le chemin du plugin configuré est automatiquement transmis.

**Mode interactif (standalone) :**
```bash
python 9_Tools/Delete_temp_dir.py
```

**Mode CLI avec plugin pré-configuré :**
```bash
python 9_Tools/Delete_temp_dir.py --default-plugin ./monPlugin.lrplugin
```

### Exemple de sortie (v2.0)

**Écran d'accueil avec auto-détection :**

```
======================================================================
           NETTOYAGE DU DOSSIER TEMPORAIRE (v2.0)
======================================================================

[OK] Plugin: piwigoPublish.lrplugin
  Chemin: D:\Lightroom\piwigoPublish.lrplugin

Dossier temporaire : __i18n_tmp__
Chemin complet     : D:\Lightroom\piwigoPublish.lrplugin\__i18n_tmp__

======================================================================
            CONTENU DU DOSSIER TEMPORAIRE
======================================================================

  1_Extractor              :   10 fichiers, 255.0 Ko
  2_Applicator             :   24 fichiers, 2.3 Mo
  3_Translator             :    8 fichiers, 45.0 Ko

------------------------------------------------------------
TOTAL: 42 fichiers, 2.6 Mo
------------------------------------------------------------
```

**Menu de sélection du mode :**

```
Que voulez-vous supprimer?
------------------------------------------------------------

  1. Supprimer UNIQUEMENT les backups
     2 session(s) de backup • 24 fichiers • 2.3 Mo

  2. Supprimer TOUT le dossier temporaire
     Tout le contenu • 42 fichiers • 2.6 Mo

  0. Annuler

Votre choix (0-2):
```

**Confirmation adaptée au mode :**

**Mode 1 (Backups uniquement) - Confirmation simple :**
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!! ATTENTION - OPÉRATION IRRÉVERSIBLE !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Cette opération va SUPPRIMER les backups suivants:

  • 20260127_091234
  • 20260129_143530

[INFO] Les autres fichiers du dossier temporaire seront conservés.

Confirmer la suppression des backups? [o/N]: o
```

**Mode 2 (Tout supprimer) - Triple confirmation :**
```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!! ATTENTION - OPÉRATION IRRÉVERSIBLE !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Cette opération va SUPPRIMER DÉFINITIVEMENT:
  D:\Lightroom\piwigoPublish.lrplugin\__i18n_tmp__

Vous perdrez:
  - Toutes les extractions précédentes
  - Tous les fichiers de backup (.bak)
  - Toutes les sorties des outils

Étape 1/3: Confirmation initiale
Voulez-vous vraiment supprimer ce dossier? [o/N]: o

Étape 2/3: Confirmation de sécurité
Tapez 'SUPPRIMER' pour confirmer: SUPPRIMER

Étape 3/3: Dernière chance
Dernière confirmation - Êtes-vous ABSOLUMENT sûr? [o/N]: o
```

**Suppression en cours :**
```
============================================================
                SUPPRESSION EN COURS
============================================================

  Suppression: 20260127_091234... [OK]
  Suppression: 20260129_143530... [OK]

============================================================
                     RÉSUMÉ
============================================================
[OK] 2 élément(s) supprimé(s) avec succès!

[INFO] Les autres fichiers du dossier temporaire ont été conservés.

Appuyez sur ENTRÉE pour quitter...
```

### Sécurité

Le script intègre plusieurs niveaux de protection adaptés au mode choisi :

**Mode "Backups uniquement" :**
1. **Validation du chemin** : Vérifie que le plugin existe
2. **Affichage détaillé** : Liste toutes les sessions de backup qui seront supprimées
3. **Confirmation simple** : Une seule étape (opération moins risquée)
4. **Message rassurant** : Rappelle que les autres fichiers sont conservés

**Mode "Tout supprimer" :**
1. **Validation du chemin** : Vérifie que le plugin existe
2. **Affichage détaillé** : Montre exactement ce qui sera supprimé
3. **Triple confirmation** :
   - Confirmation initiale (o/N)
   - Mot de passe ("SUPPRIMER")
   - Dernière chance (o/N)
4. **Gestion des erreurs** : Détecte les permissions insuffisantes

### Cas d'usage

**Scénario 1 : Nettoyage régulier (recommandé)**
```bash
# Lancer depuis LocalisationToolKit
python LocalisationToolKit.py
# Option 5 → Supprimer

# Choisir "1. Supprimer UNIQUEMENT les backups"
# → Libère de l'espace tout en conservant les extractions et traductions
```

**Scénario 2 : Nettoyage complet avant commit Git**
```bash
# Supprimer tout le dossier temporaire
python Delete_temp_dir.py --default-plugin ./plugin.lrplugin
# Choisir "2. Supprimer TOUT"
# → Prépare le plugin pour être versionné proprement
```

**Scénario 3 : Libérer de l'espace rapidement**
```bash
# Supprimer uniquement les backups (le plus gros consommateur d'espace)
# → Garde les extractions pour comparaison future
# → Garde les sorties Translator pour re-synchronisation
```

### Cas d'erreur

**Erreur de permission :**
```
  Suppression: 20260129_143530... [ERREUR]
    Permission refusée: [WinError 32] The process cannot access the file...

============================================================
                     RÉSUMÉ
============================================================
Succès: 1
Échecs: 1

[ATTENTION] Certains fichiers n'ont pas pu être supprimés.
         Fermez tous les programmes qui utilisent ces fichiers.
```

**Solution :** Fermez tous les éditeurs, explorateurs de fichiers ou programmes qui accèdent au dossier temporaire, puis relancez.

### Recommandations

**Quand supprimer uniquement les backups :**
- ✅ Vous avez validé que l'application fonctionne correctement
- ✅ Vous voulez libérer de l'espace (backups = 70-80% de la taille)
- ✅ Vous voulez garder les extractions pour comparaison ultérieure
- ✅ Vous pourriez avoir besoin de re-synchroniser les traductions

**Quand supprimer tout :**
- ✅ Vous avez terminé le cycle de localisation
- ✅ Vous préparez le plugin pour Git/distribution
- ✅ Vous voulez repartir de zéro
- ✅ Vous manquez vraiment d'espace disque

**Ne supprimez pas si :**
- ❌ Vous n'êtes pas sûr que l'application fonctionne
- ❌ Vous pourriez avoir besoin de restaurer des fichiers
- ❌ Vous travaillez encore sur les traductions

## Restore_backup.py - Restauration des backups

### Description

Cet outil restaure les fichiers `.lua` d'un plugin depuis leurs sauvegardes `.bak` créées par ***Applicator***. La session de backup la plus récente est présélectionnée automatiquement.

### Quand l'utiliser ?

- Après une application qui a produit des résultats incorrects
- Pour revenir à l'état avant localisation
- Pour tester différentes versions (appliquer → tester → restaurer → modifier → réappliquer)
- En cas d'erreur dans les remplacements
- Avant de relancer ***Applicator*** avec des paramètres différents

### Comment ça fonctionne ?

```
Plugin Lightroom                  Backups Applicator
    │                                 │
    ├── MyDialog.lua (modifié)        ├── MyDialog.lua.bak (original)
    ├── Settings.lua (modifié)        ├── Settings.lua.bak (original)
    └── Upload.lua (modifié)          └── Upload.lua.bak (original)

                    │
                    ▼
              RESTAURATION
                    │
                    ▼

    ├── MyDialog.lua (restauré ✓)
    ├── Settings.lua (restauré ✓)
    └── Upload.lua (restauré ✓)
```

### Utilisation

**Via LocalisationToolKit (recommandé) :**
```bash
python LocalisationToolKit.py
# Puis sélectionner l'option 4
```

Le chemin du plugin configuré est automatiquement transmis.

**Mode interactif (standalone) :**
```bash
python 9_Tools/Restore_backup.py
```

**Mode CLI avec auto-détection :**
```bash
python 9_Tools/Restore_backup.py --default-plugin ./plugin.lrplugin
```

**Mode CLI direct :**
```bash
python 9_Tools/Restore_backup.py /chemin/vers/plugin.lrplugin
```

**Mode dry-run (simulation) :**
```bash
python 9_Tools/Restore_backup.py --dry-run /chemin/vers/plugin.lrplugin
```

### Exemple de sortie (v3.0)

**Écran d'accueil avec auto-détection :**

```
======================================================================
            RESTAURATION DES FICHIERS .bak (v3.0)
======================================================================

[OK] Plugin: piwigoPublish.lrplugin
  Chemin: D:\Lightroom\piwigoPublish.lrplugin

[INFO] 3 session(s) Applicator trouvée(s) dans __i18n_tmp__/
```

**Sélection avec présélection :**

```
Sessions Applicator avec backups disponibles
------------------------------------------------------------

  1. [DERNIÈRE] 2026-01-31 10:25:45 (12 fichier(s))
  2.            2026-01-29 14:35:30 (12 fichier(s))
  3.            2026-01-27 09:12:34 (11 fichier(s))
  0. Annuler

Choisir une session [1 par défaut]:
```

Appuyez simplement sur Entrée pour sélectionner la session la plus récente (option 1).

**Confirmation du choix :**

```
[OK] Session sélectionnée: 2026-01-31 10:25:45

------------------------------------------------------------
Mode simulation (dry-run) ? [O/n]: n

[ATTENTION] Mode réel - Les fichiers seront modifiés
```

**Recherche et affichage des fichiers :**

```
============================================================
        RECHERCHE DES FICHIERS .bak
============================================================
Plugin: D:\Lightroom\piwigoPublish.lrplugin
Source: D:\Lightroom\piwigoPublish.lrplugin\__i18n_tmp__\2_Applicator\20260131_102545\backups

[INFO] Fichiers trouvés: 12

  [REMPLACER] MyDialog.lua
  [REMPLACER] Settings.lua
  [REMPLACER] Upload.lua
  [REMPLACER] Export.lua
  [NOUVEAU]   NewFeature.lua
  ...

Restaurer ces 12 fichier(s) ? [o/N]: o
```

**Marqueurs visuels :**
- `[REMPLACER]` : Le fichier .lua existe et sera remplacé
- `[NOUVEAU]` : Le fichier .lua n'existe pas et sera créé

**Restauration en cours :**

```
============================================================
                  RESTAURATION
============================================================

  [OK] MyDialog.lua
  [OK] Settings.lua
  [OK] Upload.lua
  [OK] Export.lua
  [OK] NewFeature.lua
  ...
```

**Option de nettoyage des backups :**

```
Supprimer les fichiers .bak ? [o/N]: n

============================================================
                     RÉSUMÉ
============================================================
Fichiers restaurés: 12

[OK] Terminé!
```

### Structure des backups

Restore_backup prend en charge deux structures et détecte automatiquement la bonne :

**1. Structure __i18n_tmp__ (recommandée, depuis v2.0) :**

```
monPlugin.lrplugin/
├── MyDialog.lua              ← Fichier à restaurer
├── Settings.lua
└── __i18n_tmp__/
    └── 2_Applicator/
        ├── 20260131_102545/   ← [DERNIÈRE]
        │   └── backups/
        │       ├── MyDialog.lua.bak
        │       └── Settings.lua.bak
        ├── 20260129_143530/
        │   └── backups/
        │       └── ...
        └── 20260127_091234/
            └── backups/
                └── ...
```

**2. Structure legacy (ancienne) :**

```
monPlugin.lrplugin/
├── MyDialog.lua              ← Fichier à restaurer
├── MyDialog.lua.bak          ← Source (à côté)
├── Settings.lua
└── Settings.lua.bak
```

L'outil détecte automatiquement la structure disponible et préfère la structure __i18n_tmp__ si elle existe.

### Mode dry-run

Le mode dry-run (simulation) permet de prévisualiser les actions sans modifier les fichiers.

```bash
python Restore_backup.py --default-plugin ./plugin.lrplugin --dry-run
```

Sortie :
```
============================================================
           RESTAURATION (SIMULATION)
============================================================

  [SIMULATION] MyDialog.lua
  [SIMULATION] Settings.lua
  [SIMULATION] Upload.lua
  ...

============================================================
                     RÉSUMÉ
============================================================
Fichiers qui seraient restaurés: 12

[ATTENTION] MODE SIMULATION - Aucun fichier modifié

[OK] Terminé!
```

### Gestion des sessions multiples

**En mode interactif**, l'outil affiche toutes les sessions avec un marqueur sur la plus récente :

```
Sessions Applicator avec backups disponibles
------------------------------------------------------------

  1. [DERNIÈRE] 2026-01-31 10:25:45 (12 fichier(s))
  2.            2026-01-29 14:35:30 (12 fichier(s))
  3.            2026-01-27 09:12:34 (11 fichier(s))
  0. Annuler

Choisir une session [1 par défaut]:
```

**Avantages de la présélection :**
- Pas besoin de taper "1" - juste appuyer sur Entrée
- Évite les erreurs de sélection
- Accélère le workflow pour le cas d'usage le plus courant

**En mode CLI**, la session la plus récente est automatiquement sélectionnée sans demander.

### Suppression des backups

Après restauration, l'outil propose de supprimer les fichiers `.bak` :

```
Supprimer les fichiers .bak ? [o/N]: o

[INFO] Suppression des .bak

  [OK] Supprimé: MyDialog.lua.bak
  [OK] Supprimé: Settings.lua.bak
  ...

[OK] 12 fichier(s) .bak supprimé(s)
```

**Recommandation :** Gardez les backups tant que vous n'êtes pas sûr du résultat. Vous pouvez toujours les supprimer plus tard avec `Delete_temp_dir.py` (option "Supprimer uniquement les backups").

### Cas d'usage avancés

**Restaurer une session spécifique (pas la dernière) :**

1. Lancez le script en mode interactif
2. Choisissez le numéro de la session souhaitée (2, 3, etc.)
3. Validez la restauration

**Restaurer après plusieurs applications :**

Si vous avez appliqué ***Applicator*** plusieurs fois, les backups de chaque session sont préservés :

```
2_Applicator/
├── 20260127_091234/    ← État original (avant toute modification)
│   └── backups/
├── 20260129_143530/    ← Après première application
│   └── backups/
└── 20260131_102545/    ← Après deuxième application [DERNIÈRE]
    └── backups/
```

**Scénarios :**
- Restaurer session 3 (20260127_091234) → Revient à l'état original
- Restaurer session 2 (20260129_143530) → Annule seulement la dernière application
- Restaurer session 1 (20260131_102545) → Annule toutes les applications

**Restaurer sélectivement certains fichiers :**

Pour ne restaurer que certains fichiers :

1. Copiez manuellement les `.bak` souhaités :
```bash
# Restaurer un seul fichier
cp monPlugin.lrplugin/__i18n_tmp__/2_Applicator/20260131_102545/backups/MyDialog.lua.bak \
   monPlugin.lrplugin/MyDialog.lua
```

2. Ou supprimez les `.bak` non désirés du dossier backups/ avant d'exécuter le script

### Intégration avec Git

Si votre plugin est versionné avec Git, une alternative à Restore_backup est :

```bash
# Voir les modifications depuis le dernier commit
git diff

# Restaurer tous les fichiers
git checkout HEAD -- monPlugin.lrplugin/*.lua

# Restaurer un fichier spécifique
git checkout HEAD -- monPlugin.lrplugin/MyDialog.lua

# Restaurer depuis un commit spécifique
git checkout abc1234 -- monPlugin.lrplugin/MyDialog.lua
```

**Avantage de Restore_backup :**
- Restaure à partir des backups locaux ***Applicator***, même si vous avez déjà commité les modifications dans Git
- Permet de revenir à un état intermédiaire entre deux commits
- Plus rapide et simple pour des tests itératifs

**Avantage de Git :**
- Historique complet de toutes les modifications
- Possibilité de revenir à n'importe quel état du projet
- Fonctionne même si les backups ont été supprimés

## FAQ générale

### Dois-je supprimer __i18n_tmp__ avant chaque nouvelle exécution ?

Non, le dossier temporaire peut contenir plusieurs exécutions horodatées. Chaque outil crée un nouveau sous-dossier daté. Supprimez uniquement :
- Les backups régulièrement (après validation)
- Tout le dossier quand l'espace disque devient un problème

### Puis-je supprimer uniquement certaines sessions de backup ?

Oui, avec Delete_temp_dir.py en mode "Supprimer UNIQUEMENT les backups", toutes les sessions sont supprimées. Pour supprimer manuellement certaines sessions :

```bash
# Supprimer une session spécifique
rm -rf monPlugin.lrplugin/__i18n_tmp__/2_Applicator/20260127_091234/

# Garder uniquement les 2 dernières sessions
cd monPlugin.lrplugin/__i18n_tmp__/2_Applicator/
ls -t | tail -n +3 | xargs rm -rf
```

### Les backups sont-ils créés automatiquement ?

Oui, ***Applicator*** crée automatiquement des backups `.bak` de tous les fichiers modifiés dans `__i18n_tmp__/2_Applicator/<timestamp>/backups/` (sauf si vous utilisez `--no-backup`, ce qui est fortement déconseillé).

### Puis-je restaurer après avoir supprimé __i18n_tmp__ ?

Non, les backups sont dans `__i18n_tmp__/2_Applicator/`. Si vous avez utilisé "Supprimer TOUT", vous ne pourrez plus les restaurer avec cet outil. Options de secours :
- Utilisez Git : `git checkout HEAD -- *.lua`
- Restaurez depuis vos propres sauvegardes

Si vous avez utilisé "Supprimer uniquement les backups", vous avez encore les extractions et sorties Translator.

### Les outils fonctionnent-ils sur Linux/Mac ?

Oui, les deux scripts sont compatibles multi-plateformes (Windows, Linux, macOS). L'intégration de menu_generator gère automatiquement la détection des couleurs ANSI selon le terminal.

### Comment intégrer ces outils dans LocalisationToolKit ?

C'est déjà fait ! Depuis la v2.0, les deux outils s'intègrent automatiquement :
- Option 4 du menu principal → Restore_backup
- Option 5 du menu principal → Delete_temp_dir

Le chemin du plugin configuré est automatiquement transmis via `--default-plugin`.

### Que faire si je n'ai ni backups ni Git ?

**Prévention :**
- Toujours laisser ***Applicator*** créer les backups (`--no-backup` déconseillé)
- Versionner votre code avec Git
- Faire des sauvegardes externes régulières

**Si c'est trop tard :**
- Les modifications sont dans le code .lua, vous devrez restaurer manuellement ou réécrire
- Relancer ***Extractor*** + ***Applicator*** sur la version restaurée

## Dépannage

### Delete_temp_dir.py - Erreur de permission

**Symptôme :**
```
  Suppression: 20260131_102545... [ERREUR]
    Permission refusée: [Errno 13] Permission denied
```

**Solutions :**
1. Fermez tous les programmes qui accèdent au dossier (éditeurs, explorateurs, Lightroom)
2. Relancez le terminal en administrateur (Windows) : clic droit → "Exécuter en tant qu'administrateur"
3. Vérifiez les permissions du dossier avec `ls -la` (Linux/Mac) ou Propriétés → Sécurité (Windows)
4. Sur Linux/Mac, utilisez `sudo` si nécessaire (déconseillé, vérifiez d'abord les permissions)

### Delete_temp_dir.py - Aucun backup trouvé

**Symptôme :**
```
  1. Supprimer UNIQUEMENT les backups (aucun backup trouvé)
```

**Causes possibles :**
1. ***Applicator*** n'a jamais été exécuté
2. ***Applicator*** a été lancé avec `--no-backup`
3. Les backups ont déjà été supprimés

**Solutions :**
- Si vous voulez des backups, relancez ***Applicator***
- Sinon, utilisez l'option "2. Supprimer TOUT"

### Restore_backup.py - Aucun backup trouvé

**Symptôme :**
```
[ATTENTION] Aucune session ***Applicator*** trouvée dans __i18n_tmp__/
Recherche des backups legacy (.lua.bak à côté des fichiers)...

[ATTENTION] Aucun fichier .bak trouvé

[INFO] Rien à restaurer
```

**Causes possibles :**
1. ***Applicator*** n'a jamais été exécuté sur ce plugin
2. ***Applicator*** a été lancé avec `--no-backup`
3. Le dossier `__i18n_tmp__` a été supprimé (option "Supprimer TOUT")
4. Les `.bak` ont été supprimés manuellement ou via "Supprimer uniquement les backups"

**Solutions :**
1. Vérifiez que le chemin du plugin est correct
2. Vérifiez la présence de `__i18n_tmp__/2_Applicator/`
3. Utilisez Git pour restaurer : `git checkout HEAD -- *.lua`
4. Si vous avez une sauvegarde externe, restaurez-la
5. En dernier recours, reprenez depuis le code source original

### Restore_backup.py - Fichiers partiellement restaurés

**Symptôme :**
```
  [OK] MyDialog.lua
  [FAIL] Settings.lua - Erreur: Permission denied
  [OK] Upload.lua
```

**Solutions :**
1. Fermez le fichier problématique s'il est ouvert dans un éditeur
2. Fermez Lightroom Classic s'il a chargé le plugin
3. Vérifiez les permissions du fichier
4. Relancez le script pour terminer la restauration

### Plugin par défaut non détecté

**Symptôme :**
```
[ATTENTION] Plugin par défaut invalide: Répertoire introuvable
```

**Causes :**
- Le chemin configuré dans `config.json` de LocalisationToolKit n'existe plus
- Le plugin a été déplacé

**Solutions :**
1. Lancez `LocalisationToolKit.py` → Option 6 (Configurer le plugin)
2. Mettez à jour le chemin du plugin
3. Ou lancez l'outil directement en mode interactif sans `--default-plugin`

### Encodage des noms de fichiers

Si les noms de fichiers contiennent des caractères spéciaux ou accentués, assurez-vous que votre terminal supporte UTF-8.

**Windows (PowerShell) :**
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

**Windows (CMD) :**
```cmd
chcp 65001
```

**Linux/Mac :**
```bash
export LANG=en_US.UTF-8
```

## Performances

Ces deux outils sont très rapides car ils effectuent des opérations simples sur le système de fichiers.

**Temps typiques :**

| Opération | Taille | Temps |
|-----------|--------|-------|
| Delete_temp_dir (backups uniquement) | 2-3 Mo, 20 sessions | < 1 seconde |
| Delete_temp_dir (tout) | 5-10 Mo complet | 1-2 secondes |
| Restore_backup | 10-20 fichiers | < 1 seconde |
| Restore_backup | 50+ fichiers | 1-2 secondes |

**Facteurs d'impact :**
- Vitesse du disque (SSD vs HDD)
- Nombre de fichiers
- Taille totale
- Antivirus (peut scanner les fichiers pendant la suppression/copie)

## Intégration dans un workflow

### Workflow complet avec nettoyage sélectif (recommandé)

```bash
#!/bin/bash
# complete_workflow.sh

PLUGIN="./monPlugin.lrplugin"

echo "=== ÉTAPE 1 : Extraction ==="
python 1_Extractor/Extractor_main.py --plugin-path "$PLUGIN"

echo ""
echo "=== ÉTAPE 2 : Application (dry-run) ==="
python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN" --dry-run

read -p "Appliquer les modifications? [o/N] " response
if [[ $response =~ ^[Oo]$ ]]; then
  echo ""
  echo "=== ÉTAPE 3 : Application réelle ==="
  python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN"

  echo ""
  echo "=== ÉTAPE 4 : Test dans Lightroom ==="
  echo "Testez le plugin dans Lightroom, puis appuyez sur Entrée..."
  read

  echo ""
  echo "=== ÉTAPE 5 : Nettoyage sélectif ==="
  echo "Voulez-vous supprimer les backups (conserve extractions) ?"
  read -p "[o/N] " clean_response

  if [[ $clean_response =~ ^[Oo]$ ]]; then
    python 9_Tools/Delete_temp_dir.py --default-plugin "$PLUGIN"
    # → L'utilisateur choisira l'option 1 (backups uniquement)
  fi
else
  echo "Application annulée"
fi
```

### Workflow avec restauration automatique en cas d'erreur

```bash
#!/bin/bash
# safe_apply.sh

PLUGIN="./monPlugin.lrplugin"

# Appliquer avec confirmation
python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN"

if [ $? -ne 0 ]; then
  echo "❌ Erreur lors de l'application"
  echo "Voulez-vous restaurer les backups?"
  read -p "[O/n] " restore

  if [[ ! $restore =~ ^[Nn]$ ]]; then
    python 9_Tools/Restore_backup.py --default-plugin "$PLUGIN"
    # → La session la plus récente sera automatiquement présélectionnée
  fi
  exit 1
fi

# Test dans Lightroom
echo ""
echo "✓ Application réussie"
echo "Testez dans Lightroom, puis appuyez sur Entrée..."
read

# Résultat du test
read -p "Le résultat est-il satisfaisant? [O/n] " result

if [[ $result =~ ^[Nn]$ ]]; then
  echo "Restauration des backups..."
  python 9_Tools/Restore_backup.py --default-plugin "$PLUGIN"
else
  echo "✓ Validation OK"

  # Proposition de nettoyage
  read -p "Supprimer les backups? [o/N] " clean
  if [[ $clean =~ ^[Oo]$ ]]; then
    python 9_Tools/Delete_temp_dir.py --default-plugin "$PLUGIN"
    # → Choisir option 1 (backups uniquement)
  fi
fi
```

### Workflow avec Python et validation Git

```python
#!/usr/bin/env python3
"""
Workflow automatisé avec validation Git et gestion des backups.
"""
import subprocess
import sys

def run_command(cmd, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print('='*60)
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    plugin_path = "./monPlugin.lrplugin"

    # Extraction
    if not run_command(
        f"python 1_Extractor/Extractor_main.py --plugin-path {plugin_path}",
        "EXTRACTION"
    ):
        print("❌ Erreur lors de l'extraction")
        return 1

    # Application dry-run
    if not run_command(
        f"python 2_Applicator/Applicator_main.py --plugin-path {plugin_path} --dry-run",
        "APPLICATION (SIMULATION)"
    ):
        print("❌ Erreur lors du dry-run")
        return 1

    # Confirmation
    response = input("\n➤ Appliquer les modifications? [o/N] ")
    if response.lower() not in ['o', 'oui', 'y', 'yes']:
        print("✗ Application annulée")
        return 0

    # Application réelle
    if not run_command(
        f"python 2_Applicator/Applicator_main.py --plugin-path {plugin_path}",
        "APPLICATION RÉELLE"
    ):
        print("❌ Erreur lors de l'application")

        # Proposition de restauration
        restore = input("\n➤ Restaurer les backups? [O/n] ")
        if restore.lower() not in ['n', 'non', 'no']:
            run_command(
                f"python 9_Tools/Restore_backup.py --default-plugin {plugin_path}",
                "RESTAURATION"
            )
        return 1

    # Vérification Git
    print("\n" + "="*60)
    print("VÉRIFICATION DES MODIFICATIONS (Git)")
    print("="*60)
    subprocess.run("git diff", shell=True)

    # Test
    print("\n➤ Testez le plugin dans Lightroom, puis appuyez sur Entrée...")
    input()

    # Validation
    result = input("➤ Le résultat est-il satisfaisant? [O/n] ")

    if result.lower() in ['n', 'non', 'no']:
        print("\n❌ Résultat non satisfaisant - Restauration...")
        run_command(
            f"python 9_Tools/Restore_backup.py --default-plugin {plugin_path}",
            "RESTAURATION"
        )
        return 1

    print("\n✓ Validation OK")

    # Nettoyage
    clean = input("➤ Supprimer les backups (conserve extractions)? [o/N] ")
    if clean.lower() in ['o', 'oui', 'y', 'yes']:
        run_command(
            f"python 9_Tools/Delete_temp_dir.py --default-plugin {plugin_path}",
            "NETTOYAGE"
        )
        print("   → Choisissez l'option 1 (Supprimer UNIQUEMENT les backups)")

    print("\n✓ Workflow terminé avec succès")
    print("  N'oubliez pas de commiter les modifications dans Git!")

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Contributions

Pour améliorer les outils, vous pouvez :
- Ajouter une option pour supprimer uniquement les sessions de plus de X jours
- Améliorer la gestion des erreurs pour des cas spécifiques Windows
- Ajouter un mode batch pour traiter plusieurs plugins
- Créer une interface graphique (GUI)
- Ajouter une option pour archiver les backups avant suppression
- Implémenter une restauration sélective par fichier dans l'interface

N'hésitez pas à proposer vos modifications via pull request !

## Ressources complémentaires

- **shutil Python** : [Documentation shutil](https://docs.python.org/3/library/shutil.html) (copie/suppression de fichiers)
- **os.path Python** : [Documentation os.path](https://docs.python.org/3/library/os.path.html)
- **Gestion des fichiers** : [Real Python - Working With Files](https://realpython.com/working-with-files-in-python/)
- **menu_generator skill** : `C:\Users\Gotcha\.claude\skills\menu_generator.py`
- **Codes couleur ANSI** : [ANSI Escape Codes](https://en.wikipedia.org/wiki/ANSI_escape_code)

## Version 1.0 (Janvier 2026)
- Version initiale des outils

---

**Développé par Julien MOREAU avec l'aide de Claude (Anthropic)**

Pour toute question ou problème, consultez le README principal ou ouvrez une issue sur le dépôt GitHub.
