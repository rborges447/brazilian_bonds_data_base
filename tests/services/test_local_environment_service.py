from __future__ import annotations

from pathlib import Path

from app.services.local_environment_service import ensure_local_environment


def test_default_data_root_under_base(tmp_path: Path) -> None:
    env = ensure_local_environment(base=tmp_path, create=False)
    assert env.data_root == tmp_path / "data" / "brazilian_bonds_db"
    assert env.sqlite_db_path == env.data_root / "database" / "app.db"


def test_custom_relative_data_root(tmp_path: Path) -> None:
    env = ensure_local_environment(data_root="custom", base=tmp_path, create=False)
    assert env.data_root == tmp_path / "custom"
    assert env.sqlite_db_path == tmp_path / "custom" / "database" / "app.db"


def test_absolute_data_root(tmp_path: Path) -> None:
    abs_root = tmp_path / "abs_pkg"
    env = ensure_local_environment(data_root=abs_root, base=tmp_path, create=False)
    assert env.data_root == abs_root


def test_create_makes_layout_directories(tmp_path: Path) -> None:
    env = ensure_local_environment(data_root=tmp_path / "pkg", create=True)
    for path in (
        env.database_dir,
        env.bronze_root,
        env.silver_root,
        env.gold_root,
        env.logs_dir,
        env.metadata_dir,
    ):
        assert path.is_dir()
    assert env.sqlite_db_path.parent.is_dir()


def test_lake_paths_under_data_root(tmp_path: Path) -> None:
    env = ensure_local_environment(data_root=tmp_path / "pkg", create=False)
    assert env.lake_root == env.data_root / "lake"
    assert env.bronze_root == env.lake_root / "bronze"
    assert env.silver_root == env.lake_root / "silver"
    assert env.gold_root == env.lake_root / "gold"
