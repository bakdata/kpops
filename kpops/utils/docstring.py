import logging

log = logging.getLogger("docstring_utils")


def describe_attr(name: str, docstr: str | None) -> str:
    """Read attribute description from class docstring

    Works only with reStructuredText docstrings.

    :param name: Attribute name
    :type name: str
    :param docstr: Docstring from which to read. Note that the class' docstring is stored in attr `__doc__`
    :type docstr: str, None
    :returns: Description of the class attribute read from the class docstring
    :rtype: str
    """
    if not isinstance(docstr, str):
        return ""

    docstr = docstr.partition(f":param {name}:")[2]
    docstr = _trim_description_end(docstr)

    return docstr


def describe_class(class_docstr: str | None) -> str:
    """Return class description from its docstring

    Excludes parameters and return definitions

    Works only with reStructuredText docstrings.

    :param class_docstr: Class whose description is to be isolated or the class' docstring
    :type class_docstr: type[BaseModel], str, None
    :returns: Class description taken from the class' docstring
    :rtype: str
    """

    class_docstr = _trim_description_end(class_docstr)

    return class_docstr


def _trim_description_end(desc: str | None) -> str:
    """Remove the unwanted text that comes after a description in a docstring

    A description is defined here as a string of text written in natural language.
    A description ends at the occurence of a separator such as `:returns:`

    Works only with reStructuredText docstrings.

    :param desc: Description to be isolated, only the end will be trimmed
    :type desc: str, None
    :returns: Isolated description
    :rtype: str
    """
    try:
        if not isinstance(desc, str):
            raise ValueError("Parameter `desc` must be a string.")
        end_index = len(desc)
    except (ValueError, TypeError):
        log.debug("Returned an empty string.", exc_info=True)
        return ""

    desc_enders: list[str] = [
        ":param ",
        ":type ",
        ":return:",
        ":rtype:",
        "defaults to ",
    ]

    for desc_ender in desc_enders:
        if (desc_ender in desc) and (desc.index(desc_ender) < end_index):
            end_index = desc.index(desc_ender)

    desc = desc[:end_index].strip().rstrip(",")

    return desc
