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
        self._client = AsyncClient(config=config)

    async def list_pvcs(self) -> AsyncIterator[str]:
        async for pvc in self._client.list(
            PersistentVolumeClaim,
            namespace=self.namespace,
            labels={"app": self.app_name},
        ):
            if not pvc.metadata or not pvc.metadata.name:
                continue
            yield pvc.metadata.name

    async def delete_pvcs(self, dry_run: bool) -> None:
        pvc_names = [pvc_name async for pvc_name in self.list_pvcs()]
        if not pvc_names:
            log.warning(
                f"No PVCs found for app '{self.app_name}', in namespace '{self.namespace}'"
            )
            return
        log.debug(
            f"Deleting in namespace '{self.namespace}' StatefulSet '{self.app_name}' PVCs '{pvc_names}'"
        )
        if dry_run:
            return
        for pvc in pvc_names:
            await self._client.delete(
                PersistentVolumeClaim, pvc, namespace=self.namespace
            )
