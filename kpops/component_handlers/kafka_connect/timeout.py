import asyncio
import builtins
import logging
from collections.abc import Coroutine
from typing import Any, TypeVar

log = logging.getLogger("Timeout")

T = TypeVar("T")


async def timeout(coro: Coroutine[Any, Any, T], *, secs: int = 0) -> T | None:
    """Set a timeout for a given lambda function.

    :param coro: The callable function
    :param secs: The timeout in seconds.
    """
    try:
        task = asyncio.create_task(coro)
        if secs == 0:
            return await task
        else:
            return await asyncio.wait_for(task, timeout=secs)
    except builtins.TimeoutError:
        log.exception(
            f"Kafka Connect operation {coro.__name__} timed out after {secs} seconds. To increase the duration, set the `timeout` option in config.yaml."
        )
