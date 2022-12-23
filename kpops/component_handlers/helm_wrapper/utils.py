import logging

from kpops.component_handlers.helm_wrapper.helm import RELEASE_NAME_MAX_LEN
from kpops.component_handlers.streams_bootstrap.streams_bootstrap_application_type import (
    ApplicationType,
)

log = logging.getLogger("HelmUtils")


def get_chart(
    repository_name: str,
    application_type: ApplicationType,
    local_chart_path: str | None = None,
) -> str:
    return (
        f"{repository_name}/{application_type.value}"
        if local_chart_path is None
        else str(local_chart_path)
    )


def trim_release_name(name: str, suffix: str = "") -> str:
    if len(name) + len(suffix) > RELEASE_NAME_MAX_LEN:
        new_name = name[: (RELEASE_NAME_MAX_LEN - len(suffix))] + suffix
        log.critical(
            f"The Helm release name {name} is invalid. We shorten it to {RELEASE_NAME_MAX_LEN} characters: \n {name + suffix} --> {new_name}"
        )
        name = new_name
    return name
