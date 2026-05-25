# Proposta de revisão — Feature 003 + README do pacote

**Data:** alinhamento pós conclusão das Features 001 e 002.

## Diagnóstico

| Item | Situação |
|------|----------|
| `app.public.read_data` / `update` | Implementado (001) |
| `brazilian_bonds_db` alias | Implementado (002) |
| Testes públicos | 19 testes em `tests/public/` |
| `docs/gold_reader_public_api.md` | Não existe |
| README consumidor (`bbdb.update`, `bbdb.read_data`) | Não documentado |

A Feature 003 deve deixar de ser tratada como **nova implementação de API** e passar a ser **contrato documentado + onboarding do usuário**.

---

## Spec 003 — texto sugerido para o topo de `spec.md`

Adicionar logo após o título:

```markdown
## Status e dependências

- **Pré-requisitos concluídos:** `001-public-database-api`, `002-import-alias-brazilian-bonds-db`
- **Escopo desta feature:** documentar o contrato de `read_data()`, validar paridade com `GoldReader`, atualizar README para consumidores do pacote
- **Fora de escopo:** reimplementar `read_data()`, novo alias, mudanças em lake/CLI (salvo menção em seção "contribuidores")
```

Substituir a seção "Objective" por:

```markdown
## Objective

Formalize and document the **public read contract** `read_data()` for package consumers.

Implementation already exists in `app.public.readers.read_data` and `brazilian_bonds_db.read_data`. This feature delivers:

1. Consumer-facing API reference (`docs/gold_reader_public_api.md`)
2. End-to-end README (install from GitHub → `update()` → `read_data()` → datasets)
3. Verification that documented datasets/methods match `GoldReader` (no invented APIs)
```

---

## Tasks 003 — revisão proposta

| Task antiga | Proposta |
|-------------|----------|
| **1** — Locate GoldReader + doc | **Manter.** Criar `docs/gold_reader_public_api.md` com seção "read_data public API" (datasets + métodos reais do `gold_reader.py`). |
| **2** — `app.public` | **Marcar concluída** (001). Opcional: 1 linha no doc referenciando `src/app/public/readers.py`. |
| **3** — `brazilian_bonds_db` | **Marcar concluída** (002). |
| **4** — Testes públicos | **Marcar concluída** (001/002). Opcional: link no doc para `tests/public/`. |
| **5** — README | **Expandir.** Não só snippet: README completo para consumidor (ver `docs/README_PACKAGE_USER_DRAFT.md`). |
| **Nova 6** (opcional) | Reorganizar README: seção **"Uso do pacote"** (consumidor) no topo; seção **"Desenvolvimento do repositório"** (CLI, `src/app`, contribuidores) abaixo ou em `docs/CONTRIBUTING_DEV.md`. |

**Agent rule** (tasks.md): manter "one task at a time", mas tasks 2–4 podem ser executadas como **verificação + checkbox** sem código.

---

## Acceptance criteria 003 — atualizados

- [ ] `docs/gold_reader_public_api.md` existe e lista datasets reais (`cdi`, `ptax`, …)
- [ ] README descreve fluxo GitHub → venv → `pip install -e .` → credenciais → `update()` → `read_data()`
- [ ] README **não** apresenta `GoldReader` como API principal do consumidor
- [ ] Testes `tests/public/` continuam verdes (regressão)
- [ ] Critérios de código de 001/002 permanecem satisfeitos (sem mudança obrigatória)

---

## README — estratégia

1. **Público principal:** quem clona/instala o pacote em outro projeto.
2. **Público secundário:** mantenedor do repo (CLI bronze/silver/gold) — seção separada no final ou link para doc dev.

Rascunho completo: [`docs/README_PACKAGE_USER_DRAFT.md`](../../../docs/README_PACKAGE_USER_DRAFT.md)

Após aprovação, opções de merge:

- **A)** Substituir `README.md` pelo rascunho + apêndice "Desenvolvimento interno" (conteúdo atual resumido)
- **B)** `README.md` = consumidor; mover CLI/lake para `docs/development.md`

Recomendação: **B** — README curto e orientado a produto; detalhes do pipeline ficam em `docs/development.md`.

---

## Próximo passo sugerido

1. Revisar e aprovar este arquivo + `docs/README_PACKAGE_USER_DRAFT.md`
2. ~~Aplicar edições em `specs/003/.../spec.md` e `tasks.md`~~ **Feito** — ver `tasks.md` e `spec.md` atualizados
3. Executar Task 1 (doc API) e Task 5/6 (README) em Agent mode
