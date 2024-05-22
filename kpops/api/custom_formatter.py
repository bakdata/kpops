import logging

import typer


class CustomFormatter(logging.Formatter):
    def format(self, record):
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
