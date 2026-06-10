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
        self.cookies = httpx.Cookies()
        self.session = httpx.AsyncClient(follow_redirects=True, cookies=self.cookies)
        self.is_authenticated = False

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

        user_url = f"{self.base_url}/users/authenticated"
        user_response = await self.session.get(user_url)
        user_response.raise_for_status()
        self.owner_id = user_response.json()["id"]

        box_url = f"{self.base_url}/indepboxes?ownerid={self.owner_id}"
        box_response = await self.session.get(box_url)
        box_response.raise_for_status()
        boxes = box_response.json()["content"]

        if not boxes:
            raise Exception("Aucune box Comwatt associée à cet utilisateur")

        self.indepbox_id = boxes[0]["id"]

    async def get_indepboxes(self, owner_id: int) -> List[Dict]:
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/indepboxes?ownerid={owner_id}"
        response = await self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Erreur récupération indepboxes : {response.status_code}")

        return response.json().get("content", [])

    async def get_authenticated_user(self) -> Dict:
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/users/authenticated"
        response = await self.session.get(url)

        if response.status_code != 200:
            raise Exception(f"Erreur lors de la récupération de l'utilisateur : {response.status_code}")

        return response.json()

    async def get_devices(self) -> List[Dict]:
        if not self.is_authenticated:
            await self.authenticate()

        url = f"{self.base_url}/devices?indepbox_id={self.indepbox_id}"
        response = await self.session.get(url)
        response.raise_for_status()
        return response.json()

    async def get_device_stats(self, device_ids: List[int]) -> Dict[str, float]:
        """Retourne la puissance instantanée (W) pour chaque device via FLOW/MINUTE.

        On interroge une fenêtre glissante de 3 minutes et on prend la dernière
        mesure disponible. Cela donne une valeur quasi-instantanée (~1-2 min de
        latence) au lieu de la moyenne horaire précédente (jusqu'à 60 min de retard).
        """
        if not self.is_authenticated:
            await self.authenticate()

        now = datetime.now()
        start = (now - timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")
        end = now.strftime("%Y-%m-%d %H:%M:%S")

        results = {}
        for device_id in device_ids:
            url = (
                f"{self.base_url}/aggregations/raw?device_id={device_id}"
                f"&measure_kind=FLOW&measure_type_id=1"
                f"&level=MINUTE&start={start}&end={end}&mm=0"
            )
            response = await self.session.get(url)
            if response.status_code == 200:
                measures = response.json()
                if measures:
                    last_entry = measures[-1]
                    if isinstance(last_entry, dict):
                        last_value = last_entry.get("value", 0.0)
                    else:
                        last_value = float(last_entry)
                    results[str(device_id)] = last_value
                else:
                    # Aucune mesure dans la fenêtre : on élargit à 10 min en fallback
                    results[str(device_id)] = await self._get_device_stat_fallback(device_id)
            else:
                results[str(device_id)] = 0.0

        return results

    async def _get_device_stat_fallback(self, device_id: int) -> float:
        """Fallback : fenêtre de 10 min si aucune mesure dans les 3 dernières minutes.

        Peut arriver la nuit (production = 0) ou lors d'une coupure réseau brève.
        """
        now = datetime.now()
        start = (now - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        end = now.strftime("%Y-%m-%d %H:%M:%S")

        url = (
            f"{self.base_url}/aggregations/raw?device_id={device_id}"
            f"&measure_kind=FLOW&measure_type_id=1"
            f"&level=MINUTE&start={start}&end={end}&mm=0"
        )
        response = await self.session.get(url)
        if response.status_code == 200:
            measures = response.json()
            if measures:
                last_entry = measures[-1]
                if isinstance(last_entry, dict):
                    return last_entry.get("value", 0.0)
                return float(last_entry)
        return 0.0

    async def get_network_stats(self) -> Dict:
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
