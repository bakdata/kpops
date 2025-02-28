from __future__ import annotations

import json
import logging
from abc import ABC
from collections.abc import Hashable, Sequence
from dataclasses import asdict
from functools import cached_property
from pathlib import Path
from typing import Any, ClassVar, Self, TypeVar, cast

import pydantic
import typer
from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    computed_field,
)
from pydantic.json_schema import SkipJsonSchema

from kpops.config import KpopsConfig, get_config
from kpops.const.file_type import KpopsFileType
from kpops.utils import cached_classproperty
from kpops.utils.dataclasses import is_dataclass_instance
from kpops.utils.dict_ops import (
    generate_substitution,
    update_nested,
    update_nested_pair,
)
from kpops.utils.docstring import describe_attr
from kpops.utils.environment import ENV, PIPELINE_PATH
from kpops.utils.pydantic import DescConfigModel, issubclass_patched, to_dash
from kpops.utils.types import JsonType
from kpops.utils.yaml import load_yaml_file, substitute_nested

log = logging.getLogger("BaseDefaultsComponent")


class BaseDefaultsComponent(DescConfigModel, ABC):
    """Base for all components, handles defaults.

    Component defaults are usually provided in a YAML file called
    `defaults.yaml`. This class ensures that the defaults are read and assigned
    correctly to the component.

    :param enrich: Whether to enrich component with defaults, defaults to False
    :param validate: Whether to run custom validation on the component, defaults to True
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(
        arbitrary_types_allowed=True,
        ignored_types=(cached_property, cached_classproperty),  # pyright: ignore[reportArgumentType]
    )
    enrich: SkipJsonSchema[bool] = Field(
        default=True,
        description=describe_attr("enrich", __doc__),
        exclude=True,
    )
    validate_: SkipJsonSchema[bool] = Field(
        validation_alias=AliasChoices("validate", "validate_"),
        default=False,
        description=describe_attr("validate", __doc__),
        exclude=True,
    )

    def __init__(self, **values: Any) -> None:
        if values.get("enrich", True):
            cls = self.__class__
            values = cls.extend_with_defaults(**values)
            tmp_self = cls(**values, enrich=False)
            values = tmp_self.model_dump(mode="json", by_alias=True)
            values = cls.substitute_in_component(**values)
            self.__init__(
                enrich=False,
                validate=True,
                **values,
            )
        else:
            super().__init__(**values)

    @pydantic.model_validator(mode="after")
    def validate_component(self) -> Self:
        if not self.enrich and self.validate_:
            self._validate_custom()
        return self

    @computed_field
    @cached_classproperty
    def type(cls: type[Self]) -> str:  # pyright: ignore[reportGeneralTypeIssues]
        """Return calling component's type.

        :returns: Component class name in dash-case
        """
        return to_dash(cls.__name__)

    @cached_classproperty
    def parents(cls: type[Self]) -> tuple[type[BaseDefaultsComponent], ...]:  # pyright: ignore[reportGeneralTypeIssues]
        """Get parent components.

        :return: All ancestor KPOps components
        """

        def gen_parents():
            for base in cls.mro():
                # skip class itself and non-component ancestors
                if base is cls or not issubclass_patched(base, BaseDefaultsComponent):
                    continue
                yield base

        return tuple(gen_parents())

    @classmethod
    def substitute_in_component(cls, **component_data: Any) -> dict[str, Any]:
        """Substitute all $-placeholders in a component in dict representation.

        :param component_as_dict: Component represented as dict
        :return: Updated component
        """
        config = get_config()
        # Leftover variables that were previously introduced in the component by the substitution
        # functions, still hardcoded, because of their names.
        # TODO(Ivan Yordanov): Get rid of them
        substitution_hardcoded: dict[str, JsonType] = {
            "error_topic_name": config.topic_name_config.default_error_topic_name,
            "output_topic_name": config.topic_name_config.default_output_topic_name,
        }
        component_substitution = generate_substitution(
            component_data,
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
                json.dumps(component_data),
                **update_nested_pair(substitution, ENV),
            )
        )

    @classmethod
    def extend_with_defaults(cls, **kwargs: Any) -> dict[str, Any]:
        """Merge parent components' defaults with own.

        :param config: KPOps configuration
        :param kwargs: The init kwargs for pydantic
        :returns: Enriched kwargs with inherited defaults
        """
        config = get_config()
        pipeline_path_str = ENV.get(PIPELINE_PATH)
        if not pipeline_path_str:
            return kwargs
        pipeline_path = Path(pipeline_path_str)
        for k, v in kwargs.items():
            if isinstance(v, pydantic.BaseModel):
                kwargs[k] = v.model_dump(exclude_unset=True)
            elif is_dataclass_instance(v):
                kwargs[k] = asdict(v)

        defaults_file_paths_ = get_defaults_file_paths(
            pipeline_path, config, ENV.get("environment")
        )
        defaults = cls.load_defaults(*defaults_file_paths_)
        log.debug(
            typer.style("Enriching component of type ", bold=False)
            + typer.style(cls.type, bold=True, underline=True)
        )
        return update_nested_pair(kwargs, defaults)

    @classmethod
    def load_defaults(cls, *defaults_file_paths: Path) -> dict[str, Any]:
        """Resolve component-specific defaults including environment defaults.

        :param defaults_file_paths: Path to `defaults.yaml`, ordered from highest to lowest priority,
         i.e. `defaults.yaml`, `defaults_{environment}`.yaml
        :returns: Component defaults
        """
        defaults: dict[str, Any] = {}
        for base in (cls, *cls.parents):
            component_type = base.type
            defaults = update_nested(
                defaults,
                *(
                    defaults_from_yaml(path, component_type)
                    for path in defaults_file_paths
                    if path.exists()
                ),
            )
        return defaults

    def _validate_custom(self) -> None:
        """Run custom validation on component."""


def defaults_from_yaml(path: Path, key: str) -> dict[str, Any]:
    """Read component-specific settings from a ``defaults*.yaml`` file and return @default if not found.

    :param path: Path to ``defaults*.yaml`` file
    :param key: Component type
    :returns: All defaults set for the given component in the provided YAML

    :Example:
    .. code-block:: python
        kafka_app_defaults = defaults_from_yaml(Path("/path/to/defaults.yaml"), "kafka-app")
    """
    content = load_yaml_file(path, substitution=ENV)
    if not isinstance(content, dict):
        msg = (
            "Default files should be structured as map ([app type] -> [default config]"
        )
        raise TypeError(msg)
    content = cast(dict[str, dict[str, Any]], content)
    value = content.get(key)
    if value is None:
        return {}
    default_path = path.relative_to(Path.cwd())
    log.debug(
        f"Found defaults for component type {typer.style(key, bold=True, fg=typer.colors.MAGENTA)} in {default_path}"
    )
    return value


def get_defaults_file_paths(
    pipeline_path: Path, config: KpopsConfig, environment: str | None
) -> list[Path]:
    """Return a list of default file paths related to the given pipeline.

    This function traverses the directory hierarchy upwards till the `pipeline_base_dir`,
    starting from the directory containing
    the pipeline.yaml file specified by `pipeline_path`, looking for default files
    associated with the pipeline.

    :param pipeline_path: The path to the pipeline.yaml file.
    :param config: The KPOps configuration object containing settings such as pipeline_base_dir.
    :param environment: Optional. The environment for which default configuration files are sought.
    :returns: A list of Path objects representing the default configuration file paths.
    """
    default_paths: list[Path] = []

    if not pipeline_path.is_file():
        msg = f"{pipeline_path} is not a valid pipeline file."
        raise FileNotFoundError(msg)

    path = pipeline_path.resolve()
    pipeline_base_dir = config.pipeline_base_dir.resolve()
    if pipeline_base_dir not in path.parents:
        msg = f"The given pipeline base path {pipeline_base_dir} is not part of the pipeline path {path}"
        raise RuntimeError(msg)
    while pipeline_base_dir != path:
        environment_default_file_path = (
            path.parent / KpopsFileType.DEFAULTS.as_yaml_file(suffix=f"_{environment}")
        )
        if environment_default_file_path.is_file():
            default_paths.append(environment_default_file_path)

        defaults_yaml_path = path.parent / KpopsFileType.DEFAULTS.as_yaml_file()
        if defaults_yaml_path.is_file():
            default_paths.append(defaults_yaml_path)

        path = path.parent

    return default_paths


_T = TypeVar("_T", bound=Hashable)


def deduplicate(seq: Sequence[_T]) -> list[_T]:
    """Deduplicate items of a sequence while preserving its order.

    :param seq: Sequence to be 'cleaned'
    :returns: Cleaned sequence in the form of a list
    """
    return list(dict.fromkeys(seq))
