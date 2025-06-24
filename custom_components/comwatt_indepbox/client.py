import hashlib
import httpx
from typing import List, Dict
from datetime import datetime, timedelta


class ComwattClient:
    """Client asynchrone pour interagir avec l'API Comwatt Indepbox."""

    def __init__(self, username: str, password: str):
        self.base_url = "https://go.comwatt.com/api"
        self.username = username
        self.password = password
        self.session = httpx.AsyncClient(follow_redirects=True)
        self.is_authenticated = False
        self.owner_id = None
        self.indepbox_id = None

    async def authenticate(self):
        """Authentifie l'utilisateur, récupère les cookies, l'owner_id et l'indepbox_id."""
        encoded_password = hashlib.sha256(
            f"jbjaonfusor_{self.password}_4acuttbuik9".encode()
        ).hexdigest()

        login_url = f"{self.base_url}/v1/authent"
        login_response = await self.session.post(login_url, json={
            "username": self.username,
            "password": encoded_password
        })

        if login_response.status_code != 200:
            raise Exception(f"Échec de l'authentification : {login_response.status_code}")

        if "cwt_session" not in login_response.cookies:
            raise Exception("Authentification échouée : cookie de session manquant")

        self.is_authenticated = True

        # Récupération de l'utilisateur authentifié
        user_url = f"{self.base_url}/users/authenticated"
        user_response = await self.session.get(user_url)
        user_response.raise_for_status()
        self.owner_id = user_response.json()["id"]

        # Récupération de la box associée à l'utilisateur
        box_url = f"{self.base_url}/indepboxes?ownerid={self.owner_id}"
        box_response = await self.session.get(box_url)
        box_response.raise_for_status()
        boxes = box_response.json()["content"]

        if not boxes:
            raise Exception("Aucune box Comwatt associée à cet utilisateur")

        self.indepbox_id = boxes[0]["id"]

    async def get_devices(self) -> List[Dict]:
        """Retourne la liste des appareils de la box."""
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/devices?indepbox_id={self.indepbox_id}"
        response = await self.session.get(url)
        response.raise_for_status()
        return response.json()

    async def get_device_stats(self, device_ids: List[int]) -> Dict[str, float]:
        """Retourne les dernières mesures (W) pour chaque device donné."""
        if not self.is_authenticated:
            await self.authenticate()

        now = datetime.now()
        start = (now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        end = now.strftime("%Y-%m-%d %H:%M:%S")

        results = {}
        for device_id in device_ids:
            url = (
                f"{self.base_url}/aggregations/raw?device_id={device_id}"
                f"&measure_kind=VIRTUAL_QUANTITY&measure_type_id=1"
                f"&level=HOUR&start={start}&end={end}&mm="
            )
            response = await self.session.get(url)
            if response.status_code == 200 and response.json():
                # On prend la dernière valeur disponible dans les mesures
                measures = response.json()
                if measures:
                    last_value = measures[-1].get("value", 0.0)
                    results[str(device_id)] = last_value
            else:
                results[str(device_id)] = 0.0

        return results

    async def get_network_stats(self) -> Dict:
        """Retourne les stats réseau de la box Comwatt."""
        if not self.is_authenticated:
            await self.authenticate()

        now = datetime.now()
        start = (now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        end = now.strftime("%Y-%m-%d %H:%M:%S")

        url = (
            f"{self.base_url}/aggregations/networkstats?indepbox_id={self.indepbox_id}"
            f"&level=HOUR&measure_kind=QUANTITY&start={start}&end={end}"
        )

        response = await self.session.get(url)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Ferme proprement la session HTTP."""
        await self.session.aclose()