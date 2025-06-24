# Comwatt Indepbox pour Home Assistant

Intégration personnalisée pour connecter une box **Comwatt Indepbox** à Home Assistant.

---

## 🔧 Fonctionnalités

- Remontée automatique des capteurs (pinces ampèremétriques, onduleurs...)
- Affichage des puissances instantanées (en Watts)
- Récupération automatique via l’API Comwatt
- Rafraîchissement des données toutes les 30 secondes
- Configuration simple via l’interface Home Assistant

---

## 📦 Installation

### 1. Via HACS (recommandé)
Ajoutez ce dépôt GitHub en tant que dépôt personnalisé :

```
https://github.com/epihm/comwatt_indepbox
```

Puis installez depuis HACS > Intégrations.

### 2. Manuelle
1. Copiez le dossier `comwatt_indepbox` dans `config/custom_components/`
2. Redémarrez Home Assistant
3. Allez dans **Paramètres > Intégrations > Ajouter une intégration**
4. Recherchez **Comwatt Indepbox**

---

## 🔐 Authentification

Votre mot de passe est sécurisé par un hachage SHA-256 côté client, comme requis par l’API Comwatt.

---

## 🖥️ Dashboard

Les entités créées seront automatiquement disponibles dans votre interface. Chaque appareil remonté apparaîtra comme un capteur de puissance (W).

---

## ❓ Support

En cas de problème, ouvrez une issue ici :  
[https://github.com/epihm/comwatt_indepbox/issues](https://github.com/epihm/comwatt_indepbox/issues)

---

## 👤 Développé par [Epihm](https://epihm.fr)