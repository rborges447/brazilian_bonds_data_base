"""One-off builder for architecture + code reference docs. Run: python docs/_build_docs.py"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "app"

CURATED: dict[str, dict[str, str]] = {
    "lake/gold/orchestrator.py": {
        "papel": "Orquestra leitura silver e materialização gold (pass-through e builders).",
        "chamado_por": "notebooks, futuro run_gold.py, testes",
        "notas": "ipca_dict usa janela mensal, não ctx.dates como partição diária.",
    },
    "lake/gold/builders/ipca_dict.py": {
        "papel": "Regras de negócio IPCA diário (projeção, fechado, dia 15 útil).",
        "chamado_por": "registry._build_ipca_dict",
        "notas": "Não alterar fórmulas sem validação vs legado/notebook.",
    },
    "lake/bronze/extractors/_projecoes_split.py": {
        "papel": "Flatten/merge JSON projeções ANBIMA por reference_month.",
        "chamado_por": "extractors/projecoes.py",
        "notas": "Partição = mes_referencia do dado, não mês da consulta API.",
    },
}


def layer(path: Path) -> str:
    p = path.as_posix()
    if "lake/bronze" in p:
        return "bronze"
    if "lake/silver" in p:
        return "silver"
    if "lake/gold" in p:
        return "gold"
    if "providers" in p:
        return "providers"
    if "contracts" in p:
        return "contracts"
    if "config" in p:
        return "config"
    if "core" in p:
        return "core"
    if "database" in p:
        return "database"
    if "cli" in p:
        return "cli"
    return "outros"


def parse_module(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return {"error": str(e)}
    doc = ast.get_docstring(tree) or ""
    funcs: list[str] = []
    classes: list[str] = []
    internal: set[str] = set()
    external: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.col_offset == 0:
            funcs.append(node.name)
        elif isinstance(node, ast.ClassDef) and node.col_offset == 0:
            classes.append(node.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            m = node.module.split(".")[0]
            if m in ("app", "config", "contracts", "core", "providers", "lake", "database"):
                internal.add(node.module)
            elif m not in ("__future__", "typing", "dataclasses", "collections", "pathlib", "datetime", "logging", "json", "re", "functools", "abc"):
                external.add(m)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                m = alias.name.split(".")[0]
                if m in ("app", "config", "contracts", "core", "providers", "lake", "database"):
                    internal.add(alias.name)
                elif m not in ("__future__", "typing"):
                    external.add(m)
    return {
        "doc": doc.split("\n")[0][:200] if doc else "",
        "funcs": funcs,
        "classes": classes,
        "internal": sorted(internal),
        "external": sorted(external),
    }


def file_entry(rel: str, path: Path) -> str:
    meta = CURATED.get(rel, {})
    info = parse_module(path)
    if "error" in info:
        return f"### `{rel}`\n\n**Erro de parse:** {info['error']}\n\n"
    papel = meta.get("papel") or (info["doc"] or "(sem docstring de módulo)")
    lines = [
        f"### `{rel}`",
        "",
        f"**Papel:** {papel}",
        f"**Camada:** {layer(path)}",
    ]
    if info["classes"]:
        lines.append(f"**Classes:** `{', '.join(info['classes'])}`")
    if info["funcs"]:
        show = info["funcs"][:20]
        extra = f" (+{len(info['funcs'])-20})" if len(info["funcs"]) > 20 else ""
        lines.append(f"**Funções:** `{', '.join(show)}`{extra}")
    if info["internal"]:
        lines.append(f"**Importa (interno):** {', '.join(f'`{x}`' for x in info['internal'])}")
    if info["external"]:
        lines.append(f"**Importa (externo):** {', '.join(f'`{x}`' for x in info['external'])}")
    if meta.get("chamado_por"):
        lines.append(f"**Chamado por:** {meta['chamado_por']}")
    if meta.get("notas"):
        lines.append(f"**Notas para IA:** {meta['notas']}")
    elif rel.endswith("__init__.py"):
        lines.append("**Notas para IA:** reexporta API do pacote; ver imports no arquivo.")
    lines.append("")
    return "\n".join(lines)


def build_code_reference() -> str:
    parts = [
        "# Referência de código para IA",
        "",
        "> Documento gerado para onboarding de outra IA. Contexto de arquitetura: "
        "[project_architecture_and_dependencies.md](project_architecture_and_dependencies.md). "
        "Estudo histórico (bronze antigo): [project_bronze_architecture_study.md](project_bronze_architecture_study.md).",
        "",
        "## Como usar este documento",
        "",
        "### Ordem de leitura",
        "1. `app.config` → `app.contracts` → `app.core` → `app.providers`",
        "2. `app.lake/bronze` → `app.lake/silver` → `app.lake/gold`",
        "3. `run_bronze.py` / `run_silver.py` / `run_gold.py` → `tests/`",
        "",
        "### Convenções",
        "- `PYTHONPATH` inclui `src/`; imports canônicos: `from app.lake...`, `from app.config...`.",
        "- Dados em `{DATA_ROOT}/raw` (bronze) e `{DATA_ROOT}/silver` (silver), Hive `partition_key=value`.",
        "",
        "### O que o repositório NÃO faz hoje",
        "- Cálculo de títulos (PU, taxa, DV01) — futuro `titulospub`, fora deste repo.",
        "- API FastAPI / Dash — não implementados.",
        "- Persistência SQL gold via repositories (stub INSERT); `run_gold` não grava ainda.",
        "",
        "### Invariantes",
        "- **Bronze:** raw fiel à fonte; 1 artefato por partição.",
        "- **Silver:** schema canônico Parquet.",
        "- **Gold:** saída pronta para INSERT (`DataFrame` ou `list[str]`); sem chamar providers.",
        "",
        "### Arquivos sensíveis",
        "- `app/lake/gold/builders/ipca_dict.py` — regras fiscais IPCA.",
        "- Não copiar comportamento do `legacy/` sem diff explícito.",
        "",
        "---",
        "",
        "## Fluxos end-to-end",
        "",
        "### 1. Bronze daily",
        "`run_bronze.py` → `cmd_daily` → `resolve_bronze_tasks(end)` → `run_bronze_phase(tasks)` → "
        "para cada `DatasetTask`: `registry.extract_dataset(name, dates)` → extractor → `writer` → `ExtractResult`.",
        "",
        "### 2. Silver one dataset",
        "`run_silver.py` → `resolve_silver_tasks` → `run_silver_phase` → `read_bronze_partition` → "
        "`registry.get_transform(name).normalize_partition(df)` → `write_partition_parquet`.",
        "",
        "### 3. Gold pass-through (CDI)",
        "`GoldOrchestrator.materialize_cdi(dates)` → `read_silver` (partições diárias) → "
        "`registry.build` → `materializers/cdi.from_silver` → DataFrame `data_referencia, cdi`.",
        "",
        "### 4. Gold ipca_dict (diário)",
        "`materialize_ipca_dict(dates)` → `resolve_feriados_set` (gold ou silver) → "
        "`read_silver_range` mensal ipca+proj → para cada data `build_for_date` → `to_dataframe`. "
        "Regra `USA_FECHADO`: ref M-1 + antes do dia 15 útil + índices distintos.",
        "",
        "### 5. Projeções bronze merge",
        "`extract_projecoes` → API latest + meses candidatos → `flatten_projecoes_payload` → "
        "`merge_projecoes_records` por `data_coleta` → JSON em `reference_month=YYYY-MM-01`.",
        "",
        "---",
        "",
        "## Contratos de dados",
        "",
        "### Partições (bronze/silver)",
        "",
        "| dataset | partition_key | granularidade | artefato bronze |",
        "|---------|---------------|---------------|-----------------|",
        "| mercado_secundario | data | day | json |",
        "| liquidacoes_mercado | data | day | parquet |",
        "| ajustes_bmf | data | day | parquet |",
        "| leiloes | data | day | json |",
        "| ipca_indice | reference_month | month | parquet |",
        "| feriados | snapshot | snapshot | parquet |",
        "| projecoes | reference_month | month | json |",
        "| cdi | data | day | parquet |",
        "| ptax | data | day | parquet |",
        "",
        "### Gold builders",
        "",
        "| name | tipo | silver inputs | saída |",
        "|------|------|---------------|-------|",
        "| feriados..leiloes | materializer | 1 dataset | DataFrame ou list |",
        "| ipca_dict | builder+materializer | ipca_indice, projecoes | DataFrame diário |",
        "| vna_lft | stub | — | NotImplemented |",
        "",
        "### Tipos (`contracts/`)",
        "- `ExtractResult`, `BronzeResult`, `BronzeExtractor`",
        "- `SilverResult`, `SilverTransform`, `SilverPartitionRef`",
        "- Protocols em `contracts/providers.py`",
        "",
        "---",
        "",
        "## Índice por pacote",
        "",
    ]
    groups: dict[str, list[Path]] = {}
    for path in sorted(APP.rglob("*.py")):
        key = path.relative_to(APP).parts[0]
        if len(path.relative_to(APP).parts) > 1:
            key = "/".join(path.relative_to(APP).parts[:2])
        groups.setdefault(key, []).append(path)
    for key in sorted(groups):
        parts.append(f"## `{key}/`")
        parts.append("")
        for path in groups[key]:
            rel = path.relative_to(APP).as_posix()
            parts.append(file_entry(rel, path))
    # entrypoints
    parts.extend([
        "## Entrypoints (raiz do repo)",
        "",
        "### `run_bronze.py`",
        "**Papel:** CLI bronze: init, daily, one, backfill.",
        "**Chama:** `resolve_bronze_tasks`, `run_bronze`, `run_bronze_phase`, `missing_partition_values`.",
        "",
        "### `run_silver.py`",
        "**Papel:** CLI silver: init, daily, one, backfill.",
        "**Chama:** `resolve_silver_tasks`, `run_silver`, `run_silver_phase`.",
        "",
        "### `run_gold.py`",
        "**Papel:** CLI gold: init, one, backfill (sem INSERT SQL).",
        "",
        "### `src/main.py`",
        "**Papel:** `rf-analytics` dispatcher: bronze|silver|gold|migrate.",
        "",
        "## Testes (`tests/`)",
        "",
        "Rodar: `pytest tests/ -q`. Gold: `pytest tests/lake/gold/ -q`.",
        "",
        "| Teste | Garante |",
        "|-------|---------|",
        "| test_ipca_dict_builder | USA_FECHADO, slice mensal |",
        "| test_ipca_dict_orchestrator | feriados fallback, materialize |",
        "| test_leiloes_materializer | datas esparsas, dedup |",
        "| test_*_materializer (gold) | colunas SQL, filtros dates |",
        "| test_*_extractor (bronze) | extractors por fonte |",
        "| test_silver_pipeline | bronze→silver |",
        "",
        "## Legacy",
        "",
        "`legacy/rf_lake/` — monólito Bronze/Silver/Gold + SQLite. Equivalência: bronze→`app/lake/bronze`, "
        "silver→`app/lake/silver`, gold SQL→`app/database/` + `app/repositories/`.",
        "",
        "## Notebooks",
        "",
        "`notebooks/test_gold.ipynb` — protótipo; produção em `src/app/lake/gold/`.",
        "",
    ])
    return "\n".join(parts)


def build_architecture() -> str:
    return r"""# Arquitetura e dependências — Brazil Fixed Income Analytics

> **Documentação canônica** do código em `src/app/`. Referência por arquivo:
> [code_reference_for_ai.md](code_reference_for_ai.md).

## 1. Contexto

Data lake renda fixa Brasil: bronze → silver → gold → SQLite (futuro).

| Componente | Local |
|------------|-------|
| Aplicação | `src/app/` |
| Entry | `src/main.py`, `run_*.py` |
| Legado | `legacy/rf_lake/` |

## 2. Árvore `src/`

```
src/
  main.py
  app/
    cli/           bronze, silver, gold CLIs
    config/        settings, paths
    core/          dates, datasets, partitioning, exceptions
    contracts/     bronze, silver, provider protocols
    providers/     APIs externas
    lake/          bronze, silver, gold
    database/      connection, migrations
    repositories/  persistência gold (stub)
    services/      facades (ipca → lake builder)
    agents/        futuro
```

## 3. Fronteira de contratos

| Pacote | Conteúdo |
|--------|----------|
| `app/contracts/` | `ExtractResult`, `SilverTransform`, provider protocols |
| `app/lake/gold/contracts.py` | `BuilderName`, `BuilderContext`, `GoldMaterialized` |
| `app/core/` | calendário, datasets, particionamento |

## 4. Imports

`PYTHONPATH` = `src/`. Canônico: `from app.config import get_settings`, `from app.lake.gold import GoldOrchestrator`.

## 5. Entrypoints

- `python run_bronze.py` / `run_silver.py` / `run_gold.py`
- `rf-analytics bronze|silver|gold|migrate` via `src/main.py`

## 6. Regras

- `app/providers` não importa `app/lake`
- `app/lake/silver` não importa providers
- `app/lake/gold` não importa providers
- `app/services` delega IPCA a `app.lake.gold.builders.ipca_dict` (sem duplicar regras)

## 7. Testes

`pytest tests/ -q`

Detalhe por módulo: [code_reference_for_ai.md](code_reference_for_ai.md).
"""


def main() -> None:
    arch = ROOT / "docs" / "project_architecture_and_dependencies.md"
    code = ROOT / "docs" / "code_reference_for_ai.md"
    arch.write_text(build_architecture(), encoding="utf-8")
    code.write_text(build_code_reference(), encoding="utf-8")
    print(f"Wrote {arch} ({len(arch.read_text(encoding='utf-8'))} chars)")
    print(f"Wrote {code} ({len(code.read_text(encoding='utf-8'))} chars)")


if __name__ == "__main__":
    main()
