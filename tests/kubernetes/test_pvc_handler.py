from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers.kubernetes.pvc_handler import PVCHandler

MODULE = "kpops.component_handlers.kubernetes.pvc_handler"


@pytest.fixture
def pvc_handler():
    return PVCHandler("test-app", "test-namespace")


async def pvc_names_return_value() -> list[str]:
    return ["test-pvc"]


@pytest.mark.asyncio
async def test_create(pvc_handler: PVCHandler):
    with patch(f"{MODULE}.config.load_kube_config") as mock_load_kube_config:
        pvc_handler = await PVCHandler.create("test-app", "test-namespace")
        mock_load_kube_config.assert_called_once()
        assert isinstance(pvc_handler, PVCHandler)
        assert pvc_handler.namespace == "test-namespace"
        assert pvc_handler.app_name == "test-app"


@pytest.mark.asyncio
async def test_pvc_names(pvc_handler: PVCHandler):
    mock_pvc = MagicMock()
    mock_pvc.metadata.name = "test-pvc"

    with patch(f"{MODULE}.client.CoreV1Api") as mock_core_v1_api:
        mock_core_v1_api.return_value.list_namespaced_persistent_volume_claim.return_value.items = [
            mock_pvc
        ]
        pvc_names = await pvc_handler.get_pvc_names()

    assert pvc_names == ["test-pvc"]


@pytest.mark.asyncio
async def test_delete_pvcs(pvc_handler: PVCHandler, mocker: MockerFixture):
    mock = mocker.patch(
        f"{MODULE}.PVCHandler.get_pvc_names",
        new_callable=AsyncMock,
        return_value=["test-pvc"],
    )
    print(mock)
    with patch(f"{MODULE}.client.CoreV1Api") as mock_core_v1_api:
        await pvc_handler.delete_pvcs()
        mock_core_v1_api.return_value.delete_namespaced_persistent_volume_claim.assert_called_once_with(
            "test-pvc", "test-namespace"
        )
