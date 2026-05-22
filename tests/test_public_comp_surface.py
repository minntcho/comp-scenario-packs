from importlib import import_module


def test_scenario_pack_uses_public_comp_surfaces():
    comp = import_module("comp")
    compiler_tool = import_module("comp.compiler_tool")
    persistence = import_module("comp.persistence")
    scenario_contracts = import_module("comp.scenario_contracts")

    assert comp.__name__ == "comp"
    assert compiler_tool.__name__ == "comp.compiler_tool"
    assert callable(persistence.ArtifactEnvelope.from_body)
    assert callable(scenario_contracts.load_manifest)
    assert callable(scenario_contracts.run_scenario)
