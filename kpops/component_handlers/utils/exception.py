from __future__ import annotations

from typing import Any

import httpx

from kpops.exception import ServiceException


class ServiceConnectionError(ServiceException):
    """Connection to an external service failed."""

    def __init__(self, url: str, cause: Exception) -> None:
        self.url: str = url
        self.cause: Exception = cause
        super().__init__(str(cause))


class HttpResponseError(ServiceException):
    """An external service responded with a non-success HTTP status."""

    def __init__(self, response: httpx.Response) -> None:
        self.error_code: int = response.status_code
        self.response: httpx.Response = response
        reason = self._extract_reason(response)
        super().__init__(reason if reason else "Unknown error")

    @property
    def body(self) -> Any | None:
        try:
            return self.response.json()
        except ValueError:
            return None

    @staticmethod
    def _extract_reason(response: httpx.Response) -> str | None:
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("application/json"):
            return None
        try:
            body = response.json()
        except ValueError:
            return None
        if isinstance(body, dict) and isinstance(body.get("message"), str):
            return body["message"]
        return None
