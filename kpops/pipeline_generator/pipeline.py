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
        self.parse_components(component_list, environment_components)

        super().__init__()

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
    def substitute_pipeline_prefix(config: PipelineConfig) -> str:
        """
        Sets the pipline_prefix field in the config with the environment variable pipeline_name.
        :param config: The pipeline config
        :return: The pipeline prefix string
        """
        return substitute(config.pipeline_prefix, dict(os.environ))

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
        config.pipeline_prefix = Pipeline.substitute_pipeline_prefix(config)

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

    def parse_components(
        self, component_list: list[dict], environment_components: list[dict]
    ) -> None:
        env_components_index = create_env_components_index(environment_components)
        previous_component: PipelineComponent | None = None
        for component in component_list:
            try:
                try:
                    component_type: str = component["type"]
                except KeyError:
                    raise ValueError(
                        "Every component must have a type defined, this component does not have one."
                    )
                component_class = self.registry[component_type]
                inflated_components = self.apply_component(
                    component, component_class, env_components_index, previous_component
                )
                self.populate_pipeline_component_names(inflated_components)
                self.components.extend(inflated_components)
                previous_component = inflated_components.pop()
            except Exception as ex:
                raise ParsingException(
                    f"{yaml.dump(component)}\n"
                    f"Enriching the component above resulted in the following exception:\n"
                    "".join(ex.args)
                ) from ex

    def populate_pipeline_component_names(
        self, inflated_components: list[PipelineComponent]
    ) -> None:
        for component in inflated_components:
            component.name = self.config.pipeline_prefix + component.name
            with suppress(
                AttributeError  # Some components like kafka connect do not have a nameOverride attribute
            ):
                if component.app and getattr(component.app, "nameOverride") is None:
                    setattr(component.app, "nameOverride", component.name)

    def apply_component(
        self,
        component: dict,
        component_class: type[PipelineComponent],
        env_components_index: dict[str, dict],
        previous_component: PipelineComponent | None,
    ) -> list[PipelineComponent]:
        # Init component for main pipeline
        component_object = self.enrich_component(
            component, component_class, env_components_index
        )

        # weave from topics
        if previous_component and previous_component.to:
            component_object.weave_from_topics(previous_component.to)

        return component_object.inflate()

    def enrich_component(
        self,
        component: dict,
        component_class: type[PipelineComponent],
        env_components_index: dict[str, dict],
    ) -> PipelineComponent:
        component_object: PipelineComponent = component_class(
            handlers=self.handlers, config=self.config, **component
        )
        env_component_definition = env_components_index.get(component_object.name, {})
        pair = update_nested_pair(
            env_component_definition,
            component_object.dict(by_alias=True),
        )

        json_object = self.substitute_component_specific_variables(
            component_object, pair
        )
        return component_class(
            enrich=False,
            handlers=self.handlers,
            config=self.config,
            **json_object,
        )

    @staticmethod
    def substitute_component_specific_variables(
        component_object: PipelineComponent, pair: dict
    ) -> dict:
        # Override component config with component config in pipeline environment definition
        json_object: dict = json.loads(
            substitute(
                json.dumps(pair),
                {
                    "component_type": component_object._type,
                    "component_name": component_object.name,
                },
            )
        )
        return json_object

    def __str__(self) -> str:
        return yaml.dump(
            PipelineComponents(components=self.components).dict(
                exclude_unset=True, exclude_none=True, by_alias=True
            )
        )

    def print_yaml(self, substitution: dict | None = None) -> None:
        syntax = Syntax(
            substitute(str(self), substitution), "yaml", background_color="default"
        )
        Console().print(syntax)

    def save(self, path: Path, substitution: dict | None = None) -> None:
        with open(path, mode="w") as file:
            file.write(substitute(str(self), substitution))

    def __iter__(self) -> Iterator[PipelineComponent]:
        return iter(self.components)
