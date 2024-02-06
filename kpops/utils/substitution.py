import json
from kpops.utils.dict_ops import generate_substitution, update_nested_pair
from kpops.utils.environment import ENV
from kpops.utils.types import JsonType
from kpops.utils.yaml import substitute_nested


def substitute_in_component(component_as_dict: dict, config) -> dict:
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
        component_as_dict,
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
            json.dumps(component_as_dict),
            **update_nested_pair(substitution, ENV),
        )
    )
