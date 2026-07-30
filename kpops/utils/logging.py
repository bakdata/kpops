from __future__ import annotations

import contextlib
import logging
from collections.abc import Generator
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from structlog.typing import EventDict, WrappedLogger

    from kpops.components.base_components.pipeline_component import PipelineComponent
    from kpops.exception import KpopsException

logging.getLogger("httpx").setLevel(logging.WARNING)


def _drop_root_logger_name(
    _: WrappedLogger, __: str, event_dict: EventDict
) -> EventDict:
    if event_dict.get("logger") in ("root", ""):
        event_dict.pop("logger", None)
    return event_dict


structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

_formatter = structlog.stdlib.ProcessorFormatter(
    # Applies to stdlib-only loggers (e.g. httpx) not migrated to structlog.
    foreign_pre_chain=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
    ],
    processors=[
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
        _drop_root_logger_name,
        structlog.dev.ConsoleRenderer(),
    ],
)
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)
logging.getLogger().addHandler(_stream_handler)

log = structlog.get_logger("")
LOG_DIVIDER = "#" * 100


def log_action(action: str, pipeline_component: PipelineComponent) -> None:
    log.info("\n")
    log.info(LOG_DIVIDER)
    log.info(f"{action} {pipeline_component.name}")
    log.info(LOG_DIVIDER)
    log.info("\n")


def log_kpops_exception(e: KpopsException) -> None:
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        log.exception(str(e))
    else:
        log.error(str(e))
    e.logged = True


@contextlib.contextmanager
def bound_service_context(**kw: str) -> Generator[None]:
    """Bind structlog context for the duration of an operation.

    On success the binding is cleared; on failure it's left in place so
    it's still bound when the exception is logged further up the stack.
    Not using structlog's `bound_contextvars`, which uses try/finally and
    would clear the binding even when an exception propagates.
    """
    tokens = structlog.contextvars.bind_contextvars(**kw)
    yield
    structlog.contextvars.reset_contextvars(**tokens)
