from pathlib import Path


def test_foundation_files_exist() -> None:
    assert Path("AGENTS.md").exists()
    assert Path("pyproject.toml").exists()
    assert Path("configs/schema.yaml").exists()
    assert Path("src/capex_ai").exists()
    assert Path("tests").exists()
