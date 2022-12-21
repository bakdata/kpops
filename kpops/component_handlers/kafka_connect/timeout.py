import logging
import signal
from typing import Callable, NoReturn, TypeVar

log = logging.getLogger("Timeout")

T = TypeVar("T")


def timeout(func: Callable[..., T], *, secs: int = 0) -> T | None:
    """
    Sets a timeout for a given lambda function
    :param func: The callable function
    :param secs: The timeout in seconds
    """

    def handler(signum, frame) -> NoReturn:
        raise TimeoutError()

    # set the timeout handler
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(secs)
    try:
        return func()
    except TimeoutError:
        log.error(
            f"Kafka Connect operation {func.__name__} timed out after {secs} seconds. To increase the duration, set the `timeout` option in config.yaml."
        )
    finally:
        signal.alarm(0)
