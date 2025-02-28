import logging
from collections.abc import AsyncIterable
from typing import final

from lightkube.core.async_client import AsyncClient
from lightkube.resources.core_v1 import PersistentVolumeClaim

log = logging.getLogger("PVC_handler")


@final
class PVCHandler:
    def __init__(self, app_name: str, namespace: str) -> None:
        self.app_name = app_name
        self.namespace = namespace
        self._client = AsyncClient(namespace=namespace)

    async def list_pvcs(self) -> AsyncIterable[PersistentVolumeClaim]:
        return self._client.list(PersistentVolumeClaim, labels={"app": self.app_name})  # pyright: ignore[reportUnknownMemberType]

    async def delete_pvcs(self, dry_run: bool) -> None:
        pvc_names: list[str] = [
            pvc.metadata.name
            async for pvc in await self.list_pvcs()
            if pvc.metadata and pvc.metadata.name
        ]
        if not pvc_names:
            log.warning(
                f"No PVCs found for app '{self.app_name}', in namespace '{self.namespace}'"
            )
            return
        log.debug(
            f"Deleting in namespace '{self.namespace}' StatefulSet '{self.app_name}' PVCs {pvc_names}"
        )
        if dry_run:
            return
        for pvc_name in pvc_names:
            await self._client.delete(PersistentVolumeClaim, pvc_name)
