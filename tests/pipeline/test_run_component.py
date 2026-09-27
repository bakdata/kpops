import asyncio
from typing import Any, cast

import pytest
import structlog
from polyfactory.factories.pydantic_factory import ModelFactory
from pytest_mock import MockerFixture
from structlog.contextvars import merge_contextvars
from structlog.testing import capture_logs

from kpops.components.base_components.models.from_section import FromSection
from kpops.components.base_components.models.to_section import ToSection
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.core.exception import KpopsException
from kpops.pipeline import Pipeline, _run_component
from kpops.utils.logging import bound_service_context


class _ComponentFactory(ModelFactory[PipelineComponent]):
    to: ToSection = ToSection()
    from_: FromSection = FromSection()
    enrich: bool = False
    validate: bool = False


def independent_component(name: str) -> PipelineComponent:
    """Build a standalone component with no topic relationships to other components."""
    component = _ComponentFactory.build(False)
    component.name = name
    return component


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

    ok_entries = [e for e in cap_logs if e["event"] == "Deploy"]
    component_names = {e.get("component_name") for e in ok_entries}
    assert component_names == {"component-a", "component-b"}


async def test_component_name_is_bound_for_nested_log_calls(
    mocker: MockerFixture,
) -> None:
    component = fake_component(mocker, "data-producer")
    nested_log = structlog.get_logger("Kafka REST Proxy")

    async def operation() -> None:
        nested_log.info("creating topic")

    with capture_logs(processors=[merge_contextvars]) as cap_logs:
        await _run_component("Deploy", component, operation())

    nested_entries = [e for e in cap_logs if e["event"] == "creating topic"]
    assert nested_entries[0]["component_name"] == "data-producer"


async def test_component_name_is_unbound_after_run_component_completes(
    mocker: MockerFixture,
) -> None:
    component = fake_component(mocker, "data-producer")

    async def operation() -> None:
        return None

    with capture_logs(processors=[merge_contextvars]):
        await _run_component("Deploy", component, operation())
        assert structlog.contextvars.get_contextvars() == {}


async def test_pipeline_name_is_bound_during_run_action(
    mocker: MockerFixture,
) -> None:
    pipeline = Pipeline(name="word-count")
    component = fake_component(mocker, "data-producer")
    pipeline._component_index[component.id] = component

    observed: list[dict[str, object]] = []

    async def action(_: PipelineComponent) -> None:
        observed.append(structlog.contextvars.get_contextvars())

    with capture_logs():
        await pipeline._run_action("Deploy", action, parallel=False, reverse=False)

    assert observed[0] == {"pipeline": "word-count", "component_name": "data-producer"}


async def test_pipeline_name_is_bound_for_parallel_components() -> None:
    pipeline = Pipeline(name="word-count")
    pipeline.add(independent_component("component-a"))
    pipeline.add(independent_component("component-b"))

    observed: list[dict[str, object]] = []

    async def action(component: PipelineComponent) -> None:
        observed.append(structlog.contextvars.get_contextvars())

    with capture_logs():
        await pipeline._run_action("Deploy", action, parallel=True, reverse=False)

    assert {frozenset(o.items()) for o in observed} == {
        frozenset({"pipeline": "word-count", "component_name": "component-a"}.items()),
        frozenset({"pipeline": "word-count", "component_name": "component-b"}.items()),
    }


def test_manifest_action_binds_pipeline_and_component_name(
    mocker: MockerFixture,
) -> None:
    pipeline = Pipeline(name="word-count")
    component_a = fake_component(mocker, "component-a")
    component_b = fake_component(mocker, "component-b")
    pipeline.add(component_a)
    pipeline.add(component_b)

    observed: list[dict[str, Any]] = []

    def mock_manifest_deploy(comp: PipelineComponent) -> tuple[()]:
        observed.append(structlog.contextvars.get_contextvars())
        return ()

    mocker.patch.object(
        component_a,
        "manifest_deploy",
        side_effect=lambda: mock_manifest_deploy(component_a),
    )
    mocker.patch.object(
        component_b,
        "manifest_deploy",
        side_effect=lambda: mock_manifest_deploy(component_b),
    )

    list(pipeline.manifest_deploy())

    assert observed == [
        {"pipeline": "word-count", "component_name": "component-a"},
        {"pipeline": "word-count", "component_name": "component-b"},
    ]
    assert structlog.contextvars.get_contextvars() == {}
