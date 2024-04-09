import json
import logging
import subprocess

log = logging.getLogger("PVC_handler")


# TODO: Use official Kubernetes client for Python to do this task


class PVCHandler:
    def __init__(self, app_name: str, namespace: str):
        self.app_name = app_name
        self.namespace = namespace

    @property
    def pvc_names(self) -> list[str]:
        pvc_data = subprocess.check_output(
            [
                "kubectl",
                "get",
                "-n",
                f"{self.namespace}",
                "pvc",
                "-l",
                f"app={self.app_name}",
                "-o",
                "json",
            ]
        )
        pvc_list = json.loads(pvc_data)

        pvc_names = [pvc["metadata"]["name"] for pvc in pvc_list["items"]]
        log.debug(
            f"In namespace '{self.namespace}' StatefulSet '{self.app_name}' has corresponding PVCs: '{pvc_names}'"
        )
        return pvc_names

    def delete_pvcs(self) -> None:
        pvc_names = self.pvc_names
        log.debug(
            f"Deleting in namespace '{self.namespace}' StatefulSet '{self.app_name}' PVCs '{pvc_names}'"
        )
        subprocess.run(
            ["kubectl", "delete", "-n", f"{self.namespace}", "pvc", *pvc_names],
            check=False,
        )
