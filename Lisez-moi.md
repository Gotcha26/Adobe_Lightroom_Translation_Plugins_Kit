# Adobe Lightroom Translation Plugins Kit

Vous développez un plugin pour **Adobe Lightroom Classic** et vous aimeriez qu'il parle plusieurs langues ?
Vous êtes traducteur et souhaitez contribuer à un plugin existant ?
Ce toolkit est fait pour vous !

---

## 🎯 Le constat

Internationaliser un plugin Lightroom, c'est fastidieux :
- Des dizaines (voire des centaines) de chaînes de texte à extraire
- Des clés de localisation à créer et à maintenir
- Des fichiers de traduction à synchroniser à chaque modification
- Un format SDK Adobe pas toujours intuitif

**Résultat ?** Beaucoup de plugins restent monolingues, faute de temps ou d'outils adaptés.

---

## ✨ La solution

Ce toolkit automatise tout le travail ingrat :

```
     Votre code Lua                        Plugin multilingue
    (texte en dur)                        (prêt à traduire)
          │                                      ▲
          │                                      │
          └──────────►  TOOLKIT  ►───────────────┘
                    (3 outils intégrés)
```

**En quelques clics**, vous passez d'un plugin monolingue à un plugin prêt pour la traduction internationale — sans toucher manuellement aux fichiers de localisation.
Et c'est 100% comforme au SDK Adobe.

---

## 💎 La promesse : La simplicité absolue

Oubliez les fichiers `.pot`, `.mo`, `.po` et les éditeurs compliqués comme POEdit avec compilation obligatoire. Oubliez aussi les resynchronisations fastidieuses du mainteneur.

**Voici ce que vous obtenez vraiment :**

### Une interface guidée, zéro danger

Tout se passe dans **une fenêtre de terminal simple** (Windows, macOS, Linux). Pas d'interface obscure, pas de ligne de commande à mémoriser, des noms pour les outils et les actions très explicites.

```
┌────────────────────────────────────┐
│ LocalizationToolKit Menu           │
├────────────────────────────────────┤
│ 1. Extractor                       │
│ 2. Applicator                      │
│ 3. Translator                      │
│ 4. AUTOSYNC                        │
│ 5. Tools & Utilities               │
│ Q. Quit                            │
│                                    │
│ Choose an option: █                │
└────────────────────────────────────┘
```

**Chaque étape est guidée.** Le toolkit vous explique exactement ce qui va se passer, demande confirmation si nécessaire, et vous prévient avant toute action. Aucune manipulation hasardeuse, aucun risque de casser quelque chose.

### Le flux réel

- **1ère utilisation : 2 clics**
  - Clic 1 : *Extractor* → analyse votre code et extrait les textes.
  - Clic 2 : *Applicator* → mise en place des clés [appels `loc()`] tout en **conservant** les chaînes de texte.

  **Et c'est fini.** Votre plugin est prêt à traduire, 100% fonctionnel, sortie de la boîte. Aucune compilation, aucun outil supplémentaire.

- **Mise à jour du code : 1 clic**
  - Clic : *AUTOSYNC* → synchronise automatiquement les traductions existantes avec les nouveautés du plugin.

  C'est tout. Si vous avez modifié du texte dans votre code, les traducteurs sont avertis. Sinon, rien à faire.

- **Format simple**
  - Pas de configuration d'outils obscurs
  - Respect strict du SDK Adobe — aucune dépendance exotique
  - Configuration préservée automatiquement

**Résultat : moins de temps à bricoler, plus de temps à créer.**

En un mot : **EN-FAN-TIN !**

---

## 👥 Pour qui ?

### Développeurs de plugins Lightroom

Vous codez, le toolkit s'occupe du reste :
- **Extraction automatique** de toutes les chaînes de texte
- **Génération des clés** selon les conventions Adobe SDK
- **Synchronisation** des fichiers de langue à chaque mise à jour
- **Backups automatiques** pour revenir en arrière si besoin

> *"Je code en anglais, je lance le toolkit, et hop : mon plugin est prêt à recevoir des traductions en français, allemand, espagnol..."*

### Traducteurs & Contributeurs

Pas besoin d'être développeur pour contribuer :
- Fichiers de traduction au format texte simple
- Instructions claires pour chaque niveau d'implication
- Possibilité de tester immédiatement vos traductions

> *"J'ai reçu un fichier, j'ai traduit les lignes, j'ai renvoyé. Simple."*

> *"Mon plugin préféré mériterait d'être traduit, je vais me lancer sans pression."*

---

## 🛠️ Trois outils, un seul lanceur

Le toolkit regroupe trois outils complémentaires, accessibles via un menu unique :

| Outil | Rôle |
|-------|------|
| ***Extractor*** | Scanne votre code lua et extrait les textes |
| ***Applicator*** | Remplace les textes par des appels `LOC()` |
| ***Translator*** | Synchronise tous les fichiers de langue |

Chaque outil peut fonctionner seul, mais le lanceur ***LocalisationToolKit*** les orchestre intelligemment en conservant votre configuration.

---

## 🚀 Démarrage express

```bash
# 1. Récupérer le toolkit
git clone https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit.git

# 2. Se placer dans le dossier
cd Adobe_Lightroom_Translation_Plugins_Kit

# 3. Lancer le menu
python LocalisationToolKit.py
```

**Aucune dépendance externe** — uniquement Python 3.7+ et la bibliothèque standard.

---

## 📖 Documentation

### Pour aller plus loin

- [Présentation du toolkit - vue globale](doc/fr/Lisez-moi.md)

### Guides par profil

| Vous êtes... | Commencez par... |
|--------------|------------------|
| Développeur d'un plugin LrC | [Guide Installation](doc/fr/dev/01_Dev_Installation.md) |
| Développeur en maintenance | [Guide Maintenance](doc/fr/dev/02_Dev_Maintenance.md) |
| Développeur avancé | [Workflows avancés](doc/fr/dev/03_Dev_Avance.md) |
| Traducteur débutant | [Contributeur simple](doc/fr/trad/01_Contributeur_simple.md) |
| Traducteur autonome | [Contributeur débrouillard](doc/fr/trad/02_Contributeur_debrouillard.md) |
| Traducteur professionnel | [Contributeur pro](doc/fr/trad/03_Contributeur_pro.md) |

### Documentation technique des outils

Chaque outil dispose de sa propre documentation détaillée :
- [Extractor](tools/extractor/__doc__/fr/Lisez-moi.md) — Extraction des chaînes
- [Applicator](tools/applicator/__doc__/fr/Lisez-moi.md) — Application des clés LOC()
- [Translator](tools/translator/__doc__/fr/Lisez-moi.md) — Gestion des traductions
- [Toolbox](tools/toolbox/__doc__/fr/Lisez-moi.md) — Utilitaires (restauration, nettoyage)

---

## 🤝 Contribuer

### Au toolkit lui-même
- Signalez un bug ou proposez une amélioration via [GitHub Issues](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit/issues)
- Les pull requests sont les bienvenues

### Aux traductions de plugins
- Consultez la documentation du plugin concerné
- Forkez, traduisez, proposez une PR
- Ou envoyez simplement votre fichier traduit au développeur

---

## 🙏 Remerciements

Ce projet est né d'un besoin personnel : rendre mon propre plugin Lightroom multilingue sans y passer des heures. Grâce à l'assistance de **Claude (Anthropic)**, il est devenu un outil que j'espère utile à toute la communauté.

Les retours, suggestions et contributions sont chaleureusement encouragés !

*Fait en France 🇫🇷 avec amour et le soleil du sud de la Drôme provençale, entre Mistral et lavandes.*

---

| 📜 | Traçabilité |  |  |
|--|--|--|--|
| **Nom** | *Lisez-moi.md* | **Version** | 1.0 |
| **Type** | Présentation - Auto-promotion | **Langue** | FR - *[EN](README.md)* |
| **Projet GitHub** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-02 |
| **Licence** | [MIT](LICENSE) | | |
