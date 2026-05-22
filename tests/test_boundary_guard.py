from pathlib import Path

from comp_scenario_packs.boundaries import (
    find_forbidden_comp_imports,
    scan_python_files,
)


ROOT = Path(__file__).resolve().parents[1]


def test_detects_forbidden_comp_test_and_private_imports():
    source = "\n".join(
        [
            "from comp.tests.domain_scenarios import helpers",
            "import comp._internal",
            "from comp.scenario_contracts import run_scenario",
            "import comp.compiler_tool",
            "from comp import ProjectionSpec",
        ]
    )

    violations = find_forbidden_comp_imports(source, path=Path("pack.py"))

    assert [(item.path, item.module, item.line, item.reason) for item in violations] == [
        ("pack.py", "comp.tests.domain_scenarios", 1, "comp_tests_import"),
        ("pack.py", "comp._internal", 2, "private_comp_import"),
    ]


def test_repository_python_files_do_not_import_internal_comp_surfaces():
    violations = scan_python_files(ROOT)

    assert violations == ()
