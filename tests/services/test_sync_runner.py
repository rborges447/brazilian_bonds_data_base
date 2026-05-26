"""Tests for daily sync task filtering (dataset scope vs gold builder names)."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.sync_runner import _filter_tasks


@dataclass(frozen=True)
class _Task:
    name: str


def test_filter_gold_includes_bmf_builder_for_ajustes_bmf_dataset() -> None:
    tasks = [_Task("cdi"), _Task("bmf"), _Task("ipca_dict"), _Task("feriados")]
    filtered = _filter_tasks(tasks, ["ajustes_bmf"])
    names = {t.name for t in filtered}
    assert names == {"bmf"}


def test_filter_gold_includes_ipca_dict_for_ipca_indice_dataset() -> None:
    tasks = [_Task("cdi"), _Task("bmf"), _Task("ipca_dict"), _Task("feriados")]
    filtered = _filter_tasks(tasks, ["ipca_indice"])
    names = {t.name for t in filtered}
    assert names == {"ipca_dict"}


def test_filter_gold_keeps_dataset_named_tasks() -> None:
    tasks = [_Task("cdi"), _Task("bmf")]
    filtered = _filter_tasks(tasks, ["cdi"])
    assert [t.name for t in filtered] == ["cdi"]
