from kpops.component_handlers.kubernetes.utils import trim
from kpops.manifests.kubernetes import K8S_LABEL_MAX_LEN

RELEASE_NAME_MAX_LEN = 53


def create_helm_release_name(name: str, suffix: str = "") -> str:
    """Shortens the long Helm release name.

    :param name: The Helm release name to be shortened.
    :param suffix: The release suffix to preserve
    :return: Trimmed + hashed version of the release name if it exceeds the Helm release character length, otherwise the input name
    """
    return trim(RELEASE_NAME_MAX_LEN, name, suffix)


def create_helm_name_override(name: str, suffix: str = "") -> str:
    """Create Helm chart name override.

    :param name: The Helm name override to be shortened.
    :param suffix: The release suffix to preserve
    :return: Trimmed + hashed version of the name override if it exceeds the Kubernetes character length, otherwise the input name
    """
    return trim(K8S_LABEL_MAX_LEN, name, suffix)
