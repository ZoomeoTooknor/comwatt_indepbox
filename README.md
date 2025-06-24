
# Comwatt Indepbox

![License](https://img.shields.io/github/license/ZoomeoTooknor/comwatt_indepbox?style=flat-square)
[![Open in HACS](https://img.shields.io/badge/Open%20in-HACS-green?logo=home-assistant&style=for-the-badge)](https://my.home-assistant.io/redirect/hacs_repository/?repository_url=https://github.com/ZoomeoTooknor/comwatt_indepbox&category=integration)

Intégration personnalisée pour Home Assistant permettant de connecter une box **Comwatt Indepbox** (ancienne génération) afin de suivre la consommation, la production, l'autoconsommation, l'autonomie, et les mesures de chaque pince de courant.

## ⚙️ Fonctionnalités

- Authentification sécurisée auprès de l'API Comwatt
- Détection automatique de tous les appareils et capteurs (pinces)
- Remontée des mesures de production, consommation et réseau
- Affichage dans le tableau de bord Énergie de Home Assistant
- Aucune donnée envoyée vers un service tiers

## 🧪 Prérequis

- Home Assistant >= 2024.1.0
- Une box Comwatt Indepbox (ancienne génération) avec accès à l'API activé

## 🚀 Installation

### Via HACS (recommandé)

1. Ouvre HACS dans Home Assistant
2. Va dans `Intégrations` > `Dépôts personnalisés`
3. Ajoute l’URL du dépôt :  
   ```
   https://github.com/ZoomeoTooknor/comwatt_indepbox
   ```
4. Sélectionne la catégorie `Intégration`
5. Installe l’intégration `Comwatt Indepbox`
6. Redémarre Home Assistant

### Configuration

1. Va dans `Paramètres > Appareils & Services`
2. Clique sur `Ajouter une intégration`
3. Choisis `Comwatt Indepbox`
4. Renseigne ton identifiant et mot de passe Comwatt

## 📦 Structure du projet

```
custom_components/
└── comwatt_indepbox/
    ├── __init__.py
    ├── client.py
    ├── config_flow.py
    ├── const.py
    ├── manifest.json
    ├── sensor.py
    └── translations/
        └── fr.json
```

## 🙋 Support

Ce projet est maintenu par [@ZoomeoTooknor](https://github.com/ZoomeoTooknor).  
N'hésitez pas à créer une _issue_ pour signaler un bug ou proposer une amélioration.

---

Made with ❤️ for the Home Assistant community.
