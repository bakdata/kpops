from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import kpops
from kpops.api.logs import log, log_action
from kpops.api.options import FilterType
from kpops.api.registry import Registry
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
    KafkaConnectHandler,
)
from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.topic.handler import TopicHandler
from kpops.component_handlers.topic.proxy_wrapper import ProxyWrapper
from kpops.config import KpopsConfig
from kpops.pipeline import (
    Pipeline,
    PipelineGenerator,
)
from kpops.utils.cli_commands import init_project

if TYPE_CHECKING:
    from kpops.components import PipelineComponent
    from kpops.components.base_components.models.resource import Resource
    from kpops.config import KpopsConfig


def generate(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path = Path(),
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    verbose: bool = False,
) -> Pipeline:
    kpops_config = KpopsConfig.create(
        config,
        dotenv,
        environment,
        verbose,
    )
    pipeline = create_pipeline(pipeline_path, kpops_config, environment)
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


def manifest(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path = Path(),
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    verbose: bool = False,
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
    return resources


def deploy(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path = Path(),
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    dry_run: bool = True,
    verbose: bool = True,
    parallel: bool = False,
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


def destroy(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path = Path(),
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    dry_run: bool = True,
    verbose: bool = True,
    parallel: bool = False,
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


def reset(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path = Path(),
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    dry_run: bool = True,
    verbose: bool = True,
    parallel: bool = False,
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


def clean(
    pipeline_path: Path,
    dotenv: list[Path] | None = None,
    config: Path = Path(),
    steps: set[str] | None = None,
    filter_type: FilterType = FilterType.INCLUDE,
    environment: str | None = None,
    dry_run: bool = True,
    verbose: bool = True,
    parallel: bool = False,
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
    config_include_opt: bool = False,
):
    if not path.exists():
        path.mkdir(parents=False)
    elif next(path.iterdir(), False):
        log.warning("Please provide a path to an empty directory.")
        return
    init_project(path, config_include_opt)


def create_pipeline(
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
