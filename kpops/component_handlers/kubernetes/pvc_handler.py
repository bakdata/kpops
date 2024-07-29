from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from lightkube.config.kubeconfig import KubeConfig
from lightkube.core.async_client import AsyncClient
from lightkube.resources.core_v1 import PersistentVolumeClaim

log = logging.getLogger("PVC_handler")


class PVCHandler:
    def __init__(self, app_name: str, namespace: str) -> None:
        self.app_name = app_name
        self.namespace = namespace
        config = KubeConfig.from_env()
        self.client = AsyncClient(config=config)

    async def list_pvcs(self) -> list[str]:
        async def read_pvcs() -> AsyncIterator[str]:
            async for pvc in self.client.list(
                PersistentVolumeClaim,
                namespace=self.namespace,
                labels={"app": self.app_name},
            ):
                if not pvc.metadata or not pvc.metadata.name:
                    continue
                yield pvc.metadata.name

        pvc_names = [pvc async for pvc in read_pvcs()]

        if not pvc_names:
            log.warning(
                f"No PVCs found for app '{self.app_name}', in namespace '{self.namespace}'"
            )
        log.debug(
            f"In namespace '{self.namespace}' StatefulSet '{self.app_name}' has corresponding PVCs: '{pvc_names}'"
        )
        return pvc_names

    async def delete_pvcs(self) -> None:
        pvc_names = await self.list_pvcs()

        log.debug(
            f"Deleting in namespace '{self.namespace}' StatefulSet '{self.app_name}' PVCs '{pvc_names}'"
        )
        for pvc in pvc_names:
            await self.client.delete(
                PersistentVolumeClaim, pvc, namespace=self.namespace
            )
