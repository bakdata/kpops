from contextlib import suppress
from typing import Iterator

from pydantic import BaseModel

from kpops.components import PipelineComponent


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

    def add_list(self, components: list[PipelineComponent]):
        for component in components:
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
            if (app := getattr(component, "app")) and app.name_override is None:
                app.name_override = component.name
