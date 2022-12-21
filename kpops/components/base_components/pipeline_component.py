from __future__ import annotations

import os

from pydantic import BaseConfig, Extra, Field

from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
)
from kpops.components.base_components.models.from_section import (
    FromSection,
    FromTopic,
    InputTopicTypes,
)
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)
from kpops.utils.yaml_loading import substitute


class PipelineComponent(BaseDefaultsComponent):
    name: str
    from_: FromSection | None = Field(default=None, alias="from")
    app: object | None = None
    to: ToSection | None = None

    class Config(BaseConfig):
        extra = Extra.allow

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.substitute_output_topic_names()
        self.substitute_name()
        self.set_input_topics()
        self.set_output_topics()

    def substitute_output_topic_names(self):
        """
        Substitutes component and topic sepcific names in output topics
        """
        if self.to:
            updated_to = {}
            for name, topic in self.to.topics.items():
                name = self.substitute_component_variables(name)
                updated_to[name] = topic
            self.to.topics = updated_to

    @staticmethod
    def substitute_component_names(key: str, _type: str, **kwargs) -> str:
        return substitute(key, {"component_type": _type, **kwargs})

    def substitute_component_variables(self, topic_name: str) -> str:
        """
        Substitutes component, env and topic specific variables in the topic name

        :param topic_name: topic name
        :return: final topic name
        """
        error_topic_name = self.substitute_component_names(
            self.config.topic_name_config.default_error_topic_name,
            self._type,
            **os.environ,
        )
        output_topic_name = self.substitute_component_names(
            self.config.topic_name_config.default_output_topic_name,
            self._type,
            **os.environ,
        )
        return self.substitute_component_names(
            topic_name,
            self._type,
            error_topic_name=error_topic_name,
            topic_name=output_topic_name,
        )

    def add_input_topics(self, topics: list[str]) -> None:
        pass

    def add_extra_input_topic(self, role: str, topics: list[str]) -> None:
        pass

    def set_input_pattern(self, name: str) -> None:
        pass

    def add_extra_input_pattern(self, role: str, topic: str) -> None:
        pass

    def set_output_topic(self, topic_name: str) -> None:
        pass

    def set_error_topic(self, topic_name: str) -> None:
        pass

    def add_extra_output_topic(self, topic_name: str, role: str) -> None:
        pass

    def set_input_topics(self) -> None:
        """
        Puts values of config.from into the streams config section of streams bootstrap
        Supports extra_input_topics (topics by role) or input_topics.
        """
        if self.from_:
            for name, topic in self.from_.topics.items():
                self.apply_from_inputs(name, topic)

    def apply_from_inputs(self, name: str, topic: FromTopic) -> None:
        match (topic.type):
            case InputTopicTypes.INPUT:
                self.add_input_topics([name])
            case InputTopicTypes.EXTRA if topic.role:
                self.add_extra_input_topic(topic.role, [name])
            case InputTopicTypes.INPUT_PATTERN:
                self.set_input_pattern(name)
            case InputTopicTypes.EXTRA_PATTERN if topic.role:
                self.add_extra_input_pattern(topic.role, name)

    def set_output_topics(self) -> None:
        if self.to:
            for name, topic in self.to.topics.items():
                self.apply_to_outputs(name, topic)

    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        match (topic.type):
            case OutputTopicTypes.OUTPUT:
                self.set_output_topic(name)
            case OutputTopicTypes.ERROR:
                self.set_error_topic(name)
            case OutputTopicTypes.EXTRA if topic.role:
                self.add_extra_output_topic(name, topic.role)

    def weave_from_topics(self, prev_component_to: ToSection) -> None:
        """
        Weave output topics of upstream component or from component into config
        Override this method if you want to apply custom logic
        """
        if self.from_:
            return
        input_topics = [
            topic_name
            for topic_name, topic_config in prev_component_to.topics.items()
            if topic_config.type == OutputTopicTypes.OUTPUT
        ]
        if input_topics:
            self.add_input_topics(input_topics)

    def substitute_name(self):
        if self.name:
            self.name = self.substitute_component_names(self.name, self._type)
        else:
            raise ValueError("Every component must have a name in the end.")

    def inflate(self) -> list[PipelineComponent]:
        """Inflate a component. This is helpful if one component should result in multiple components.
        If you wish to support this, override this method and return a list of components the component you result in.
        The order of the components is the order the components will be deployed
        """
        return [self]

    def deploy(self, dry_run: bool) -> None:
        pass

    def destroy(self, dry_run: bool, clean: bool, delete_outputs: bool) -> None:
        pass
