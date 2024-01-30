from __future__ import annotations

import asyncio
import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import dtyper
import typer

from kpops import __version__
from kpops.cli.custom_formatter import CustomFormatter
from kpops.cli.registry import Registry
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
    KafkaConnectHandler,
)
from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.topic.handler import TopicHandler
from kpops.component_handlers.topic.proxy_wrapper import ProxyWrapper
from kpops.components.base_components.models.resource import Resource
from kpops.config import ENV_PREFIX, KpopsConfig
from kpops.pipeline import Pipeline, PipelineGenerator
from kpops.utils.gen_schema import (
    SchemaScope,
    gen_config_schema,
    gen_defaults_schema,
    gen_pipeline_schema,
)
from kpops.utils.pydantic import YamlConfigSettingsSource
from kpops.utils.yaml import print_yaml

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Coroutine, Iterator

    from kpops.components.base_components.pipeline_component import PipelineComponent


LOG_DIVIDER = "#" * 100

app = dtyper.Typer(pretty_exceptions_enable=False)

DOTENV_PATH_OPTION: Optional[list[Path]] = typer.Option(
    default=None,
    exists=True,
    dir_okay=False,
    file_okay=True,
    envvar=f"{ENV_PREFIX}DOTENV_PATH",
    help=(
        "Path to dotenv file. Multiple files can be provided. "
        "The files will be loaded in order, with each file overriding the previous one."
    ),
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
    default=Path(),
    exists=True,
    dir_okay=True,
    file_okay=False,
    readable=True,
    envvar=f"{ENV_PREFIX}CONFIG_PATH",
    help="Path to the dir containing config.yaml files",
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

PARALLEL: bool = typer.Option(
    False,
    "--parallel/--no-parallel",
    rich_help_panel="EXPERIMENTAL: features in preview, not production-ready",
    help="Enable or disable parallel execution of pipeline steps. If enabled, multiple steps can be processed concurrently. If disabled, steps will be processed sequentially.",
)


class FilterType(str, Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"


FILTER_TYPE: FilterType = typer.Option(
    default=FilterType.INCLUDE.value,
    case_sensitive=False,
    help="Whether the --steps option should include/exclude the steps",
)

OUTPUT_OPTION = typer.Option(True, help="Enable output printing")
VERBOSE_OPTION = typer.Option(False, help="Enable verbose printing")

ENVIRONMENT: str | None = typer.Option(
    default=None,
    envvar=f"{ENV_PREFIX}ENVIRONMENT",
    help=(
        "The environment you want to generate and deploy the pipeline to. "
        "Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development). "
    ),
)

logger = logging.getLogger()
logging.getLogger("httpx").setLevel(logging.WARNING)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(CustomFormatter())
logger.addHandler(stream_handler)

log = logging.getLogger("")


def setup_pipeline(
    pipeline_path: Path,
    kpops_config: KpopsConfig,
    environment: str | None,
) -> Pipeline:
    registry = Registry()
    if kpops_config.components_module:
        registry.find_components(kpops_config.components_module)
    registry.find_components("kpops.components")

    handlers = setup_handlers(kpops_config)
    parser = PipelineGenerator(kpops_config, registry, handlers)
    return parser.load_yaml(pipeline_path, environment)


def setup_handlers(config: KpopsConfig) -> ComponentHandlers:
    schema_handler = SchemaHandler.load_schema_handler(config)
    connector_handler = KafkaConnectHandler.from_kpops_config(config)
    proxy_wrapper = ProxyWrapper(config.kafka_rest)
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


def get_reverse_concurrently_tasks_to_execute(
    pipeline: Pipeline,
    steps: str | None,
    filter_type: FilterType,
    runner: Callable[[PipelineComponent], Coroutine],
) -> Awaitable:
    steps_to_apply = reverse_pipeline_steps(pipeline, steps, filter_type)
    return pipeline.build_execution_graph_from(list(steps_to_apply), True, runner)


def get_concurrently_tasks_to_execute(
    pipeline: Pipeline,
    steps: str | None,
    filter_type: FilterType,
    runner: Callable[[PipelineComponent], Coroutine],
) -> Awaitable:
    steps_to_apply = get_steps_to_apply(pipeline, steps, filter_type)
    return pipeline.build_execution_graph_from(steps_to_apply, False, runner)


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


def create_kpops_config(
    config: Path,
    defaults: Path | None = None,
    dotenv: list[Path] | None = None,
    environment: str | None = None,
    verbose: bool = False,
) -> KpopsConfig:
    setup_logging_level(verbose)
    YamlConfigSettingsSource.config_dir = config
    YamlConfigSettingsSource.environment = environment
    kpops_config = KpopsConfig(
        _env_file=dotenv  # pyright: ignore[reportGeneralTypeIssues]
    )
    if defaults:
        kpops_config.defaults_path = defaults
    else:
        kpops_config.defaults_path = config / kpops_config.defaults_path
    return kpops_config


@app.command(  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
    help="""
    Generate JSON schema.

    The schemas can be used to enable support for KPOps files in a text editor.
    """
)
def schema(
    scope: SchemaScope = typer.Argument(
        ...,
        show_default=False,
        help="""
        Scope of the generated schema
        \n\n\n
        pipeline: Schema of PipelineComponents. Includes the built-in KPOps components by default. To include custom components, provide components module in config.
        \n\n\n
        config: Schema of KpopsConfig.""",
    ),
    config: Path = CONFIG_PATH_OPTION,
    include_stock_components: bool = typer.Option(
        default=True, help="Include the built-in KPOps components."
    ),
) -> None:
    match scope:
        case SchemaScope.PIPELINE:
            kpops_config = create_kpops_config(config)
            gen_pipeline_schema(
                kpops_config.components_module, include_stock_components
            )
        case SchemaScope.DEFAULTS:
            kpops_config = create_kpops_config(config)
            gen_defaults_schema(
                kpops_config.components_module, include_stock_components
            )
        case SchemaScope.CONFIG:
            gen_config_schema()


@app.command(  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
    short_help="Generate enriched pipeline representation",
    help="Enrich pipeline steps with defaults. The enriched pipeline is used for all KPOps operations (deploy, destroy, ...).",
)
def generate(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    output: bool = OUTPUT_OPTION,
    environment: Optional[str] = ENVIRONMENT,
    verbose: bool = VERBOSE_OPTION,
) -> Pipeline:
    kpops_config = create_kpops_config(
        config,
        defaults,
        dotenv,
        environment,
        verbose,
    )

    pipeline = setup_pipeline(pipeline_path, kpops_config, environment)
    if output:
        print_yaml(pipeline.to_yaml())
    return pipeline


@app.command(  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
    short_help="Render final resource representation",
    help="In addition to generate, render final resource representation for each pipeline step, e.g. Kubernetes manifests.",
)
def manifest(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    output: bool = OUTPUT_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    verbose: bool = VERBOSE_OPTION,
) -> list[Resource]:
    pipeline = generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        defaults=defaults,
        config=config,
        output=False,
        environment=environment,
        verbose=verbose,
    )
    steps_to_apply = get_steps_to_apply(pipeline, steps, filter_type)
    resources: list[Resource] = []
    for component in steps_to_apply:
        resource = component.manifest()
        resources.append(resource)
        if output:
            for manifest in resource:
                print_yaml(manifest)
    return resources


@app.command(help="Deploy pipeline steps")  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
def deploy(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
):
    async def deploy_runner(component: PipelineComponent):
        log_action("Deploy", component)
        await component.deploy(dry_run)

    async def async_deploy():
        kpops_config = create_kpops_config(
            config,
            defaults,
            dotenv,
            environment,
            verbose,
        )
        pipeline = setup_pipeline(pipeline_path, kpops_config, environment)

        if parallel:
            pipeline_tasks = get_concurrently_tasks_to_execute(
                pipeline, steps, filter_type, deploy_runner
            )
            await pipeline_tasks
        else:
            steps_to_apply = get_steps_to_apply(pipeline, steps, filter_type)
            for component in steps_to_apply:
                await deploy_runner(component)

    asyncio.run(async_deploy())


@app.command(help="Destroy pipeline steps")  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
def destroy(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
):
    async def destroy_runner(component: PipelineComponent):
        log_action("Destroy", component)
        await component.destroy(dry_run)

    async def async_destroy():
        kpops_config = create_kpops_config(
            config,
            defaults,
            dotenv,
            environment,
            verbose,
        )

        pipeline = setup_pipeline(pipeline_path, kpops_config, environment)

        if parallel:
            pipeline_tasks = get_reverse_concurrently_tasks_to_execute(
                pipeline, steps, filter_type, destroy_runner
            )
            await pipeline_tasks
        else:
            pipeline_steps = reverse_pipeline_steps(pipeline, steps, filter_type)
            for component in pipeline_steps:
                await destroy_runner(component)

    asyncio.run(async_destroy())


@app.command(help="Reset pipeline steps")  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
def reset(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
):
    async def reset_runner(component: PipelineComponent):
        log_action("Reset", component)
        await component.destroy(dry_run)
        await component.reset(dry_run)

    async def async_reset():
        kpops_config = create_kpops_config(
            config,
            defaults,
            dotenv,
            environment,
            verbose,
        )
        pipeline = setup_pipeline(pipeline_path, kpops_config, environment)
        if parallel:
            pipeline_tasks = get_reverse_concurrently_tasks_to_execute(
                pipeline, steps, filter_type, reset_runner
            )
            await pipeline_tasks
        else:
            pipeline_steps = reverse_pipeline_steps(pipeline, steps, filter_type)
            for component in pipeline_steps:
                await reset_runner(component)

    asyncio.run(async_reset())


@app.command(help="Clean pipeline steps")  # pyright: ignore[reportGeneralTypeIssues] https://github.com/rec/dtyper/issues/8
def clean(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    defaults: Optional[Path] = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
):
    async def clean_runner(component: PipelineComponent):
        log_action("Clean", component)
        await component.destroy(dry_run)
        await component.clean(dry_run)

    async def async_clean():
        kpops_config = create_kpops_config(
            config,
            defaults,
            dotenv,
            environment,
            verbose,
        )
        pipeline = setup_pipeline(pipeline_path, kpops_config, environment)
        if parallel:
            pipeline_steps = get_reverse_concurrently_tasks_to_execute(
                pipeline, steps, filter_type, clean_runner
            )
            await pipeline_steps
        else:
            pipeline_steps = reverse_pipeline_steps(pipeline, steps, filter_type)
            for component in pipeline_steps:
                await clean_runner(component)

    asyncio.run(async_clean())


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
