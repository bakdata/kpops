from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import typer

from kpops.cli.custom_formatter import CustomFormatter
from kpops.cli.pipeline_config import ENV_PREFIX, PipelineConfig
from kpops.cli.registry import Registry
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.kafka_connect.handler import ConnectorHandler
from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.streams_bootstrap.handler import AppHandler
from kpops.component_handlers.topic.handler import TopicHandler
from kpops.component_handlers.topic.proxy_wrapper import ProxyWrapper
from kpops.pipeline_generator.pipeline import Pipeline

if TYPE_CHECKING:
    from kpops.components.base_components import PipelineComponent


LOG_DIVIDER = "#" * 100

app = typer.Typer(
    pretty_exceptions_show_locals=False,
)

BASE_DIR_PATH_OPTION: Path = typer.Option(
    default=Path("."),
    exists=True,
    dir_okay=True,
    file_okay=False,
    envvar=f"{ENV_PREFIX}PIPELINE_BASE_DIR",
    help="Base directory to the pipelines (default is current working directory)",
)

DEFAULT_PATH_OPTION: Path = typer.Option(
    default=Path("defaults"),
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

COMPONENTS_MODULES: str | None = typer.Argument(
    default=None,
    help="Custom Python module containing your project-specific components",
)

logger = logging.getLogger()
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
    app_handler = AppHandler.from_pipeline_config(config)
    connector_handler = ConnectorHandler.from_pipeline_config(config)
    proxy_wrapper = ProxyWrapper(config)
    topic_handler = TopicHandler(proxy_wrapper)

    return ComponentHandlers(
        schema_handler, app_handler, connector_handler, topic_handler
    )


def setup_logging_level(verbose: bool):
    logging.getLogger().setLevel(logging.DEBUG if verbose else logging.INFO)


def parse_steps(steps: str) -> set[str]:
    return set(steps.split(","))


def remove_pipeline_prefix(name: str, pipeline: Pipeline) -> str:
    return name.removeprefix(pipeline.config.pipeline_prefix)


def get_step_names(
    steps_to_apply: list[PipelineComponent], pipeline: Pipeline
) -> list[str]:
    return [remove_pipeline_prefix(step.name, pipeline) for step in steps_to_apply]


def filter_steps_to_apply(
    pipeline: Pipeline, steps: set[str]
) -> list[PipelineComponent]:
    skipped_steps: list[str] = []

    def filter_component(component: PipelineComponent) -> bool:
        if remove_pipeline_prefix(component.name, pipeline) in steps:
            return True
        skipped_steps.append(remove_pipeline_prefix(component.name, pipeline))
        return False

    steps_to_apply = list(filter(filter_component, pipeline))
    log.info("KPOPS_PIPELINE_STEPS is defined.")
    log.info(
        f"Executing only on the following steps: {get_step_names(steps_to_apply, pipeline)}"
        f", \n ignoring {skipped_steps}"
    )
    return steps_to_apply


def get_steps_to_apply(
    pipeline: Pipeline, steps: str | None
) -> list[PipelineComponent]:
    return (
        list(pipeline)
        if not steps or steps == '""'  # workaround to allow "" as empty value for CI
        else filter_steps_to_apply(pipeline, steps=parse_steps(steps))
    )


def log_action(action: str, pipeline_component: PipelineComponent):
    log.info("\n")
    log.info(LOG_DIVIDER)
    log.info(f"{action} {pipeline_component.name}")
    log.info(LOG_DIVIDER)
    log.info("\n")


def run_destroy_clean_reset(
    pipeline_base_dir: Path,
    components_module: str | None,
    config: Path,
    defaults,
    dry_run: bool,
    pipeline_path: Path,
    steps: str | None,
    verbose,
    clean: bool,
    delete_outputs: bool,
):
    pipeline_config = create_pipeline_config(config, defaults, verbose)
    pipeline = setup_pipeline(
        pipeline_base_dir, pipeline_path, components_module, pipeline_config
    )
    for component in reversed(get_steps_to_apply(pipeline, steps)):
        log_action("Destroy", component)
        component.destroy(dry_run=dry_run, clean=clean, delete_outputs=delete_outputs)


def create_pipeline_config(
    config: Path, defaults: Path, verbose: bool
) -> PipelineConfig:
    setup_logging_level(verbose=verbose)
    PipelineConfig.Config.config_path = config
    pipeline_config = PipelineConfig(defaults_path=defaults)
    return pipeline_config


@app.command(
    help="Enriches pipelines steps with defaults. The output is used as input for the deploy/destroy/... commands."
)
def generate(
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    defaults: Path = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    print_yaml: bool = typer.Option(
        True, help="Print enriched pipeline yaml definition"
    ),
    save: bool = typer.Option(False, help="Save pipeline to yaml file"),
    out_path: Optional[Path] = typer.Option(
        None, help="Path to file the yaml pipeline should be saved to"
    ),
    verbose: bool = typer.Option(False, help="Enable verbose printing"),
):
    pipeline_config = create_pipeline_config(config, defaults, verbose)
    pipeline = setup_pipeline(
        pipeline_base_dir, pipeline_path, components_module, pipeline_config
    )
    if print_yaml:
        pipeline.print_yaml()

    if save:
        if not out_path:
            raise ValueError(
                "Please provide a output path if you want to save the generated deployment."
            )
        pipeline.save(out_path)


@app.command(help="Deploy pipeline steps")
def deploy(
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    defaults: Path = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    verbose: bool = False,
    dry_run: bool = DRY_RUN,
    steps: Optional[str] = PIPELINE_STEPS,
):
    pipeline_config = create_pipeline_config(config, defaults, verbose)
    pipeline = setup_pipeline(
        pipeline_base_dir, pipeline_path, components_module, pipeline_config
    )

    steps_to_apply = get_steps_to_apply(pipeline, steps)

    for component in steps_to_apply:
        log_action("Deploy", component)
        component.deploy(dry_run=dry_run)


@app.command(help="Destroy pipeline steps")
def destroy(
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    defaults: Path = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    dry_run: bool = DRY_RUN,
    verbose: bool = False,
):
    run_destroy_clean_reset(
        pipeline_base_dir,
        components_module,
        config,
        defaults,
        dry_run,
        pipeline_path,
        steps,
        verbose,
        clean=False,
        delete_outputs=False,
    )


@app.command(help="Reset pipeline steps")
def reset(
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    defaults: Path = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    dry_run: bool = DRY_RUN,
    verbose: bool = False,
):
    run_destroy_clean_reset(
        pipeline_base_dir,
        components_module,
        config,
        defaults,
        dry_run,
        pipeline_path,
        steps,
        verbose,
        clean=True,
        delete_outputs=False,
    )


@app.command(help="Clean pipeline steps")
def clean(
    pipeline_base_dir: Path = BASE_DIR_PATH_OPTION,
    pipeline_path: Path = PIPELINE_PATH_ARG,
    components_module: Optional[str] = COMPONENTS_MODULES,
    defaults: Path = DEFAULT_PATH_OPTION,
    config: Path = CONFIG_PATH_OPTION,
    steps: Optional[str] = PIPELINE_STEPS,
    dry_run: bool = DRY_RUN,
    verbose: bool = False,
):
    run_destroy_clean_reset(
        pipeline_base_dir,
        components_module,
        config,
        defaults,
        dry_run,
        pipeline_path,
        steps,
        verbose,
        clean=True,
        delete_outputs=True,
    )


if __name__ == "__main__":
    app()
