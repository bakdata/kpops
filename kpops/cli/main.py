from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

import kpops.api as kpops
from kpops.api.logs import log
from kpops.api.options import FilterType
from kpops.cli.utils import (
    collect_pipeline_paths,
)
from kpops.config import ENV_PREFIX
from kpops.const import KPOPS, __version__
from kpops.const.file_type import (
    CONFIG_YAML,
    DEFAULTS_YAML,
    PIPELINE_YAML,
    KpopsFileType,
)
from kpops.core.operation import OperationMode
from kpops.utils.gen_schema import (
    gen_config_schema,
    gen_defaults_schema,
    gen_pipeline_schema,
)
from kpops.utils.yaml import print_yaml

app = typer.Typer(pretty_exceptions_enable=False)

DOTENV_PATH_OPTION: list[Path] | None = typer.Option(
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

PIPELINE_PATHS_ARG: list[Path] = typer.Argument(
    exists=True,
    file_okay=True,
    dir_okay=True,
    readable=True,
    envvar=f"{ENV_PREFIX}PIPELINE_PATHS",
    help="Paths to dir containing 'pipeline.yaml' or files named 'pipeline.yaml'.",
)

PROJECT_PATH: Path = typer.Argument(
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


FILTER_TYPE: FilterType = typer.Option(
    default=FilterType.INCLUDE,
    case_sensitive=False,
    help="Whether the --steps option should include/exclude the steps",
)

OUTPUT_OPTION: bool = typer.Option(True, help="Enable output printing")
VERBOSE_OPTION: bool = typer.Option(False, help="Enable verbose printing")

ENVIRONMENT: str | None = typer.Option(
    default=None,
    envvar=f"{ENV_PREFIX}ENVIRONMENT",
    help=(
        "The environment you want to generate and deploy the pipeline to. "
        "Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development). "
    ),
)
OPERATION_MODE_OPTION: OperationMode = typer.Option(
    default=OperationMode.MANAGED,
    envvar=f"{ENV_PREFIX}OPERATION_MODE",
    help="How KPOps should operate.",
)


def parse_steps(steps: str | None) -> set[str] | None:
    return set(steps.split(",")) if steps else None


@app.command(help="Initialize a new KPOps project.")
def init(
    path: Path = PROJECT_PATH,
    config_include_optional: bool = CONFIG_INCLUDE_OPTIONAL,
):
    kpops.init(path, config_include_optional=config_include_optional)


@app.command(
    short_help="Generate enriched pipeline representation",
    help="Enrich pipeline steps with defaults. The enriched pipeline is used for all KPOps operations (deploy, destroy, ...).",
)
def generate(
    pipeline_paths: list[Path] = PIPELINE_PATHS_ARG,
    dotenv: list[Path] | None = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: str | None = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: str | None = ENVIRONMENT,
    verbose: bool = VERBOSE_OPTION,
):
    for pipeline_file_path in collect_pipeline_paths(pipeline_paths):
        pipeline = kpops.generate(
            pipeline_path=pipeline_file_path,
            dotenv=dotenv,
            config=config,
            steps=parse_steps(steps),
            filter_type=filter_type,
            environment=environment,
            verbose=verbose,
        )
        print_yaml(pipeline.to_yaml())


@app.command(help="Deploy pipeline steps")
def deploy(
    pipeline_paths: list[Path] = PIPELINE_PATHS_ARG,
    dotenv: list[Path] | None = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: str | None = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: str | None = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
    operation_mode: OperationMode = OPERATION_MODE_OPTION,
):
    match operation_mode:
        case OperationMode.MANAGED:
            for pipeline_file_path in collect_pipeline_paths(pipeline_paths):
                kpops.deploy(
                    pipeline_path=pipeline_file_path,
                    dotenv=dotenv,
                    config=config,
                    steps=parse_steps(steps),
                    filter_type=filter_type,
                    environment=environment,
                    dry_run=dry_run,
                    verbose=verbose,
                    parallel=parallel,
                )
        case _:
            for pipeline_file_path in collect_pipeline_paths(pipeline_paths):
                resources = kpops.manifest_deploy(
                    pipeline_file_path,
                    dotenv,
                    config,
                    parse_steps(steps),
                    filter_type,
                    environment,
                    verbose,
                    operation_mode,
                )
                for resource in resources:
                    for rendered_manifest in resource:
                        print_yaml(rendered_manifest.model_dump())


@app.command(help="Destroy pipeline steps")
def destroy(
    pipeline_paths: list[Path] = PIPELINE_PATHS_ARG,
    dotenv: list[Path] | None = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: str | None = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: str | None = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
    operation_mode: OperationMode = OPERATION_MODE_OPTION,
):
    match operation_mode:
        case OperationMode.MANAGED:
            for pipeline_file_path in collect_pipeline_paths(pipeline_paths):
                kpops.destroy(
                    pipeline_path=pipeline_file_path,
                    dotenv=dotenv,
                    config=config,
                    steps=parse_steps(steps),
                    filter_type=filter_type,
                    environment=environment,
                    dry_run=dry_run,
                    verbose=verbose,
                    parallel=parallel,
                )
        case _:
            for pipeline_file_path in collect_pipeline_paths(pipeline_paths):
                resources = kpops.manifest_destroy(
                    pipeline_file_path,
                    dotenv,
                    config,
                    parse_steps(steps),
                    filter_type,
                    environment,
                    verbose,
                    operation_mode,
                )
                for resource in resources:
                    for rendered_manifest in resource:
                        print_yaml(rendered_manifest.model_dump())


@app.command(help="Reset pipeline steps")
def reset(
    pipeline_paths: list[Path] = PIPELINE_PATHS_ARG,
    dotenv: list[Path] | None = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: str | None = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: str | None = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
    operation_mode: OperationMode = OPERATION_MODE_OPTION,
):
    match operation_mode:
        case OperationMode.MANAGED:
            for pipeline_file_path in collect_pipeline_paths(pipeline_paths):
                kpops.reset(
                    pipeline_path=pipeline_file_path,
                    dotenv=dotenv,
                    config=config,
                    steps=parse_steps(steps),
                    filter_type=filter_type,
                    environment=environment,
                    dry_run=dry_run,
                    verbose=verbose,
                    parallel=parallel,
                )
        case _:
            for pipeline_file_path in collect_pipeline_paths(pipeline_paths):
                resources = kpops.manifest_reset(
                    pipeline_file_path,
                    dotenv,
                    config,
                    parse_steps(steps),
                    filter_type,
                    environment,
                    verbose,
                    operation_mode,
                )
                for resource in resources:
                    for rendered_manifest in resource:
                        print_yaml(rendered_manifest.model_dump())


@app.command(help="Clean pipeline steps")
def clean(
    pipeline_paths: list[Path] = PIPELINE_PATHS_ARG,
    dotenv: list[Path] | None = DOTENV_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: str | None = PIPELINE_STEPS,
    filter_type: FilterType = FILTER_TYPE,
    environment: str | None = ENVIRONMENT,
    dry_run: bool = DRY_RUN,
    verbose: bool = VERBOSE_OPTION,
    parallel: bool = PARALLEL,
    operation_mode: OperationMode = OPERATION_MODE_OPTION,
):
    match operation_mode:
        case OperationMode.MANAGED:
            for pipeline_file_path in collect_pipeline_paths(pipeline_paths):
                kpops.clean(
                    pipeline_path=pipeline_file_path,
                    dotenv=dotenv,
                    config=config,
                    steps=parse_steps(steps),
                    filter_type=filter_type,
                    environment=environment,
                    dry_run=dry_run,
                    verbose=verbose,
                    parallel=parallel,
                )
        case OperationMode.MANIFEST:
            for pipeline_file_path in collect_pipeline_paths(pipeline_paths):
                resources = kpops.manifest_clean(
                    pipeline_file_path,
                    dotenv,
                    config,
                    parse_steps(steps),
                    filter_type,
                    environment,
                    verbose,
                    operation_mode,
                )
                for resource in resources:
                    for rendered_manifest in resource:
                        print_yaml(rendered_manifest.model_dump())
        case OperationMode.ARGO:
            log.warning(
                "No cleanup jobs are manifested in Argo mode. The cleanup jobs with Argo hooks are manifested with 'deploy' command.\n"
                "If you wish to see the cleanup job manifest use the 'manifest' operation mode."
            )


def version_callback(show_version: bool) -> None:
    if show_version:
        typer.echo(f"{KPOPS} {__version__}")
        raise typer.Exit


@app.command(
    help="""
    Generate JSON schema.

    The schemas can be used to enable support for KPOps files in a text editor.
    """
)
def schema(
    scope: Annotated[
        KpopsFileType,
        typer.Argument(
            show_default=False,
            help=f"""
        Scope of the generated schema
        \n\n\n
        - {KpopsFileType.PIPELINE.value}: Schema of PipelineComponents for KPOps {PIPELINE_YAML}
        \n\n
        - {KpopsFileType.DEFAULTS.value}: Schema of PipelineComponents for KPOps {DEFAULTS_YAML}
        \n\n
        - {KpopsFileType.CONFIG.value}: Schema for KPOps {CONFIG_YAML}""",
        ),
    ],
) -> None:
    match scope:
        case KpopsFileType.PIPELINE:
            gen_pipeline_schema()
        case KpopsFileType.DEFAULTS:
            gen_defaults_schema()
        case KpopsFileType.CONFIG:
            gen_config_schema()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Print KPOps version",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
): ...


if __name__ == "__main__":
    app()
