from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio
import json
import subprocess
import logging
import time
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SecretValue:
    id: str
    name: str
    value: str
    folder: Optional[str] = None
    type: str = "login"


class SecretsProvider(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    async def set(self, key: str, value: str, folder: Optional[str] = None) -> bool:
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    async def list(self, folder: Optional[str] = None) -> List[SecretValue]:
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        pass


class BitwardenCloudProvider(SecretsProvider):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        master_password: str,
        vault_url: str = "https://vault.bitwarden.com",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.master_password = master_password
        self.vault_url = vault_url
        self._session_token: Optional[str] = None
        self._session_expires = 0

    async def _run_bw(self, *args: str) -> Dict[str, Any]:
        cmd = ["bw"] + list(args)
        try:
            env = {**os.environ}
            if self._session_token:
                env["BW_SESSION"] = self._session_token
            env["BW_CLIENTID"] = self.client_id
            env["BW_CLIENTSECRET"] = self.client_secret
            env["BW_BASEURL"] = self.vault_url

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )
            if result.returncode != 0:
                logger.error(f"bw error: {result.stderr}")
                raise RuntimeError(f"bw command failed: {result.stderr}")
            return json.loads(result.stdout) if result.stdout else {}
        except Exception as e:
            logger.error(f"BitwardenProvider._run_bw error: {e}")
            raise

    async def _auth(self) -> None:
        now = time.time()
        if self._session_token and self._session_expires > now:
            return

        try:
            result = subprocess.run(
                ["bw", "login", "--apikey", "--raw"],
                input=f"{self.client_id}\n{self.client_secret}\n{self.master_password}",
                capture_output=True,
                text=True,
                timeout=10,
                env={**os.environ, "BW_BASEURL": self.vault_url},
            )
            if result.returncode == 0:
                self._session_token = result.stdout.strip()
                self._session_expires = now + 3600
            else:
                raise RuntimeError(f"bw login failed: {result.stderr}")
        except Exception as e:
            logger.error(f"BitwardenProvider auth failed: {e}")
            raise

    async def get(self, key: str) -> Optional[str]:
        await self._auth()
        try:
            if "/" in key:
                folder, name = key.split("/", 1)
                items = await self._run_bw("list", "items", "--search", name)
                for item in items:
                    if item.get("name") == name and item.get("folderId") == folder:
                        return item.get("login", {}).get("password") or item.get("notes")
                return None
            else:
                item = await self._run_bw("get", "item", key)
                return item.get("login", {}).get("password") or item.get("notes")
        except Exception as e:
            logger.error(f"BitwardenProvider.get({key}) error: {e}")
            return None

    async def set(self, key: str, value: str, folder: Optional[str] = None) -> bool:
        await self._auth()
        try:
            payload = {
                "organizationId": None,
                "type": 1,
                "name": key,
                "notes": None,
                "fields": [],
                "login": {"username": "", "password": value},
                "folderId": folder,
            }
            item_json = json.dumps(payload)
            result = subprocess.run(
                ["bw", "encode", item_json],
                capture_output=True,
                text=True,
                timeout=5,
            )
            encoded = result.stdout.strip()
            await self._run_bw("create", "item", encoded)
            logger.info(f"Secret set: {key}")
            return True
        except Exception as e:
            logger.error(f"BitwardenProvider.set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        await self._auth()
        try:
            await self._run_bw("delete", "item", key)
            logger.info(f"Secret deleted: {key}")
            return True
        except Exception as e:
            logger.error(f"BitwardenProvider.delete error: {e}")
            return False

    async def list(self, folder: Optional[str] = None) -> List[SecretValue]:
        await self._auth()
        try:
            items = await self._run_bw("list", "items")
            result = []
            for item in items:
                if folder and item.get("folderId") != folder:
                    continue
                result.append(
                    SecretValue(
                        id=item.get("id"),
                        name=item.get("name"),
                        value=item.get("login", {}).get("password")
                        or item.get("notes", ""),
                        folder=item.get("folderId"),
                        type=self._type_from_item(item),
                    )
                )
            return result
        except Exception as e:
            logger.error(f"BitwardenProvider.list error: {e}")
            return []

    async def health(self) -> Dict[str, Any]:
        start = time.time()
        try:
            await self._auth()
            await self._run_bw("sync")
            latency_ms = int((time.time() - start) * 1000)
            return {
                "status": "healthy",
                "provider": "bitwarden-cloud",
                "latency_ms": latency_ms,
                "vault_url": self.vault_url,
            }
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            logger.error(f"BitwardenProvider health check failed: {e}")
            return {
                "status": "unhealthy",
                "provider": "bitwarden-cloud",
                "latency_ms": latency_ms,
                "error": str(e),
            }

    @staticmethod
    def _type_from_item(item: Dict) -> str:
        if item.get("login"):
            return "login"
        elif item.get("card"):
            return "card"
        elif item.get("identity"):
            return "identity"
        return "note"


class VaultwardenProvider(SecretsProvider):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        vault_url: str,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.vault_url = vault_url.rstrip("/")
        self._bitwarden = BitwardenCloudProvider(
            client_id, client_secret, "", vault_url
        )

    async def get(self, key: str) -> Optional[str]:
        return await self._bitwarden.get(key)

    async def set(self, key: str, value: str, folder: Optional[str] = None) -> bool:
        return await self._bitwarden.set(key, value, folder)

    async def delete(self, key: str) -> bool:
        return await self._bitwarden.delete(key)

    async def list(self, folder: Optional[str] = None) -> List[SecretValue]:
        return await self._bitwarden.list(folder)

    async def health(self) -> Dict[str, Any]:
        health = await self._bitwarden.health()
        health["provider"] = "vaultwarden-selfhosted"
        return health


def get_provider() -> SecretsProvider:
    backend = os.getenv("SECRETS_BACKEND", "bitwarden").lower()

    if backend == "bitwarden":
        return BitwardenCloudProvider(
            client_id=os.getenv("BW_CLIENT_ID", ""),
            client_secret=os.getenv("BW_CLIENT_SECRET", ""),
            master_password=os.getenv("BW_MASTER_PASSWORD", ""),
            vault_url=os.getenv("BW_VAULT_URL", "https://vault.bitwarden.com"),
        )
    elif backend == "vaultwarden":
        return VaultwardenProvider(
            client_id=os.getenv("BW_CLIENT_ID", ""),
            client_secret=os.getenv("BW_CLIENT_SECRET", ""),
            vault_url=os.getenv("BW_VAULT_URL", "http://vaultwarden:80"),
        )
    else:
        raise ValueError(f"Unknown SECRETS_BACKEND: {backend}")
