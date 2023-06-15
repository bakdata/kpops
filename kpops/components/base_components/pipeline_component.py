from __future__ import annotations

from functools import cached_property
from typing import Literal

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
from kpops.utils.docstring import describe_attr, describe_object
from kpops.utils.pydantic import CamelCaseConfig, DescConfig


class PipelineComponent(BaseDefaultsComponent):
    """Base class for all components

    :param name: Component name
    :type name: str
    :param from_: Topic(s) and/or components from which the component will read
        input, defaults to None
    :type from_: FromSection, optional
    :param app: Application-specific settings, defaults to None
    :type app: object, optional
    :param to: Topic(s) into which the component will write output,
        defaults to None
    :type to: ToSection, optional
    :param prefix: Pipeline prefix that will prefix every component name.
        If you wish to not have any prefix you can specify an empty string.,
        defaults to "${pipeline_name}-"
    :type prefix: str, optional
    """

    type: str = Field(
        default="pipeline-component",
        description=describe_attr("type", __doc__),
        const=True,
    )
    schema_type: Literal["pipeline-component"] = Field(
        default="pipeline-component",
        title="Component type",
        description=describe_object(__doc__),
        exclude=True,
    )
    name: str = Field(default=..., description="Component name")
    from_: FromSection | None = Field(
        default=None,
        alias="from",
        title="From",
        description=describe_attr("from_", __doc__),
    )
    app: object | None = Field(
        default=None,
        description=describe_attr("app", __doc__),
    )
    to: ToSection | None = Field(
        default=None,
        description=describe_attr("to", __doc__),
    )
    prefix: str = Field(
        default="${pipeline_name}-",
        description=describe_attr("prefix", __doc__),
    )

    class Config(CamelCaseConfig, DescConfig):
        extra = Extra.allow
        keep_untouched = (cached_property,)

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_input_topics()
        self.set_output_topics()

    def add_input_topics(self, topics: list[str]) -> None:
        """Add given topics to the list of input topics.

        :param topics: Input topics
        :type topics: list[str]
        """

    def add_extra_input_topic(self, role: str, topics: list[str]) -> None:
        """Add given extra topics that share a role to the list of extra input topics.

        :param topics: Extra input topics
        :type topics: list[str]
        :param role: Topic role
        :type role: str
        """

    def set_input_pattern(self, name: str) -> None:
        """Set input pattern

        :param name: Input pattern name
        :type name: str
        """

    def add_extra_input_pattern(self, role: str, topic: str) -> None:
        """Add an input pattern of type extra

        :param role: Custom identifier belonging to one or multiple topics
        :type role: str
        :param topic: Topic name
        :type topic: str
        """

    def set_output_topic(self, topic_name: str) -> None:
        """Set output topic

        :param topic_name: Output topic name
        :type topic_name: str
        """

    def set_error_topic(self, topic_name: str) -> None:
        """Set error topic

        :param topic_name: Error topic name
        :type topic_name: str
        """

    def add_extra_output_topic(self, topic_name: str, role: str) -> None:
        """Add an output topic of type extra

        :param topic_name: Output topic name
        :type topic_name: str
        :param role: Role that is unique to the extra output topic
        :type role: str
        """

    def set_input_topics(self) -> None:
        """Put values of config.from into the streams config section of streams bootstrap

        Supports extra_input_topics (topics by role) or input_topics.
        """
        if self.from_:
            for name, topic in self.from_.topics.items():
                self.apply_from_inputs(name, topic)

    def apply_from_inputs(self, name: str, topic: FromTopic) -> None:
        """Add a `from` section input to the component config

        :param name: Name of the field
        :type name: str
        :param topic: Value of the field
        :type topic: FromTopic
        """
        match topic.type:
            case InputTopicTypes.INPUT:
                self.add_input_topics([name])
            case InputTopicTypes.EXTRA if topic.role:
                self.add_extra_input_topic(topic.role, [name])
            case InputTopicTypes.INPUT_PATTERN:
                self.set_input_pattern(name)
            case InputTopicTypes.EXTRA_PATTERN if topic.role:
                self.add_extra_input_pattern(topic.role, name)

    def set_output_topics(self) -> None:
        """Put values of config.to into the producer config section of streams bootstrap

        Supports extra_output_topics (topics by role) or output_topics.
        """
        if self.to:
            for name, topic in self.to.topics.items():
                self.apply_to_outputs(name, topic)

    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        """Add a `to` section input to the component config

        :param name: Name of the field
        :type name: str
        :param topic: Value of the field
        :type topic: TopicConfig
        """
        match topic.type:
            case OutputTopicTypes.OUTPUT:
                self.set_output_topic(name)
            case OutputTopicTypes.ERROR:
                self.set_error_topic(name)
            case OutputTopicTypes.EXTRA if topic.role:
                self.add_extra_output_topic(name, topic.role)

    def weave_from_topics(
        self,
        to: ToSection | None,
        from_topic: FromTopic = FromTopic(type=InputTopicTypes.INPUT),
    ) -> None:
        """Weave output topics of upstream component or from component into config

        Override this method to apply custom logic
        """
        if not to:
            return
        input_topics = [
            topic_name
            for topic_name, topic_config in to.topics.items()
            if topic_config.type == OutputTopicTypes.OUTPUT
        ]
        for input_topic in input_topics:
            self.apply_from_inputs(input_topic, from_topic)

    def inflate(self) -> list[PipelineComponent]:
        """Inflate a component

        This is helpful if one component should result in multiple components.
        To support this, override this method and return a list of components
        the component you result in. The order of the components is the order
        the components will be deployed in.
        """
        return [self]

    def template(
        self, api_version: str | None, ca_file: str | None, cert_file: str | None
    ) -> None:
        """
        Runs `helm template`

        From HELM: Render chart templates locally and display the output.
        Any values that would normally be looked up or retrieved in-cluster will
        be faked locally. Additionally, none of the server-side testing of chart
        validity (e.g. whether an API is supported) is done.

        :param api_version: Kubernetes API version used for
            Capabilities.APIVersions, `--api_versions` in Helm
        :type api_version: str, optional
        :param ca_file: verify certificates of HTTPS-enabled servers using this
            CA bundle, `--ca-file` in Helm
        :type ca_file: str, optional
        :param cert_file: identify HTTPS client using this SSL certificate file,
            `--cert-file` in Helm
        :type cert_file: str, optional
        """

    def deploy(self, dry_run: bool) -> None:
        """Deploy the component (self) to the k8s cluster

        :param dry_run: Whether to do a dry run of the command
        :type dry_run: bool
        """

    def destroy(self, dry_run: bool) -> None:
        """Uninstall the component (self) from the k8s cluster

        :param dry_run: Whether to do a dry run of the command
        :type dry_run: bool
        """

    def reset(self, dry_run: bool) -> None:
        """Reset component (self) state

        :param dry_run: Whether to do a dry run of the command
        :type dry_run: bool
        """

    def clean(self, dry_run: bool) -> None:
        """Remove component (self) and any trace of it

        :param dry_run: Whether to do a dry run of the command
        :type dry_run: bool
        """
