from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import dtyper
import typer

from kpops import __version__
from kpops.cli.custom_formatter import CustomFormatter
from kpops.cli.pipeline_config import ENV_PREFIX, PipelineConfig
from kpops.cli.registry import Registry
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
    KafkaConnectHandler,
)
from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.topic.handler import TopicHandler
from kpops.component_handlers.topic.proxy_wrapper import ProxyWrapper
from kpops.pipeline_generator.pipeline import Pipeline
from kpops.utils.gen_schema import SchemaScope, gen_config_schema, gen_pipeline_schema

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kpops.components.base_components import PipelineComponent

LOG_DIVIDER = "#" * 100

app = dtyper.Typer(pretty_exceptions_enable=False)

BASE_DIR_PATH_OPTION: Path = typer.Option(
    default=Path(),
    exists=True,
    dir_okay=True,
    file_okay=False,
    envvar=f"{ENV_PREFIX}PIPELINE_BASE_DIR",
    help="Base directory to the pipelines (default is current working directory)",
)

DEFAULT_PATH_OPTION: Optional[Path] = typer.Option(
    default=None,
    exists=True,
    dir_okay=True,
    file_okay=False,
    envvar=f"{ENV_PREFIX}DEFAULT_PATH",
    help="Path to defaults folder",
)

CONFIG_PATH_OPTION: Path = typer.Option(
    default=Path("config.yaml"),
    exists=False,
    dir_okay=False,
    file_okay=True,
    readable=True,
    envvar=f"{ENV_PREFIX}CONFIG_PATH",
    help="Path to the config.yaml file",
)

PIPELINE_PATH_ARG: Path = typer.Argument(
    default=...,
    exists=True,
    file_okay=True,
    dir_okay=False,
    readable=True,
    envvar=f"{ENV_PREFIX}PIPELINE_PATH",
    help="Path to YAML with pipeline definition",
)

PIPELINE_STEPS: str | None = typer.Option(
    default=None,
    envvar=f"{ENV_PREFIX}PIPELINE_STEPS",
    help="Comma separated list of steps to apply the command on",
)

DRY_RUN: bool = typer.Option(
    True,
    "--dry-run/--execute",
    help="Whether to dry run the command or execute it",
)


class FilterType(str, Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"


FILTER_TYPE: FilterType = typer.Option(
    default=FilterType.INCLUDE.value,
    case_sensitive=False,
    help="Whether the --steps option should include/exclude the steps",
)

VERBOSE_OPTION = typer.Option(False, help="Enable verbose printing")

COMPONENTS_MODULES: str | None = typer.Argument(
    default=None,
    help="Custom Python module containing your project-specific components",
)

logger = logging.getLogger()
logging.getLogger("httpx").setLevel(logging.WARNING)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(CustomFormatter())
logger.addHandler(stream_handler)

log = logging.getLogger("")


def setup_pipeline(
    pipeline_base_dir: Path,
    pipeline_path: Path,
    components_module: str | None,
    pipeline_config: PipelineConfig,
) -> Pipeline:
    registry = Registry()
    if components_module:
        registry.find_components(components_module)
    registry.find_components("kpops.components")

    handlers = setup_handlers(components_module, pipeline_config)
    return Pipeline.load_from_yaml(
        pipeline_base_dir, pipeline_path, registry, pipeline_config, handlers
    )


def setup_handlers(
    components_module: str | None, config: PipelineConfig
) -> ComponentHandlers:
    schema_handler = SchemaHandler.load_schema_handler(components_module, config)
    connector_handler = KafkaConnectHandler.from_pipeline_config(config)
    proxy_wrapper = ProxyWrapper(config)
    topic_handler = TopicHandler(proxy_wrapper)

    return ComponentHandlers(schema_handler, connector_handler, topic_handler)


def setup_logging_level(verbose: bool):
    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)


def parse_steps(steps: str) -> set[str]:
    return set(steps.split(","))


def get_step_names(steps_to_apply: list[PipelineComponent]) -> list[str]:
    return [step.name for step in steps_to_apply]


def filter_steps_to_apply(
    pipeline: Pipeline, steps: set[str], filter_type: FilterType
) -> list[PipelineComponent]:
    def is_in_steps(component: PipelineComponent) -> bool:
        return component.name in steps

    log.debug(
        f"KPOPS_PIPELINE_STEPS is defined with values: {steps} and filter type of {filter_type.value}"
    )
    filtered_steps = [
        component
        for component in pipeline
        if (
            is_in_steps(component)
            if filter_type is FilterType.INCLUDE
            else not is_in_steps(component)
        )
    ]
    log.info(f"The following steps are included:\n{get_step_names(filtered_steps)}")
    return filtered_steps


def get_steps_to_apply(
    pipeline: Pipeline, steps: str | None, filter_type: FilterType
) -> list[PipelineComponent]:
    if steps:
        return filter_steps_to_apply(pipeline, parse_steps(steps), filter_type)
    return list(pipeline)


def reverse_pipeline_steps(
    pipeline: Pipeline, steps: str | None, filter_type: FilterType
) -> Iterator[PipelineComponent]:
    return reversed(get_steps_to_apply(pipeline, steps, filter_type))


def log_action(action: str, pipeline_component: PipelineComponent):
    log.info("\n")
    log.info(LOG_DIVIDER)
    log.info(f"{action} {pipeline_component.name}")
    log.info(LOG_DIVIDER)
    log.info("\n")


def create_pipeline_config(
    config: Path, defaults: Optional[Path], verbose: bool
) -> PipelineConfig:
    setup_logging_level(verbose)
    PipelineConfig.Config.config_path = config
    if defaults:
        pipeline_config = PipelineConfig(defaults_path=defaults)
    else:
        pipeline_config = PipelineConfig()
        pipeline_config.defaults_path = config.parent / pipeline_config.defaults_path
    return pipeline_config


@app.command(  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
    help="""
    Generate json schema.

    The schemas can be used to enable support for kpops files in a text editor.
    """
)
def schema(
    scope: SchemaScope = typer.Argument(
        ...,
        show_default=False,
        help="""
        Scope of the generated schema
        \n\n\n
        pipeline: Schema of PipelineComponents. Includes the built-in kpops components by default. To include custom components, provide [COMPONENTS_MODULES].
        \n\n\n
        config: Schema of PipelineConfig.""",
    ),
    components_module: Optional[str] = COMPONENTS_MODULES,
    include_stock_components: bool = typer.Option(
        default=True, help="Include the built-in KPOps components."
    ),
) -> None:
    match scope:
        case SchemaScope.PIPELINE:
            gen_pipeline_schema(components_module, include_stock_components)
        case SchemaScope.CONFIG:
            gen_config_schema()


@app.command(  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
    help="Enriches pipelines steps with defaults. The output is used as input for the deploy/destroy/... commands."
)
def generate(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    template: bool = typer.Option(False, help="Run Helm template"),
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    verbose: bool = VERBOSE_OPTION,
) -> Pipeline:
    pipeline_config = create_pipeline_config(config, defaults, verbose)
    pipeline = setup_pipeline(
        pipeline_base_dir, pipeline_path, components_module, pipeline_config
    )

    if not template:
        pipeline.print_yaml()

    if template:
        steps_to_apply = get_steps_to_apply(pipeline, steps, filter_type)
        for component in steps_to_apply:
            component.template()
    elif steps:
        log.warning(
            "The following flags are considered only when `--template` is set: \n \
                '--steps'"
        )

    return pipeline


@app.command(
    help="Deploy pipeline steps"
)  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
def deploy(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
):
    pipeline_config = create_pipeline_config(config, defaults, verbose)
    pipeline = setup_pipeline(
        pipeline_base_dir, pipeline_path, components_module, pipeline_config
    )

    steps_to_apply = get_steps_to_apply(pipeline, steps, filter_type)
    for component in steps_to_apply:
        log_action("Deploy", component)
        component.deploy(dry_run)


@app.command(
    help="Destroy pipeline steps"
)  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
def destroy(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
):
    pipeline_config = create_pipeline_config(config, defaults, verbose)
    pipeline = setup_pipeline(
        pipeline_base_dir, pipeline_path, components_module, pipeline_config
    )
    pipeline_steps = reverse_pipeline_steps(pipeline, steps, filter_type)
    for component in pipeline_steps:
        log_action("Destroy", component)
        component.destroy(dry_run)


@app.command(
    help="Reset pipeline steps"
)  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
def reset(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
):
    pipeline_config = create_pipeline_config(config, defaults, verbose)
    pipeline = setup_pipeline(
        pipeline_base_dir, pipeline_path, components_module, pipeline_config
    )
    pipeline_steps = reverse_pipeline_steps(pipeline, steps, filter_type)
    for component in pipeline_steps:
        log_action("Reset", component)
        component.destroy(dry_run)
        component.reset(dry_run)


@app.command(
    help="Clean pipeline steps"
)  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
def clean(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
):
    pipeline_config = create_pipeline_config(config, defaults, verbose)
    pipeline = setup_pipeline(
        pipeline_base_dir, pipeline_path, components_module, pipeline_config
    )
    pipeline_steps = reverse_pipeline_steps(pipeline, steps, filter_type)
    for component in pipeline_steps:
        log_action("Clean", component)
        component.destroy(dry_run)
        component.clean(dry_run)


def version_callback(show_version: bool) -> None:
    if show_version:
        typer.echo(f"KPOps {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Print KPOps version",
        callback=version_callback,
        is_eager=True,
    ),
):
    ...


if __name__ == "__main__":
    app()
