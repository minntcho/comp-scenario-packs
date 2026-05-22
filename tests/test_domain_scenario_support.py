from pathlib import Path

import tomllib

from comp_scenario_packs.domains.esg_energy.filters import (
    get_energy_projection_filter,
)


ROOT = Path(__file__).resolve().parents[1]


def test_esg_energy_filter_preset_returns_copy():
    first = get_energy_projection_filter("plant_diesel_jan")
    second = get_energy_projection_filter("plant_diesel_jan")

    assert first == {
        "activity_type": "diesel",
        "period": "2026-01",
        "site": "plant-a",
    }
    assert first is not second


def test_domain_scenario_support_doc_defines_non_authority_boundary():
    doc = (ROOT / "docs" / "domain-scenario-support.md").read_text(
        encoding="utf-8"
    )

    assert "must not authorize receipts" in doc
    assert "must not bypass replay" in doc
    assert "must not replace comp projection authority" in doc


def test_scenario_support_blueprint_documents_operational_layout():
    doc = (ROOT / "docs" / "scenario-support-blueprint.md").read_text(
        encoding="utf-8"
    )

    required_phrases = [
        "comp is the trust kernel",
        "comp-scenario-packs is the reality rehearsal layer",
        "common/ contains domain-neutral benchmark machinery",
        "domains/ contains scenario fixtures and presets",
        "scenarios/ contains prepared canonical bundles",
        "Adding a new domain support helper",
        "Adding a nested scenario",
        "Do not put receipt authorization logic here",
        "Do not bypass replay",
        "Use --filter-preset when a domain helper owns the reusable query shape",
    ]
    for phrase in required_phrases:
        assert phrase in doc


def test_pyproject_includes_subpackages():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["tool"]["setuptools"]["packages"]["find"] == {
        "where": ["src"],
        "include": ["comp_scenario_packs*"],
    }
