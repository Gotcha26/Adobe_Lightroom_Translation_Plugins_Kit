# Tools - Documentation technique

**Version 1.0 | Janvier 2026**

## Vue d'ensemble

Le dossier Tools contient deux utilitaires pratiques pour gérer les fichiers temporaires et restaurer les backups. Ces outils sont simples mais essentiels pour maintenir un environnement de travail propre et sécurisé.

## Architecture du projet

```
9_Tools/
├── Delete_temp_dir.py       ← Suppression du dossier temporaire
├── Restore_backup.py        ← Restauration des backups
└── __doc/
    └── README.md            ← Ce fichier
```

Ces deux scripts sont indépendants et peuvent être utilisés directement en CLI ou via le `LocalisationToolKit.py`.

## Delete_temp_dir.py - Nettoyage du dossier temporaire

### Description

Cet outil supprime le dossier temporaire `__i18n_tmp__` (ou le nom configuré) d'un plugin Lightroom. Ce dossier contient toutes les sorties des outils (extractions, backups, rapports).

### Quand l'utiliser ?

- Pour libérer de l'espace disque
- Après avoir terminé un cycle complet de localisation
- Pour nettoyer les anciennes exécutions qui ne sont plus nécessaires
- Avant de versionner le plugin (le dossier temporaire ne doit pas être dans Git)

### Comment ça fonctionne ?

```
Plugin Lightroom
    │
    └── __i18n_tmp__/
        ├── 1_Extractor/
        │   ├── 20260120_100000/    (5 fichiers, 120 Ko)
        │   └── 20260129_143022/    (5 fichiers, 135 Ko)
        ├── 2_Applicator/
        │   └── 20260129_143530/    (15 backups, 2.3 Mo)
        └── 3_TranslationManager/
            └── 20260129_144000/    (8 fichiers, 45 Ko)

        TOTAL: 33 fichiers, 2.6 Mo

        ▼

    SUPPRESSION (après triple confirmation)

        ▼

    __i18n_tmp__/ supprimé
```

### Utilisation

**Mode interactif :**
```bash
python 9_Tools/Delete_temp_dir.py
```

L'outil affiche :
1. Le chemin du dossier temporaire
2. Le contenu détaillé (nombre de fichiers et taille par sous-dossier)
3. La taille totale
4. Une triple confirmation pour la sécurité

**Exemple de sortie :**

```
==================================================
     SUPPRESSION DU DOSSIER TEMPORAIRE
==================================================

Chemin du plugin : ./monPlugin.lrplugin

Dossier temporaire : __i18n_tmp__
Chemin complet     : ./monPlugin.lrplugin/__i18n_tmp__

==================================================
       CONTENU DU DOSSIER TEMPORAIRE
==================================================

  Extractor                 :   10 fichiers, 255.0 Ko
  Applicator                :   15 fichiers, 2.3 Mo
  TranslationManager        :    8 fichiers, 45.0 Ko

--------------------------------------------------
TOTAL: 33 fichiers, 2.6 Mo
--------------------------------------------------

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!! ATTENTION - OPÉRATION IRRÉVERSIBLE !!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Cette opération va SUPPRIMER DÉFINITIVEMENT:
  ./monPlugin.lrplugin/__i18n_tmp__

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

Suppression de ./monPlugin.lrplugin/__i18n_tmp__...
✓ Dossier temporaire supprimé avec succès!
```

### Sécurité

Le script intègre plusieurs niveaux de protection :

1. **Validation du chemin** : Vérifie que le plugin existe
2. **Affichage détaillé** : Montre exactement ce qui sera supprimé
3. **Triple confirmation** :
   - Confirmation initiale (o/N)
   - Mot de passe ("SUPPRIMER")
   - Dernière chance (o/N)
4. **Gestion des erreurs** : Détecte les permissions insuffisantes

### Cas d'erreur

**Erreur de permission :**
```
✗ Permission refusée: [WinError 32] The process cannot access the file...
  Fermez tous les programmes qui utilisent ces fichiers.
```

**Solution :** Fermez tous les éditeurs, explorateurs de fichiers ou programmes qui accèdent au dossier temporaire.

### Recommandations

- **Ne supprimez pas** si vous avez besoin des backups pour restaurer des fichiers
- **Ne supprimez pas** si vous voulez comparer deux extractions avec TranslationManager
- **Supprimez régulièrement** pour éviter l'accumulation de fichiers temporaires
- **Ajoutez au .gitignore** : `__i18n_tmp__/` pour ne pas versionner ce dossier

## Restore_backup.py - Restauration des backups

### Description

Cet outil restaure les fichiers `.lua` d'un plugin depuis leurs sauvegardes `.bak` créées par Applicator. Utile pour annuler les modifications en cas d'erreur ou de résultat non souhaité.

### Quand l'utiliser ?

- Après une application qui a produit des résultats incorrects
- Pour revenir à l'état avant localisation
- Pour tester différentes versions (appliquer → tester → restaurer → modifier → réappliquer)
- En cas d'erreur dans les remplacements

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

    ├── MyDialog.lua (restauré)
    ├── Settings.lua (restauré)
    └── Upload.lua (restauré)
```

### Utilisation

**Mode interactif :**
```bash
python 9_Tools/Restore_backup.py
```

**Mode CLI avec auto-détection :**
```bash
python 9_Tools/Restore_backup.py /chemin/vers/plugin.lrplugin
```

**Mode dry-run (simulation) :**
```bash
python 9_Tools/Restore_backup.py --dry-run /chemin/vers/plugin.lrplugin
```

### Exemple de sortie

**Détection automatique :**

```
============================================================
  RESTAURATION DES FICHIERS .bak (v2.0)
============================================================

Repertoire du plugin a restaurer:
  Exemples: ./piwigoPublish.lrplugin
            C:\Lightroom\plugin

Chemin: ./monPlugin.lrplugin

[OK] Repertoire: ./monPlugin.lrplugin

[OK] 2 session(s) Applicator trouvee(s) dans __i18n_tmp__/

Sessions Applicator avec backups disponibles:
------------------------------------------------------------
  1. 2026-01-29 14:35:30 (12 fichier(s))
  2. 2026-01-27 09:12:34 (12 fichier(s))
  0. Annuler

Choisir une session (0 pour annuler): 1

[OK] Session selectionnee: 2026-01-29 14:35:30

Mode simulation (dry-run) ? [O/n]: n

[OK] Mode reel - Les fichiers seront modifies

============================================================
RECHERCHE DES FICHIERS .bak
============================================================
Plugin: ./monPlugin.lrplugin
Source: ./monPlugin.lrplugin/__i18n_tmp__/2_Applicator/20260129_143530/backups

Fichiers trouves: 12

  [OK] MyDialog.lua
  [OK] Settings.lua
  [OK] Upload.lua
  [OK] Export.lua
  ...

Restaurer ces 12 fichier(s) ? [o/N]: o

============================================================
RESTAURATION
============================================================

  [OK] MyDialog.lua
  [OK] Settings.lua
  [OK] Upload.lua
  [OK] Export.lua
  ...

Supprimer les fichiers .bak ? [o/N]: n

============================================================
RESUME
============================================================
Fichiers restaures: 12

Termine!
```

### Structure des backups

Restore_backup prend en charge deux structures :

**1. Structure __i18n_tmp__ (recommandée, depuis v2.0) :**

```
monPlugin.lrplugin/
├── MyDialog.lua              ← Fichier à restaurer
├── Settings.lua
└── __i18n_tmp__/
    └── Applicator/
        ├── 20260129_143530/
        │   └── backups/
        │       ├── MyDialog.lua.bak    ← Source
        │       └── Settings.lua.bak
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

L'outil détecte automatiquement la structure disponible.

### Mode dry-run

Le mode dry-run (simulation) permet de prévisualiser les actions sans modifier les fichiers.

```bash
python Restore_backup.py --dry-run ./plugin.lrplugin
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
RESUME
============================================================
Fichiers qui seraient restaures: 12

!!! MODE SIMULATION - Aucun fichier modifie

Termine!
```

### Gestion des sessions multiples

Si plusieurs sessions Applicator existent, l'outil permet de choisir laquelle restaurer :

```
Sessions Applicator avec backups disponibles:
------------------------------------------------------------
  1. 2026-01-29 14:35:30 (12 fichier(s))  ← La plus récente
  2. 2026-01-28 10:20:15 (12 fichier(s))
  3. 2026-01-27 09:12:34 (11 fichier(s))
  0. Annuler
```

**En mode CLI**, la session la plus récente est automatiquement sélectionnée.

### Suppression des backups

Après restauration, l'outil propose de supprimer les fichiers `.bak` :

```
Supprimer les fichiers .bak ? [o/N]: o

Suppression des .bak:
  [OK] Supprime: MyDialog.lua.bak
  [OK] Supprime: Settings.lua.bak
  ...

[OK] 12 fichier(s) .bak supprime(s)
```

**Recommandation :** Gardez les backups tant que vous n'êtes pas sûr du résultat. Vous pouvez toujours les supprimer plus tard avec `Delete_temp_dir.py`.

### Cas d'usage avancés

**Restaurer une session spécifique :**

1. Listez les sessions disponibles :
```bash
ls monPlugin.lrplugin/__i18n_tmp__/2_Applicator/
```

2. Notez le timestamp de la session souhaitée

3. En mode interactif, choisissez cette session dans le menu

**Restaurer après plusieurs applications :**

Si vous avez appliqué Applicator plusieurs fois, les backups de chaque session sont préservés :

```
Applicator/
├── 20260127_091234/    ← Première application
│   └── backups/
├── 20260129_143530/    ← Deuxième application (avec modifications)
│   └── backups/
└── 20260130_101500/    ← Troisième application
    └── backups/
```

Pour revenir à l'état avant la deuxième application, restaurez la session `20260127_091234`.

**Restaurer sélectivement :**

Pour ne restaurer que certains fichiers :

1. Copiez manuellement les `.bak` souhaités :
```bash
cp monPlugin.lrplugin/__i18n_tmp__/2_Applicator/<timestamp>/backups/MyDialog.lua.bak \
   monPlugin.lrplugin/MyDialog.lua
```

2. Ou supprimez les `.bak` non désirés avant d'exécuter le script

### Intégration avec Git

Si votre plugin est versionné avec Git, une alternative à Restore_backup est :

```bash
# Voir les modifications
git diff

# Restaurer tous les fichiers
git checkout HEAD -- monPlugin.lrplugin/*.lua

# Restaurer un fichier spécifique
git checkout HEAD -- monPlugin.lrplugin/MyDialog.lua
```

**Avantage de Restore_backup :** Restaure à partir des backups locaux, même si vous avez déjà commité les modifications dans Git.

## FAQ générale

### Dois-je supprimer __i18n_tmp__ avant chaque nouvelle exécution ?

Non, le dossier temporaire peut contenir plusieurs exécutions horodatées. Chaque outil crée un nouveau sous-dossier daté. Supprimez uniquement quand l'espace disque devient un problème.

### Les backups sont-ils créés automatiquement ?

Oui, Applicator crée automatiquement des backups `.bak` de tous les fichiers modifiés (sauf si vous utilisez `--no-backup`).

### Puis-je restaurer après avoir supprimé __i18n_tmp__ ?

Non, les backups sont dans `__i18n_tmp__/2_Applicator/`. Si vous les supprimez, vous ne pourrez plus les restaurer avec cet outil. Utilisez Git ou vos propres sauvegardes.

### Les outils fonctionnent-ils sur Linux/Mac ?

Oui, les deux scripts sont compatibles multi-plateformes (Windows, Linux, macOS).

### Comment automatiser le nettoyage ?

Vous pouvez créer un script cron ou tâche planifiée :

```bash
#!/bin/bash
# cleanup_old_backups.sh

PLUGIN_PATH="./monPlugin.lrplugin"
I18N_DIR="$PLUGIN_PATH/__i18n_tmp__"

# Supprimer les dossiers de plus de 30 jours
find "$I18N_DIR" -type d -mtime +30 -exec rm -rf {} \;
```

**Attention :** Testez bien votre script avant de l'automatiser.

### Puis-je restaurer manuellement sans le script ?

Oui, copiez simplement les `.bak` :

```bash
# Structure __i18n_tmp__
cp monPlugin/__i18n_tmp__/2_Applicator/<timestamp>/backups/*.bak monPlugin/

# Puis renommez pour retirer .bak
for f in monPlugin/*.lua.bak; do mv "$f" "${f%.bak}"; done
```

## Dépannage

### Delete_temp_dir.py - Erreur de permission

**Symptôme :**
```
✗ Permission refusée: [Errno 13] Permission denied
```

**Solutions :**
1. Fermez tous les programmes qui accèdent au dossier (éditeurs, explorateurs)
2. Relancez le terminal en administrateur (Windows)
3. Vérifiez les permissions du dossier avec `ls -la` (Linux/Mac)

### Restore_backup.py - Aucun backup trouvé

**Symptôme :**
```
Aucun fichier .bak trouve.
Rien a restaurer.
```

**Causes possibles :**
1. Applicator n'a jamais été exécuté sur ce plugin
2. Applicator a été lancé avec `--no-backup`
3. Le dossier `__i18n_tmp__` a été supprimé
4. Les `.bak` ont été supprimés manuellement

**Solutions :**
1. Vérifiez que le chemin du plugin est correct
2. Vérifiez la présence de `__i18n_tmp__/2_Applicator/`
3. Utilisez Git pour restaurer : `git checkout HEAD -- *.lua`

### Restore_backup.py - Fichiers partiellement restaurés

**Symptôme :**
```
  [OK] MyDialog.lua
  [FAIL] Settings.lua - Erreur: Permission denied
  [OK] Upload.lua
```

**Solutions :**
1. Fermez le fichier problématique s'il est ouvert dans un éditeur
2. Vérifiez les permissions du fichier
3. Relancez le script pour les fichiers échoués

### Encodage des noms de fichiers

Si les noms de fichiers contiennent des caractères spéciaux ou accentués, assurez-vous que votre terminal supporte UTF-8.

**Windows :**
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

- **Delete_temp_dir.py** : 1-2 secondes (dépend de la taille du dossier)
- **Restore_backup.py** : < 1 seconde pour 10-20 fichiers

## Intégration dans un workflow

### Workflow complet avec nettoyage

```bash
#!/bin/bash
# complete_workflow.sh

PLUGIN="./monPlugin.lrplugin"

# 1. Extraction
python 1_Extractor/Extractor_main.py --plugin-path "$PLUGIN"

# 2. Application (avec confirmation)
python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN" --dry-run
read -p "Appliquer? [o/N] " response
if [[ $response =~ ^[Oo]$ ]]; then
  python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN"
fi

# 3. Test dans Lightroom
echo "Testez dans Lightroom, puis appuyez sur Entrée..."
read

# 4. Si OK, nettoyer
read -p "Supprimer les fichiers temporaires? [o/N] " response
if [[ $response =~ ^[Oo]$ ]]; then
  python 9_Tools/Delete_temp_dir.py
fi
```

### Workflow avec restauration automatique

```bash
#!/bin/bash
# safe_apply.sh

PLUGIN="./monPlugin.lrplugin"

# Sauvegarder avant application
BACKUP_DIR="/tmp/plugin_backup_$(date +%s)"
cp -r "$PLUGIN" "$BACKUP_DIR"

# Appliquer
python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN"

# Tester
echo "Testez dans Lightroom."
read -p "Résultat OK? [o/N] " response

if [[ ! $response =~ ^[Oo]$ ]]; then
  echo "Restauration des backups..."
  python 9_Tools/Restore_backup.py "$PLUGIN"
  echo "Ou restauration complète depuis sauvegarde externe:"
  echo "  rm -rf $PLUGIN && cp -r $BACKUP_DIR $PLUGIN"
fi
```

## Contributions

Pour améliorer les outils, vous pouvez :
- Ajouter une option pour supprimer uniquement les sessions de plus de X jours
- Améliorer la gestion des erreurs pour des cas spécifiques
- Ajouter un mode batch pour traiter plusieurs plugins
- Créer une interface graphique

N'hésitez pas à proposer vos modifications !

## Ressources complémentaires

- **shutil Python** : [Documentation shutil](https://docs.python.org/3/library/shutil.html) (copie/suppression de fichiers)
- **os.path Python** : [Documentation os.path](https://docs.python.org/3/library/os.path.html)
- **Gestion des fichiers** : [Real Python - Working With Files](https://realpython.com/working-with-files-in-python/)

---

**Développé par Julien MOREAU avec l'aide de Claude (Anthropic)**

Pour toute question ou problème, consultez le README principal ou ouvrez une issue sur le dépôt GitHub.
