import logging
from collections.abc import AsyncIterator
from pathlib import Path
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


@pytest.fixture()
def pvc_handler(kubeconfig: Path) -> PVCHandler:
    return PVCHandler("test-app", "test-namespace")


def test_init(pvc_handler: PVCHandler, mocker: MockerFixture):
    assert isinstance(pvc_handler, PVCHandler)
    assert pvc_handler.namespace == "test-namespace"
    assert pvc_handler.app_name == "test-app"
    assert pvc_handler._client.config.context_name == "test"


@pytest.fixture()
def pvc1() -> PersistentVolumeClaim:
    return PersistentVolumeClaim(
        apiVersion="v1",
        kind="PersistentVolumeClaim",
        metadata=ObjectMeta(name="datadir-test-app-1"),
        spec=PersistentVolumeClaimSpec(),
        status=PersistentVolumeClaimStatus(),
    )


@pytest.fixture()
def pvc2() -> PersistentVolumeClaim:
    return PersistentVolumeClaim(
        apiVersion="v1",
        kind="PersistentVolumeClaim",
        metadata=ObjectMeta(name="datadir-test-app-2"),
        spec=PersistentVolumeClaimSpec(),
        status=PersistentVolumeClaimStatus(),
    )


@pytest.fixture()
def mock_list_pvcs(
    pvc_handler: PVCHandler,
    mocker: MockerFixture,
    pvc1: PersistentVolumeClaim,
    pvc2: PersistentVolumeClaim,
):
    async def async_generator_side_effect() -> AsyncIterator[PersistentVolumeClaim]:
        yield pvc1
        yield pvc2

    mocker.patch.object(
        pvc_handler,
        "list_pvcs",
        side_effect=async_generator_side_effect,
    )


@pytest.mark.usefixtures("mock_list_pvcs")
async def test_list_pvcs(
    pvc_handler: PVCHandler,
    mocker: MockerFixture,
    pvc1: PersistentVolumeClaim,
    pvc2: PersistentVolumeClaim,
):
    pvcs = await pvc_handler.list_pvcs()
    assert isinstance(pvcs, AsyncIterator)
    assert [pvc async for pvc in pvcs] == [pvc1, pvc2]


@pytest.mark.usefixtures("mock_list_pvcs")
async def test_delete_pvcs_dry_run(
    pvc_handler: PVCHandler,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(logging.DEBUG)
    mock_delete = mocker.patch.object(
        pvc_handler._client, "delete", return_value=AsyncMock()
    )
    await pvc_handler.delete_pvcs(True)
    mock_delete.assert_not_called()
    assert (
        "Deleting in namespace 'test-namespace' StatefulSet 'test-app' PVCs ['datadir-test-app-1', 'datadir-test-app-2']"
        in caplog.text
    )


async def test_delete_pvcs_dry_run_no_pvcs(
    pvc_handler: PVCHandler,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(logging.DEBUG)
    mock_list = mocker.patch.object(
        pvc_handler._client, "list", return_value=AsyncMock()
    )
    mock_delete = mocker.patch.object(
        pvc_handler._client, "delete", return_value=AsyncMock()
    )
    await pvc_handler.delete_pvcs(True)
    mock_list.assert_called_once()
    mock_delete.assert_not_called()
    assert (
        "No PVCs found for app 'test-app', in namespace 'test-namespace'" in caplog.text
    )


@pytest.mark.usefixtures("mock_list_pvcs")
async def test_delete_pvcs(
    pvc_handler: PVCHandler,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
):
    caplog.set_level(logging.DEBUG)
    mock_delete = mocker.patch.object(
        pvc_handler._client, "delete", return_value=AsyncMock()
    )
    await pvc_handler.delete_pvcs(False)
    mock_delete.assert_has_calls(
        [
            mocker.call.delete(PersistentVolumeClaim, "datadir-test-app-1"),
            mocker.call.delete(PersistentVolumeClaim, "datadir-test-app-2"),
        ]
    )
    assert (
        "Deleting in namespace 'test-namespace' StatefulSet 'test-app' PVCs ['datadir-test-app-1', 'datadir-test-app-2']"
        in caplog.text
    )
