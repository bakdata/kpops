import logging

log = logging.getLogger("HelmUtils")


RELEASE_NAME_MAX_LEN = 52


def trim_release_name(name: str, suffix: str = "") -> str:
    if len(name) + len(suffix) > RELEASE_NAME_MAX_LEN:
        new_name = name[: (RELEASE_NAME_MAX_LEN - len(suffix))] + suffix
        log.critical(
            f"The Helm release name {name} is invalid. We shorten it to {RELEASE_NAME_MAX_LEN} characters: \n {name + suffix} --> {new_name}"
        )
        name = new_name
    return name
