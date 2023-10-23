import inspect
import logging
from collections import deque
from collections.abc import Sequence
from functools import cached_property
from pathlib import Path
from typing import TypeVar

import typer
from pydantic import BaseModel, Field

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers import ComponentHandlers
from kpops.utils import cached_classproperty
from kpops.utils.dict_ops import update_nested
from kpops.utils.docstring import describe_attr
from kpops.utils.environment import ENV
from kpops.utils.pydantic import DescConfig, to_dash
from kpops.utils.yaml_loading import load_yaml_file

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

log = logging.getLogger("BaseDefaultsComponent")


class BaseDefaultsComponent(BaseModel):
    """Base for all components, handles defaults.

    Component defaults are usually provided in a yaml file called
    `defaults.yaml`. This class ensures that the defaults are read and assigned
    correctly to the component.

    :param enrich: Whether to enrich component with defaults, defaults to False
    :param config: Pipeline configuration to be accessed by this component
    :param handlers: Component handlers to be accessed by this component
    :param validate: Whether to run custom validation on the component, defaults to True
    """

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
    validate_: bool = Field(
        alias="validate",
        default=True,
        description=describe_attr("validate", __doc__),
        exclude=True,
        hidden_from_schema=True,
    )

    class Config(DescConfig):
        arbitrary_types_allowed = True
        keep_untouched = (cached_property, cached_classproperty)

    def __init__(self, **kwargs) -> None:
        if kwargs.get("enrich", True):
            kwargs = self.extend_with_defaults(**kwargs)
        super().__init__(**kwargs)
        if kwargs.get("validate", True):
            self._validate_custom(**kwargs)

    @cached_classproperty
    def type(cls: type[Self]) -> str:  # pyright: ignore[reportGeneralTypeIssues]
        """Return calling component's type.

        :returns: Component class name in dash-case
        """
        return to_dash(cls.__name__)

    def extend_with_defaults(self, **kwargs) -> dict:
        """Merge parent components' defaults with own.

        :param kwargs: The init kwargs for pydantic
        :returns: Enriched kwargs with inheritted defaults
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
        return update_nested(kwargs, defaults)

    def _validate_custom(self, **kwargs) -> None:
        """Run custom validation on component.

        :param kwargs: The init kwargs for the component
        """


def load_defaults(
    component_class: type[BaseDefaultsComponent],
    defaults_file_path: Path,
    environment_defaults_file_path: Path | None = None,
) -> dict:
    """Resolve component-specific defaults including environment defaults.

    :param component_class: Component class
    :param defaults_file_path: Path to `defaults.yaml`
    :param environment_defaults_file_path: Path to `defaults_{environment}.yaml`,
        defaults to None
    :returns: Component defaults
    """
    classes = deque(inspect.getmro(component_class))
    classes.appendleft(component_class)
    defaults: dict = {}
    for base in deduplicate(classes):
        if issubclass(base, BaseDefaultsComponent):
            component_type = base.type
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
    """Read component-specific settings from a defaults yaml file and return @default if not found.

    :param path: Path to defaults yaml file
    :param key: Component type
    :returns: All defaults set for the given component in the provided yaml

    :Example:

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


def get_defaults_file_paths(config: PipelineConfig) -> tuple[Path, Path]:
    """Return the paths to the main and the environment defaults-files.

    The files need not exist, this function will only check if the dir set in
    `config.defaults_path` exists and return paths to the defaults files
    calculated from it. It is up to the caller to handle any false paths.

    :param config: Pipeline configuration
    :returns: The defaults files paths
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
    :returns: Cleaned sequence in the form of a list
    """
    return list(dict.fromkeys(seq))
