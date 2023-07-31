import json

from kpops.cli.pipeline_config import PipelineConfig
from kpops.cli.registry import Registry
from kpops.component_handlers import ComponentHandlers
from kpops.components import PipelineComponent
from kpops.pipeline_generator.exception import ParsingException
from kpops.pipeline_generator.pipeline_components import PipelineComponents
from kpops.utils.dict_ops import generate_substitution, update_nested_pair
from kpops.utils.environment import ENV
from kpops.utils.yaml_loading import substitute_nested


class PipelineComponentFactory:
    def __init__(
        self,
        component_list: list[dict],
        registry: Registry,
        config: PipelineConfig,
        handlers: ComponentHandlers,
    ) -> None:
        self._component_list = component_list
        self._handlers = handlers
        self._config = config
        self._registry = registry
        self._components = PipelineComponents()

    def create_components(
        self,
        environment_components: list[dict],
    ) -> PipelineComponents:
        env_components_index = self.create_env_components_index(environment_components)
        self.parse_components(env_components_index)
        return self._components

    @staticmethod
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

    def parse_components(self, env_components_index: dict[str, dict]) -> None:
        """Instantiate, enrich and inflate a list of components

        :param component_list: List of components
        :type component_list: list[dict]
        :raises ValueError: Every component must have a type defined
        :raises ParsingException: Error enriching component
        :raises ParsingException: All undefined exceptions
        """
        for component_data in self._component_list:
            try:
                try:
                    component_type: str = component_data["type"]
                except KeyError:
                    raise ValueError(
                        "Every component must have a type defined, this component does not have one."
                    )
                component_class = self._registry[component_type]

                self.apply_component(
                    component_class, component_data, env_components_index
                )
            except Exception as ex:
                if "name" in component_data:
                    raise ParsingException(
                        f"Error enriching {component_data['type']} component {component_data['name']}"
                    ) from ex
                else:
                    raise ParsingException() from ex

    def apply_component(
        self,
        component_class: type[PipelineComponent],
        component_data: dict,
        env_components_index: dict[str, dict],
    ) -> None:
        """Instantiate, enrich and inflate pipeline component.

        Applies input topics according to FromSection.

        :param component_class: Type of pipeline component
        :type component_class: type[PipelineComponent]
        :param component_data: Arguments for instantiation of pipeline component
        :type component_data: dict
        """
        component = component_class(
            config=self._config,
            handlers=self._handlers,
            validate=False,
            **component_data,
        )
        component = self.enrich_component(component, env_components_index)

        # inflate & enrich components
        for inflated_component in component.inflate():  # TODO: recursively
            enriched_component = self.enrich_component(
                inflated_component, env_components_index
            )
            if enriched_component.from_:
                # read from specified components
                for (
                    original_from_component_name,
                    from_topic,
                ) in enriched_component.from_.components.items():
                    original_from_component = self._components.find(
                        original_from_component_name
                    )
                    inflated_from_component = original_from_component.inflate()[-1]
                    if inflated_from_component is not original_from_component:
                        resolved_from_component_name = inflated_from_component.name
                    else:
                        resolved_from_component_name = original_from_component_name
                    resolved_from_component = self._components.find(
                        resolved_from_component_name
                    )
                    enriched_component.weave_from_topics(
                        resolved_from_component.to, from_topic
                    )
            elif self._components:
                # read from previous component
                prev_component = self._components.last
                enriched_component.weave_from_topics(prev_component.to)
            self._components.add(enriched_component)

    def enrich_component(
        self,
        component: PipelineComponent,
        env_components_index: dict[str, dict],
    ) -> PipelineComponent:
        """Enrich a pipeline component with env-specific config and substitute variables

        :param component: Component to be enriched
        :type component: PipelineComponent
        :returns: Enriched component
        :rtype: PipelineComponent
        """
        component.validate_ = True
        env_component_as_dict = update_nested_pair(
            env_components_index.get(component.name, {}),
            # HACK: Pydantic .dict() doesn't create jsonable dict
            json.loads(component.json(by_alias=True)),
        )

        component_data = self.substitute_in_component(env_component_as_dict)

        component_class = type(component)
        return component_class(
            enrich=False,
            config=self._config,
            handlers=self._handlers,
            **component_data,
        )

    def substitute_in_component(self, component_as_dict: dict) -> dict:
        """Substitute all $-placeholders in a component in dict representation

        :param component_as_dict: Component represented as dict
        :type component_as_dict: dict
        :return: Updated component
        :rtype: dict
        """
        config = self._config
        # Leftover variables that were previously introduced in the component by the substitution
        # functions, still hardcoded, because of their names.
        # TODO: Get rid of them
        substitution_hardcoded = {
            "error_topic_name": config.topic_name_config.default_error_topic_name,
            "output_topic_name": config.topic_name_config.default_output_topic_name,
        }
        component_substitution = generate_substitution(
            component_as_dict,
            "component",
            substitution_hardcoded,
        )
        substitution = generate_substitution(
            json.loads(config.json()), existing_substitution=component_substitution
        )

        return json.loads(
            substitute_nested(
                json.dumps(component_as_dict),
                **update_nested_pair(substitution, ENV),
            )
        )
