import logging

import requests

log = logging.getLogger("RequestException")


class RequestsException(Exception):
    def __init__(self, response: requests.Response) -> None:
        self.error_code = response.status_code
        self.error_msg = "Something went wrong!"
        try:
            log.error(
                f"The request responded with the code {self.error_code}. Error body: {response.json()}"
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            self.error_msg = str(e)
            log.error(f"More information: {self.error_msg}")
        super().__init__()
