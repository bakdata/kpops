import logging

from kubernetes_asyncio import client, config
from kubernetes_asyncio.client import ApiClient

log = logging.getLogger("PVC_handler")


class PVCHandler:
    def __init__(self, app_name: str, namespace: str):
        self.app_name = app_name
        self.namespace = namespace

    @classmethod
    async def create(cls, app_name: str, namespace: str):
        self = cls(app_name, namespace)
        await config.load_kube_config()
        return self

    @property
    async def pvc_names(self) -> list[str]:
        async with ApiClient() as api:
            core_v1_api = client.CoreV1Api(api)
            pvc_list = core_v1_api.list_namespaced_persistent_volume_claim(
                self.namespace, label_selector=f"app={self.app_name}"
            )

            pvc_names = [pvc.metadata.name for pvc in pvc_list.items]
            if not pvc_names:
                log.warning(
                    f"No PVCs found for app '{self.app_name}', in namespace '{self.namespace}'"
                )
            log.debug(
                f"In namespace '{self.namespace}' StatefulSet '{self.app_name}' has corresponding PVCs: '{pvc_names}'"
            )
            return pvc_names

    async def delete_pvcs(self) -> None:
        async with ApiClient() as api:
            core_v1_api = client.CoreV1Api(api)
            pvc_names = await self.pvc_names
            log.debug(
                f"Deleting in namespace '{self.namespace}' StatefulSet '{self.app_name}' PVCs '{pvc_names}'"
            )
            for pvc_name in pvc_names:
                core_v1_api.delete_namespaced_persistent_volume_claim(
                    pvc_name, self.namespace
                )
