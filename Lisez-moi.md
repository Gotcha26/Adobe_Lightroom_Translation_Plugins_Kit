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

- [Présentation du toolkit - vue globale](0_doc/fr/Lisez-moi.md)

### Guides par profil

| Vous êtes... | Commencez par... |
|--------------|------------------|
| Développeur d'un plugin LrC | [Guide Installation](0_doc/fr/Developpeur/01_Installation.md) |
| Développeur en maintenance | [Guide Maintenance](0_doc/fr/Developpeur/02_Maintenance.md) |
| Développeur avancé | [Workflows avancés](0_doc/fr/Developpeur/03_Avance.md) |
| Traducteur débutant | [Contributeur simple](0_doc/fr/Traducteur/01_Contributeur_simple.md) |
| Traducteur autonome | [Contributeur débrouillard](0_doc/fr/Traducteur/02_Contributeur_debrouillard.md) |
| Traducteur professionnel | [Contributeur pro](0_doc/fr/Traducteur/03_Contributeur_pro.md) |

### Documentation technique des outils

Chaque outil dispose de sa propre documentation détaillée :
- [Extractor](1_Extractor/__doc/fr/Lisez-moi.md) — Extraction des chaînes
- [Applicator](2_Applicator/__doc/fr/Lisez-moi.md) — Application des clés LOC()
- [Translator](3_Translator/__doc/fr/Lisez-moi.md) — Gestion des traductions
- [Tools](9_Tools/__doc/fr/Lisez-moi.md) — Utilitaires (restauration, nettoyage)

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

*Fais avec amour et le soleil du sud de la Drôme, entre Mistral et lavandes.*

---

| 📜 | Traçabilité |  |  |
|--|--|--|--|
| **Nom** | *Lisez-moi.md* | **Version** | 1.0 |
| **Type** | Présentation - Auto-promotion | **Langue** | FR - *[EN](README.md)* |
| **Projet GitHub** | [Adobe Lightroom Translation Toolkit](https://github.com/Gotcha26/Adobe_Lightroom_Translation_Plugins_Kit) | **Date** | 2026-02-02 |
| **Licence** | Open source | | |
