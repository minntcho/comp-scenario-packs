from pathlib import Path

import tomllib

from comp_scenario_packs.domains.esg_energy.filters import (
    get_energy_projection_filter,
)
from comp_scenario_packs.domains.esg_energy.fields import (
    get_energy_projection_fields,
)
from comp_scenario_packs.domains.esg_energy.rows import get_energy_projection_rows
from comp_scenario_packs.domains.presets import get_projection_row_preset


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


def test_esg_energy_projection_fields_describe_public_activity_rows():
    assert get_energy_projection_fields("pcf_activity_public_v0") == (
        "supplier_id",
        "site",
        "period",
        "activity_type",
        "amount",
        "unit",
        "emissions_kgco2e",
    )


def test_esg_energy_row_preset_returns_selective_query_rows():
    rows = get_energy_projection_rows("mixed_activity_rows")

    assert rows[0] == {
        "activity_type": "diesel",
        "amount": 1200,
        "emissions_kgco2e": 3216,
        "period": "2026-01",
        "site": "plant-a",
        "supplier_id": "supplier:l-energy-fuel-a",
        "unit": "L",
    }
    assert rows[1]["activity_type"] == "electricity"
    assert rows[2]["site"] == "plant-b"

    mutated = rows[0]
    mutated["activity_type"] = "changed"
    assert get_energy_projection_rows("mixed_activity_rows")[0]["activity_type"] == (
        "diesel"
    )


def test_domain_preset_resolver_returns_esg_energy_rows():
    rows = get_projection_row_preset("esg_energy:mixed_activity_rows")

    assert len(rows) == 4
    assert rows[0]["activity_type"] == "diesel"


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
        "Use --row-preset when a domain helper owns the reusable row mix",
    ]
    for phrase in required_phrases:
        assert phrase in doc


def test_pyproject_includes_subpackages():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["tool"]["setuptools"]["packages"]["find"] == {
        "where": ["src"],
        "include": ["comp_scenario_packs*"],
    }
