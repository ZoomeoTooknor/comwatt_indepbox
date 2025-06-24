DOMAIN = "comwatt_indepbox"
NAME = "Comwatt Indepbox"
VERSION = "1.0.0"
MANUFACTURER = "Comwatt"

# Adresse de base de l'API
API_BASE = "https://go.comwatt.com/api"

# Données du client stockées dans hass.data[DOMAIN]
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

# Temps d'actualisation des entités (en secondes)
DEFAULT_SCAN_INTERVAL = 300

# Icône par défaut
DEFAULT_ICON = "mdi:solar-power"

# Catégories de plateforme
PLATFORMS = ["sensor"]