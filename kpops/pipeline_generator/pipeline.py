from __future__ import annotations

import json
import logging
import os
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
from kpops.components.base_components.base_defaults_component import update_nested_pair
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.yaml_loading import load_yaml_file, substitute

log = logging.getLogger("PipelineGenerator")


class ParsingException(Exception):
    pass


class PipelineComponents(BaseModel):
    components: list[PipelineComponent]


def create_env_components_index(
    environment_components: list[dict],
) -> dict[str, dict]:
    """
    Create an index for all registered components in the project

    :param environment_components: list of components
    :return: component index
    """
    index = {}
    for component in environment_components:
        if "type" not in component or "name" not in component:
            raise ValueError(
                "To override components per environment, every component should at least have a type and a name."
            )
        index[
            PipelineComponent.substitute_component_names(
                component["name"], component["type"], **os.environ
            )
        ] = component
    return index


class Pipeline:
    def __init__(
        self,
        component_list: list[dict],
        environment_components: list[dict],
        registry: Registry,
        config: PipelineConfig,
        handlers: ComponentHandlers,
    ):
        self.components: list[PipelineComponent] = []
        self.handlers = handlers
        self.config = config
        self.registry = registry
        self.env_components_index = create_env_components_index(environment_components)
        self.parse_components(component_list)

    @staticmethod
    def pipeline_filename_environment(path: Path, config: PipelineConfig) -> Path:
        """
        Adds the environment name from the PipelineConfig to the pipeline.yaml path
        :param path: Path to pipeline.yaml file
        :param config: The PipelineConfig
        :return: Absolute path to the pipeline_<environment>.yaml
        """
        return path.with_stem(f"{path.stem}_{config.environment}")

    @staticmethod
    def set_pipeline_name_env_vars(base_dir: Path, path: Path) -> None:
        """
        Sets the environment variable pipeline_name relative to the given base_dir.
        Moreover, for each sub-path an environment variable is set.
        For example, for a given path ./data/v1/dev/pipeline.yaml the pipeline_name would be
        set to data-v1-dev. Then the sub environment variables are set:
        pipeline_name_0 = data
        pipeline_name_1 = v1
        pipeline_name_2 = dev
        :param base_dir: Base directory to the pipeline files
        :param path: Path to pipeline.yaml file
        """
        path_without_file = path.resolve().relative_to(base_dir.resolve()).parts[:-1]
        if not path_without_file:
            raise ValueError("The pipeline-base-dir should not equal the pipeline-path")
        pipeline_name = "-".join(path_without_file)
        os.environ["pipeline_name"] = pipeline_name
        for level, parent in enumerate(path_without_file):
            os.environ[f"pipeline_name_{level}"] = parent

    @classmethod
    def load_from_yaml(
        cls,
        base_dir: Path,
        path: Path,
        registry: Registry,
        config: PipelineConfig,
        handlers: ComponentHandlers,
    ) -> Pipeline:
        Pipeline.set_pipeline_name_env_vars(base_dir, path)

        main_content = load_yaml_file(path, substitution=dict(os.environ))
        if not isinstance(main_content, list):
            raise TypeError(
                f"The pipeline definition {path} should contain a list of components"
            )

        env_content = []
        if (env_file := Pipeline.pipeline_filename_environment(path, config)).exists():
            env_content = load_yaml_file(env_file, substitution=dict(os.environ))
            if not isinstance(env_content, list):
                raise TypeError(
                    f"The pipeline definition {env_file} should contain a list of components"
                )

        pipeline = cls(main_content, env_content, registry, config, handlers)
        return pipeline

    def parse_components(self, component_list: list[dict]) -> None:
        previous_component: PipelineComponent | None = None
        for component_data in component_list:
            try:
                try:
                    component_type: str = component_data["type"]
                except KeyError:
                    raise ValueError(
                        "Every component must have a type defined, this component does not have one."
                    )
                component_class = self.registry[component_type]
                inflated_components = self.apply_component(
                    component_data,
                    component_class,
                    previous_component,
                )
                self.populate_pipeline_component_names(inflated_components)
                self.components.extend(inflated_components)
                previous_component = inflated_components.pop()
            except Exception as ex:
                if "name" in component_data:
                    raise ParsingException(
                        f"Error enriching {component_data['type']} component {component_data['name']}"
                    ) from ex
                else:
                    raise ParsingException() from ex

    def populate_pipeline_component_names(
        self, inflated_components: list[PipelineComponent]
    ) -> None:
        for component in inflated_components:
            component.name = component.prefix + component.name
            with suppress(
                AttributeError  # Some components like Kafka Connect do not have a name_override attribute
            ):
                if component.app and getattr(component.app, "name_override") is None:
                    setattr(component.app, "name_override", component.name)

    def apply_component(
        self,
        component_data: dict,
        component_class: type[PipelineComponent],
        previous_component: PipelineComponent | None,
    ) -> list[PipelineComponent]:
        component = component_class(
            config=self.config,
            handlers=self.handlers,
            **component_data,
        )
        component = self.enrich_component(component)
        # weave from topics
        if previous_component and previous_component.to:
            component.weave_from_topics(previous_component.to)

        # inflate & enrich components
        enriched_components: list[PipelineComponent] = []
        for inflated_component in component.inflate():  # TODO: recursively:
            enriched_component = self.enrich_component(inflated_component)
            if enriched_components:
                prev = enriched_components[-1]
                if prev.to:
                    enriched_component.weave_from_topics(prev.to)
            enriched_components.append(enriched_component)

        return enriched_components

    def enrich_component(
        self,
        component: PipelineComponent,
    ) -> PipelineComponent:
        env_component_definition = self.env_components_index.get(component.name, {})
        pair = update_nested_pair(
            env_component_definition, component.dict(by_alias=True)
        )

        component_data = self.substitute_component_specific_variables(component, pair)

        component_class = type(component)
        return component_class(
            enrich=False,
            config=self.config,
            handlers=self.handlers,
            **component_data,
        )

    @staticmethod
    def substitute_component_specific_variables(
        component: PipelineComponent, pair: dict  # TODO: better parameter name for pair
    ) -> dict:
        # Override component config with component config in pipeline environment definition
        # HACK: why do we need an intermediate JSON object?
        component_data: dict = json.loads(
            substitute(
                json.dumps(pair),
                {
                    "component_type": component.type,
                    "component_name": component.name,
                },
            )
        )
        return component_data

    def __str__(self) -> str:
        return yaml.dump(
            PipelineComponents(components=self.components).dict(
                exclude_none=True, by_alias=True
            )
        )

    def print_yaml(self, substitution: dict | None = None) -> None:
        syntax = Syntax(
            substitute(str(self), substitution), "yaml", background_color="default"
        )
        Console(
            width=1000  # HACK: overwrite console width to avoid truncating output
        ).print(syntax)

    def __iter__(self) -> Iterator[PipelineComponent]:
        return iter(self.components)
