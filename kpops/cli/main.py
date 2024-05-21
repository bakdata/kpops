from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import dtyper
import typer

import kpops
from kpops import __version__
from kpops.cli.custom_formatter import CustomFormatter
from kpops.cli.options import FilterType
from kpops.components.base_components.models.resource import Resource
from kpops.config import ENV_PREFIX, KpopsConfig
from kpops.utils.cli_commands import init_project
from kpops.utils.gen_schema import (
    SchemaScope,
    gen_config_schema,
    gen_defaults_schema,
    gen_pipeline_schema,
)
from kpops.utils.yaml import print_yaml

if TYPE_CHECKING:
    from kpops.components import PipelineComponent


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

PROJECT_PATH: Path = typer.Argument(
    default=...,
    exists=False,
    file_okay=False,
    dir_okay=True,
    readable=True,
    resolve_path=True,
    help="Path for a new KPOps project. It should lead to an empty (or non-existent) directory. The part of the path that doesn't exist will be created.",
)

CONFIG_INCLUDE_OPTIONAL: bool = typer.Option(
    default=False,
    help="Whether to include non-required settings in the generated 'config.yaml'",
)

PIPELINE_STEPS: Optional[str] = typer.Option(
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


FILTER_TYPE: FilterType = typer.Option(
    default=FilterType.INCLUDE,
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


def parse_steps(steps: str) -> set[str]:
    return set(steps.split(","))


def log_action(action: str, pipeline_component: PipelineComponent):
    log.info("\n")
    log.info(LOG_DIVIDER)
    log.info(f"{action} {pipeline_component.name}")
    log.info(LOG_DIVIDER)
    log.info("\n")


@app.command(  # pyright: ignore[reportCallIssue] https://github.com/rec/dtyper/issues/8
    help="Initialize a new KPOps project."
)
def init(
    path: Path = PROJECT_PATH,
    config_include_opt: bool = CONFIG_INCLUDE_OPTIONAL,
):
    if not path.exists():
        path.mkdir(parents=False)
    elif next(path.iterdir(), False):
        log.warning("Please provide a path to an empty directory.")
        return
    init_project(path, config_include_opt)


@app.command(  # pyright: ignore[reportCallIssue] https://github.com/rec/dtyper/issues/8
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
            kpops_config = KpopsConfig.create(config)
            gen_pipeline_schema(
                kpops_config.components_module, include_stock_components
            )
        case SchemaScope.DEFAULTS:
            kpops_config = KpopsConfig.create(config)
            gen_defaults_schema(
                kpops_config.components_module, include_stock_components
            )
        case SchemaScope.CONFIG:
            gen_config_schema()


@app.command(  # pyright: ignore[reportCallIssue] https://github.com/rec/dtyper/issues/8
    short_help="Generate enriched pipeline representation",
    help="Enrich pipeline steps with defaults. The enriched pipeline is used for all KPOps operations (deploy, destroy, ...).",
)
def generate(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    verbose: bool = VERBOSE_OPTION,
):
    pipeline = kpops.generate(
        pipeline_path,
        dotenv,
        config,
        steps,
        filter_type,
        environment,
        verbose,
    )
    print_yaml(pipeline.to_yaml())


@app.command(  # pyright: ignore[reportCallIssue] https://github.com/rec/dtyper/issues/8
    short_help="Render final resource representation",
    help="In addition to generate, render final resource representation for each pipeline step, e.g. Kubernetes manifests.",
)
def manifest(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    output: bool = OUTPUT_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    verbose: bool = VERBOSE_OPTION,
) -> list[Resource]:
    pipeline = kpops.generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )
    resources: list[Resource] = []
    for component in pipeline.components:
        resource = component.manifest()
        resources.append(resource)
        if output:
            for manifest in resource:
                print_yaml(manifest)
    return resources


@app.command(help="Deploy pipeline steps")  # pyright: ignore[reportCallIssue] https://github.com/rec/dtyper/issues/8
def deploy(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
):
    pipeline = kpops.generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )

    async def deploy_runner(component: PipelineComponent):
        log_action("Deploy", component)
        await component.deploy(dry_run)

    async def async_deploy():
        if parallel:
            pipeline_tasks = pipeline.build_execution_graph(deploy_runner)
            await pipeline_tasks
        else:
            for component in pipeline.components:
                await deploy_runner(component)

    asyncio.run(async_deploy())


@app.command(help="Destroy pipeline steps")  # pyright: ignore[reportCallIssue] https://github.com/rec/dtyper/issues/8
def destroy(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
):
    pipeline = kpops.generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )

    async def destroy_runner(component: PipelineComponent):
        log_action("Destroy", component)
        await component.destroy(dry_run)

    async def async_destroy():
        if parallel:
            pipeline_tasks = pipeline.build_execution_graph(
                destroy_runner, reverse=True
            )
            await pipeline_tasks
        else:
            for component in reversed(pipeline.components):
                await destroy_runner(component)

    asyncio.run(async_destroy())


@app.command(help="Reset pipeline steps")  # pyright: ignore[reportCallIssue] https://github.com/rec/dtyper/issues/8
def reset(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
):
    pipeline = kpops.generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )

    async def reset_runner(component: PipelineComponent):
        await component.destroy(dry_run)
        log_action("Reset", component)
        await component.reset(dry_run)

    async def async_reset():
        if parallel:
            pipeline_tasks = pipeline.build_execution_graph(reset_runner, reverse=True)
            await pipeline_tasks
        else:
            for component in reversed(pipeline.components):
                await reset_runner(component)

    asyncio.run(async_reset())


@app.command(help="Clean pipeline steps")  # pyright: ignore[reportCallIssue] https://github.com/rec/dtyper/issues/8
def clean(
    pipeline_path: Path = PIPELINE_PATH_ARG,
    dotenv: Optional[list[Path]] = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
):
    pipeline = kpops.generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )

    async def clean_runner(component: PipelineComponent):
        await component.destroy(dry_run)
        log_action("Clean", component)
        await component.clean(dry_run)

    async def async_clean():
        if parallel:
            pipeline_tasks = pipeline.build_execution_graph(clean_runner, reverse=True)
            await pipeline_tasks
        else:
            for component in reversed(pipeline.components):
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
): ...


if __name__ == "__main__":
    app()
