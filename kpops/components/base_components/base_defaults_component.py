from __future__ import annotations

import json
import logging
from abc import ABC
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, TypeVar

import pydantic
import typer
from pydantic import (
    AliasChoices,
    ConfigDict,
    Field,
    computed_field,
)
from pydantic.json_schema import SkipJsonSchema

from kpops.component_handlers import ComponentHandlers
from kpops.config import KpopsConfig
from kpops.utils import cached_classproperty
from kpops.utils.dict_ops import (
    generate_substitution,
    update_nested,
    update_nested_pair,
)
from kpops.utils.docstring import describe_attr
from kpops.utils.environment import ENV
from kpops.utils.pydantic import DescConfigModel, issubclass_patched, to_dash
from kpops.utils.types import JsonType
from kpops.utils.yaml import load_yaml_file, substitute_nested

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

log = logging.getLogger("BaseDefaultsComponent")


class BaseDefaultsComponent(DescConfigModel, ABC):
    """Base for all components, handles defaults.

    Component defaults are usually provided in a YAML file called
    `defaults.yaml`. This class ensures that the defaults are read and assigned
    correctly to the component.

    :param enrich: Whether to enrich component with defaults, defaults to False
    :param config: KPOps configuration to be accessed by this component
    :param handlers: Component handlers to be accessed by this component
    :param validate: Whether to run custom validation on the component, defaults to True
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        ignored_types=(cached_property, cached_classproperty),
    )

    enrich: SkipJsonSchema[bool] = Field(
        default=True,
        description=describe_attr("enrich", __doc__),
        exclude=True,
    )
    config: SkipJsonSchema[KpopsConfig] = Field(
        default=...,
        description=describe_attr("config", __doc__),
        exclude=True,
    )
    handlers: SkipJsonSchema[ComponentHandlers] = Field(
        default=...,
        description=describe_attr("handlers", __doc__),
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
            values = cls.substitute_in_component(tmp_self.config, **values)
            # HACK: why is double substitution necessary for test_substitute_in_component
            values = cls.substitute_in_component(tmp_self.config, **values)
            self.__init__(
                enrich=False,
                validate=True,
                config=tmp_self.config,
                handlers=tmp_self.handlers,
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
    def substitute_in_component(
        cls, config: KpopsConfig, **component_data: Any
    ) -> dict[str, Any]:
        """Substitute all $-placeholders in a component in dict representation.

        :param component_as_dict: Component represented as dict
        :return: Updated component
        """
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
    def extend_with_defaults(cls, config: KpopsConfig, **kwargs: Any) -> dict[str, Any]:
        """Merge parent components' defaults with own.

        :param config: KPOps configuration
        :param kwargs: The init kwargs for pydantic
        :returns: Enriched kwargs with inherited defaults
        """
        kwargs["config"] = config
        for k, v in kwargs.items():
            if isinstance(v, pydantic.BaseModel):
                kwargs[k] = v.model_dump(exclude_unset=True)
            elif is_dataclass(v):
                kwargs[k] = asdict(v)

        log.debug(
            typer.style(
                "Enriching component of type ", fg=typer.colors.GREEN, bold=False
            )
            + typer.style(cls.type, fg=typer.colors.GREEN, bold=True, underline=True)
        )
        main_default_file_path, environment_default_file_path = get_defaults_file_paths(
            config, ENV.get("environment")
        )
        defaults = cls.load_defaults(
            main_default_file_path, environment_default_file_path
        )
        return update_nested_pair(kwargs, defaults)

    @classmethod
    def load_defaults(cls, *defaults_file_paths: Path) -> dict[str, Any]:
        """Resolve component-specific defaults including environment defaults.

        :param *defaults_file_paths: Path to `defaults.yaml`, ordered from lowest to highest priority, i.e. `defaults.yaml`, `defaults_{environment}`.yaml
        :returns: Component defaults
        """
        defaults: dict[str, Any] = {}
        for base in (cls, *cls.parents):
            component_type: str = base.type
            defaults = update_nested(
                defaults,
                *(
                    defaults_from_yaml(path, component_type)
                    for path in reversed(defaults_file_paths)
                    if path.exists()
                ),
            )
        return defaults

    def _validate_custom(self) -> None:
        """Run custom validation on component."""


def defaults_from_yaml(path: Path, key: str) -> dict:
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
    value = content.get(key)
    if value is None:
        return {}
    log.debug(
        f"\tFound defaults for component type {typer.style(key, bold=True, fg=typer.colors.MAGENTA)} in file:  {path}"
    )
    return value


def get_defaults_file_paths(
    config: KpopsConfig, environment: str | None
) -> tuple[Path, Path]:
    """Return the paths to the main and the environment defaults-files.

    The files need not exist, this function will only check if the dir set in
    `config.defaults_path` exists and return paths to the defaults files
    calculated from it. It is up to the caller to handle any false paths.

    :param config: KPOps configuration
    :param environment: Environment
    :returns: The defaults files paths
    """
    defaults_dir = Path(config.defaults_path).resolve()
    main_default_file_path = defaults_dir / Path(
        config.defaults_filename_prefix
    ).with_suffix(".yaml")

    environment_default_file_path = (
        defaults_dir
        / Path(f"{config.defaults_filename_prefix}_{environment}").with_suffix(".yaml")
        if environment is not None
        else main_default_file_path
    )

    return main_default_file_path, environment_default_file_path


_T = TypeVar("_T")


def deduplicate(seq: Sequence[_T]) -> list[_T]:
    """Deduplicate items of a sequence while preserving its order.

    :param seq: Sequence to be 'cleaned'
    :returns: Cleaned sequence in the form of a list
    """
    return list(dict.fromkeys(seq))
