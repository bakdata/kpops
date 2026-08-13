from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from kpops.api.options import FilterType
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
    KafkaConnectHandler,
)
from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.topic.handler import TopicHandler
from kpops.component_handlers.topic.kafka_rest import KafkaRest
from kpops.config import KpopsConfig
from kpops.core.operation import OperationMode
from kpops.core.registry import Registry
from kpops.pipeline import (
    Pipeline,
    PipelineGenerator,
)
from kpops.utils.cli_commands import init_project
from kpops.utils.logging import log

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kpops.config import KpopsConfig
    from kpops.manifests.kubernetes import KubernetesManifest


def generate(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path | None = None,
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    verbose: bool = False,
    operation_mode: OperationMode = OperationMode.MANAGED,
) -> Pipeline:
    """Generate enriched pipeline representation.

    :param pipeline_path: Path to pipeline definition yaml file.
    :param dotenv: Paths to dotenv files.
    :param config: Path to the dir containing config.yaml files.
    :param steps: Set of steps (components) to apply the command on.
    :param filter_type: Whether `steps` should include/exclude the steps.
    :param environment: The environment to generate and deploy the pipeline to.
    :param verbose: Enable verbose printing.
    :param operation_mode: How KPOps should operate.
    :return: Generated `Pipeline` object.
    """
    kpops_config = KpopsConfig.create(
        config, dotenv, environment, verbose, operation_mode
    )
    pipeline = _create_pipeline(pipeline_path, kpops_config, environment)
    log.info("Picked up pipeline", pipeline=pipeline_path.parent.name)
    if steps:
        component_names = steps
        log.debug(
            "KPOPS_PIPELINE_STEPS is defined",
            steps=component_names,
            filter_type=filter_type.value,
        )

        predicate = filter_type.create_default_step_names_filter_predicate(
            component_names
        )
        pipeline.filter(predicate)
        log.info("Filtered pipeline", steps=pipeline.step_names)
    return pipeline


def manifest_deploy(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path | None = None,
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    verbose: bool = True,
    operation_mode: OperationMode = OperationMode.MANIFEST,
) -> Iterator[tuple[KubernetesManifest, ...]]:
    pipeline = generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
        operation_mode=operation_mode,
    )
    return pipeline.manifest_deploy()


def manifest_destroy(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path | None = None,
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    verbose: bool = True,
    operation_mode: OperationMode = OperationMode.MANIFEST,
) -> Iterator[tuple[KubernetesManifest, ...]]:
    pipeline = generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
        operation_mode=operation_mode,
    )
    return pipeline.manifest_destroy()


def manifest_reset(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path | None = None,
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    verbose: bool = True,
    operation_mode: OperationMode = OperationMode.MANIFEST,
) -> Iterator[tuple[KubernetesManifest, ...]]:
    pipeline = generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
        operation_mode=operation_mode,
    )
    return pipeline.manifest_reset()


def manifest_clean(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path | None = None,
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    verbose: bool = True,
    operation_mode: OperationMode = OperationMode.MANIFEST,
) -> Iterator[tuple[KubernetesManifest, ...]]:
    pipeline = generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
        operation_mode=operation_mode,
    )
    return pipeline.manifest_clean()


def deploy(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path | None = None,
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    dry_run: bool = True,
    verbose: bool = True,
    parallel: bool = False,
) -> None:
    """Deploy pipeline steps.

    :param pipeline_path: Path to pipeline definition yaml file.
    :param dotenv: Paths to dotenv files.
    :param config: Path to the dir containing config.yaml files.
    :param steps: Set of steps (components) to apply the command on.
    :param filter_type: Whether `steps` should include/exclude the steps.
    :param dry_run: Whether to dry run the command or execute it.
    :param environment: The environment to generate and deploy the pipeline to.
    :param verbose: Enable verbose printing.
    :param parallel: Enable or disable parallel execution of pipeline steps.
    """
    pipeline = generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )
    asyncio.run(pipeline.deploy(dry_run, parallel))


def destroy(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path | None = None,
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    dry_run: bool = True,
    verbose: bool = True,
    parallel: bool = False,
) -> None:
    """Destroy pipeline steps.

    :param pipeline_path: Path to pipeline definition yaml file.
    :param dotenv: Paths to dotenv files.
    :param config: Path to the dir containing config.yaml files.
    :param steps: Set of steps (components) to apply the command on.
    :param filter_type: Whether `steps` should include/exclude the steps.
    :param dry_run: Whether to dry run the command or execute it.
    :param environment: The environment to generate and deploy the pipeline to.
    :param verbose: Enable verbose printing.
    :param parallel: Enable or disable parallel execution of pipeline steps.
    """
    pipeline = generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )
    asyncio.run(pipeline.destroy(dry_run, parallel))


def reset(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path | None = None,
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    dry_run: bool = True,
    verbose: bool = True,
    parallel: bool = False,
) -> None:
    """Reset pipeline steps.

    :param pipeline_path: Path to pipeline definition yaml file.
    :param dotenv: Paths to dotenv files.
    :param config: Path to the dir containing config.yaml files.
    :param steps: Set of steps (components) to apply the command on.
    :param filter_type: Whether `steps` should include/exclude the steps.
    :param dry_run: Whether to dry run the command or execute it.
    :param environment: The environment to generate and deploy the pipeline to.
    :param verbose: Enable verbose printing.
    :param parallel: Enable or disable parallel execution of pipeline steps.
    """
    pipeline = generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )
    asyncio.run(pipeline.reset(dry_run, parallel))


def clean(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path | None = None,
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    dry_run: bool = True,
    verbose: bool = True,
    parallel: bool = False,
) -> None:
    """Clean pipeline steps.

    :param pipeline_path: Path to pipeline definition yaml file.
    :param dotenv: Paths to dotenv files.
    :param config: Path to the dir containing config.yaml files.
    :param steps: Set of steps (components) to apply the command on.
    :param filter_type: Whether `steps` should include/exclude the steps.
    :param dry_run: Whether to dry run the command or execute it.
    :param environment: The environment to generate and deploy the pipeline to.
    :param verbose: Enable verbose printing.
    :param parallel: Enable or disable parallel execution of pipeline steps.
    """
    pipeline = generate(
        pipeline_path=pipeline_path,
        dotenv=dotenv,
        config=config,
        steps=steps,
        filter_type=filter_type,
        environment=environment,
        verbose=verbose,
    )
    asyncio.run(pipeline.clean(dry_run, parallel))


def init(
    path: Path,
    config_include_optional: bool = False,
) -> None:
    """Initiate a default empty project.

    :param path: Directory in which the project should be initiated.
    :param config_include_optional: Whether to include non-required settings
        in the generated config file.
    """
    if not path.exists():
        path.mkdir(parents=False)
    elif next(path.iterdir(), False):
        log.warning("Please provide a path to an empty directory.")
        return
    init_project(path, config_include_optional)


def _create_pipeline(
    pipeline_path: Path,
    kpops_config: KpopsConfig,
    environment: str | None,
) -> Pipeline:
    """Create pipeline.

    :param pipeline_path: Path to pipeline definition yaml file.
    :param config: KPOps Config.
    :param environment: The environment to generate and deploy the pipeline to.
    :return: Created `Pipeline` object.
    """
    registry = Registry()
    registry.discover_components()

    handlers = _setup_handlers(kpops_config)
    parser = PipelineGenerator(kpops_config, registry, handlers)
    return parser.load_yaml(pipeline_path, environment)


def _setup_handlers(config: KpopsConfig) -> ComponentHandlers:
    """Set up handlers for a component.

    :param config: KPOps config.
    :return: Handlers for a component.
    """
    schema_handler = SchemaHandler.load_schema_handler(config)
    connector_handler = KafkaConnectHandler.from_kpops_config(config)
    kafka_rest = KafkaRest(config.kafka_rest)
    topic_handler = TopicHandler(kafka_rest)

    return ComponentHandlers(schema_handler, connector_handler, topic_handler)
