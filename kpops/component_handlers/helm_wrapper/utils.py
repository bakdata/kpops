import logging

log = logging.getLogger("HelmUtils")


RELEASE_NAME_MAX_LEN = 52


def trim_release_name(name: str, suffix: str = "") -> str:
    """
    Trim Helm release name while preserving suffix.
    :param name: The release name including optional suffix
    :param suffix: The release suffix to preserve
    :return: Truncated release name
    """
    if len(name) > RELEASE_NAME_MAX_LEN:
        new_name = name[: (RELEASE_NAME_MAX_LEN - len(suffix))] + suffix
        log.critical(
            f"Invalid Helm release name '{name}'. Truncating to {RELEASE_NAME_MAX_LEN} characters: \n {name} --> {new_name}"
        )
        name = new_name
    return name
