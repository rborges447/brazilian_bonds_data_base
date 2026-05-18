from importlib.metadata import version

import main


def test_package_version() -> None:
    assert version("brazil-fixed-income-analytics") == "0.2.0"


def test_main_entrypoint() -> None:
    assert callable(main.main)
