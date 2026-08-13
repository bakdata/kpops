import asyncio
from typing import cast

import pytest
from pytest_mock import MockerFixture
from structlog.contextvars import merge_contextvars
from structlog.testing import capture_logs

from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.core.exception import KpopsException
from kpops.pipeline import _run_component
from kpops.utils.logging import bound_service_context


def fake_component(mocker: MockerFixture, name: str) -> PipelineComponent:
    component = mocker.MagicMock()
    component.name = name
    return cast("PipelineComponent", component)


async def test_reraised_exception_is_marked_logged_to_avoid_double_logging(
    mocker: MockerFixture,
) -> None:
    component = fake_component(mocker, "test-component")

    async def failing_operation() -> None:
        msg = "boom"
        raise KpopsException(msg)

    with pytest.raises(KpopsException) as exc_info:
        await _run_component("Deploy", component, failing_operation())

    assert exc_info.value.logged is True


async def test_does_not_swallow_non_kpops_exceptions(mocker: MockerFixture) -> None:
    component = fake_component(mocker, "test-component")

    async def failing_operation() -> None:
        msg = "not a kpops exception"
        raise ValueError(msg)

    with pytest.raises(ValueError, match="not a kpops exception"):
        await _run_component("Deploy", component, failing_operation())


async def test_parallel_component_failures_are_isolated(
    mocker: MockerFixture,
) -> None:
    """A failing component's bound context must not leak into a sibling's log line.

    Mirrors the asyncio.gather()-isolation finding: contextvars bound inside
    one component's task/coroutine must not appear on another's.
    """
    component_a = fake_component(mocker, "component-a")
    component_b = fake_component(mocker, "component-b")

    async def failing(name: str) -> None:
        with bound_service_context(url=f"http://{name}"):
            msg = f"{name} failed"
            raise KpopsException(msg)

    async def ok(name: str) -> None:
        return None

    with capture_logs(processors=[merge_contextvars]) as cap_logs:
        results = await asyncio.gather(
            _run_component("Deploy", component_a, failing("component-a")),
            _run_component("Deploy", component_b, ok("component-b")),
            return_exceptions=True,
        )

    assert isinstance(results[0], KpopsException)
    assert results[1] is None

    error_entries = [e for e in cap_logs if e["log_level"] == "error"]
    assert len(error_entries) == 1
    assert error_entries[0]["event"] == "component-a failed"
    assert error_entries[0].get("url") == "http://component-a"
