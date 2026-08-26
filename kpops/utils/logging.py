from __future__ import annotations

import contextlib
import logging
import zlib
from collections.abc import Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

from kpops.core.exception import KpopsException, ServiceException

if TYPE_CHECKING:
    from structlog.typing import EventDict, WrappedLogger

logging.getLogger("httpx2").setLevel(logging.WARNING)


def _drop_root_logger_name(
    _: WrappedLogger, __: str, event_dict: EventDict
) -> EventDict:
    if event_dict.get("logger") in ("root", ""):
        event_dict.pop("logger", None)
    return event_dict


# 256-color xterm codes for component log prefixes; red is reserved for the error level.
_COMPONENT_COLORS = (
    "\033[38;5;39m",
    "\033[38;5;208m",
    "\033[38;5;135m",
    "\033[38;5;76m",
    "\033[38;5;220m",
    "\033[38;5;213m",
    "\033[38;5;80m",
    "\033[38;5;214m",
    "\033[38;5;105m",
    "\033[38;5;156m",
    "\033[38;5;111m",
    "\033[38;5;45m",
    "\033[38;5;178m",
    "\033[38;5;120m",
)


def _component_color(name: str) -> str:
    """Map a component name to a stable color from the palette.

    Uses crc32 instead of hash(), which is randomized per process.
    """
    return _COMPONENT_COLORS[zlib.crc32(name.encode()) % len(_COMPONENT_COLORS)]


@dataclass
class _ComponentNameColumnFormatter:
    """Bracket formatter assigning each component name a stable color."""

    bright_style: str
    reset_style: str
    colors: bool

    def __call__(self, key: str, value: object) -> str:
        name = str(value)
        if not self.colors:
            return f"[{name}]"
        return f"[{self.bright_style}{_component_color(name)}{name}{self.reset_style}]"


def _build_console_renderer() -> structlog.dev.ConsoleRenderer:
    """Build a ConsoleRenderer with the logger name before the event message.

    The default column order renders `[level] event  [logger] key=value...`;
    we want `[level] [pipeline] [component] [logger] event  key=value...` instead.
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
    pipeline_name_formatter = structlog.dev.KeyValueColumnFormatter(
        key_style=None,
        value_style=styles.bright,
        reset_style=styles.reset,
        value_repr=str,
        prefix="[",
        postfix="]",
    )
    component_name_formatter = _ComponentNameColumnFormatter(
        bright_style=styles.bright,
        reset_style=styles.reset,
        colors=colors,
    )
    return structlog.dev.ConsoleRenderer(
        columns=[
            structlog.dev.Column(
                "level",
                structlog.dev.LogLevelColumnFormatter(
                    level_styles, reset_style=styles.reset
                ),
            ),
            structlog.dev.Column("pipeline", pipeline_name_formatter),
            structlog.dev.Column("component_name", component_name_formatter),
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


_console_renderer = _build_console_renderer()


def _render_console_line(
    logger: WrappedLogger, name: str, event_dict: EventDict
) -> str:
    diff: str | None = event_dict.pop("diff", None)
    line = _console_renderer(logger, name, event_dict)
    return f"{line}\n{diff}" if diff else line


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
        _render_console_line,
    ],
)
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)
logging.getLogger().addHandler(_stream_handler)

log = structlog.get_logger("")


def log_action(action: str) -> None:
    log.info(action)


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

    If a `KpopsException` propagates, the bound kwargs are attached to it so
    they're still available when logged further up the stack, since the
    contextvars binding itself is reset.
    """
    try:
        with structlog.contextvars.bound_contextvars(**kwargs):
            yield
    except KpopsException as e:
        if not e.context:
            e.context = kwargs
        raise
