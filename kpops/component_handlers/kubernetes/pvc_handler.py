from collections.abc import AsyncIterable
from typing import final

import structlog
from lightkube.core.async_client import AsyncClient
from lightkube.resources.core_v1 import PersistentVolumeClaim

log = structlog.get_logger("PVCHandler")


@final
class PVCHandler:
    def __init__(self, app_name: str, namespace: str) -> None:
        self.app_name = app_name
        self.namespace = namespace
        self._client = AsyncClient(namespace=namespace)

    async def list_pvcs(self) -> AsyncIterable[PersistentVolumeClaim]:
        return self._client.list(
            PersistentVolumeClaim, labels={"app.kubernetes.io/name": self.app_name}
        )

    async def delete_pvcs(self, dry_run: bool) -> None:
        pvc_names: list[str] = [
            pvc.metadata.name
            async for pvc in await self.list_pvcs()
            if pvc.metadata and pvc.metadata.name
        ]
        if not pvc_names:
            log.warning(
                "No PVCs found.",
                app_name=self.app_name,
                namespace=self.namespace,
            )
            return
        log.debug(
            "Deleting PVCs.",
            app_name=self.app_name,
            namespace=self.namespace,
            pvc_names=pvc_names,
        )
        if dry_run:
            return
        for pvc_name in pvc_names:
            await self._client.delete(PersistentVolumeClaim, pvc_name)
