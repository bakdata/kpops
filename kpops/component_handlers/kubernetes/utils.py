import hashlib
import logging

log = logging.getLogger("K8sUtils")


def trim(max_len: int, name: str, suffix: str) -> str:
    """Shortens long K8s identifiers.

    Kubernetes has a character limit for certain identifiers.
    If the name exceeds the character limit:
    1. trim the string and fetch the first ``max_len - len(suffix)`` characters.
    2. replace the last 6 characters with the SHA-1 encoded string (with "-") to avoid collision
    3. append the suffix if given

    :param name: The name to be shortened.
    :param suffix: The release suffix to preserve
    :return: Trimmed + hashed version of the name if it exceeds the character length otherwise the actual name
    """
    if len(name) > max_len:
        exact_name = name[: max_len - len(suffix)]
        hash_name = hashlib.sha1(name.encode()).hexdigest()
        new_name = exact_name[:-6] + "-" + hash_name[:5] + suffix
        log.critical(
            f"Kubernetes identifier '{name}' exceeds character limit. Truncating and hashing to {max_len} characters: \n {name} --> {new_name}"
        )
        return new_name
    return name
