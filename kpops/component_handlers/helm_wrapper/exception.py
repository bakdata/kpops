from typing import ClassVar

from kpops.core.exception import ServiceException


class HelmException(ServiceException):
    service: ClassVar[str] = "Helm"


class ReleaseNotFoundException(HelmException):
    pass


class ParseError(HelmException):
    pass


class HelmError(HelmException):
    def __init__(self, stderr: str) -> None:
        self.stderr: str = stderr
        super().__init__(stderr)
