from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import typer
from typing_extensions import override

if TYPE_CHECKING:
    from kpops.components.base_components.pipeline_component import PipelineComponent


class CustomFormatter(logging.Formatter):
    @override
    def format(self, record: logging.LogRecord) -> str:
        message_format = "%(name)s - %(message)s"

        if record.name == "root":
            message_format = "%(message)s"

        formats = {
            logging.DEBUG: message_format,
            logging.INFO: message_format,
            logging.WARNING: typer.style(message_format, fg=typer.colors.YELLOW),
            logging.ERROR: typer.style(message_format, fg=typer.colors.RED),
            logging.CRITICAL: typer.style(
                message_format, fg=typer.colors.RED, bold=True
            ),
        }

        log_fmt = formats.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


logger = logging.getLogger()
logging.getLogger("httpx").setLevel(logging.WARNING)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(CustomFormatter())
logger.addHandler(stream_handler)

log = logging.getLogger("")
LOG_DIVIDER = "#" * 100


def log_action(action: str, pipeline_component: PipelineComponent):
    log.info("\n")
    log.info(LOG_DIVIDER)
    log.info(f"{action} {pipeline_component.name}")
    log.info(LOG_DIVIDER)
    log.info("\n")
