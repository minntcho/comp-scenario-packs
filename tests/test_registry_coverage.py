from comp_scenario_packs import (
    SCENARIO_PACKS as TOP_LEVEL_SCENARIO_PACKS,
    discover_registered_scenario_packs as top_level_discover_registered_scenario_packs,
)
from comp_scenario_packs.metadata import PackMetadata, SourceRef, discover_pack_metadata
from comp_scenario_packs.registry import (
    AUTHORITY_POLICY,
    COMP_DEPENDENCY_BEFORE_V1,
    SCENARIO_PACKS,
    discover_registered_scenario_packs,
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
                "runnable_contracts": ["canonical_projection_smoke"],
                "source_refs": [
                    {
                        "repo": "minntcho/example-platform",
                        "path": "tests/e2e/cases/metadata-only.yaml",
                    }
                ],
            }
        ],
    }


def test_scenario_pack_coverage_uses_checked_in_metadata_by_default():
    coverage = scenario_pack_coverage()
    explicit_coverage = scenario_pack_coverage(discover_pack_metadata("scenarios"))

    assert len(coverage["packs"]) == len(SCENARIO_PACKS)
    assert coverage == explicit_coverage


def test_scenario_pack_coverage_respects_empty_metadata_input():
    coverage = scenario_pack_coverage(())

    assert coverage["covered_comp_scenario_ids"] == []
    assert coverage["cutover_states"] == []
    assert coverage["packs"] == []


def test_registered_scenario_packs_are_derived_from_checked_in_metadata():
    assert SCENARIO_PACKS == discover_registered_scenario_packs("scenarios")


def test_registered_scenario_packs_can_be_derived_from_any_metadata_root(tmp_path):
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir()
    (pack_dir / "pack.json").write_text(
        """
        {
          "schema_version": 1,
          "pack_id": "derived_pack",
          "status": "experimental",
          "scope": "metadata-derived-registry-smoke",
          "cutover_state": "parallel-validation",
          "covers_comp_scenario_ids": ["derived.scenario.v1"],
          "comp_relationship": "public_api_consumer",
          "authority_policy": "compatibility_signal_not_authority_source",
          "public_surfaces": ["comp.scenario_contracts"],
          "input_mode": "canonical_bundle",
          "scenario_manifest": "scenario.json",
          "prepared_inputs": [
            "prepared/runtime_case.json",
            "prepared/artifact_envelopes.jsonl"
          ]
        }
        """,
        encoding="utf-8",
    )

    packs = discover_registered_scenario_packs(tmp_path)

    assert [pack.pack_id for pack in packs] == ["derived_pack"]
    assert packs[0].covered_comp_scenario_ids == ("derived.scenario.v1",)


def test_top_level_registry_exports_remain_metadata_derived_convenience():
    assert TOP_LEVEL_SCENARIO_PACKS == SCENARIO_PACKS
    assert top_level_discover_registered_scenario_packs("scenarios") == SCENARIO_PACKS
