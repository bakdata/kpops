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
    if docstr is None:
        log.debug("Returned an empty string.", exc_info=True)
        return ""

    docstr = docstr.partition(f":param {name}:")[2]

    return _trim_description_end(docstr)


def describe_class(docstr: str | None) -> str:
    """Return class description from its docstring

    Excludes parameters and return definitions

    Works only with reStructuredText docstrings.

    :param docstr: The class' docstring
    :type docstr: str, None
    :returns: Class description taken from its docstiirng
    :rtype: str
    """
    if docstr is None:
        log.debug("Returned an empty string.", exc_info=True)
        return ""

    return _trim_description_end(docstr)


def _trim_description_end(desc: str) -> str:
    """Remove the unwanted text that comes after a description in a docstring

    A description is defined here as a string of text written in natural language.
    A description ends at the occurence of a separator such as `:returns:`

    Works only with reStructuredText docstrings.

    :param desc: Description to be isolated, only the end will be trimmed
    :type desc: str
    :returns: Isolated description
    :rtype: str
    """
    desc_enders = [
        ":param ",
        ":type ",
        ":return:",
        ":rtype:",
        "defaults to ",
    ]

    end_index = len(desc)

    for desc_ender in desc_enders:
        if (desc_ender in desc) and (desc.index(desc_ender) < end_index):
            end_index = desc.index(desc_ender)

    desc = desc[:end_index].strip().rstrip(",")

    return desc
