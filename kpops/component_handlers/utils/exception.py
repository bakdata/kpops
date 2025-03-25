import json
import logging

import httpx

log = logging.getLogger("HttpxException")


class HttpxException(Exception):
    def __init__(self, response: httpx.Response) -> None:
        self.error_code: int = response.status_code
        self.error_msg: str = "Something went wrong!"
        log_lines = [f"The request responded with the code {self.error_code}."]
        if response.headers.get("Content-Type") == "application/json":
            log_lines.append("Error body:")
            log_lines.append(json.dumps(response.json(), indent=2))
        try:
            response.raise_for_status()
        except httpx.HTTPError as e:
            log_lines.append(str(e))
        log.exception(" ".join(log_lines))
        super().__init__()
