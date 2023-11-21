import hashlib
import logging

log = logging.getLogger("HelmUtils")

ENCODING = "utf-8"


def create_helm_release_name(name: str) -> str:
    """Shortens the long Helm release name. Creates a 40 character (SHA-1 is 160 bits) long release name.

    :param: name: The Helm release name to be shortened.
    :return: SHA-1 encoded String
    """
    return hashlib.sha1(name.encode(ENCODING)).hexdigest()
