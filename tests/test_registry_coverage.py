from comp_scenario_packs.metadata import PackMetadata, SourceRef
from comp_scenario_packs.registry import (
    AUTHORITY_POLICY,
    COMP_DEPENDENCY_BEFORE_V1,
    SCENARIO_PACKS,
    scenario_pack_coverage,
)


def test_scenario_pack_coverage_uses_metadata_when_provided():
    metadata = PackMetadata(
        pack_id="metadata_only_pack",
        status="experimental",
        scope="metadata-first-coverage-smoke",
        cutover_state="parallel-validation",
        covers_comp_scenario_ids=("metadata.scenario.v1",),
        comp_relationship="public_api_consumer",
        authority_policy=AUTHORITY_POLICY,
        public_surfaces=("comp.scenario_contracts",),
        input_mode="canonical_bundle",
        scenario_manifest="scenario.json",
        prepared_inputs=(
            "prepared/runtime_case.json",
            "prepared/artifact_envelopes.jsonl",
        ),
        runnable_contracts=("canonical_projection_smoke",),
        source_refs=(
            SourceRef(
                repo="minntcho/example-platform",
                path="tests/e2e/cases/metadata-only.yaml",
            ),
        ),
    )

    coverage = scenario_pack_coverage((metadata,))

    assert coverage == {
        "comp_dependency": COMP_DEPENDENCY_BEFORE_V1,
        "covered_comp_scenario_ids": ["metadata.scenario.v1"],
        "cutover_states": ["parallel-validation"],
        "packs": [
            {
                "pack_id": "metadata_only_pack",
                "status": "experimental",
                "scope": "metadata-first-coverage-smoke",
                "cutover_state": "parallel-validation",
                "covered_comp_scenario_ids": ["metadata.scenario.v1"],
                "authority_policy": AUTHORITY_POLICY,
                "comp_relationship": "public_api_consumer",
                "source_refs": [
                    {
                        "repo": "minntcho/example-platform",
                        "path": "tests/e2e/cases/metadata-only.yaml",
                    }
                ],
            }
        ],
    }


def test_scenario_pack_coverage_keeps_registry_fallback_without_metadata():
    coverage = scenario_pack_coverage()

    assert len(coverage["packs"]) == len(SCENARIO_PACKS)


def test_scenario_pack_coverage_respects_empty_metadata_input():
    coverage = scenario_pack_coverage(())

    assert coverage["covered_comp_scenario_ids"] == []
    assert coverage["cutover_states"] == []
    assert coverage["packs"] == []
