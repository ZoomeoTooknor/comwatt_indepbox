import hashlib
import httpx
from typing import List, Dict

class ComwattClient:
    """Client asynchrone pour interagir avec l'API Comwatt Indepbox."""

    def __init__(self, username: str, password: str):
        self.base_url = "https://go.comwatt.com/api"
        self.username = username
        self.password = password
        self.session = httpx.AsyncClient(follow_redirects=True)
        self.is_authenticated = False

    async def authenticate(self):
        """Authentifie l'utilisateur et récupère le cookie de session."""
        encoded_password = hashlib.sha256(
            f"jbjaonfusor_{self.password}_4acuttbuik9".encode()
        ).hexdigest()

        url = f"{self.base_url}/v1/authent"
        response = await self.session.post(url, json={
            "username": self.username,
            "password": encoded_password
        })

        if response.status_code != 200:
            raise Exception(f"Échec de l'authentification : {response.status_code}")

        # Vérification de la présence du cookie de session
        if "cwt_session" not in response.cookies:
            raise Exception("Authentification échouée : cookie de session manquant")

        self.is_authenticated = True

    async def get_devices(self) -> List[Dict]:
        """Retourne la liste des appareils enregistrés (pinces, capteurs, etc.)."""
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/devices"
        response = await self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Erreur lors de la récupération des appareils : {response.status_code}")

        return response.json()

    async def get_device_stats(self) -> Dict[str, float]:
        """Retourne les dernières mesures (en W) de tous les appareils."""
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/device_stats"
        response = await self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Erreur lors de la récupération des mesures : {response.status_code}")

        result = {}
        for stat in response.json():
            # On suppose que chaque élément contient un device_id et une puissance (W)
            if "device_id" in stat and "w" in stat:
                result[str(stat["device_id"])] = stat["w"]

        return result

    async def get_network_stats(self) -> Dict:
        """Retourne les données globales de production, consommation et réseau."""
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/network_stats"
        response = await self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Erreur lors de la récupération des stats réseau : {response.status_code}")

        return response.json()

    async def close(self):
        """Ferme proprement la session HTTP."""
        await self.session.aclose()