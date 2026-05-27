from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "migration-checklist.md"


def test_migration_checklist_defines_shadow_migration_rules():
    assert CHECKLIST.exists()
    text = CHECKLIST.read_text(encoding="utf-8")

    required_fragments = [
        "# Scenario Pack Migration Checklist",
        "## Migration Rule",
        "## Keep In comp",
        "## Move To Scenario Packs",
        "## Shadow Run Before Removal",
        "shadowed_comp_scenarios",
        "parallel-validation",
        "discover_pack_metadata",
        "PackMetadataError",
        "public_surfaces",
        "ALLOWED_COMP_IMPORTS",
        "runnable_contracts",
        "authority_invariant",
        "source_refs",
        "provenance signal",
        "public_projection_smoke",
        "tests/domain_scenarios",
        "comp.scenario_contracts",
        "Do not remove internal smoke tests until the external pack is green in CI.",
    ]
    for fragment in required_fragments:
        assert fragment in text
