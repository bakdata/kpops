from typing import ClassVar

import httpx2
import pytest

from kpops.component_handlers.utils.exception import (
    HttpResponseError,
    ServiceConnectionError,
)

REQUEST = httpx2.Request("GET", "http://service.local")


class _ExampleHttpError(HttpResponseError):
    service: ClassVar[str] = "Example Service"


class _ExampleConnectionError(ServiceConnectionError):
    service: ClassVar[str] = "Example Service"


class TestHttpResponseError:
    def test_uses_message_field_from_json_body_as_reason(self) -> None:
        response = httpx2.Response(
            404,
            json={"error_code": 40403, "message": "Topic not found."},
            request=REQUEST,
        )
        error = _ExampleHttpError(response)
        assert str(error) == "Topic not found."
        assert error.error_code == 404
        assert error.response is response

    def test_falls_back_to_unknown_error_when_no_json_body(self) -> None:
        response = httpx2.Response(500, request=REQUEST)
        error = _ExampleHttpError(response)
        assert str(error) == "Unknown error"

    def test_falls_back_to_unknown_error_when_json_body_has_no_message(self) -> None:
        response = httpx2.Response(500, json={"foo": "bar"}, request=REQUEST)
        error = _ExampleHttpError(response)
        assert str(error) == "Unknown error"

    def test_message_never_embeds_service_name_or_status_code(self) -> None:
        response = httpx2.Response(
            503, json={"message": "Service unavailable"}, request=REQUEST
        )
        error = _ExampleHttpError(response)
        assert "Example Service" not in str(error)
        assert "503" not in str(error)

    def test_body_property_returns_parsed_json(self) -> None:
        response = httpx2.Response(
            500, json={"message": "oops", "detail": "x"}, request=REQUEST
        )
        error = _ExampleHttpError(response)
        assert error.body == {"message": "oops", "detail": "x"}

    def test_body_property_returns_none_for_non_json_response(self) -> None:
        response = httpx2.Response(500, text="not json", request=REQUEST)
        error = _ExampleHttpError(response)
        assert error.body is None


class TestServiceConnectionError:
    def test_message_is_just_the_cause_not_service_or_url(self) -> None:
        cause = ConnectionRefusedError("Connection refused")
        error = _ExampleConnectionError(url="http://service.local", cause=cause)
        assert str(error) == "Connection refused"
        assert "Example Service" not in str(error)
        assert error.url == "http://service.local"
        assert error.cause is cause


@pytest.mark.parametrize("cls", [HttpResponseError, ServiceConnectionError])
def test_requires_service_class_var_defined_by_subclass(cls: type) -> None:
    assert not hasattr(cls, "service")
