# Applicator - Documentation technique

**Version 7.0 | Janvier 2026**

## Vue d'ensemble

Applicator est le deuxième outil de la chaîne de localisation. Son rôle est d'appliquer automatiquement les remplacements dans le code Lua en transformant les chaînes en dur en appels à la fonction `LOC` du SDK Lightroom.

## Architecture du projet

```
2_Applicator/
├── Applicator_main.py        ← Point d'entrée, logique principale
├── Applicator_menu.py        ← Interface interactive
└── __doc/
    └── README.md             ← Ce fichier
```

L'architecture est volontairement simple : un seul fichier principal contient toute la logique. Cela facilite la compréhension et les modifications ponctuelles.

## Fonctionnement détaillé

### Phase 1 : Chargement des données d'extraction

```
Dossier Extractor (auto-détecté)
    │
    ├── replacements.json
    │   │
    │   └── Structure :
    │       {
    │         "files": {
    │           "MyFile.lua": {
    │             "replacements": [
    │               {
    │                 "line_num": 42,
    │                 "original_line": "title = \"Submit\",",
    │                 "members": [...]
    │               }
    │             ]
    │           }
    │         }
    │       }
    │
    └── spacing_metadata.json (optionnel)
```

Applicator lit le fichier `replacements.json` généré par Extractor. Ce fichier contient toutes les instructions précises pour chaque ligne à modifier.

### Phase 2 : Application des remplacements

```
Pour chaque fichier .lua
    │
    ├── Lecture du fichier ligne par ligne
    │
    ├── Pour chaque ligne référencée dans replacements.json
    │   │
    │   ├── Recherche de chaque chaîne (guillemets doubles ET simples)
    │   │
    │   ├── Vérification que la chaîne n'est pas déjà dans un LOC
    │   │
    │   ├── Construction de l'appel LOC avec métadonnées
    │   │   │
    │   │   ├── Espaces avant : '" " .. '
    │   │   ├── Appel LOC : 'LOC "$$$/Key=Default"'
    │   │   ├── Suffixe : ' .. ":"'
    │   │   └── Espaces après : ' .. " "'
    │   │
    │   └── Remplacement dans la ligne
    │
    ├── Création backup (.bak) AVANT modification
    │
    └── Écriture du fichier modifié
```

### Phase 3 : Génération du rapport

```
Rapport d'application
    │
    ├── Statistiques globales
    │   ├── Fichiers traités
    │   ├── Fichiers modifiés
    │   ├── Lignes modifiées
    │   └── Chaînes remplacées
    │
    ├── Détails des modifications
    │   ├── Fichier : MyDialog.lua
    │   ├── Ligne 42
    │   ├── AVANT : title = "Submit",
    │   ├── APRÈS : title = LOC "$$$/App/Submit=Submit",
    │   └── Chaînes : "Submit" → $$$/App/Submit
    │
    └── Recommandations post-traitement
        ├── Vérifier avec git diff
        ├── Redémarrer Lightroom (reload ne suffit pas)
        └── Tester les textes dans l'interface
```

## Format SDK Lightroom

Le SDK Lightroom impose un format strict pour la localisation :

```lua
LOC "$$$/Key=Default Value"
```

### Pourquoi la valeur par défaut est obligatoire ?

Sans valeur par défaut, Lightroom affiche la clé brute (`$$$/App/Submit`) au lieu du texte. C'est inesthétique et déroutant pour l'utilisateur.

### Exemples de transformations

**Simple :**
```lua
-- AVANT
title = "Submit"

-- APRÈS
title = LOC "$$$/Piwigo/Submit=Submit"
```

**Avec espaces :**
```lua
-- AVANT
label = "  Username:  "

-- APRÈS
label = "  " .. LOC "$$$/Piwigo/Username=Username" .. ":  "
```

**Concaténation :**
```lua
-- AVANT
message = "Uploading " .. count .. " photos"

-- APRÈS
message = LOC "$$$/Piwigo/Uploading=Uploading " .. count .. LOC "$$$/Piwigo/Photos= photos"
```

**Guillemets simples :**
```lua
-- AVANT
text = 'Hello World'

-- APRÈS
text = LOC "$$$/Piwigo/HelloWorld=Hello World"
```

## Options de configuration

### Mode interactif

Lancez `Applicator_main.py` pour accéder au menu :

```
==================================================
        APPLICATOR - Configuration
==================================================

Plugin configuré : ./monPlugin.lrplugin

Dernière extraction détectée :
  __i18n_tmp__/Extractor/20260129_143022/

Options:
  [1] Utiliser cette extraction
  [2] Sélectionner une autre extraction
  [3] Mode dry-run (simulation)
  [4] Options de backup
  [0] Annuler
```

### Mode CLI

```bash
python Applicator_main.py --plugin-path ./plugin.lrplugin [OPTIONS]
```

**Options disponibles :**

| Option | Description | Défaut | Exemple |
|--------|-------------|--------|---------|
| `--plugin-path` | Chemin du plugin (OBLIGATOIRE) | - | `./monPlugin.lrplugin` |
| `--extraction-dir` | Dossier Extractor spécifique | Auto-détection | `./plugin/__i18n_tmp__/Extractor/20260129_143022/` |
| `--dry-run` | Mode simulation (pas de modification) | false | `--dry-run` |
| `--no-backup` | Ne pas créer de backups .bak | false (backup actif) | `--no-backup` |

### Exemples d'utilisation

**Application standard avec auto-détection :**
```bash
python Applicator_main.py --plugin-path ./piwigoPublish.lrplugin
```

**Mode dry-run (simulation) :**
```bash
python Applicator_main.py --plugin-path ./plugin.lrplugin --dry-run
```

**Application sans backup (déconseillé) :**
```bash
python Applicator_main.py --plugin-path ./plugin.lrplugin --no-backup
```

**Application avec extraction spécifique :**
```bash
python Applicator_main.py \
  --plugin-path ./plugin.lrplugin \
  --extraction-dir ./plugin/__i18n_tmp__/Extractor/20260128_120000/
```

## Structure des backups

Les backups sont essentiels pour restaurer les fichiers en cas d'erreur.

### Organisation

```
monPlugin.lrplugin/
├── MyDialog.lua                     ← Fichier modifié
├── Settings.lua                     ← Fichier modifié
└── __i18n_tmp__/
    └── Applicator/
        └── 20260129_143530/         ← Timestamp de l'application
            ├── application_report.txt
            └── backups/
                ├── MyDialog.lua.bak
                └── Settings.lua.bak
```

Chaque exécution crée un nouveau dossier horodaté avec ses propres backups.

### Restauration manuelle

Si vous devez restaurer manuellement :

```bash
# Restaurer un fichier
cp monPlugin.lrplugin/__i18n_tmp__/2_Applicator/20260129_143530/backups/MyDialog.lua.bak \
   monPlugin.lrplugin/MyDialog.lua

# Restaurer tous les fichiers
cp monPlugin.lrplugin/__i18n_tmp__/2_Applicator/20260129_143530/backups/*.bak \
   monPlugin.lrplugin/
```

Ou utilisez l'outil `Restore_backup.py` du kit.

## Gestion des cas complexes

### Lignes déjà partiellement localisées

Applicator détecte si une ligne contient déjà des appels `LOC` et n'applique que les remplacements nécessaires.

```lua
-- Ligne mixte (avant)
title = "Prefix " .. LOC "$$$/App/Existing=Existing" .. " Suffix"

-- Applicator détecte LOC existant et remplace uniquement "Prefix " et " Suffix"
title = LOC "$$$/App/Prefix=Prefix " .. LOC "$$$/App/Existing=Existing" .. LOC "$$$/App/Suffix= Suffix"
```

### Guillemets doubles vs simples

Lua accepte les deux types de guillemets. Applicator les détecte tous les deux :

```lua
-- Guillemets doubles
title = "Submit"  -- ✓ Détecté

-- Guillemets simples
title = 'Submit'  -- ✓ Détecté

-- Guillemets échappés
text = "He said: \"Hello\""  -- ✓ Géré correctement
```

### Positions multiples de la même chaîne

Si une chaîne apparaît plusieurs fois sur la même ligne :

```lua
-- Avant
text = "OK" .. separator .. "OK"

-- Après (chaque occurrence remplacée)
text = LOC "$$$/App/OK=OK" .. separator .. LOC "$$$/App/OK_2=OK"
```

Applicator évite les doublons en trackant les positions déjà utilisées.

## Auto-détection de l'extraction

Applicator recherche automatiquement la dernière extraction dans `__i18n_tmp__/Extractor/`.

### Algorithme de détection

```
1. Chercher le dossier __i18n_tmp__/Extractor/ dans le plugin
2. Lister tous les sous-dossiers horodatés (YYYYMMDD_HHMMSS)
3. Trier par timestamp décroissant
4. Prendre le plus récent contenant replacements.json
```

Si aucun dossier n'est trouvé, Applicator affiche une erreur et demande de lancer Extractor d'abord.

### Forcer une extraction spécifique

Si vous voulez utiliser une extraction plus ancienne :

```bash
python Applicator_main.py \
  --plugin-path ./plugin.lrplugin \
  --extraction-dir ./plugin/__i18n_tmp__/Extractor/20260127_090000/
```

## Rapport d'application

Le fichier `application_report.txt` contient tous les détails de l'exécution.

### Structure du rapport

```
================================================================================
RAPPORT DE LOCALISATION - PiwigoPublish Plugin
================================================================================

STATISTIQUES GLOBALES
--------------------------------------------------------------------------------
Fichiers traités        : 12
Fichiers modifiés       : 8
Lignes modifiées        : 156
Chaînes remplacées      : 142
Chaînes ignorées        : 14
Erreurs                 : 0

================================================================================
MODIFICATIONS EFFECTUÉES
================================================================================

--------------------------------------------------------------------------------
Fichier: MyDialog.lua
--------------------------------------------------------------------------------

  Ligne 42:
  AVANT : title = "Submit",
  APRÈS : title = LOC "$$$/Piwigo/Submit=Submit",
    - "Submit" -> $$$/Piwigo/Submit

  Ligne 58:
  AVANT : label = "Username:"
  APRÈS : label = LOC "$$$/Piwigo/Username=Username" .. ":"
    - "Username" -> $$$/Piwigo/Username

...

================================================================================
CHAINES IGNORÉES
================================================================================

  MyDialog.lua:23
    Raison: Chaine déjà localisée
    Contenu: title = LOC "$$$/Piwigo/ExistingKey=Value",

  Settings.lua:67
    Raison: Chaine non trouvée (modifiée depuis extraction?)
    Contenu: text = "Old Value"

================================================================================
RECOMMANDATIONS POST-TRAITEMENT
================================================================================

1. Vérifier les modifications avec Git diff
2. REDEMARRER Lightroom Classic (reload ne suffit pas)
3. Vérifier que TranslatedStrings_fr.txt existe à la racine
4. Tester les textes dans l'interface
```

### Interprétation des statistiques

- **Fichiers modifiés** : Nombre de fichiers où au moins un remplacement a été effectué
- **Lignes modifiées** : Nombre de lignes transformées
- **Chaînes remplacées** : Nombre total de chaînes converties en LOC
- **Chaînes ignorées** : Chaînes non remplacées (déjà LOC, introuvables, etc.)

## Gestion des fichiers de traduction

Après l'application, Applicator propose de gérer les fichiers `TranslatedStrings_xx.txt`.

### Scénario 1 : Aucun fichier de traduction

```
Aucun fichier TranslatedStrings_xx.txt trouvé à la racine du plugin.
Ce fichier est nécessaire pour les traductions Lightroom.

Un fichier template a été trouvé dans l'extraction:
  __i18n_tmp__/Extractor/20260129_143022/TranslatedStrings_en.txt

Voulez-vous le copier à la racine du plugin?
  -> ./monPlugin.lrplugin/TranslatedStrings_en.txt

Copier le fichier? [O/n]:
```

Si vous acceptez, le fichier est copié automatiquement.

### Scénario 2 : Fichiers existants

```
Fichier(s) de traduction trouvé(s):
  - TranslatedStrings_en.txt
  - TranslatedStrings_fr.txt

Voulez-vous ouvrir le gestionnaire de traductions (TranslationManager)?
Cela permet de synchroniser les traductions avec les nouvelles clés.

Ouvrir TranslationManager? [o/N]:
```

Si vous acceptez, TranslationManager est lancé automatiquement.

## Cas d'usage avancés

### Application en mode dry-run pour validation

Avant d'appliquer réellement les modifications, testez en dry-run :

```bash
# 1. Dry-run pour voir ce qui sera modifié
python Applicator_main.py --plugin-path ./plugin.lrplugin --dry-run

# 2. Consulter le rapport
cat ./plugin.lrplugin/__i18n_tmp__/2_Applicator/<timestamp>/application_report.txt

# 3. Si OK, appliquer réellement
python Applicator_main.py --plugin-path ./plugin.lrplugin
```

### Application après modification manuelle de replacements.json

Si vous avez édité `replacements.json` pour personnaliser les clés ou les valeurs :

```bash
# Appliquer avec votre replacements.json modifié
python Applicator_main.py \
  --plugin-path ./plugin.lrplugin \
  --extraction-dir ./chemin/vers/extraction/modifiee/
```

### Application sélective (certains fichiers uniquement)

Éditez `replacements.json` pour ne garder que les fichiers souhaités :

```json
{
  "files": {
    "MyDialog.lua": { ... },
    // Supprimez les autres fichiers
  }
}
```

Puis lancez Applicator normalement.

### Réapplication après modification du code

Si vous avez modifié le code après une extraction mais avant l'application :

1. Relancez Extractor pour générer un nouveau `replacements.json`
2. Puis lancez Applicator avec la nouvelle extraction

## Dépannage

### Erreur : "Aucune extraction trouvée"

**Cause :** Aucun dossier `__i18n_tmp__/Extractor/` dans le plugin.

**Solution :**
```bash
# Lancer Extractor d'abord
python 1_Extractor/Extractor_main.py --plugin-path ./plugin.lrplugin
```

### Erreur : "Fichier replacements.json introuvable"

**Cause :** Le dossier d'extraction est incomplet ou corrompu.

**Solution :**
```bash
# Relancer une extraction complète
python 1_Extractor/Extractor_main.py --plugin-path ./plugin.lrplugin
```

### Chaînes non remplacées

Si des chaînes attendues ne sont pas remplacées :

**Causes possibles :**
1. Le code a changé depuis l'extraction (ligne différente)
2. La chaîne est déjà dans un LOC
3. Les guillemets sont différents (échappés, etc.)

**Solutions :**
1. Relancer Extractor pour mettre à jour `replacements.json`
2. Vérifier le rapport dans la section "CHAÎNES IGNORÉES"
3. Vérifier manuellement le fichier concerné

### Lightroom n'affiche pas les traductions

**Vérifications :**

1. Le fichier `TranslatedStrings_xx.txt` est à la racine du plugin ?
```bash
ls ./monPlugin.lrplugin/TranslatedStrings_*.txt
```

2. Le code contient bien les appels LOC ?
```bash
grep "LOC " ./monPlugin.lrplugin/*.lua
```

3. Lightroom a été redémarré (pas juste "Reload Plugin") ?

4. La langue système correspond au fichier ?
   - Système français → `TranslatedStrings_fr.txt`
   - Système anglais → `TranslatedStrings_en.txt`

### Backups corrompus ou manquants

Si les backups sont corrompus :

1. Vérifiez l'intégrité :
```bash
diff ./plugin.lrplugin/MyFile.lua \
     ./plugin.lrplugin/__i18n_tmp__/2_Applicator/<timestamp>/backups/MyFile.lua.bak
```

2. Si nécessaire, restaurez depuis Git :
```bash
git checkout HEAD -- ./plugin.lrplugin/MyFile.lua
```

## FAQ technique

### Puis-je appliquer deux fois le même replacements.json ?

Non, la deuxième application échouerait car les chaînes sont déjà dans des LOC. Applicator les détecterait comme "déjà localisées".

### Les backups sont-ils automatiquement supprimés ?

Non, ils restent dans `__i18n_tmp__/2_Applicator/` jusqu'à ce que vous les supprimiez manuellement ou utilisiez l'outil `Delete_temp_dir.py`.

### Puis-je annuler une application sans les backups ?

Si vous n'avez pas de backups, utilisez Git pour restaurer :
```bash
git checkout HEAD -- monPlugin.lrplugin/*.lua
```

C'est pourquoi il est recommandé de versionner votre code avec Git.

### Applicator modifie-t-il Info.lua ?

Oui, si `Info.lua` contient des chaînes à localiser et qu'elles sont dans `replacements.json`. Généralement, `Info.lua` contient peu de texte localisable (nom du plugin, version, etc.).

### Puis-je personnaliser le format LOC généré ?

Le format `LOC "$$$/Key=Default"` est imposé par le SDK Lightroom. Si vous modifiez le format, Lightroom ne reconnaîtra pas les clés.

### Comment gérer les traductions de textes dynamiques ?

Pour les textes dynamiques (ex: "Uploading 5 photos"), séparez le texte statique du dynamique :

```lua
-- Avant
message = "Uploading " .. count .. " photos"

-- Après (par Applicator)
message = LOC "$$$/App/Uploading=Uploading " .. count .. LOC "$$$/App/Photos= photos"
```

Les traductions pourront ensuite adapter l'ordre :
```
# Anglais
"$$$/App/Uploading=Uploading "
"$$$/App/Photos= photos"

# Français
"$$$/App/Uploading=Envoi de "
"$$$/App/Photos= photos"
→ "Envoi de 5 photos"
```

## Performances

### Temps d'exécution typiques

- Petit plugin (5-10 fichiers, 50 remplacements) : < 1 seconde
- Plugin moyen (20-30 fichiers, 200 remplacements) : 2-3 secondes
- Gros plugin (50+ fichiers, 500+ remplacements) : 5-10 secondes

### Impact des backups

La création de backups ajoute ~10-20% de temps d'exécution. C'est négligeable et essentiel pour la sécurité.

### Optimisations possibles

Applicator est déjà optimisé, mais vous pouvez :

1. Utiliser `--no-backup` si vous avez Git (gain de temps minimal)
2. Exclure des fichiers dans Extractor pour réduire `replacements.json`
3. Appliquer hors heures de développement actif

## Intégration dans un workflow automatisé

### Exemple de script bash complet

```bash
#!/bin/bash
# apply_localization.sh

PLUGIN_PATH="./monPlugin.lrplugin"

echo "=== Étape 1 : Extraction ==="
python 1_Extractor/Extractor_main.py --plugin-path "$PLUGIN_PATH"

if [ $? -ne 0 ]; then
  echo "Erreur lors de l'extraction"
  exit 1
fi

echo ""
echo "=== Étape 2 : Application (dry-run) ==="
python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN_PATH" --dry-run

read -p "Appliquer réellement les modifications? [o/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[OoYy]$ ]]; then
  echo ""
  echo "=== Étape 3 : Application réelle ==="
  python 2_Applicator/Applicator_main.py --plugin-path "$PLUGIN_PATH"

  if [ $? -eq 0 ]; then
    echo "✓ Localisation appliquée avec succès"
    echo "  N'oubliez pas de redémarrer Lightroom pour tester"
  else
    echo "✗ Erreur lors de l'application"
    exit 1
  fi
else
  echo "Application annulée"
fi
```

### Exemple avec Python et validation Git

```python
#!/usr/bin/env python3
import subprocess
import sys

def run_command(cmd, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n=== {description} ===")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    plugin_path = "./monPlugin.lrplugin"

    # Extraction
    if not run_command(
        f"python 1_Extractor/Extractor_main.py --plugin-path {plugin_path}",
        "Extraction"
    ):
        print("Erreur lors de l'extraction")
        return 1

    # Application dry-run
    if not run_command(
        f"python 2_Applicator/Applicator_main.py --plugin-path {plugin_path} --dry-run",
        "Application (dry-run)"
    ):
        print("Erreur lors du dry-run")
        return 1

    # Confirmation
    response = input("\nAppliquer les modifications? [o/N] ")
    if response.lower() not in ['o', 'oui', 'y', 'yes']:
        print("Application annulée")
        return 0

    # Application réelle
    if not run_command(
        f"python 2_Applicator/Applicator_main.py --plugin-path {plugin_path}",
        "Application réelle"
    ):
        print("Erreur lors de l'application")
        return 1

    # Vérification Git
    print("\n=== Vérification des modifications (Git) ===")
    subprocess.run("git diff", shell=True)

    print("\n✓ Localisation appliquée avec succès")
    print("  Redémarrez Lightroom pour tester les modifications")

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## Checklist post-application

Après avoir exécuté Applicator, suivez cette checklist :

- [ ] Consulter le rapport d'application (`application_report.txt`)
- [ ] Vérifier les modifications avec `git diff`
- [ ] S'assurer que `TranslatedStrings_en.txt` est à la racine du plugin
- [ ] Copier et traduire les fichiers pour les autres langues (`TranslatedStrings_fr.txt`, etc.)
- [ ] **Redémarrer** Lightroom Classic (pas juste "Reload Plugin")
- [ ] Tester toutes les interfaces utilisateur du plugin
- [ ] Vérifier que les textes s'affichent correctement
- [ ] Valider que les espaces et la mise en forme sont préservés
- [ ] Commit des modifications dans Git avec un message clair

## Ressources complémentaires

- **SDK Lightroom** : [Adobe Developer Console](https://developer.adobe.com/console)
- **Format LOC** : `LOC "$$$/Key=Default"` (documentation officielle)
- **Expressions régulières Python** : [Documentation re](https://docs.python.org/3/library/re.html)
- **JSON Python** : [Documentation json](https://docs.python.org/3/library/json.html)

## Contributions

Pour améliorer Applicator, vous pouvez :
- Ajouter de nouveaux cas de gestion (guillemets échappés complexes, etc.)
- Optimiser la détection des chaînes déjà localisées
- Améliorer le rapport d'application
- Ajouter des validations supplémentaires

N'hésitez pas à proposer vos modifications !

---

**Développé par Julien MOREAU avec l'aide de Claude (Anthropic)**

Pour toute question ou problème, consultez le README principal ou ouvrez une issue sur le dépôt GitHub.
