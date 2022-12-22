from kpops.component_handlers.streams_bootstrap.streams_bootstrap_application_type import (
    ApplicationType,
)


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
