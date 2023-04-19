import inspect
import logging
import os
from collections import deque
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeVar

import typer
from pydantic import BaseModel, Field

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers import ComponentHandlers
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfig
from kpops.utils.yaml_loading import load_yaml_file

log = logging.getLogger("PipelineComponentEnricher")


class BaseDefaultsComponent(BaseModel):
    """Base for all components, handles defaults.

    Component defaults are usually provided in a yaml file called
    `defaults.yaml`. This class ensures that the defaults are read and assigned
    correctly to the component.

    :param type: Component type
    :type type: str
    :param enrich: Whether to enrich component with defaults, defaults to False
    :type enrich: bool, optional
    :param config: Pipeline configuration to be accessed by this component
    :type config: PipelineConfig
    :param handlers: Component handlers to be accessed by this component
    :type handlers: ComponentHandlers
    """

    type: str = Field(
        default=..., description=describe_attr("type", __doc__), const=True
    )

    enrich: bool = Field(
        default=False,
        description=describe_attr("enrich", __doc__),
        exclude=True,
        hidden_from_schema=True,
    )
    config: PipelineConfig = Field(
        default=...,
        description=describe_attr("config", __doc__),
        exclude=True,
        hidden_from_schema=True,
    )
    handlers: ComponentHandlers = Field(
        default=...,
        description=describe_attr("handlers", __doc__),
        exclude=True,
        hidden_from_schema=True,
    )

    class Config(DescConfig):
        arbitrary_types_allowed = True

    def __init__(self, **kwargs) -> None:
        if kwargs.get("enrich", True):
            kwargs = self.extend_with_defaults(**kwargs)
        super().__init__(**kwargs)

    @classmethod  # NOTE: property as classmethod deprecated in Python 3.11
    def get_component_type(cls) -> str:
        """Return calling component's type

        :returns: Component type
        :rtype: str
        """
        # HACK: access type attribute through default value
        # because exporting type as ClassVar from Pydantic models
        # is not reliable
        return cls.__fields__["type"].default

    def extend_with_defaults(self, **kwargs) -> dict:
        """Merge parent components' defaults with own

        :param kwargs: The init kwargs for pydantic
        :returns: Enriched kwargs with inheritted defaults
        :rtype: dict[str, Any]
        """
        config: PipelineConfig = kwargs["config"]
        log.debug(
            typer.style(
                "Enriching component of type ", fg=typer.colors.GREEN, bold=False
            )
            + typer.style(
                kwargs.get("type"), fg=typer.colors.GREEN, bold=True, underline=True
            )
        )
        main_default_file_path, environment_default_file_path = get_defaults_file_paths(
            config
        )
        defaults = load_defaults(
            self.__class__, main_default_file_path, environment_default_file_path
        )
        kwargs = update_nested(kwargs, defaults)
        return kwargs


def load_defaults(
    component_class: type[BaseDefaultsComponent],
    defaults_file_path: Path,
    environment_defaults_file_path: Path | None = None,
) -> dict:
    """Resolve component-specific defaults including environment defaults

    :param component_class: Component class
    :type component_class: type[BaseDefaultsComponent]
    :param defaults_file_path: Path to `defaults.yaml`
    :type defaults_file_path: Path
    :param environment_defaults_file_path: Path to `defaults_{environment}.yaml`,
        defaults to None
    :type environment_defaults_file_path: Path, optional
    :returns: Component defaults
    :rtype: dict
    """
    classes = deque(inspect.getmro(component_class))
    classes.appendleft(component_class)
    defaults: dict = {}
    for base in deduplicate(classes):
        if issubclass(base, BaseDefaultsComponent):
            component_type = base.get_component_type()
            if (
                not environment_defaults_file_path
                or not environment_defaults_file_path.exists()
            ):
                defaults = update_nested(
                    defaults,
                    defaults_from_yaml(defaults_file_path, component_type),
                )
            else:
                defaults = update_nested(
                    defaults,
                    defaults_from_yaml(environment_defaults_file_path, component_type),
                    defaults_from_yaml(defaults_file_path, component_type),
                )
    return defaults


def defaults_from_yaml(path: Path, key: str) -> dict:
    """Read component-specific settings from a defaults yaml file and return @default if not found

    :param path: Path to defaults yaml file
    :type path: Path
    :param key: Component type
    :type key: str
    :returns: All defaults set for the given component in the provided yaml
    :rtype: dict

    :Example:

    kafka_app_defaults = defaults_from_yaml(Path("/path/to/defaults.yaml"), "kafka-app")
    """
    content = load_yaml_file(path, substitution=dict(os.environ))
    if not isinstance(content, dict):
        raise TypeError(
            "Default files should be structured as map ([app type] -> [default config]"
        )
    value = content.get(key)
    if value is None:
        return {}
    log.debug(
        f"\tFound defaults for component type {typer.style(key, bold=True, fg=typer.colors.MAGENTA)} in file:  {path}"
    )
    return value


def get_defaults_file_paths(config: PipelineConfig) -> tuple[Path, Path]:
    """Return the paths to the main and the environment defaults-files

    The files need not exist, this function will only check if the dir set in
    `config.defaults_path` exists and return paths to the defaults files
    calculated from it. It is up to the caller to handle any false paths.

    :param config: Pipeline configuration
    :type config: PipelineConfig
    :returns: The defaults files paths
    :rtype: tuple[Path, Path]
    """
    defaults_dir = Path(config.defaults_path).resolve()
    main_default_file_path = defaults_dir / Path(
        config.defaults_filename_prefix
    ).with_suffix(".yaml")

    environment_default_file_path = defaults_dir / Path(
        f"{config.defaults_filename_prefix}_{config.environment}"
    ).with_suffix(".yaml")

    return main_default_file_path, environment_default_file_path


T = TypeVar("T")


def deduplicate(seq: Sequence[T]) -> list[T]:
    """Deduplicate items of a sequence while preserving its order.

    :param seq: Sequence to be 'cleaned'
    :type seq: Sequence[T]
    :returns: Cleaned sequence in the form of a list
    :rtype: list[T]
    """
    return list(dict.fromkeys(seq))


def update_nested_pair(original_dict: dict, other_dict: Mapping) -> dict:
    """Nested update for 2 dictionaries

    :param original_dict: Dictionary to be updated
    :type original_dict: dict
    :param other_dict: Mapping that contains new or updated key-value pairs
    :type other_dict: Mapping
    :return: Updated dictionary
    :rtype: dict
    """
    for key, value in other_dict.items():
        if isinstance(value, Mapping):
            nested_val = original_dict.get(key, {})
            if nested_val is not None:
                original_dict[key] = update_nested_pair(nested_val, value)
        else:
            if key not in original_dict:
                original_dict[key] = value
    return original_dict


def update_nested(*argv: dict) -> dict:
    """Merge multiple configuration dicts.

    The dicts have multiple layers. These layers will be merged recursively.

    :param argv: n dictionaries
    :type argv: dict
    :returns: Merged configuration dict
    :rtype: dict
    """
    if len(argv) == 0:
        return {}
    if len(argv) == 1:
        return argv[0]
    if len(argv) == 2:
        return update_nested_pair(argv[0], argv[1])
    return update_nested(update_nested_pair(argv[0], argv[1]), *argv[2:])
