from kpops.component_handlers.kubernetes.utils import trim

RELEASE_NAME_MAX_LEN = 53


def create_helm_release_name(name: str, suffix: str = "") -> str:
    """Shortens the long Helm release name.

    :param name: The Helm release name to be shortened.
    :param suffix: The release suffix to preserve
    :return: Trimmed + hashed version of the release name if it exceeds the Helm release character length otherwise the actual release name
    """
    return trim(RELEASE_NAME_MAX_LEN, name, suffix)
