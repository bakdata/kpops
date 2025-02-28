import logging

import httpx

log = logging.getLogger("HttpxException")


class HttpxException(Exception):
    def __init__(self, response: httpx.Response) -> None:
        self.error_code: int = response.status_code
        self.error_msg: str = "Something went wrong!"
        try:
            log.exception(
                f"The request responded with the code {self.error_code}. Error body: {response.json()}",
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            self.error_msg = str(e)
            log.exception(f"More information: {self.error_msg}")
        super().__init__()
