import httpx
import structlog
from structlog.testing import capture_logs

from kpops.component_handlers.topic.exception import (
    KafkaRestProxyConnectionError,
    KafkaRestProxyError,
)
from kpops.core.exception import KpopsException
from kpops.utils.logging import log_kpops_exception


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
    request = httpx.Request("GET", "http://x")
    response = httpx.Response(500, json={"message": "oops"}, request=request)
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
