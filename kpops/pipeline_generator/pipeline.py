from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path

import yaml
from pydantic import BaseModel
from rich.console import Console
from rich.syntax import Syntax

from kpops.cli.pipeline_config import PipelineConfig
from kpops.cli.registry import Registry
from kpops.component_handlers import ComponentHandlers
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.dict_ops import generate_substitution, update_nested_pair
from kpops.utils.environment import ENV
from kpops.utils.yaml_loading import load_yaml_file, substitute, substitute_nested

log = logging.getLogger("PipelineGenerator")


class ParsingException(Exception):
    pass


class PipelineComponents(BaseModel):
    """Stores the pipeline components"""

    components: list[PipelineComponent] = []

    @property
    def last(self) -> PipelineComponent:
        return self.components[-1]

    def find(self, component_name: str) -> PipelineComponent:
        for component in self.components:
            if component_name == component.name.removeprefix(component.prefix):
                return component
        raise ValueError(f"Component {component_name} not found")

    def add(self, component: PipelineComponent) -> None:
        self._populate_component_name(component)
        self.components.append(component)

    def __bool__(self) -> bool:
        return bool(self.components)

    def __iter__(self) -> Iterator[PipelineComponent]:
        return iter(self.components)

    @staticmethod
    def _populate_component_name(component: PipelineComponent) -> None:
        component.name = component.prefix + component.name
        with suppress(
            AttributeError  # Some components like Kafka Connect do not have a name_override attribute
        ):
            if component.app and getattr(component.app, "name_override") is None:
                setattr(component.app, "name_override", component.name)


def create_env_components_index(
    environment_components: list[dict],
) -> dict[str, dict]:
    """Create an index for all registered components in the project

    :param environment_components: List of all components to be included
    :type environment_components: list[dict]
    :return: component index
    :rtype: dict[str, dict]
    """
    index: dict[str, dict] = {}
    for component in environment_components:
        if "type" not in component or "name" not in component:
            raise ValueError(
                "To override components per environment, every component should at least have a type and a name."
            )
        index[component["name"]] = component
    return index


class Pipeline:
    def __init__(
        self,
        component_list: list[dict],
        environment_components: list[dict],
        registry: Registry,
        config: PipelineConfig,
        handlers: ComponentHandlers,
    ) -> None:
        self.components: PipelineComponents = PipelineComponents()
        self.handlers = handlers
        self.config = config
        self.registry = registry
        self.env_components_index = create_env_components_index(environment_components)
        self.parse_components(component_list)

    @classmethod
    def load_from_yaml(
        cls,
        base_dir: Path,
        path: Path,
        registry: Registry,
        config: PipelineConfig,
        handlers: ComponentHandlers,
    ) -> Pipeline:
        """Load pipeline definition from yaml

        The file is often named ``pipeline.yaml``

        :param base_dir: Base directory to the pipelines (default is current working directory)
        :type base_dir: Path
        :param path: Path to pipeline definition yaml file
        :type path: Path
        :param registry: Pipeline components registry
        :type registry: Registry
        :param config: Pipeline config
        :type config: PipelineConfig
        :param handlers: Component handlers
        :type handlers: ComponentHandlers
        :raises TypeError: The pipeline definition should contain a list of components
        :raises TypeError: The env-specific pipeline definition should contain a list of components
        :returns: Initialized pipeline object
        :rtype: Pipeline
        """
        Pipeline.set_pipeline_name_env_vars(base_dir, path)

        main_content = load_yaml_file(path, substitution=ENV)
        if not isinstance(main_content, list):
            raise TypeError(
                f"The pipeline definition {path} should contain a list of components"
            )
        env_content = []
        if (env_file := Pipeline.pipeline_filename_environment(path, config)).exists():
            env_content = load_yaml_file(env_file, substitution=ENV)
            if not isinstance(env_content, list):
                raise TypeError(
                    f"The pipeline definition {env_file} should contain a list of components"
                )

        pipeline = cls(main_content, env_content, registry, config, handlers)
        return pipeline

    def parse_components(self, component_list: list[dict]) -> None:
        """Instantiate, enrich and inflate a list of components

        :param component_list: List of components
        :type component_list: list[dict]
        :raises ValueError: Every component must have a type defined
        :raises ParsingException: Error enriching component
        :raises ParsingException: All undefined exceptions
        """
        for component_data in component_list:
            try:
                try:
                    component_type: str = component_data["type"]
                except KeyError:
                    raise ValueError(
                        "Every component must have a type defined, this component does not have one."
                    )
                component_class = self.registry[component_type]
                self.apply_component(component_class, component_data)
            except Exception as ex:
                if "name" in component_data:
                    raise ParsingException(
                        f"Error enriching {component_data['type']} component {component_data['name']}"
                    ) from ex
                else:
                    raise ParsingException() from ex

    def apply_component(
        self, component_class: type[PipelineComponent], component_data: dict
    ) -> None:
        """Instantiate, enrich and inflate pipeline component.

        Applies input topics according to FromSection.

        :param component_class: Type of pipeline component
        :type component_class: type[PipelineComponent]
        :param component_data: Arguments for instantiation of pipeline component
        :type component_data: dict
        """
        component = component_class(
            config=self.config,
            handlers=self.handlers,
            validate=False,
            **component_data,
        )
        component = self.enrich_component(component)

        # inflate & enrich components
        for inflated_component in component.inflate():  # TODO: recursively
            enriched_component = self.enrich_component(inflated_component)
            if enriched_component.from_:
                # read from specified components
                for (
                    original_from_component_name,
                    from_topic,
                ) in enriched_component.from_.components.items():
                    original_from_component = self.components.find(
                        original_from_component_name
                    )
                    inflated_from_component = original_from_component.inflate()[-1]
                    if inflated_from_component is not original_from_component:
                        resolved_from_component_name = inflated_from_component.name
                    else:
                        resolved_from_component_name = original_from_component_name
                    resolved_from_component = self.components.find(
                        resolved_from_component_name
                    )
                    enriched_component.weave_from_topics(
                        resolved_from_component.to, from_topic
                    )
            elif self.components:
                # read from previous component
                prev_component = self.components.last
                enriched_component.weave_from_topics(prev_component.to)
            self.components.add(enriched_component)

    def enrich_component(
        self,
        component: PipelineComponent,
    ) -> PipelineComponent:
        """Enrich a pipeline component with env-specific config and substitute variables

        :param component: Component to be enriched
        :type component: PipelineComponent
        :returns: Enriched component
        :rtype: PipelineComponent
        """
        component.validate_ = True
        env_component_as_dict = update_nested_pair(
            self.env_components_index.get(component.name, {}),
            # HACK: Pydantic .dict() doesn't create jsonable dict
            json.loads(component.json(by_alias=True)),
        )

        component_data = self.substitute_in_component(env_component_as_dict)

        component_class = type(component)
        return component_class(
            enrich=False,
            config=self.config,
            handlers=self.handlers,
            **component_data,
        )

    def print_yaml(self, substitution: dict | None = None) -> None:
        """Print the generated pipeline definition

        :param substitution: Substitution dictionary, defaults to None
        :type substitution: dict | None, optional
        """
        syntax = Syntax(
            substitute(str(self), substitution),
            "yaml",
            background_color="default",
            theme="ansi_dark",
        )
        Console(
            width=1000  # HACK: overwrite console width to avoid truncating output
        ).print(syntax)

    def __iter__(self) -> Iterator[PipelineComponent]:
        return iter(self.components)

    def __str__(self) -> str:
        return yaml.dump(
            json.loads(  # HACK: serialize types on Pydantic model export, which are not serialized by .dict(); e.g. pathlib.Path
                self.components.json(exclude_none=True, by_alias=True)
            )
        )

    def substitute_in_component(self, component_as_dict: dict) -> dict:
        """Substitute all $-placeholders in a component in dict representation

        :param component_as_dict: Component represented as dict
        :type component_as_dict: dict
        :return: Updated component
        :rtype: dict
        """
        config = self.config
        # Leftover variables that were previously introduced in the component by the substitution
        # functions, still hardcoded, because of their names.
        # TODO: Get rid of them
        substitution_hardcoded = {
            "error_topic_name": config.topic_name_config.default_error_topic_name,
            "output_topic_name": config.topic_name_config.default_output_topic_name,
        }
        component_substitution = generate_substitution(
            component_as_dict,
            "component",
            substitution_hardcoded,
        )
        substitution = generate_substitution(
            json.loads(config.json()), existing_substitution=component_substitution
        )

        return json.loads(
            substitute_nested(
                json.dumps(component_as_dict),
                **update_nested_pair(substitution, ENV),
            )
        )

    @staticmethod
    def pipeline_filename_environment(path: Path, config: PipelineConfig) -> Path:
        """Add the environment name from the PipelineConfig to the pipeline.yaml path

        :param path: Path to pipeline.yaml file
        :param config: The PipelineConfig
        :returns: An absolute path to the pipeline_<environment>.yaml
        """
        return path.with_stem(f"{path.stem}_{config.environment}")

    @staticmethod
    def set_pipeline_name_env_vars(base_dir: Path, path: Path) -> None:
        """Set the environment variable pipeline_name relative to the given base_dir.

        Moreover, for each sub-path an environment variable is set.
        For example, for a given path ./data/v1/dev/pipeline.yaml the pipeline_name would be
        set to data-v1-dev. Then the sub environment variables are set:

        pipeline_name_0 = data
        pipeline_name_1 = v1
        pipeline_name_2 = dev

        :param base_dir: Base directory to the pipeline files
        :type base_dir: Path
        :param path: Path to pipeline.yaml file
        :type path: Path
        """
        path_without_file = path.resolve().relative_to(base_dir.resolve()).parts[:-1]
        if not path_without_file:
            raise ValueError("The pipeline-base-dir should not equal the pipeline-path")
        pipeline_name = "-".join(path_without_file)
        ENV["pipeline_name"] = pipeline_name
        for level, parent in enumerate(path_without_file):
            ENV[f"pipeline_name_{level}"] = parent
