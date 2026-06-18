from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from kpops.api.logs import log, log_action
from kpops.api.options import FilterType
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
    KafkaConnectHandler,
)
from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.topic.handler import TopicHandler
from kpops.component_handlers.topic.proxy_wrapper import ProxyWrapper
from kpops.config import KpopsConfig
from kpops.core.operation import OperationMode
from kpops.core.registry import Registry
from kpops.manifests.kubernetes import KubernetesManifest
from kpops.pipeline import (
    Pipeline,
    PipelineGenerator,
)
from kpops.utils.cli_commands import init_project

if TYPE_CHECKING:
    from kpops.components.base_components.pipeline_component import PipelineComponent
    from kpops.config import KpopsConfig


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
    log.info(f"Picked up pipeline '{pipeline_path.parent.name}'")
    if steps:
        component_names = steps
        log.debug(
            f"KPOPS_PIPELINE_STEPS is defined with values: {component_names} and filter type of {filter_type.value}"
        )

        predicate = filter_type.create_default_step_names_filter_predicate(
            component_names
        )
        pipeline.filter(predicate)
        log.info(f"Filtered pipeline:\n{pipeline.step_names}")
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
    for component in pipeline.components:
        resource = component.manifest_deploy()
        yield resource


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
    for component in pipeline.components:
        resource = component.manifest_destroy()
        yield resource


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
    for component in pipeline.components:
        resource = component.manifest_reset()
        yield resource


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
    for component in pipeline.components:
        resource = component.manifest_clean()
        yield resource


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
):
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
):
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
):
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

    async def reset_runner(component: PipelineComponent):
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
):
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

    async def clean_runner(component: PipelineComponent):
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


def init(
    path: Path,
    config_include_optional: bool = False,
):
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
    proxy_wrapper = ProxyWrapper(config.kafka_rest)
    topic_handler = TopicHandler(proxy_wrapper)

    return ComponentHandlers(schema_handler, connector_handler, topic_handler)
