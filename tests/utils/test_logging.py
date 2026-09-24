import re
from typing import ClassVar

import httpx2
import pytest
import structlog
from structlog.testing import capture_logs

from kpops.component_handlers.topic.exception import (
    KafkaRestProxyConnectionError,
    KafkaRestProxyError,
)
from kpops.core.exception import KpopsException, ServiceException
from kpops.utils.logging import (
    _build_console_renderer,
    _component_color,
    _render_console_line,
    bound_service_context,
    log_kpops_exception,
)

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


def test_logs_and_marks_exception_as_logged() -> None:
    msg = "boom"
    error = KpopsException(msg)

    with capture_logs() as cap_logs:
        log_kpops_exception(error)

    assert error.logged is True
    assert {
        "event": "boom",
        "log_level": "error",
    }.items() <= next(e for e in cap_logs if e["log_level"] == "error").items()


def test_falls_back_to_generic_logger_for_exceptions_without_service() -> None:
    error = KpopsException("boom")

    with capture_logs(processors=[structlog.stdlib.add_logger_name]) as cap_logs:
        log_kpops_exception(error)

    error_entries = [e for e in cap_logs if e["log_level"] == "error"]
    assert len(error_entries) == 1
    assert error_entries[0].get("logger") in ("root", "")


def test_uses_named_logger_matching_the_failing_service() -> None:
    error = KafkaRestProxyConnectionError(url="http://x", cause=ValueError("boom"))

    with capture_logs(processors=[structlog.stdlib.add_logger_name]) as cap_logs:
        log_kpops_exception(error)

    error_entries = [e for e in cap_logs if e["log_level"] == "error"]
    assert len(error_entries) == 1
    assert error_entries[0]["logger"] == "Kafka REST Proxy"


def test_logs_response_body_details_for_http_response_errors() -> None:
    request = httpx2.Request("GET", "http://x")
    response = httpx2.Response(500, json={"message": "oops"}, request=request)
    error = KafkaRestProxyError(response)

    with capture_logs() as cap_logs:
        log_kpops_exception(error)

    debug_entries = [e for e in cap_logs if e["log_level"] == "debug"]
    assert any(
        e["event"] == "Response details"
        and e.get("status_code") == 500
        and e.get("body") == {"message": "oops"}
        for e in debug_entries
    )


def test_recovered_exception_does_not_leak_context_into_later_operations() -> None:
    class DummyNotFoundException(KpopsException):
        pass

    def get_topic() -> None:
        with bound_service_context(topic_name="topic-a", url="http://kafka-rest"):
            raise DummyNotFoundException

    with pytest.raises(DummyNotFoundException):
        get_topic()

    with bound_service_context(connector_name="my-connector"):
        assert structlog.contextvars.get_contextvars() == {
            "connector_name": "my-connector"
        }


def test_exception_context_is_logged_when_it_propagates() -> None:
    class DummyServiceException(ServiceException):
        service: ClassVar[str] = "Dummy"

    def get_topic() -> None:
        msg = "boom"
        with bound_service_context(url="http://kafka-rest", topic_name="topic-a"):
            raise DummyServiceException(msg)

    with pytest.raises(DummyServiceException) as exc_info:
        get_topic()

    assert structlog.contextvars.get_contextvars() == {}

    with capture_logs() as cap_logs:
        log_kpops_exception(exc_info.value)

    error_entries = [e for e in cap_logs if e["log_level"] == "error"]
    assert len(error_entries) == 1
    assert error_entries[0].get("url") == "http://kafka-rest"
    assert error_entries[0].get("topic_name") == "topic-a"


def test_component_color_is_deterministic() -> None:
    assert _component_color("data-producer") == _component_color("data-producer")


def test_component_color_varies_across_component_names() -> None:
    names = [f"component-{i}" for i in range(6)]
    colors = {_component_color(name) for name in names}
    assert len(colors) > 1


def test_console_renderer_prefixes_pipeline_and_component_brackets() -> None:
    renderer = _build_console_renderer()
    event_dict = {
        "event": "creating topic",
        "level": "info",
        "pipeline": "word-count",
        "component_name": "data-producer",
        "logger": "Kafka REST Proxy",
    }

    output = strip_ansi(renderer(None, "", dict(event_dict)))

    assert "[word-count]" in output
    assert "[data-producer]" in output
    assert "[Kafka REST Proxy]" in output
    assert (
        output.index("[word-count]")
        < output.index("[data-producer]")
        < output.index("[Kafka REST Proxy]")
        < output.index("creating topic")
    )
    # pipeline/component are rendered as brackets, not leaked as key=value pairs
    assert "pipeline=" not in output
    assert "component_name=" not in output


def test_console_renderer_omits_pipeline_and_component_brackets_when_absent() -> None:
    renderer = _build_console_renderer()
    event_dict = {"event": "hello", "level": "info"}

    output = strip_ansi(renderer(None, "", event_dict))

    assert output.strip() == "[info     ] hello"


def test_render_console_line_appends_diff_after_summary_line() -> None:
    event_dict = {
        "event": "Config changes for topic",
        "level": "info",
        "topic_name": "topic-X",
        "diff": "+ cleanup.policy: compact",
    }

    output = strip_ansi(_render_console_line(None, "", event_dict))
    summary, _, diff = output.partition("\n")

    assert "Config changes for topic" in summary
    assert "topic_name=topic-X" in summary
    assert diff == "+ cleanup.policy: compact"


def test_render_console_line_without_diff_is_unaffected() -> None:
    event_dict = {"event": "hello", "level": "info"}

    output = strip_ansi(_render_console_line(None, "", event_dict))

    assert "\n" not in output
    assert output.strip() == "[info     ] hello"


def test_render_console_line_does_not_leak_diff_into_key_value_tail() -> None:
    event_dict = {"event": "hello", "level": "info", "diff": "some diff content"}

    output = strip_ansi(_render_console_line(None, "", event_dict))

    assert "diff=" not in output
