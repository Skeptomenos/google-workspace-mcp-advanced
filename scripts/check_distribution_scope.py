"""Distribution scope guard for uvx-first packaging references."""

from __future__ import annotations

from pathlib import Path

import tomllib


def _read_project_version(pyproject_path: Path) -> str:
    data = tomllib.loads(_read_text(pyproject_path))
    version = str(data.get("project", {}).get("version", "")).strip()
    if not version:
        raise ValueError(f"{pyproject_path}: project.version is empty")
    return version


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check_readme(readme_path: Path, expected_version: str) -> list[str]:
    errors: list[str] = []
    readme = _read_text(readme_path)

    required_snippets = (
        "uvx google-workspace-mcp-advanced --transport stdio",
        f"uvx google-workspace-mcp-advanced=={expected_version} --transport stdio",
    )
    for snippet in required_snippets:
        if snippet not in readme:
            errors.append(f"{readme_path}: missing required snippet: {snippet!r}")

    return errors


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    readme_path = repo_root / "README.md"
    pyproject_path = repo_root / "pyproject.toml"

    errors: list[str] = []
    expected_version = ""
    if not pyproject_path.exists():
        errors.append(f"missing required file: {pyproject_path}")
    else:
        try:
            expected_version = _read_project_version(pyproject_path)
        except ValueError as exc:
            errors.append(str(exc))

    if not readme_path.exists():
        errors.append(f"missing required file: {readme_path}")
    else:
        if expected_version:
            errors.extend(_check_readme(readme_path, expected_version))

    if errors:
        for error in errors:
            print(error)
        return 1

    print("distribution scope check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
