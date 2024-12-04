from typing import Any

import pytest

from kpops.manifests.argo import ArgoHook, ArgoSyncWave


@pytest.fixture
def empty_manifest() -> dict[str, Any]:
    return {}


@pytest.fixture
def manifest_with_annotations() -> dict[str, Any]:
    return {"annotations": {"existing-annotation": "annotation-value"}}


def test_argo_hook_enrich_empty_manifest(empty_manifest: dict[str, Any]):
    hook = ArgoHook.POST_DELETE
    enriched_manifest = hook.enrich(empty_manifest)
    assert enriched_manifest["annotations"][hook.key] == hook.value
    assert len(enriched_manifest["annotations"]) == 1


def test_argo_hook_enrich_existing_annotations(
    manifest_with_annotations: dict[str, Any],
):
    hook = ArgoHook.POST_DELETE
    enriched_manifest = hook.enrich(manifest_with_annotations)
    assert enriched_manifest["annotations"][hook.key] == hook.value
    assert enriched_manifest["annotations"]["existing-annotation"] == "annotation-value"


def test_argo_sync_wave_enrich_empty_manifest(empty_manifest):
    sync_wave = ArgoSyncWave().create(1)
    enriched_manifest = sync_wave.enrich(empty_manifest)
    assert enriched_manifest["annotations"][sync_wave.key] == sync_wave.value
    assert len(enriched_manifest["annotations"]) == 1


def test_argo_sync_wave_enrich_existing_annotations(
    manifest_with_annotations: dict[str, Any],
):
    sync_wave = ArgoSyncWave.create(2)
    enriched_manifest = sync_wave.enrich(manifest_with_annotations)
    assert enriched_manifest["annotations"][sync_wave.key] == sync_wave.value
    assert enriched_manifest["annotations"]["existing-annotation"] == "annotation-value"


def test_argo_sync_wave_multiple_enrichments(empty_manifest: dict[str, Any]):
    sync_wave_1 = ArgoSyncWave().create(1)
    sync_wave_2 = ArgoSyncWave.create(2)
    enriched_manifest = sync_wave_1.enrich(empty_manifest)
    enriched_manifest = sync_wave_2.enrich(enriched_manifest)
    assert enriched_manifest["annotations"][sync_wave_1.key] == sync_wave_2.value
    assert len(enriched_manifest["annotations"]) == 1
