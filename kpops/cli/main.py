from __future__ import annotations

from pathlib import Path
from typing import Optional

import dtyper
import typer

import kpops
from kpops import __version__
from kpops.api.options import FilterType
from kpops.config import ENV_PREFIX, KpopsConfig
from kpops.utils.gen_schema import (
    SchemaScope,
    gen_config_schema,
    gen_defaults_schema,
    gen_pipeline_schema,
)
from kpops.utils.yaml import print_yaml

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


@app.command(  # pyright: ignore[reportCallIssue] https://github.com/rec/dtyper/issues/8
    help="Initialize a new KPOps project."
)
def init(
    path: Path = PROJECT_PATH,
    config_include_opt: bool = CONFIG_INCLUDE_OPTIONAL,
):
    kpops.init(path, config_include_opt=config_include_opt)


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
    steps: Optional[str] = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: Optional[str] = ENVIRONMENT,
    verbose: bool = VERBOSE_OPTION,
):
    resources = kpops.manifest(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )
    for resource in resources:
        for rendered_manifest in resource:
            print_yaml(rendered_manifest)


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
    kpops.deploy(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        dry_run=dry_run,
        verbose=verbose,
        parallel=parallel,
    )


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
    kpops.destroy(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        dry_run=dry_run,
        verbose=verbose,
        parallel=parallel,
    )


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
    kpops.reset(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        dry_run=dry_run,
        verbose=verbose,
        parallel=parallel,
    )


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
    kpops.clean(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        dry_run=dry_run,
        verbose=verbose,
        parallel=parallel,
    )


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
