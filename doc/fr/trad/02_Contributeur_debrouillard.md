# Guide Traducteur : Contributeur débrouillard

Le plugin que vous voulez traduire **n'a pas encore de fichier** `TranslatedStrings_xx.txt` pour votre langue ? Ce guide vous montre comment le créer vous-même.

---

## 📋 Situation type

Vous avez trouvé un plugin Lightroom intéressant, mais il n'existe qu'en anglais :

```
monPlugin.lrplugin/
├── Info.lua
├── PluginCode.lua
└── TranslatedStrings_en.txt      ← Seul fichier existant
```

Vous voulez créer la version française (ou autre langue).

---

## 🎯 Deux approches possibles

### Approche A : Duplication simple (sans le toolkit)

Si vous n'avez pas Python ou ne souhaitez pas installer le toolkit :

1. **Copiez** le fichier anglais
2. **Renommez-le** avec votre code langue
3. **Traduisez** ligne par ligne

```bash
# Dans le dossier du plugin
cp TranslatedStrings_en.txt TranslatedStrings_fr.txt
```

Puis ouvrez `TranslatedStrings_fr.txt` et traduisez chaque valeur.

### Approche B : Avec le toolkit (recommandé)

Si vous avez Python installé, le toolkit facilite le travail.

---

## 🚀 Approche B détaillée : Avec le toolkit

### Étape 1 : Installer le toolkit

```bash
git clone https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit.git
cd Adobe_Lightroom_Translation_Plugins_Kit
```

### Étape 2 : Configurer le plugin cible

```bash
python LocalisationToolKit.py
# Choisir [6] Configuration
# Entrer le chemin vers le plugin
```

### Étape 3 : Extraire les chaînes (optionnel mais recommandé)

Si le plugin n'a pas de fichier `TranslatedStrings_en.txt` ou si vous voulez valider sa structure :

```bash
# Choisir [1] Extractor
```

Cela génère un fichier de référence propre.

### Étape 4 : Créer le fichier pour votre langue

**Option simple** : Dupliquez manuellement le fichier anglais :

```bash
cp monPlugin.lrplugin/TranslatedStrings_en.txt monPlugin.lrplugin/TranslatedStrings_fr.txt
```

**Option toolkit** : Utilisez ***Translator*** :

```bash
python LocalisationToolKit.py
# Choisir [3] Translator
# Choisir l'option pour créer un nouveau fichier de langue
```

### Étape 5 : Traduire

Ouvrez votre fichier `TranslatedStrings_fr.txt` et traduisez chaque ligne :

```
AVANT  : "$$$/Plugin/Menu/File=File"
APRÈS  : "$$$/Plugin/Menu/File=Fichier"
```

Consultez le [Guide Contributeur simple](01_Contributeur_simple.md) pour les détails de traduction.

---

## 📝 Points d'attention

### Respecter le format exact

Chaque ligne doit conserver sa structure :

```
"$$$/Prefixe/Categorie/Cle=Valeur traduite"
```

- Les guillemets `"` au début et à la fin
- La clé complète avant le `=`
- Pas d'espace autour du `=`

### Préserver les placeholders

```
✅ "$$$/Status=Téléversé %d fichiers sur %s"
❌ "$$$/Status=Téléversé fichiers sur"  (placeholders supprimés)
```

### Encoder en UTF-8

Pour les accents (é, è, ê, ç, etc.), le fichier doit être en UTF-8.

---

## 🧪 Tester vos traductions

### Test local immédiat

1. Placez votre fichier traduit dans le plugin :
   ```
   monPlugin.lrplugin/TranslatedStrings_fr.txt
   ```

2. Changez la langue de votre système en français

3. Relancez Lightroom **complètement** (pas juste "Recharger le plugin")

4. Vérifiez que vos traductions apparaissent

### Si ça ne fonctionne pas

- Vérifiez le nom du fichier : `TranslatedStrings_fr.txt` (pas `FR`, pas `french`)
- Vérifiez que le fichier est à la racine du `.lrplugin`
- Vérifiez l'encodage UTF-8
- Redémarrez complètement Lightroom

---

## 📤 Partager votre traduction

Une fois satisfait de votre traduction, partagez-la avec la communauté !

### Via GitHub (recommandé)

1. **Forkez** le repository du plugin
2. **Ajoutez** votre fichier `TranslatedStrings_fr.txt`
3. **Créez une Pull Request**

```bash
git add TranslatedStrings_fr.txt
git commit -m "i18n(fr): Add French translation"
git push origin main
# Puis créez la Pull Request sur GitHub
```

### Sans GitHub

Envoyez simplement le fichier au développeur par email ou message.

---

## 💡 Conseils pour une traduction de qualité

### Comprenez le contexte

- Téléchargez et installez le plugin
- Utilisez-le pour comprendre où chaque texte apparaît
- Adaptez la traduction au contexte (menu, bouton, message d'erreur...)

### Créez un glossaire

Avant de commencer, définissez vos choix de traduction :

```
GLOSSAIRE
─────────────────────────
Export      → Exporter (pas "Exportation")
Settings    → Paramètres (pas "Réglages")
Publish     → Publier
Upload      → Téléverser
Download    → Télécharger
Sync        → Synchroniser
```

### Testez régulièrement

Ne traduisez pas tout d'un coup. Traduisez par sections et testez au fur et à mesure.

---

## 🔗 Ressources

- [Guide contributeur simple](01_Contributeur_simple.md) — Détails sur le format et la traduction
- [Guide contributeur professionnel](03_Contributeur_pro.md) — Outils avancés
- [Documentation technique](../Lisez-moi.md)

---

| 📜 | Traçabilité |  |  |
|--|--|--|--|
| **Nom** | *02_Contributeur_debrouillard.md* | **Version** | 1.0 |
| **Type** | Guide traducteurs - Intermidaire | **Langue** | FR - *[EN](../../en/trad/02_Resourceful_Contributor.md)* |
| **Projet GitHub** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-02 |
| **Licence** | [MIT](../../../LICENSE) | | |
