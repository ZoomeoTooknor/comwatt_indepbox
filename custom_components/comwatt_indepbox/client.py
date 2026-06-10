import hashlib
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class ComwattClient:
    """Client asynchrone pour interagir avec l'API Comwatt Indepbox."""

    def __init__(self, username: str, password: str):
        self.base_url = "https://go.comwatt.com/api"
        self.username = username
        self.password = password
        self.cookies = httpx.Cookies()
        self._session: Optional[httpx.AsyncClient] = None  # lazy init — évite le blocking call SSL au démarrage
        self.is_authenticated = False

    async def _get_session(self) -> httpx.AsyncClient:
        """Retourne la session HTTP en la créant à la première utilisation (lazy init).

        httpx.AsyncClient charge les certificats SSL de façon synchrone à
        l'instanciation. Le créer dans __init__ (appelé depuis le event loop HA)
        déclenche un warning 'blocking call'. En différant la création au premier
        appel async, on évite ce problème.
        """
        if self._session is None:
            self._session = httpx.AsyncClient(follow_redirects=True, cookies=self.cookies)
        return self._session

    async def authenticate(self):
        """Authentifie l'utilisateur, récupère les cookies, l'owner_id et l'indepbox_id."""
        session = await self._get_session()
        encoded_password = hashlib.sha256(
            f"jbjaonfusor_{self.password}_4acuttbuik9".encode()
        ).hexdigest()

        login_url = f"{self.base_url}/v1/authent"
        login_response = await session.post(login_url, json={
            "username": self.username,
            "password": encoded_password
        })

        if login_response.status_code != 200:
            raise Exception(f"Échec de l'authentification : {login_response.status_code}")

        if "cwt_session" not in login_response.cookies:
            raise Exception("Authentification échouée : cookie de session manquant")

        self.is_authenticated = True

        user_url = f"{self.base_url}/users/authenticated"
        user_response = await session.get(user_url)
        user_response.raise_for_status()
        self.owner_id = user_response.json()["id"]

        box_url = f"{self.base_url}/indepboxes?ownerid={self.owner_id}"
        box_response = await session.get(box_url)
        box_response.raise_for_status()
        boxes = box_response.json()["content"]

        if not boxes:
            raise Exception("Aucune box Comwatt associée à cet utilisateur")

        self.indepbox_id = boxes[0]["id"]

    async def get_indepboxes(self, owner_id: int) -> List[Dict]:
        """Récupère les Indepbox associées à un utilisateur."""
        if not self.is_authenticated:
            await self.authenticate()

        session = await self._get_session()
        url = f"{self.base_url}/indepboxes?ownerid={owner_id}"
        response = await session.get(url)

        if response.status_code != 200:
            raise Exception(f"Erreur récupération indepboxes : {response.status_code}")

        return response.json().get("content", [])

    async def get_authenticated_user(self) -> Dict:
        """Retourne les informations de l'utilisateur connecté (y compris son ID)."""
        if not self.is_authenticated:
            await self.authenticate()

        session = await self._get_session()
        url = f"{self.base_url}/users/authenticated"
        response = await session.get(url)

        if response.status_code != 200:
            raise Exception(f"Erreur lors de la récupération de l'utilisateur : {response.status_code}")

        return response.json()

    async def get_devices(self) -> List[Dict]:
        """Retourne la liste des appareils de la box."""
        if not self.is_authenticated:
            await self.authenticate()

        session = await self._get_session()
        url = f"{self.base_url}/devices?indepbox_id={self.indepbox_id}"
        response = await session.get(url)
        response.raise_for_status()
        return response.json()

    async def get_device_stats(self, device_ids: List[int]) -> Dict[str, float]:
        """Retourne la puissance instantanée (W) pour chaque device.

        Stratégie à deux niveaux :
        1. Tente FLOW/MINUTE sur une fenêtre de 3 min → mesure quasi-instantanée (~1-2 min de latence)
        2. Si aucune donnée (endpoint non supporté par ce device ou box ancienne génération),
           fallback sur VIRTUAL_QUANTITY/HOUR → moyenne horaire, compatible toutes boxes
        """
        if not self.is_authenticated:
            await self.authenticate()

        session = await self._get_session()
        now = datetime.now()

        results = {}
        for device_id in device_ids:
            value = await self._fetch_flow_minute(session, device_id, now)
            if value is None:
                # FLOW/MINUTE non disponible pour ce device → fallback horaire
                value = await self._fetch_virtual_quantity_hour(session, device_id, now)
            results[str(device_id)] = value if value is not None else 0.0

        return results

    async def _fetch_flow_minute(
        self, session: httpx.AsyncClient, device_id: int, now: datetime
    ) -> Optional[float]:
        """Tente de récupérer la puissance instantanée via FLOW/MINUTE (fenêtre 3 min).

        Retourne None si l'endpoint ne renvoie aucune donnée pour ce device.
        """
        start = (now - timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")
        end = now.strftime("%Y-%m-%d %H:%M:%S")
        url = (
            f"{self.base_url}/aggregations/raw?device_id={device_id}"
            f"&measure_kind=FLOW&measure_type_id=1"
            f"&level=MINUTE&start={start}&end={end}&mm=0"
        )
        response = await session.get(url)
        if response.status_code == 200:
            measures = response.json()
            if measures:
                last_entry = measures[-1]
                if isinstance(last_entry, dict):
                    return float(last_entry.get("value", 0.0))
                return float(last_entry)
        return None

    async def _fetch_virtual_quantity_hour(
        self, session: httpx.AsyncClient, device_id: int, now: datetime
    ) -> Optional[float]:
        """Fallback : récupère la mesure via VIRTUAL_QUANTITY/HOUR (fenêtre 2h).

        Compatible avec toutes les boxes Comwatt ancienne génération.
        Latence jusqu'à ~60 min mais toujours disponible.
        """
        start = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        end = now.strftime("%Y-%m-%d %H:%M:%S")
        url = (
            f"{self.base_url}/aggregations/raw?device_id={device_id}"
            f"&measure_kind=VIRTUAL_QUANTITY&measure_type_id=1"
            f"&level=HOUR&start={start}&end={end}&mm="
        )
        response = await session.get(url)
        if response.status_code == 200:
            measures = response.json()
            if measures:
                last_entry = measures[-1]
                if isinstance(last_entry, dict):
                    return float(last_entry.get("value", 0.0))
                return float(last_entry)
        return None

    async def get_network_stats(self) -> Dict:
        """Retourne les stats réseau de la box Comwatt."""
        if not self.is_authenticated:
            await self.authenticate()

        session = await self._get_session()
        now = datetime.now()
        start = (now - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        end = now.strftime("%Y-%m-%d %H:%M:%S")

        url = (
            f"{self.base_url}/aggregations/networkstats?indepbox_id={self.indepbox_id}"
            f"&level=HOUR&measure_kind=QUANTITY&start={start}&end={end}"
        )

        response = await session.get(url)
        response.raise_for_status()
        return response.json()

    async def close(self):
        """Ferme proprement la session HTTP."""
        if self._session is not None:
            await self._session.aclose()
            self._session = None
