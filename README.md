<p align="center">
  <img src="https://github.com/ZoomeoTooknor/comwatt_indepbox/blob/main/custom_components/comwatt_indepbox/logo.png?raw=true" alt="Logo Comwatt Indepbox" width="150">
</p>

# Comwatt Indepbox

[![Add Integration to Home Assistant](https://my.home-assistant.io/badges/integration.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=comwatt_indepbox)

Intégration personnalisée pour Home Assistant permettant de connecter une box **Comwatt Indepbox** (ancienne génération) afin de suivre la consommation, la production, l'autoconsommation, l'autonomie, et les mesures de chaque pince de courant.

## ⚙️ Fonctionnalités

- Authentification sécurisée auprès de l’API Comwatt
- Détection automatique de tous les appareils et capteurs (pinces)
- Remontée des mesures de production, consommation et réseau
- Affichage dans le tableau de bord Énergie de Home Assistant
- Aucune donnée envoyée vers un service tiers

## 📋 Prérequis

- Home Assistant >= 2024.1.0
- Une box Comwatt Indepbox (ancienne génération) avec accès à l'API activé

## 🚀 Installation

### Via HACS (recommandé)

1. Ouvre HACS dans Home Assistant
2. Va dans **Intégrations > Dépôts personnalisés**
3. Ajoute l’URL du dépôt :  
   ```text
   https://github.com/ZoomeoTooknor/comwatt_indepbox
   ```
4. Sélectionne la catégorie **Intégration**
5. Installe l’intégration **Comwatt Indepbox**
6. Redémarre Home Assistant

### Configuration

1. Va dans **Paramètres > Appareils & Services**
2. Clique sur **Ajouter une intégration**
3. Choisis **Comwatt Indepbox**
4. Renseigne ton identifiant et mot de passe Comwatt
5.	Associe un rôle à chaque pince détectée :
    •	Production (autoconsommation)
    •	Production (revente totale)
    •	Consommation
Ces choix permettent à Home Assistant d’intégrer correctement chaque source dans le tableau de bord énergie.

### ⚡ Ajout au tableau de bord Énergie

Pour visualiser les données dans le tableau de bord Énergie de Home Assistant, il est nécessaire de créer des capteurs personnalisés qui agrègent les mesures issues des différentes pinces.

1. Créer des capteurs de puissance (en Watts)
Dans votre fichier templates.yaml, créez un capteur par type d’énergie à agréger (exemples : consommation globale, production solaire en autoconsommation, production solaire revendue).

Voici un exemple générique :
<
# templates.yaml

- sensor:
    - name: "Consommation Globale W"
      unique_id: consommation_globale_w
      unit_of_measurement: "W"
      state_class: measurement
      device_class: power
      state: >
        {{ (
          states('sensor.nom_capteur_consommation_1') | float(0) +
          states('sensor.nom_capteur_consommation_2') | float(0)
        ) | round(2) }}

    - name: "Production Solaire Autoconsommation W"
      unique_id: production_autoconso_w
      unit_of_measurement: "W"
      state_class: measurement
      device_class: power
      state: >
        {{ (
          states('sensor.nom_capteur_solaire_autoconso_1') | float(0) +
          states('sensor.nom_capteur_solaire_autoconso_2') | float(0)
        ) | round(2) }}

    - name: "Production Solaire Revente W"
      unique_id: production_revente_w
      unit_of_measurement: "W"
      state_class: measurement
      device_class: power
      state: >
        {{ (
          states('sensor.nom_capteur_solaire_revente_1') | float(0) +
          states('sensor.nom_capteur_solaire_revente_2') | float(0)
        ) | round(2) }}
>
💡 Remplace les noms sensor.nom_capteur_... par ceux créés automatiquement par l’intégration Comwatt Indepbox selon ta configuration.

2. Créer les capteurs d’énergie (en kWh)

Dans ton fichier sensors.yaml, convertis chaque capteur de puissance en énergie via la plateforme integration :
<
# sensors.yaml

- platform: integration
  source: sensor.consommation_globale_w
  name: Consommation Globale kWh
  unique_id: consommation_globale_kwh
  unit_prefix: k
  unit_time: h
  round: 2
  method: trapezoidal

- platform: integration
  source: sensor.production_autoconso_w
  name: Production Autoconsommée kWh
  unique_id: production_autoconso_kwh
  unit_prefix: k
  unit_time: h
  round: 2
  method: trapezoidal

- platform: integration
  source: sensor.production_revente_w
  name: Production Revente kWh
  unique_id: production_revente_kwh
  unit_prefix: k
  unit_time: h
  round: 2
  method: trapezoidal
>

3. Vérifier la configuration

Assure-toi que ton fichier configuration.yaml contient bien :
<
template: !include templates.yaml
sensor: !include sensors.yaml
>

4. Redémarrer Home Assistant

Redémarre Home Assistant (ou recharge les modèles + capteurs si tu es à l’aise), puis va dans Paramètres > Tableau de bord Énergie pour ajouter :
	•	une source de consommation (Consommation Globale kWh)
	•	une ou plusieurs sources de production solaire (Production Autoconsommée kWh, Production Revente kWh)


## 🗂️ Structure du projet

```
custom_components/
└── comwatt_indepbox/
    ├── __init__.py
    ├── api.py
    ├── config_flow.py
    ├── const.py
    ├── manifest.json
    ├── sensor.py
    ├── translations/
    │   └── fr.json
    └── ...
```

## 🔐 Respect de la vie privée

Cette intégration ne transmet aucune donnée à un tiers. Toutes les communications se font en local ou vers l'API Comwatt.