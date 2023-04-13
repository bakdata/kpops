import logging
from pydantic import BaseModel

log = logging.getLogger("docstring_utils")


def describe_attr(name: str, docstr: str) -> str:
    """Read attribute description from class docstring

    Works only with reStructuredText docstrings.

    :param name: Attribute name
    :type name: str
    :param docstr: Docstring from which to read, Class' docstring is stored in attr `__doc__`
    :type docstr: str
    :returns: Description of the class attribute read from the class docstring
    :rtype: str
    """
    docstr = docstr.partition(f":param {name}:")[2]

    docstr = _trim_description_end(docstr)

    return docstr


def describe_class(class_: type[BaseModel]) -> str:
    """Returns class description from docstring

    Excludes parameters and return definitions

    Works only with reStructuredText docstrings.

    :param class_: Class whose description is to be isolated
    :type class_: type[BaseModel]
    :returns: Class description taken from the class' docstring
    :rtype: str
    """

    class_doc = _trim_description_end(class_.__doc__)

    return class_doc


def _trim_description_end(desc: str) -> str:
    """Removes the unwanted text that comes after a description in a docstring

    A description is defined here as a string of text written in natural language.
    A description ends at the occurence of a separator such as `:returns:`

    Works only with reStructuredText docstrings.

    :param desc: Description to be isolated, only the end will be trimmed
    :type desc: str
    :returns: Isolated description
    :rtype: str
    """
    desc_enders: list[str] = [
        ":param ",
        ":type ",
        ":return:",
        ":rtype:",
        "defaults to ",
    ]

    try:
        if not isinstance(desc, str):
            raise ValueError("Parameter `desc` must be a string.")
        end_index = len(desc)
    except (ValueError, TypeError) as error:
        log.debug("%s, returned an empty string.", error, exc_info=True)
        return ""

    end_index = len(desc)

    for desc_ender in desc_enders:
        if (desc_ender in desc) and (desc.index(desc_ender) < end_index):
            end_index = desc.index(desc_ender)

    desc = desc[:end_index].strip()

    return desc
