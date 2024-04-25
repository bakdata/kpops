from unittest.mock import MagicMock

import pytest
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
    mock_pvc = MagicMock()
    mock_pvc.metadata.name = "test-pvc"

    mock_core_v1_api = mocker.patch(f"{MODULE}.client.CoreV1Api")
    mock_core_v1_api.return_value.list_namespaced_persistent_volume_claim.return_value.items = [
        mock_pvc
    ]
    pvcs = await pvc_handler.list_pvcs()

    assert pvcs == ["test-pvc"]


@pytest.mark.asyncio
async def test_delete_pvcs(pvc_handler: PVCHandler, mocker: MockerFixture):
    mocker.patch.object(
        pvc_handler, "list_pvcs", return_value=["test-pvc-1", "test-pvc-2"]
    )
    mock_core_v1_api = mocker.patch(f"{MODULE}.client.CoreV1Api")
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
