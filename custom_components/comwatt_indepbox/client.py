import hashlib
import httpx
import logging
from typing import List, Dict

_LOGGER = logging.getLogger(__name__)

class ComwattClient:
    """Client asynchrone pour interagir avec l'API Comwatt Indepbox."""

    def __init__(self, username: str, password: str):
        self.base_url = "https://go.comwatt.com/api"
        self.username = username
        self.password = password
        self.session = httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(10.0)  # Timeout global pour éviter les blocages
        )
        self.is_authenticated = False

    async def authenticate(self):
        """Authentifie l'utilisateur et récupère le cookie de session."""
        encoded_password = hashlib.sha256(
            f"jbjaonfusor_{self.password}_4acuttbuik9".encode()
        ).hexdigest()

        url = f"{self.base_url}/v1/authent"
        try:
            response = await self.session.post(url, json={
                "username": self.username,
                "password": encoded_password
            })
        except httpx.HTTPError as e:
            _LOGGER.error("Erreur HTTP lors de l'authentification : %s", str(e))
            raise

        if response.status_code != 200:
            _LOGGER.error("Échec de l'authentification (%s): %s", response.status_code, response.text)
            raise ValueError("Échec de l'authentification")

        if "cwt_session" not in response.cookies:
            _LOGGER.error("Authentification échouée : cookie de session manquant")
            raise ValueError("Cookie de session manquant")

        self.is_authenticated = True
        _LOGGER.debug("Authentification réussie pour l'utilisateur %s", self.username)

    async def get_devices(self) -> List[Dict]:
        """Retourne la liste des appareils enregistrés (pinces, capteurs, etc.)."""
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/devices"
        try:
            response = await self.session.get(url)
        except httpx.HTTPError as e:
            _LOGGER.error("Erreur HTTP lors de get_devices : %s", str(e))
            raise

        if response.status_code != 200:
            _LOGGER.error("Erreur get_devices (%s): %s", response.status_code, response.text)
            raise ValueError("Impossible de récupérer les appareils")

        return response.json()

    async def get_device_stats(self) -> Dict[str, float]:
        """Retourne les dernières mesures (en W) de tous les appareils."""
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/device_stats"
        try:
            response = await self.session.get(url)
        except httpx.HTTPError as e:
            _LOGGER.error("Erreur HTTP lors de get_device_stats : %s", str(e))
            raise

        if response.status_code != 200:
            _LOGGER.error("Erreur get_device_stats (%s): %s", response.status_code, response.text)
            raise ValueError("Impossible de récupérer les statistiques")

        result = {}
        for stat in response.json():
            if "device_id" in stat and "w" in stat:
                result[str(stat["device_id"])] = stat["w"]

        return result

    async def get_network_stats(self) -> Dict:
        """Retourne les données globales de production, consommation et réseau."""
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/network_stats"
        try:
            response = await self.session.get(url)
        except httpx.HTTPError as e:
            _LOGGER.error("Erreur HTTP lors de get_network_stats : %s", str(e))
            raise

        if response.status_code != 200:
            _LOGGER.error("Erreur get_network_stats (%s): %s", response.status_code, response.text)
            raise ValueError("Impossible de récupérer les stats réseau")

        return response.json()

    async def close(self):
        """Ferme proprement la session HTTP."""
        await self.session.aclose()