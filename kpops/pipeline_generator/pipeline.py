from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from itertools import chain
from pathlib import Path

import yaml
from rich.console import Console
from rich.syntax import Syntax

from kpops.cli.pipeline_config import PipelineConfig
from kpops.cli.registry import Registry
from kpops.component_handlers import ComponentHandlers
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.pipeline_generator.pipeline_components import PipelineComponents
from kpops.pipeline_generator.pipeline_factory import PipelineComponentFactory
from kpops.utils.environment import ENV
from kpops.utils.yaml_loading import load_yaml_file, substitute

log = logging.getLogger("PipelineGenerator")


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
    def __init__(self, pipeline_components: PipelineComponents) -> None:
        self.components = pipeline_components

    @classmethod
    def load_from_yaml(
        cls,
        base_dir: Path,
        paths: list[Path],
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
        pipeline_components_list = []
        environment_components_content = []
        for path in paths:
            Pipeline.set_pipeline_name_env_vars(base_dir, path)
            component_list = load_yaml_file(path, substitution=ENV)
            if not isinstance(component_list, list):
                raise TypeError(
                    f"The pipeline definition {path} should contain a list of components"
                )
            if (
                env_file := Pipeline.pipeline_filename_environment(path, config)
            ).exists():
                environment_components_content = load_yaml_file(
                    env_file, substitution=ENV
                )
                if not isinstance(environment_components_content, list):
                    raise TypeError(
                        f"The pipeline definition {env_file} should contain a list of components"
                    )
            pipeline_components = PipelineComponentFactory(
                component_list,
                environment_components_content,
                registry,
                config,
                handlers,
            )
            pipeline_components_list.append(pipeline_components.components)

        pipeline_components = PipelineComponents(
            **{"components": list(chain(*pipeline_components_list))}
        )
        return Pipeline(pipeline_components)

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
