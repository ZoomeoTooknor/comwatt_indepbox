import hashlib
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

_LOGGER = logging.getLogger(__name__)


class ComwattClient:
    """Client asynchrone pour interagir avec l'API Comwatt Indepbox."""

    def __init__(self, username: str, password: str):
        self.base_url = "https://go.comwatt.com/api"
        self.username = username
        self.password = password
        self.cookies = httpx.Cookies()
        self._session: Optional[httpx.AsyncClient] = None
        self.is_authenticated = False

    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            self._session = httpx.AsyncClient(follow_redirects=True, cookies=self.cookies)
        return self._session

    async def authenticate(self):
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
        if not self.is_authenticated:
            await self.authenticate()
        session = await self._get_session()
        url = f"{self.base_url}/indepboxes?ownerid={owner_id}"
        response = await session.get(url)
        if response.status_code != 200:
            raise Exception(f"Erreur récupération indepboxes : {response.status_code}")
        return response.json().get("content", [])

    async def get_authenticated_user(self) -> Dict:
        if not self.is_authenticated:
            await self.authenticate()
        session = await self._get_session()
        url = f"{self.base_url}/users/authenticated"
        response = await session.get(url)
        if response.status_code != 200:
            raise Exception(f"Erreur lors de la récupération de l'utilisateur : {response.status_code}")
        return response.json()

    async def get_devices(self) -> List[Dict]:
        if not self.is_authenticated:
            await self.authenticate()
        session = await self._get_session()
        url = f"{self.base_url}/devices?indepbox_id={self.indepbox_id}"
        response = await session.get(url)
        response.raise_for_status()
        return response.json()

    async def get_device_stats(self, device_ids: List[int]) -> Dict[str, float]:
        if not self.is_authenticated:
            await self.authenticate()

        session = await self._get_session()
        now = datetime.now()
        results = {}

        for device_id in device_ids:
            flow_value = await self._fetch_flow_minute(session, device_id, now)
            if flow_value is not None:
                _LOGGER.debug(
                    "[COMWATT] device=%s → FLOW/MINUTE=%.2f W (instantané)",
                    device_id, flow_value
                )
                results[str(device_id)] = flow_value
            else:
                _LOGGER.warning(
                    "[COMWATT] device=%s → FLOW/MINUTE vide, fallback HOUR",
                    device_id
                )
                hour_value = await self._fetch_virtual_quantity_hour(session, device_id, now)
                _LOGGER.warning(
                    "[COMWATT] device=%s → HOUR fallback=%.2f W",
                    device_id, hour_value if hour_value is not None else 0.0
                )
                results[str(device_id)] = hour_value if hour_value is not None else 0.0

        return results

    async def _fetch_flow_minute(
        self, session: httpx.AsyncClient, device_id: int, now: datetime
    ) -> Optional[float]:
        start = (now - timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S")
        end = now.strftime("%Y-%m-%d %H:%M:%S")
        url = (
            f"{self.base_url}/aggregations/raw?device_id={device_id}"
            f"&measure_kind=FLOW&measure_type_id=1"
            f"&level=MINUTE&start={start}&end={end}&mm=0"
        )
        response = await session.get(url)
        _LOGGER.debug(
            "[COMWATT] FLOW/MINUTE device=%s status=%s body=%s",
            device_id, response.status_code, response.text[:200]
        )
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
        start = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        end = now.strftime("%Y-%m-%d %H:%M:%S")
        url = (
            f"{self.base_url}/aggregations/raw?device_id={device_id}"
            f"&measure_kind=VIRTUAL_QUANTITY&measure_type_id=1"
            f"&level=HOUR&start={start}&end={end}&mm="
        )
        response = await session.get(url)
        _LOGGER.debug(
            "[COMWATT] HOUR device=%s status=%s body=%s",
            device_id, response.status_code, response.text[:200]
        )
        if response.status_code == 200:
            measures = response.json()
            if measures:
                last_entry = measures[-1]
                if isinstance(last_entry, dict):
                    return float(last_entry.get("value", 0.0))
                return float(last_entry)
        return None

    async def get_network_stats(self) -> Dict:
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

        _LOGGER.warning("[COMWATT] networkstats body: %s", response.text[:500])
        return response.json()

    async def close(self):
        if self._session is not None:
            await self._session.aclose()
            self._session = None
