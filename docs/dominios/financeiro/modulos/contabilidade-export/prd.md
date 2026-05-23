---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
diataxis: explanation
audiencia: agente
modulo: contabilidade-export
dominio: financeiro
relacionados:
  - docs/adr/0053-export-sped-contabil.md
  - docs/dominios/financeiro/modulos/fiscal/prd.md
  - docs/dominios/financeiro/modulos/billing-saas/prd.md
---

# PRD — Módulo Contabilidade Export (SPED + layouts contadores externos)

> **PRÉ-REQUISITO Wave A.** Contador externo bloqueia 1º tenant pago sem export no layout do software dele (Sage/Domínio/Alterdata). SPED ECF + EFD Contribuições são obrigação federal.

## 1. O que este módulo é

Exporta movimentação contábil do tenant em 4 layouts: SPED ECF (anual Receita), EFD Contribuições (mensal Receita), Sage/Domínio/Alterdata/Contmatic (layout do software do contador), CSV genérico.

## 2. Por que existe

90% do mercado PME BR terceiriza contabilidade. Contador cobra R$ 800-3000/mês "redigitação" se Aferê não exporta no layout dele. Atrito mata venda — contador é decisor técnico oculto.

## 3. Personas

- **P-CON-01 Admin tenant** — configura plano de contas + agenda export.
- **P-CON-02 Contador externo** — recebe arquivo + importa no Sage/Domínio.

## 4. Escopo

- Mapeamento `PlanoContasMapeamento` por tenant (conta_origem_afere → conta_destino_contador).
- Geração SPED ECF (`.txt` layout Bloco I/J/K).
- Geração EFD Contribuições (`.txt` layout C100/M100).
- Geração Sage/Domínio/Alterdata/Contmatic — layouts proprietários documentados publicamente.
- CSV genérico (debit/credit/conta/historico/data).
- Storage WORM em B2 por 5 anos (Receita).
- Job assíncrono (procrastinate).
- UI: agenda mensal automática + download manual.

## 5. Non-goals

- **Contabilizar internamente** (Aferê NÃO é software contábil; só exporta).
- **Integração API direta com Sage** (Sage cobra R$ 5k/mês licença API; arquivo é suficiente).
- **DRE oficial / Balanço Patrimonial** — só gerencial em `bi`.

## 6. User Stories

### US-CON-001: Tenant mapeia plano de contas

- **AC-CON-001-1**: admin abre "Contabilidade > Plano de Contas", mapeia origem→destino, salva.
- **AC-CON-001-2**: tenta export sem mapeamento → bloqueia (INV-SPED-001).

### US-CON-002: Export SPED ECF anual

- **AC-CON-002-1**: GIVEN ano-base fechado, WHEN tenant clica "Gerar SPED ECF", THEN job assíncrono gera `.txt` Bloco I/J/K com hash; armazena B2 WORM 5 anos.
- **AC-CON-002-2**: arquivo passa validação layout (Receita publica validador) antes de disponibilizar download.

### US-CON-003: Export EFD Contribuições mensal

- **AC-CON-003-1**: GIVEN dia 1º do mês, WHEN job dispara, THEN gera `.txt` mês anterior; envia link por e-mail ao contador cadastrado.

### US-CON-004: Export Sage/Domínio/Alterdata

- **AC-CON-004-1**: tenant escolhe layout do contador; export gera arquivo no formato do software escolhido.

### US-CON-005: Export CSV genérico

- **AC-CON-005-1**: tenant escolhe colunas + período + filtros → CSV gerado.

## 7. Métricas

- 100% dos lançamentos do mês exportados sem linha rejeitada por mapeamento ausente.
- % contadores externos que aceitam arquivo Aferê sem retrabalho > 95%.

## 8. NFR

- **Performance:** export ≤ 2min para 100k lançamentos.
- **Segurança:** arquivo WORM em B2; criptografia em repouso; download autenticado.
- **Audit:** `audit_trail.contabilidade_export` registra quem gerou, quando, qual layout, hash do arquivo.

## 9. Glossário

Termos contábeis padrão (Receita Federal).

## 10. Como evolui

- Layout novo (Contmatic, Folhamatic, Questor) → adicionar adapter + teste fixture validador.
- Mudança regulamentar Receita (IN nova) → ADR + reler layout.
