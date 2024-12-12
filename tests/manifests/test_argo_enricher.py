from typing import Any

import pytest

from kpops.manifests.argo import ArgoHook, ArgoSyncWave, enrich_annotations


@pytest.fixture
def empty_manifest() -> dict[str, Any]:
    return {}


@pytest.fixture
def manifest_with_annotations() -> dict[str, Any]:
    return {"annotations": {"existing-annotation": "annotation-value"}}


def test_argo_hook_enrich_empty_manifest(empty_manifest: dict[str, Any]):
    hook = ArgoHook.POST_DELETE
    enriched_manifest = enrich_annotations(empty_manifest, hook.key, hook.value)
    assert enriched_manifest["annotations"][hook.key] == hook.value
    assert len(enriched_manifest["annotations"]) == 1


def test_argo_hook_enrich_existing_annotations(
    manifest_with_annotations: dict[str, Any],
):
    hook = ArgoHook.POST_DELETE
    enriched_manifest = enrich_annotations(
        manifest_with_annotations, hook.key, hook.value
    )
    assert enriched_manifest["annotations"][hook.key] == hook.value
    assert enriched_manifest["annotations"]["existing-annotation"] == "annotation-value"


def test_argo_sync_wave_enrich_empty_manifest(empty_manifest):
    sync_wave = ArgoSyncWave(sync_wave=1)
    enriched_manifest = enrich_annotations(
        empty_manifest, sync_wave.key, sync_wave.value
    )
    assert enriched_manifest["annotations"][sync_wave.key] == sync_wave.value
    assert len(enriched_manifest["annotations"]) == 1


def test_argo_sync_wave_enrich_existing_annotations(
    manifest_with_annotations: dict[str, Any],
):
    sync_wave = ArgoSyncWave(sync_wave=2)
    enriched_manifest = enrich_annotations(
        manifest_with_annotations, sync_wave.key, sync_wave.value
    )
    assert enriched_manifest["annotations"][sync_wave.key] == sync_wave.value
    assert enriched_manifest["annotations"]["existing-annotation"] == "annotation-value"


def test_argo_sync_wave_multiple_enrichments(empty_manifest: dict[str, Any]):
    sync_wave_1 = ArgoSyncWave(sync_wave=1)
    sync_wave_2 = ArgoSyncWave(sync_wave=2)
    enriched_manifest = enrich_annotations(
        empty_manifest, sync_wave_1.key, sync_wave_1.value
    )
    enriched_manifest = enrich_annotations(
        enriched_manifest, sync_wave_2.key, sync_wave_2.value
    )
    assert enriched_manifest["annotations"][sync_wave_1.key] == sync_wave_2.value
    assert len(enriched_manifest["annotations"]) == 1
