"""
Gold orchestrator: read silver → optional builder → gold-ready value.

Used by the gold pipeline (``run_gold`` in a later phase). No scraping, no .pkl cache.
"""

from __future__ import annotations

from pipelines.bronze.partitioning import SNAPSHOT_VALUE, is_snapshot_dataset
from pipelines.gold import registry
from pipelines.gold._io import (
    read_silver_partition,
    read_silver_partitions,
    read_silver_range,
)
from pipelines.gold.contracts import (
    BUILDER_NAMES,
    BUILDER_SILVER_DATASETS,
    BuilderContext,
    BuilderName,
    GoldMaterialized,
    SilverFrames,
    is_snapshot_only_builder,
)


class GoldOrchestrator:
    """Load silver datasets and materialize one gold builder output."""

    def read_silver(
        self,
        name: BuilderName,
        start_date: str | None = None,
        end_date: str | None = None,
        ctx: BuilderContext | None = None,
    ) -> SilverFrames:
        """
        Read silver tables required by ``name``.

        Snapshot-only builders (e.g. feriados) read the full snapshot; ``start_date``
        and ``end_date`` are optional and ignored if provided.

        Partitioned builders with ``ctx.dates`` read only those partitions (no range).
        Otherwise ``start_date`` and ``end_date`` are required.
        """
        if name not in BUILDER_NAMES:
            raise ValueError(f"Unknown builder: {name}. Allowed: {BUILDER_NAMES}")

        datasets = BUILDER_SILVER_DATASETS.get(name, ())
        if not datasets:
            return {}

        snapshot_only = is_snapshot_only_builder(name)
        use_dates = bool(ctx and ctx.dates)

        if not snapshot_only and not use_dates and (not start_date or not end_date):
            raise ValueError(
                f"Builder '{name}' requires start_date and end_date, or ctx.dates "
                "(partitioned datasets)."
            )

        frames: SilverFrames = {}
        for dataset in datasets:
            if is_snapshot_dataset(dataset):
                frames[dataset] = read_silver_partition(dataset, SNAPSHOT_VALUE)
            elif use_dates and ctx is not None:
                frames[dataset] = read_silver_partitions(
                    dataset, ctx.dates, skip_missing=True
                )
            else:
                frames[dataset] = read_silver_range(
                    dataset, start_date, end_date, only_existing=True
                )
        return frames

    def materialize(
        self,
        name: BuilderName,
        start_date: str | None = None,
        end_date: str | None = None,
        ctx: BuilderContext | None = None,
    ) -> GoldMaterialized:
        """Read silver for ``name`` and run its materializer or builder."""
        base = ctx or BuilderContext()
        run_ctx = BuilderContext(
            start_date=base.start_date if base.start_date is not None else start_date,
            end_date=base.end_date if base.end_date is not None else end_date,
            dates=base.dates,
            as_of_date=base.as_of_date,
            extras=base.extras,
        )
        silver = self.read_silver(name, start_date, end_date, ctx=run_ctx)
        value = registry.build(name, silver, run_ctx)
        return GoldMaterialized(name=name, silver=silver, value=value)

    def read_feriados(self) -> SilverFrames:
        """Read full feriados snapshot from silver (no date range)."""
        return self.read_silver("feriados")

    def materialize_feriados(self, ctx: BuilderContext | None = None) -> GoldMaterialized:
        """Materialize feriados: ``value`` is ``list[str]`` ISO dates for SQL."""
        return self.materialize("feriados", ctx=ctx)

    def materialize_cdi(
        self,
        dates: list[str],
        ctx: BuilderContext | None = None,
    ) -> GoldMaterialized:
        """Materialize CDI for ``dates``: ``value`` is a DataFrame for SQL insert."""
        base = ctx or BuilderContext()
        run_ctx = BuilderContext(
            dates=dates,
            start_date=base.start_date,
            end_date=base.end_date,
            as_of_date=base.as_of_date,
            extras=base.extras,
        )
        return self.materialize("cdi", ctx=run_ctx)

    def materialize_ptax(
        self,
        dates: list[str],
        ctx: BuilderContext | None = None,
    ) -> GoldMaterialized:
        """Materialize PTAX USD for ``dates``: ``value`` is a DataFrame for SQL insert."""
        base = ctx or BuilderContext()
        run_ctx = BuilderContext(
            dates=dates,
            start_date=base.start_date,
            end_date=base.end_date,
            as_of_date=base.as_of_date,
            extras=base.extras,
        )
        return self.materialize("ptax", ctx=run_ctx)

    def materialize_bmf(
        self,
        dates: list[str],
        ctx: BuilderContext | None = None,
    ) -> GoldMaterialized:
        """Materialize BMF ajustes for ``dates``: ``value`` is a DataFrame for SQL insert."""
        base = ctx or BuilderContext()
        run_ctx = BuilderContext(
            dates=dates,
            start_date=base.start_date,
            end_date=base.end_date,
            as_of_date=base.as_of_date,
            extras=base.extras,
        )
        return self.materialize("bmf", ctx=run_ctx)

    def materialize_mercado_secundario(
        self,
        dates: list[str],
        ctx: BuilderContext | None = None,
    ) -> GoldMaterialized:
        """Materialize mercado secundario for ``dates``: ``value`` is a DataFrame for SQL."""
        base = ctx or BuilderContext()
        run_ctx = BuilderContext(
            dates=dates,
            start_date=base.start_date,
            end_date=base.end_date,
            as_of_date=base.as_of_date,
            extras=base.extras,
        )
        return self.materialize("mercado_secundario", ctx=run_ctx)

    def materialize_liquidacoes_mercado(
        self,
        dates: list[str],
        ctx: BuilderContext | None = None,
    ) -> GoldMaterialized:
        """Materialize liquidações mercado for ``dates``: ``value`` is a DataFrame for SQL."""
        base = ctx or BuilderContext()
        run_ctx = BuilderContext(
            dates=dates,
            start_date=base.start_date,
            end_date=base.end_date,
            as_of_date=base.as_of_date,
            extras=base.extras,
        )
        return self.materialize("liquidacoes_mercado", ctx=run_ctx)

    def materialize_many(
        self,
        names: list[BuilderName],
        start_date: str | None = None,
        end_date: str | None = None,
        ctx: BuilderContext | None = None,
    ) -> dict[BuilderName, GoldMaterialized]:
        """Run ``materialize`` for each builder (snapshot-only names ignore dates)."""
        return {name: self.materialize(name, start_date, end_date, ctx) for name in names}
