from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportViolation:
    path: str
    module: str
    line: int
    reason: str


ALLOWED_COMP_IMPORTS = (
    "comp",
    "comp.compiler_tool",
    "comp.persistence",
    "comp.runtime",
    "comp.scenario_contracts",
)


def find_forbidden_comp_imports(
    source: str,
    *,
    path: Path,
) -> tuple[ImportViolation, ...]:
    tree = ast.parse(source)
    violations: list[ImportViolation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                reason = _forbidden_reason(alias.name)
                if reason is not None:
                    violations.append(
                        ImportViolation(
                            path=str(path),
                            module=alias.name,
                            line=node.lineno,
                            reason=reason,
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            reason = _forbidden_reason(module)
            if reason is None and module == "comp":
                private_names = [
                    alias.name for alias in node.names if alias.name.startswith("_")
                ]
                if private_names:
                    reason = "private_comp_import"
                    module = f"comp.{private_names[0]}"
            if reason is not None:
                violations.append(
                    ImportViolation(
                        path=str(path),
                        module=module,
                        line=node.lineno,
                        reason=reason,
                    )
                )
    return tuple(violations)


def scan_python_files(root: Path) -> tuple[ImportViolation, ...]:
    root = root.resolve()
    violations: list[ImportViolation] = []
    for path in sorted(root.rglob("*.py")):
        if _should_skip(path, root=root):
            continue
        relative_path = path.relative_to(root)
        violations.extend(
            find_forbidden_comp_imports(
                path.read_text(encoding="utf-8"),
                path=relative_path,
            )
        )
    return tuple(violations)


def _forbidden_reason(module: str) -> str | None:
    if module == "comp.tests" or module.startswith("comp.tests."):
        return "comp_tests_import"
    if module == "tests.domain_scenarios" or module.startswith(
        "tests.domain_scenarios."
    ):
        return "comp_tests_import"
    if module == "comp._internal" or module.startswith("comp._"):
        return "private_comp_import"
    if module.startswith("comp.") and module not in ALLOWED_COMP_IMPORTS:
        return "undeclared_comp_surface"
    return None


def _should_skip(path: Path, *, root: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    ignored_dirs = {"__pycache__", ".git", ".pytest_cache", ".venv", "build", "dist"}
    return any(part in ignored_dirs for part in relative_parts)


__all__ = [
    "ALLOWED_COMP_IMPORTS",
    "ImportViolation",
    "find_forbidden_comp_imports",
    "scan_python_files",
]
