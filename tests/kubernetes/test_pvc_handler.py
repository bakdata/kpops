from collections.abc import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from lightkube.models.core_v1 import (
    PersistentVolumeClaimSpec,
    PersistentVolumeClaimStatus,
)
from lightkube.models.meta_v1 import ObjectMeta
from lightkube.resources.core_v1 import PersistentVolumeClaim
from pytest_mock import MockerFixture

from kpops.component_handlers.kubernetes.pvc_handler import PVCHandler

MODULE = "kpops.component_handlers.kubernetes.pvc_handler"


@pytest.fixture
def pvc_handler() -> PVCHandler:
    return PVCHandler("test-app", "test-namespace")


def test_init(pvc_handler: PVCHandler, mocker: MockerFixture):
    assert isinstance(pvc_handler, PVCHandler)
    assert pvc_handler.namespace == "test-namespace"
    assert pvc_handler.app_name == "test-app"


@pytest.mark.asyncio
async def test_list_pvcs(pvc_handler: PVCHandler, mocker: MockerFixture):
    mock_list_pvcs = mocker.patch.object(pvc_handler._client, "list")
    await pvc_handler.list_pvcs()
    mock_list_pvcs.assert_called_with(PersistentVolumeClaim, labels={"app": "test-app"})


@pytest.mark.asyncio
async def test_pvc_names(pvc_handler: PVCHandler, mocker: MockerFixture):
    test_pvc1 = PersistentVolumeClaim(
        apiVersion="v1",
        kind="PersistentVolumeClaim",
        metadata=ObjectMeta(name="datadir-test-app-1"),
        spec=PersistentVolumeClaimSpec(),
        status=PersistentVolumeClaimStatus(),
    )
    test_pvc2 = PersistentVolumeClaim(
        apiVersion="v1",
        kind="PersistentVolumeClaim",
        metadata=ObjectMeta(name="datadir-test-app-2"),
        spec=PersistentVolumeClaimSpec(),
        status=PersistentVolumeClaimStatus(),
    )

    async def async_generator_side_effect() -> AsyncIterator[PersistentVolumeClaim]:
        yield test_pvc1
        yield test_pvc2

    mocker.patch.object(
        pvc_handler,
        "list_pvcs",
        side_effect=async_generator_side_effect,
    )

    pvcs = await pvc_handler.list_pvcs()
    assert isinstance(pvcs, AsyncIterator)
    assert [pvc async for pvc in pvcs] == [test_pvc1, test_pvc2]


@pytest.mark.asyncio
async def test_delete_pvcs(pvc_handler: PVCHandler, mocker: MockerFixture):
    test_pvc1 = PersistentVolumeClaim(
        apiVersion="v1",
        kind="PersistentVolumeClaim",
        metadata=ObjectMeta(name="datadir-test-app-1"),
        spec=PersistentVolumeClaimSpec(),
        status=PersistentVolumeClaimStatus(),
    )
    test_pvc2 = PersistentVolumeClaim(
        apiVersion="v1",
        kind="PersistentVolumeClaim",
        metadata=ObjectMeta(name="datadir-test-app-2"),
        spec=PersistentVolumeClaimSpec(),
        status=PersistentVolumeClaimStatus(),
    )

    async def async_generator_side_effect() -> AsyncIterator[PersistentVolumeClaim]:
        yield test_pvc1
        yield test_pvc2

    mocker.patch.object(
        pvc_handler,
        "list_pvcs",
        side_effect=async_generator_side_effect,
    )

    pvcs = await pvc_handler.list_pvcs()
    assert isinstance(pvcs, AsyncIterator)
    assert [pvc async for pvc in pvcs] == [test_pvc1, test_pvc2]

    mock_client = mocker.patch.object(
        pvc_handler._client, "delete", return_value=AsyncMock()
    )
    await pvc_handler.delete_pvcs(False)
    mock_client.assert_has_calls(
        [
            mocker.call.delete(PersistentVolumeClaim, "datadir-test-app-1"),
            mocker.call.delete(PersistentVolumeClaim, "datadir-test-app-2"),
        ]
    )
