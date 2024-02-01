import hashlib
import logging

log = logging.getLogger("HelmUtils")

ENCODING = "utf-8"
RELEASE_NAME_MAX_LEN = 53


def create_helm_release_name(name: str, suffix: str = "") -> str:
    """Shortens the long Helm release name.

    Helm has a limit of 53 characters for release names.
    If the name exceeds the character limit:
    1. trim the string and fetch the first ``RELEASE_NAME_MAX_LEN - len(suffix)`` characters.
    2. replace the last 6 characters with the SHA-1 encoded string (with "-") to avoid collision
    3. append the suffix if given

    :param name: The Helm release name to be shortened.
    :param suffix: The release suffix to preserve
    :return: Trimmed + hashed version of the release name if it exceeds the Helm release character length otherwise the actual release name
    """
    if len(name) > RELEASE_NAME_MAX_LEN:
        exact_name = name[: RELEASE_NAME_MAX_LEN - len(suffix)]
        hash_name = hashlib.sha1(name.encode(ENCODING)).hexdigest()
        new_name = exact_name[:-6] + "-" + hash_name[:5] + suffix
        log.critical(
            f"Invalid Helm release name '{name}'. Truncating and hashing the release name: \n {name} --> {new_name}"
        )
        return new_name
    return name
