import hashlib
import logging

log = logging.getLogger("HelmUtils")

ENCODING = "utf-8"
RELEASE_NAME_MAX_LEN = 52


def create_helm_release_name(name: str) -> str:
    """Shortens the long Helm release name.

    Creates a 52 character long release name if the name length exceeds the Helm release character length.
    It first trims the string and fetches the first 52 characters.
    Then it replaces the last 5 characters with the SHA-1 encoded string to avoid collision.

    :param: name: The Helm release name to be shortened.
    :return: SHA-1 encoded String
    """
    if len(name) > RELEASE_NAME_MAX_LEN:
        exact_name = name[:RELEASE_NAME_MAX_LEN]
        hash_name = hashlib.sha1(name.encode(ENCODING)).hexdigest()
        new_name = exact_name[:-6] + "-" + hash_name[len(hash_name) - 4 :]
        log.critical(
            f"Invalid Helm release name '{name}'. Truncating to {RELEASE_NAME_MAX_LEN} characters: \n {name} --> {new_name}"
        )
        name = new_name
    return name
