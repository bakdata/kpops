from __future__ import annotations

from abc import ABC

from pydantic import Extra, Field

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
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import DescConfig


class PipelineComponent(BaseDefaultsComponent, ABC):
    """Base class for all components.

    :param name: Component name
    :param prefix: Pipeline prefix that will prefix every component name.
        If you wish to not have any prefix you can specify an empty string.,
        defaults to "${pipeline_name}-"
    :param from_: Topic(s) and/or components from which the component will read
        input, defaults to None
    :param to: Topic(s) into which the component will write output,
        defaults to None
    """

    name: str = Field(default=..., description=describe_attr("name", __doc__))
    prefix: str = Field(
        default="${pipeline_name}-",
        description=describe_attr("prefix", __doc__),
    )
    from_: FromSection | None = Field(
        default=None,
        alias="from",
        title="From",
        description=describe_attr("from_", __doc__),
    )
    to: ToSection | None = Field(
        default=None,
        description=describe_attr("to", __doc__),
    )

    class Config(DescConfig):
        extra = Extra.allow

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_input_topics()
        self.set_output_topics()

    @property
    def full_name(self) -> str:
        return self.prefix + self.name

    def add_input_topics(self, topics: list[str]) -> None:
        """Add given topics to the list of input topics.

        :param topics: Input topics
        """

    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        """Add given extra topics that share a role to the list of extra input topics.

        :param topics: Extra input topics
        :param role: Topic role
        """

    def set_input_pattern(self, name: str) -> None:
        """Set input pattern.

        :param name: Input pattern name
        """

    def add_extra_input_pattern(self, role: str, topic: str) -> None:
        """Add an input pattern of type extra.

        :param role: Custom identifier belonging to one or multiple topics
        :param topic: Topic name
        """

    def set_output_topic(self, topic_name: str) -> None:
        """Set output topic.

        :param topic_name: Output topic name
        """

    def set_error_topic(self, topic_name: str) -> None:
        """Set error topic.

        :param topic_name: Error topic name
        """

    def add_extra_output_topic(self, topic_name: str, role: str) -> None:
        """Add an output topic of type extra.

        :param topic_name: Output topic name
        :param role: Role that is unique to the extra output topic
        """

    def set_input_topics(self) -> None:
        """Put values of config.from into the streams config section of streams bootstrap.

        Supports extra_input_topics (topics by role) or input_topics.
        """
        if self.from_:
            for name, topic in self.from_.topics.items():
                self.apply_from_inputs(name, topic)

    def apply_from_inputs(self, name: str, topic: FromTopic) -> None:
        """Add a `from` section input to the component config.

        :param name: Name of the field
        :param topic: Value of the field
        """
        match topic.type:
            case None if topic.role:
                self.add_extra_input_topics(topic.role, [name])
            case InputTopicTypes.PATTERN if topic.role:
                self.add_extra_input_pattern(topic.role, name)
            case InputTopicTypes.PATTERN:
                self.set_input_pattern(name)
            case _:
                self.add_input_topics([name])

    def set_output_topics(self) -> None:
        """Put values of config.to into the producer config section of streams bootstrap.

        Supports extra_output_topics (topics by role) or output_topics.
        """
        if self.to:
            for name, topic in self.to.topics.items():
                self.apply_to_outputs(name, topic)

    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        """Add a `to` section input to the component config.

        :param name: Name of the field
        :param topic: Value of the field
        """
        match topic.type:
            case None if topic.role:
                self.add_extra_output_topic(name, topic.role)
            case OutputTopicTypes.ERROR:
                self.set_error_topic(name)
            case _:
                self.set_output_topic(name)

    def weave_from_topics(
        self,
        to: ToSection | None,
        from_topic: FromTopic | None = None,
    ) -> None:
        """Weave output topics of upstream component or from component into config.

        Override this method to apply custom logic
        """
        if from_topic is None:
            from_topic = FromTopic(type=InputTopicTypes.INPUT)
        if not to:
            return
        input_topics = [
            topic_name
            for topic_name, topic_config in to.topics.items()
            if topic_config.type != OutputTopicTypes.ERROR and not topic_config.role
        ]
        for input_topic in input_topics:
            self.apply_from_inputs(input_topic, from_topic)

    def inflate(self) -> list[PipelineComponent]:
        """Inflate a component.

        This is helpful if one component should result in multiple components.
        To support this, override this method and return a list of components
        the component you result in. The order of the components is the order
        the components will be deployed in.
        """
        return [self]

    def template(self) -> None:
        """Run `helm template`.

        From HELM: Render chart templates locally and display the output.
        Any values that would normally be looked up or retrieved in-cluster will
        be faked locally. Additionally, none of the server-side testing of chart
        validity (e.g. whether an API is supported) is done.
        """

    def deploy(self, dry_run: bool) -> None:
        """Deploy the component (self) to the k8s cluster.

        :param dry_run: Whether to do a dry run of the command
        """

    def destroy(self, dry_run: bool) -> None:
        """Uninstall the component (self) from the k8s cluster.

        :param dry_run: Whether to do a dry run of the command
        """

    def reset(self, dry_run: bool) -> None:
        """Reset component (self) state.

        :param dry_run: Whether to do a dry run of the command
        """

    def clean(self, dry_run: bool) -> None:
        """Remove component (self) and any trace of it.

        :param dry_run: Whether to do a dry run of the command
        """
