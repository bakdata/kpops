from __future__ import annotations

import contextlib
import logging
from collections.abc import Generator
from typing import TYPE_CHECKING

import structlog

from kpops.core.exception import KpopsException, ServiceException

if TYPE_CHECKING:
    from structlog.typing import EventDict, WrappedLogger

    from kpops.components.base_components.pipeline_component import PipelineComponent

logging.getLogger("httpx2").setLevel(logging.WARNING)


def _drop_root_logger_name(
    _: WrappedLogger, __: str, event_dict: EventDict
) -> EventDict:
    if event_dict.get("logger") in ("root", ""):
        event_dict.pop("logger", None)
    return event_dict


def _build_console_renderer() -> structlog.dev.ConsoleRenderer:
    """Build a ConsoleRenderer with the logger name before the event message.

    The default column order renders `[level] event  [logger] key=value...`;
    we want `[level] [logger] event  key=value...` instead.
    """
    colors = structlog.dev.ConsoleRenderer().colors
    styles = structlog.dev.ConsoleRenderer.get_default_column_styles(colors)
    level_styles = structlog.dev.ConsoleRenderer.get_default_level_styles(colors)

    logger_name_formatter = structlog.dev.KeyValueColumnFormatter(
        key_style=None,
        value_style=styles.bright + styles.logger_name,
        reset_style=styles.reset,
        value_repr=str,
        prefix="[",
        postfix="]",
    )
    return structlog.dev.ConsoleRenderer(
        columns=[
            structlog.dev.Column(
                "level",
                structlog.dev.LogLevelColumnFormatter(
                    level_styles, reset_style=styles.reset
                ),
            ),
            structlog.dev.Column("logger", logger_name_formatter),
            structlog.dev.Column("logger_name", logger_name_formatter),
            structlog.dev.Column(
                "event",
                structlog.dev.KeyValueColumnFormatter(
                    key_style=None,
                    value_style=styles.bright,
                    reset_style=styles.reset,
                    value_repr=str,
                ),
            ),
            structlog.dev.Column(
                "",
                structlog.dev.KeyValueColumnFormatter(
                    key_style=styles.kv_key,
                    value_style=styles.kv_value,
                    reset_style=styles.reset,
                    value_repr=str,
                ),
            ),
        ]
    )


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
        _build_console_renderer(),
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
    log.info(action, component_name=pipeline_component.name)
    log.info(LOG_DIVIDER)
    log.info("\n")


def log_kpops_exception(e: KpopsException) -> None:
    logger = structlog.get_logger(e.service) if isinstance(e, ServiceException) else log
    if e.context:
        logger = logger.bind(**e.context)
    e.log_extra(logger)
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        logger.exception(str(e))
    else:
        logger.error(str(e))
    e.logged = True


@contextlib.contextmanager
def bound_service_context(**kwargs: str) -> Generator[None]:
    """Bind structlog context for the duration of an operation.

    Always resets on exit. If a `KpopsException` propagates, the bound kwargs
    are attached to it so they're still available when logged further up the
    stack, since the contextvars binding itself won't survive there.
    """
    tokens = structlog.contextvars.bind_contextvars(**kwargs)
    try:
        yield
    except KpopsException as e:
        if not e.context:
            e.context = kwargs
        raise
    finally:
        structlog.contextvars.reset_contextvars(**tokens)
