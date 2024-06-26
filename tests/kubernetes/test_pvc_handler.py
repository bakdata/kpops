from unittest.mock import AsyncMock

import pytest
from kubernetes_asyncio.client import (
    V1ObjectMeta,
    V1PersistentVolumeClaim,
    V1PersistentVolumeClaimList,
    V1PersistentVolumeClaimSpec,
    V1PersistentVolumeClaimStatus,
)
from pytest_mock import MockerFixture

from kpops.component_handlers.kubernetes.pvc_handler import PVCHandler

MODULE = "kpops.component_handlers.kubernetes.pvc_handler"


@pytest.fixture
def pvc_handler():
    return PVCHandler("test-app", "test-namespace")


@pytest.mark.asyncio
async def test_create(pvc_handler: PVCHandler, mocker: MockerFixture):
    mock_load_kube_config = mocker.patch(f"{MODULE}.config.load_kube_config")
    pvc_handler = await PVCHandler.create("test-app", "test-namespace")
    mock_load_kube_config.assert_called_once()
    assert isinstance(pvc_handler, PVCHandler)
    assert pvc_handler.namespace == "test-namespace"
    assert pvc_handler.app_name == "test-app"


@pytest.mark.asyncio
async def test_pvc_names(pvc_handler: PVCHandler, mocker: MockerFixture):
    test_pvc1 = V1PersistentVolumeClaim(
        api_version="v1",
        kind="PersistentVolumeClaim",
        metadata=V1ObjectMeta(name="datadir-test-app-1"),
        spec=V1PersistentVolumeClaimSpec(),
        status=V1PersistentVolumeClaimStatus(),
    )
    test_pvc2 = V1PersistentVolumeClaim(
        api_version="v1",
        kind="PersistentVolumeClaim",
        metadata=V1ObjectMeta(name="datadir-test-app-2"),
        spec=V1PersistentVolumeClaimSpec(),
        status=V1PersistentVolumeClaimStatus(),
    )
    volume_claim_list = V1PersistentVolumeClaimList(items=[test_pvc1, test_pvc2])

    async_mock = AsyncMock()
    async_mock.list_namespaced_persistent_volume_claim.return_value = volume_claim_list

    mocker.patch(f"{MODULE}.client.CoreV1Api", return_value=async_mock)

    pvcs = await pvc_handler.list_pvcs()

    assert pvcs == ["datadir-test-app-1", "datadir-test-app-2"]


@pytest.mark.asyncio
async def test_delete_pvcs(pvc_handler: PVCHandler, mocker: MockerFixture):
    mocker.patch.object(
        pvc_handler, "list_pvcs", return_value=["test-pvc-1", "test-pvc-2"]
    )
    mock_core_v1_api = mocker.patch(
        f"{MODULE}.client.CoreV1Api", return_value=AsyncMock()
    )
    await pvc_handler.delete_pvcs()
    mock_core_v1_api.return_value.assert_has_calls(
        [
            mocker.call.delete_namespaced_persistent_volume_claim(
                "test-pvc-1", "test-namespace"
            ),
            mocker.call.delete_namespaced_persistent_volume_claim(
                "test-pvc-2", "test-namespace"
            ),
        ]
    )
