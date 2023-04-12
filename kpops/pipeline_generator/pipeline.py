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

    def __iter__(self) -> Iterator[PipelineComponent]:  # type: ignore[override]
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
        """Instantiates, enriches and inflates pipeline component.
        Applies input topics according to FromSection.

        :param component_class: Type of pipeline component
        :param component_data: Arguments for instantiation of pipeline component
        """
        component = component_class(
            config=self.config,
            handlers=self.handlers,
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
        env_component_definition = self.env_components_index.get(component.name, {})
        pair = update_nested_pair(
            env_component_definition,
            # HACK: Pydantic .dict() doesn't create jsonable dict
            json.loads(component.json(by_alias=True)),
        )

        component_data = self.substitute_component_specific_variables(component, pair)

        component_class = type(component)
        return component_class(
            enrich=False,
            config=self.config,
            handlers=self.handlers,
            **component_data,
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

    def __str__(self) -> str:
        return yaml.dump(
            json.loads(  # HACK: serialize types on Pydantic model export, which are not serialized by .dict(); e.g. pathlib.Path
                self.components.json(exclude_none=True, by_alias=True)
            )
        )

    @staticmethod
    def substitute_component_specific_variables(
        component: PipelineComponent, pair: dict  # TODO: better parameter name for pair
    ) -> dict:
        """Overrides component config with component config in pipeline environment definition."""
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
