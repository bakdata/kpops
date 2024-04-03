import logging

log = logging.getLogger("docstring_utils")


def describe_attr(name: str, docstr: str | None) -> str:
    """Read attribute description from class docstring.

    **Works only with reStructuredText docstrings.**

    :param name: Attribute name
    :param docstr: Docstring from which to read. Note that the class' docstring is stored in attr ``__doc__``
    :returns: Description of the class attribute read from the class docstring
    """
    if docstr is None:
        return ""
    docstr = docstr.partition(f":param {name}:")[2]
    return _trim_description_end(docstr)


def describe_object(docstr: str | None) -> str:
    """Return description from an object's docstring.

    Excludes parameters and return definitions

    **Works only with reStructuredText docstrings.**

    :param docstr: The docstring
    :returns: Description taken from the docstring
    """
    if docstr is None:
        return ""

    # reST docstrings have a short description/title as their first line.
    # Optionally, they have a longer description below. Here we separate the
    # title from the rest with a newline as `_trim_description_end()`
    # removes all newlines.
    docstr = docstr.strip()
    if "\n" in docstr:
        title_end = docstr.index("\n")
        desc = docstr[:title_end] + "\n" + _trim_description_end(docstr[title_end:])
        return desc.rstrip()
    return _trim_description_end(docstr)


def _trim_description_end(desc: str) -> str:
    """Remove the unwanted text that comes after a description in a docstring.

    Also removes all whitespaces and newlines and replaces them with a single space.

    A description is defined here as a string of text written in natural language.
    A description ends at the occurence of a separator such as ``returns``.

    **Works only with reStructuredText docstrings.**

    :param desc: Description to be isolated, only the end will be trimmed
    :returns: Isolated description
    """
    desc_enders = [
        ":param ",
        ":returns:",
        ":raises:",
        "defaults to ",
    ]
    end_index = len(desc)
    for desc_ender in desc_enders:
        if (desc_ender in desc) and (desc.index(desc_ender) < end_index):
            end_index = desc.index(desc_ender)
    desc_split = desc[:end_index].split()
    for line in desc_split:
        line = line.rstrip()
    desc = " ".join(desc_split)
    return desc.rstrip(",").rstrip()
