import asyncio
import logging
from asyncio import TimeoutError
from collections.abc import Coroutine
from typing import Any, TypeVar

log = logging.getLogger("Timeout")

T = TypeVar("T")


async def timeout(func: Coroutine[Any, Any, T], *, secs: int = 0) -> T | None:
    """Set a timeout for a given lambda function.

    :param func: The callable function
    :param secs: The timeout in seconds.
    """
    try:
        task = asyncio.create_task(func)
        if secs == 0:
            return await task
        else:
            return await asyncio.wait_for(task, timeout=secs)
    except TimeoutError:
        log.exception(
            f"Kafka Connect operation {func.__name__} timed out after {secs} seconds. To increase the duration, set the `timeout` option in config.yaml."
        )
