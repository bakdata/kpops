from textwrap import dedent

import pytest

from kpops.manifests.kubernetes import KubernetesManifest, ObjectMeta


class TestCRD(KubernetesManifest):
    api_version: str = "v1"
    kind: str = "TestCRD"


@pytest.fixture
def crd_manifest() -> TestCRD:
    return TestCRD(metadata=ObjectMeta.model_validate({"foo": "bar"}))


@pytest.fixture
def example_manifest() -> KubernetesManifest:
    """Fixture providing an example KubernetesManifest instance."""
    metadata = ObjectMeta(
        name="example",
        namespace="default",
        labels={"app": "test"},
    )
    return KubernetesManifest(
        api_version="v1",
        kind="Deployment",
        metadata=metadata,
    )


def test_serialize_model_include_required_fields(crd_manifest: TestCRD):
    """Test that the serialize_model method excludes unset fields."""
    serialized = crd_manifest.model_dump()
    expected_serialized = {
        "apiVersion": "v1",
        "kind": "TestCRD",
        "metadata": {"foo": "bar"},
    }
    assert serialized == expected_serialized


def test_serialize_model_excludes_none(example_manifest: KubernetesManifest):
    """Test that the serialize_model method excludes unset fields."""
    serialized = example_manifest.model_dump()
    expected_serialized = {
        "apiVersion": "v1",
        "kind": "Deployment",
        "metadata": {
            "name": "example",
            "namespace": "default",
            "labels": {"app": "test"},
        },
    }
    assert serialized == expected_serialized


def test_serialize_model_includes_required_fields():
    """Test that required fields are always included in serialization."""
    metadata = ObjectMeta(name="example", namespace="default")
    manifest = KubernetesManifest(api_version="v1", kind="Pod", metadata=metadata)
    serialized = manifest.model_dump()
    assert "apiVersion" in serialized
    assert "kind" in serialized
    assert "metadata" in serialized


def test_from_yaml_parsing():
    """Test the from_yaml method parses YAML into KubernetesManifest objects."""
    yaml_content = dedent(
        """
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: test-service
      namespace: test-namespace

    ---
    apiVersion: v1
    kind: Pod
    metadata:
      name: test-pod
      namespace: test-namespace
    """
    )
    manifests = list(KubernetesManifest.from_yaml(yaml_content))
    assert len(manifests) == 2
    assert manifests[0].api_version == "v1"
    assert manifests[0].kind == "Service"
    assert manifests[0].metadata.name == "test-service"
    assert manifests[1].kind == "Pod"
    assert manifests[1].metadata.name == "test-pod"


def test_model_dump_json_output(example_manifest: KubernetesManifest):
    """Test the model_dump method for JSON output."""
    dumped = example_manifest.model_dump()
    expected_dumped = {
        "apiVersion": "v1",
        "kind": "Deployment",
        "metadata": {
            "name": "example",
            "namespace": "default",
            "labels": {"app": "test"},
        },
    }
    assert dumped == expected_dumped


def test_objectmeta_serialization():
    """Test ObjectMeta serialization with optional fields."""
    metadata = ObjectMeta(
        name="example",
        namespace="default",
        labels={"app": "test"},
        annotations=None,  # This field should be included
    )
    serialized = metadata.model_dump()
    expected_serialized = {
        "annotations": None,
        "name": "example",
        "namespace": "default",
        "labels": {"app": "test"},
    }
    assert serialized == expected_serialized
