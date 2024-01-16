from __future__ import annotations

import json
import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import yaml
from pydantic import Field, RootModel, SerializeAsAny

from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.dict_ops import generate_substitution, update_nested_pair
from kpops.utils.environment import ENV
from kpops.utils.types import JsonType
from kpops.utils.yaml import load_yaml_file, substitute_nested

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from kpops.cli.registry import Registry
    from kpops.component_handlers import ComponentHandlers
    from kpops.config import KpopsConfig

log = logging.getLogger("PipelineGenerator")


class ParsingException(Exception):
    pass


class ValidationError(Exception):
    pass


class Pipeline(RootModel):
    """Pipeline representation."""

    root: list[SerializeAsAny[PipelineComponent]] = Field(
        default=[], title="Components"
    )

    @property
    def last(self) -> PipelineComponent:
        return self.root[-1]

    def find(self, component_name: str) -> PipelineComponent:
        for component in self.root:
            if component_name == component.name:
                return component
        msg = f"Component {component_name} not found"
        raise ValueError(msg)

    def add(self, component: PipelineComponent) -> None:
        self.root.append(component)

    def __bool__(self) -> bool:
        return bool(self.root)

    def __iter__(self) -> Iterator[PipelineComponent]:
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def to_yaml(self) -> str:
        return yaml.dump(self.model_dump(mode="json", by_alias=True, exclude_none=True))

    def validate(self) -> None:
        self.validate_unique_names()

    def validate_unique_names(self) -> None:
        step_names = [component.full_name for component in self.root]
        duplicates = [name for name, count in Counter(step_names).items() if count > 1]
        if duplicates:
            msg = f"step names should be unique. duplicate step names: {', '.join(duplicates)}"
            raise ValidationError(msg)


def create_env_components_index(
    environment_components: list[dict],
) -> dict[str, dict]:
    """Create an index for all registered components in the project.

    :param environment_components: List of all components to be included
    :return: component index
    """
    index: dict[str, dict] = {}
    for component in environment_components:
        if "type" not in component or "name" not in component:
            msg = "To override components per environment, every component should at least have a type and a name."
            raise ValueError(msg)
        index[component["name"]] = component
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
        """Load pipeline definition from yaml.

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
        self, component_class: type[PipelineComponent], component_data: dict
    ) -> None:
        """Instantiate, enrich and inflate pipeline component.

        Applies input topics according to FromSection.

        :param component_class: Type of pipeline component
        :param component_data: Arguments for instantiation of pipeline component
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
                    original_from_component = self.pipeline.find(
                        original_from_component_name
                    )
                    inflated_from_component = original_from_component.inflate()[-1]
                    resolved_from_component = self.pipeline.find(
                        inflated_from_component.name
                    )
                    enriched_component.weave_from_topics(
                        resolved_from_component.to, from_topic
                    )
            elif self.pipeline:
                # read from previous component
                prev_component = self.pipeline.last
                enriched_component.weave_from_topics(prev_component.to)
            self.pipeline.add(enriched_component)

    def enrich_component(
        self,
        component: PipelineComponent,
    ) -> PipelineComponent:
        """Enrich a pipeline component with env-specific config and substitute variables.

        :param component: Component to be enriched
        :returns: Enriched component
        """
        component.validate_ = True
        env_component_as_dict = update_nested_pair(
            self.env_components_index.get(component.name, {}),
            component.model_dump(mode="json", by_alias=True),
        )

        component_data = self.substitute_in_component(env_component_as_dict)

        component_class = type(component)
        return component_class(
            enrich=False,
            config=self.config,
            handlers=self.handlers,
            **component_data,
        )

    def substitute_in_component(self, component_as_dict: dict) -> dict:
        """Substitute all $-placeholders in a component in dict representation.

        :param component_as_dict: Component represented as dict
        :return: Updated component
        """
        config = self.config
        # Leftover variables that were previously introduced in the component by the substitution
        # functions, still hardcoded, because of their names.
        # TODO(Ivan Yordanov): Get rid of them
        substitution_hardcoded: dict[str, JsonType] = {
            "error_topic_name": config.topic_name_config.default_error_topic_name,
            "output_topic_name": config.topic_name_config.default_output_topic_name,
        }
        component_substitution = generate_substitution(
            component_as_dict,
            "component",
            substitution_hardcoded,
            separator=".",
        )
        substitution = generate_substitution(
            config.model_dump(mode="json"),
            "config",
            existing_substitution=component_substitution,
            separator=".",
        )

        return json.loads(
            substitute_nested(
                json.dumps(component_as_dict),
                **update_nested_pair(substitution, ENV),
            )
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
