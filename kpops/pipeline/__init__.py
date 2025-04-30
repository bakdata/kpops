from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeAlias

import networkx as nx
import yaml
from pydantic import (
    SerializeAsAny,
    computed_field,
)

from kpops.component_handlers import ComponentHandlers
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.core.exception import ParsingException, ValidationError
from kpops.core.registry import Registry
from kpops.utils.dict_ops import update_nested_pair
from kpops.utils.environment import ENV, PIPELINE_PATH
from kpops.utils.yaml import CustomSafeDumper, load_yaml_file

if TYPE_CHECKING:
    from collections.abc import Awaitable, Coroutine, Iterator
    from pathlib import Path

    from kpops.config import KpopsConfig

log = logging.getLogger("PipelineGenerator")

ComponentFilterPredicate: TypeAlias = Callable[[PipelineComponent], bool]


@dataclass
class Pipeline:
    """Pipeline representation."""

    _component_index: dict[str, PipelineComponent] = field(default_factory=dict)
    _graph: nx.DiGraph[str] = field(default_factory=nx.DiGraph)

    @property
    def step_names(self) -> list[str]:
        return [step.name for step in self.components]

    @computed_field(title="Components")
    @property
    def components(self) -> list[SerializeAsAny[PipelineComponent]]:
        return list(self._component_index.values())

    @property
    def last(self) -> PipelineComponent:
        return self.components[-1]

    def add(self, component: PipelineComponent) -> None:
        if self._component_index.get(component.id) is not None:
            msg = (
                f"Pipeline steps must have unique id, '{component.id}' already exists."
            )
            raise ValidationError(msg)
        self._component_index[component.id] = component
        self.__add_to_graph(component)

    def remove(self, component_id: str) -> None:
        self._component_index.pop(component_id)

    def get(self, component_id: str) -> PipelineComponent | None:
        return self._component_index.get(component_id)

    def find(self, predicate: ComponentFilterPredicate) -> Iterator[PipelineComponent]:
        """Find pipeline components matching a custom predicate.

        :param predicate: Filter function,
            returns boolean value whether the component should be kept or removed
        :returns: Iterator of components matching the predicate
        """
        for component in self.components:
            if predicate(component):
                yield component

    def filter(self, predicate: ComponentFilterPredicate) -> None:
        """Filter pipeline components using a custom predicate.

        :param predicate: Filter function,
            returns boolean value whether the component should be kept or removed
        """
        for component in self.components:
            # filter out components not matching the predicate
            if not predicate(component):
                self.remove(component.id)

    def validate(self) -> None:
        self.__validate_graph()

    def generate(self) -> list[dict[str, Any]]:
        return [component.generate() for component in self.components]

    def to_yaml(self) -> str:
        return yaml.dump(self.generate(), sort_keys=False, Dumper=CustomSafeDumper)

    def build_execution_graph(
        self,
        runner: Callable[[PipelineComponent], Coroutine[Any, Any, None]],
        /,
        reverse: bool = False,
    ) -> Awaitable[None]:
        async def run_parallel_tasks(
            coroutines: list[Coroutine[Any, Any, None]],
        ) -> None:
            tasks: list[asyncio.Task[None]] = []
            for coro in coroutines:
                tasks.append(asyncio.create_task(coro))
            await asyncio.gather(*tasks)

        async def run_graph_tasks(pending_tasks: list[Awaitable[None]]) -> None:
            for pending_task in pending_tasks:
                await pending_task

        graph: nx.DiGraph[str] = self._graph.copy()

        # We add an extra node to the graph, connecting all the leaf nodes to it
        # in that way we make this node the root of the graph, avoiding backtracking
        root_node = "root_node_bfs"
        graph.add_node(root_node)

        for node in graph:
            predecessors = list(graph.predecessors(node))
            if not predecessors:
                graph.add_edge(root_node, node)

        layers_graph: list[list[str]] = list(nx.bfs_layers(graph, root_node))

        sorted_tasks: list[Awaitable[None]] = []
        for layer in layers_graph[1:]:
            if parallel_tasks := self.__get_parallel_tasks_from(layer, runner):
                sorted_tasks.append(run_parallel_tasks(parallel_tasks))

        if reverse:
            sorted_tasks.reverse()

        return run_graph_tasks(sorted_tasks)

    def __getitem__(self, component_id: str) -> PipelineComponent:
        try:
            return self._component_index[component_id]
        except KeyError as exc:
            msg = f"Component {component_id} not found"
            raise ValueError(msg) from exc

    def __bool__(self) -> bool:
        return bool(self._component_index)

    def __iter__(self) -> Iterator[PipelineComponent]:
        yield from self._component_index.values()

    def __len__(self) -> int:
        return len(self.components)

    def __add_to_graph(self, component: PipelineComponent):
        self._graph.add_node(component.id)

        for input_topic in component.inputs:
            self.__add_input(input_topic.id, component.id)

        for output_topic in component.outputs:
            self.__add_output(output_topic.id, component.id)

    def __add_output(self, topic_id: str, source: str) -> None:
        self._graph.add_node(topic_id)
        self._graph.add_edge(source, topic_id)

    def __add_input(self, topic_id: str, target: str) -> None:
        self._graph.add_node(topic_id)
        self._graph.add_edge(topic_id, target)

    def __get_parallel_tasks_from(
        self,
        layer: list[str],
        runner: Callable[[PipelineComponent], Coroutine[Any, Any, None]],
    ) -> list[Coroutine[Any, Any, None]]:
        def gen_parallel_tasks():
            for node_in_layer in layer:
                # check if component, skip topics
                if (component := self._component_index.get(node_in_layer)) is not None:
                    yield runner(component)

        return list(gen_parallel_tasks())

    def __validate_graph(self) -> None:
        if not nx.is_directed_acyclic_graph(self._graph):
            msg = "Pipeline is not a valid DAG."
            raise ValueError(msg)


def create_env_components_index(
    environment_components: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Create an index for all registered components in the project.

    :param environment_components: List of all components to be included
    :return: component index
    """
    index: dict[str, dict[str, Any]] = {}
    for component in environment_components:
        if "type" not in component or "name" not in component:
            msg = "To override components per environment, every component should at least have a type and a name."
            raise ValueError(msg)
        index[component["name"]] = component  # TODO: id
    return index


@dataclass
class PipelineGenerator:
    config: KpopsConfig
    registry: Registry
    handlers: ComponentHandlers
    pipeline: Pipeline = field(init=False, default_factory=Pipeline)
    env_components_index: dict[str, dict[str, Any]] = field(
        init=False, default_factory=dict
    )

    def parse(
        self,
        components: list[dict[str, Any]],
        environment_components: list[dict[str, Any]],
    ) -> Pipeline:
        """Parse pipeline from sequence of component dictionaries.

        :param components: List of components
        :param environment_components: List of environment-specific components
        :returns: Initialized pipeline object
        """
        self.env_components_index = create_env_components_index(environment_components)
        self.parse_components(components)
        self.pipeline.validate()
        return self.pipeline

    def load_yaml(self, path: Path, environment: str | None) -> Pipeline:
        """Load pipeline definition from YAML file.

        The file is often named ``pipeline.yaml``

        :param path: Path to pipeline definition yaml file
        :param environment: Environment name
        :raises TypeError: The pipeline definition should contain a list of components
        :raises TypeError: The env-specific pipeline definition should contain a list of components
        :returns: Initialized pipeline object
        """
        ENV.clear()
        PipelineGenerator.set_pipeline_name_env_vars(
            self.config.pipeline_base_dir, path
        )
        PipelineGenerator.set_environment_name(environment)
        PipelineGenerator.set_pipeline_path(path)

        main_content = load_yaml_file(path, substitution=ENV)
        if not isinstance(main_content, list):
            msg = f"The pipeline definition {path} should contain a list of components"
            raise TypeError(msg)
        env_content = []
        if (
            environment
            and (
                env_file := PipelineGenerator.pipeline_filename_environment(
                    path, environment
                )
            ).exists()
        ):
            env_content = load_yaml_file(env_file, substitution=ENV)
            if not isinstance(env_content, list):
                msg = f"The pipeline definition {env_file} should contain a list of components"
                raise TypeError(msg)

        return self.parse(main_content, env_content)  # pyright: ignore[reportUnknownArgumentType]

    def parse_components(self, components: list[dict[str, Any]]) -> None:
        """Instantiate, enrich and inflate a list of components.

        :param components: List of components
        :raises ValueError: Every component must have a type defined
        :raises ParsingException: Error enriching component
        :raises ParsingException: All undefined exceptions
        """
        for component_data in components:
            try:
                try:
                    component_type: str = component_data["type"]
                except KeyError as ke:
                    msg = "Every component must have a type defined, this component does not have one."
                    raise ValueError(msg) from ke
                component_class = self.registry[component_type]
                self.apply_component(component_class, component_data)
            except Exception as ex:
                if "name" in component_data:
                    msg = f"Error enriching {component_data['type']} component {component_data['name']}"
                    raise ParsingException(msg) from ex
                else:
                    raise ParsingException from ex

    def apply_component(
        self, component_class: type[PipelineComponent], component_data: dict[str, Any]
    ) -> None:
        """Instantiate, enrich and inflate pipeline component.

        Applies input topics according to FromSection.

        :param component_class: Type of pipeline component
        :param component_data: Arguments for instantiation of pipeline component
        """
        component = component_class(**component_data)
        component = self.enrich_component_with_env(component)
        # inflate & enrich components
        for inflated_component in component.inflate():  # TODO: recursively
            if inflated_component.from_:
                # read from specified components
                for (
                    original_from_component_id,
                    from_topic,
                ) in inflated_component.from_.components.items():
                    original_from_component = self.pipeline[original_from_component_id]

                    inflated_from_component = original_from_component.inflate()[-1]
                    resolved_from_component = self.pipeline[inflated_from_component.id]

                    inflated_component.weave_from_topics(
                        resolved_from_component.to, from_topic
                    )
            elif self.pipeline:
                # read from previous component
                prev_component = self.pipeline.last
                inflated_component.weave_from_topics(prev_component.to)
            self.pipeline.add(inflated_component)

    def enrich_component_with_env(
        self, component: PipelineComponent
    ) -> PipelineComponent:
        """Enrich a pipeline component with env-specific config.

        :param component: Component to be enriched
        :returns: Enriched component
        """
        env_component = self.env_components_index.get(component.name)
        if not env_component:
            return component
        env_component_as_dict = update_nested_pair(
            env_component,
            component.model_dump(mode="json", by_alias=True),
        )

        return component.__class__(**env_component_as_dict)

    @staticmethod
    def pipeline_filename_environment(pipeline_path: Path, environment: str) -> Path:
        """Add the environment name from the KpopsConfig to the pipeline.yaml path.

        :param pipeline_path: Path to pipeline.yaml file
        :param environment: Environment name
        :returns: An absolute path to the pipeline_<environment>.yaml
        """
        return pipeline_path.with_stem(f"{pipeline_path.stem}_{environment}")

    @staticmethod
    def set_pipeline_name_env_vars(
        pipeline_base_dir: Path, pipeline_path: Path
    ) -> None:
        """Set the environment variable pipeline_name relative to the given base_dir.

        Moreover, for each sub-path an environment variable is set.
        For example, for a given path ./data/v1/dev/pipeline.yaml the pipeline_name would be
        set to data-v1-dev. Then the sub environment variables are set:

        .. code-block:: python
            pipeline.name_0 = data
            pipeline.name_1 = v1
            pipeline.name_2 = dev

        :param pipeline_base_dir: Base directory to the pipeline files
        :param pipeline_path: Path to pipeline.yaml file
        """
        path_without_file = (
            pipeline_path.resolve().relative_to(pipeline_base_dir.resolve()).parts[:-1]
        )
        if not path_without_file:
            msg = "The pipeline-base-dir should not equal the pipeline-path"
            raise ValueError(msg)
        pipeline_name = "-".join(path_without_file)
        parent_pipeline_name = "-".join(path_without_file[:-1])
        ENV["pipeline.name"] = pipeline_name
        ENV["pipeline.parent.name"] = parent_pipeline_name
        for level, parent in enumerate(path_without_file):
            ENV[f"pipeline.name_{level}"] = parent

    @staticmethod
    def set_environment_name(environment: str | None) -> None:
        """Set the environment name.

        It will be used to find environment-specific pipeline definitions,
        defaults and configs.

        :param environment: Environment name
        """
        if environment is not None:
            ENV["environment"] = environment

    @staticmethod
    def set_pipeline_path(path: Path):
        ENV[PIPELINE_PATH] = str(path.resolve())
