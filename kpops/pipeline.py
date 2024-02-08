from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeAlias

import networkx as nx
import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    SerializeAsAny,
    computed_field,
)

from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.dict_ops import update_nested_pair
from kpops.utils.environment import ENV
from kpops.utils.yaml import load_yaml_file

if TYPE_CHECKING:
    from collections.abc import Awaitable, Coroutine, Iterator
    from pathlib import Path

    from kpops.cli.registry import Registry
    from kpops.component_handlers import ComponentHandlers
    from kpops.config import KpopsConfig

log = logging.getLogger("PipelineGenerator")


class ParsingException(Exception):
    pass


class ValidationError(Exception):
    pass


ComponentFilterPredicate: TypeAlias = Callable[[PipelineComponent], bool]


class Pipeline(BaseModel):
    """Pipeline representation."""

    _component_index: dict[str, PipelineComponent] = {}
    _graph: nx.DiGraph = nx.DiGraph()

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
        self._component_index.get(component_id)

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

    def to_yaml(self) -> str:
        return yaml.dump(
            self.model_dump(mode="json", by_alias=True, exclude_none=True)["components"]
        )

    def build_execution_graph(
        self, runner: Callable[[PipelineComponent], Coroutine], /, reverse: bool = False
    ) -> Awaitable:
        async def run_parallel_tasks(coroutines: list[Coroutine]) -> None:
            tasks = []
            for coro in coroutines:
                tasks.append(asyncio.create_task(coro))
            await asyncio.gather(*tasks)

        async def run_graph_tasks(pending_tasks: list[Awaitable]) -> None:
            for pending_task in pending_tasks:
                await pending_task

        graph: nx.DiGraph = self._graph.copy()  # pyright: ignore[reportAssignmentType, reportGeneralTypeIssues] imprecise type hint in networkx

        # We add an extra node to the graph, connecting all the leaf nodes to it
        # in that way we make this node the root of the graph, avoiding backtracking
        root_node = "root_node_bfs"
        graph.add_node(root_node)

        for node in graph:
            predecessors = list(graph.predecessors(node))
            if not predecessors:
                graph.add_edge(root_node, node)

        layers_graph: list[list[str]] = list(nx.bfs_layers(graph, root_node))

        sorted_tasks = []
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
            self.__add_input(input_topic, component.id)

        for output_topic in component.outputs:
            self.__add_output(output_topic, component.id)

    def __add_output(self, topic_id: str, source: str) -> None:
        self._graph.add_node(topic_id)
        self._graph.add_edge(source, topic_id)

    def __add_input(self, topic_id: str, target: str) -> None:
        self._graph.add_node(topic_id)
        self._graph.add_edge(topic_id, target)

    def __get_parallel_tasks_from(
        self, layer: list[str], runner: Callable[[PipelineComponent], Coroutine]
    ) -> list[Coroutine]:
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

    def parse(
        self,
        components: list[dict],
        environment_components: list[dict],
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
        PipelineGenerator.set_pipeline_name_env_vars(
            self.config.pipeline_base_dir, path
        )
        PipelineGenerator.set_environment_name(environment)

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

        return self.parse(main_content, env_content)

    def parse_components(self, components: list[dict]) -> None:
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
            except Exception as ex:  # noqa: BLE001
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

        def is_name(name: str) -> ComponentFilterPredicate:
            def predicate(component: PipelineComponent) -> bool:
                return component.name == name

            return predicate

        # NOTE: temporary until we can just get components by id
        # performance improvement
        def find(component_name: str) -> PipelineComponent:
            """Find component in pipeline by name.

            :param component_name: Name of component to get
            :returns: Component matching the name
            :raises ValueError: Component not found
            """
            try:
                return next(self.pipeline.find(is_name(component_name)))
            except StopIteration as exc:
                msg = f"Component {component_name} not found"
                raise ValueError(msg) from exc

        component = component_class(
            config=self.config,
            handlers=self.handlers,
            **component_data,
        )
        component = self.enrich_component_with_env(component)
        # inflate & enrich components
        for inflated_component in component.inflate():  # TODO: recursively
            if inflated_component.from_:
                # read from specified components
                for (
                    original_from_component_name,
                    from_topic,
                ) in inflated_component.from_.components.items():
                    original_from_component = find(original_from_component_name)

                    inflated_from_component = original_from_component.inflate()[-1]
                    resolved_from_component = find(inflated_from_component.name)

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

        return component.__class__(
            config=self.config,
            handlers=self.handlers,
            **env_component_as_dict,
        )

    @staticmethod
    def pipeline_filename_environment(pipeline_path: Path, environment: str) -> Path:
        """Add the environment name from the KpopsConfig to the pipeline.yaml path.

        :param pipeline_path: Path to pipeline.yaml file
        :param environment: Environment name
        :returns: An absolute path to the pipeline_<environment>.yaml
        """
        return pipeline_path.with_stem(f"{pipeline_path.stem}_{environment}")

    @staticmethod
    def set_pipeline_name_env_vars(base_dir: Path, path: Path) -> None:
        """Set the environment variable pipeline_name relative to the given base_dir.

        Moreover, for each sub-path an environment variable is set.
        For example, for a given path ./data/v1/dev/pipeline.yaml the pipeline_name would be
        set to data-v1-dev. Then the sub environment variables are set:

        .. code-block:: python
            pipeline.name_0 = data
            pipeline.name_1 = v1
            pipeline.name_2 = dev

        :param base_dir: Base directory to the pipeline files
        :param path: Path to pipeline.yaml file
        """
        path_without_file = path.resolve().relative_to(base_dir.resolve()).parts[:-1]
        if not path_without_file:
            msg = "The pipeline-base-dir should not equal the pipeline-path"
            raise ValueError(msg)
        pipeline_name = "-".join(path_without_file)
        ENV["pipeline.name"] = pipeline_name
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
