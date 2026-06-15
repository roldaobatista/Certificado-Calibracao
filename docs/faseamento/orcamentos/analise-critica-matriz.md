---
owner: agente-ia
revisado-em: 2026-06-14
proximo-review: 2026-09-14
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: orcamentos
tipo: nota-design
relacionados:
  - docs/faseamento/orcamentos/spec.md
  - docs/faseamento/orcamentos/tasks.md
  - docs/adr/0076-fonte-faixa-cobertura-declarada-config-vs-pontos-emissao.md
---

# Análise crítica cl. 7.1 do orçamento — matriz validada (handoff Onda 2c-2)

> Parecer do subagente `consultor-rbc-iso17025` (2026-06-14): **CONFIRMA** D-ORC-5 com
> 6 ajustes. Base para implementar `aprovar_orcamento` (T-ORC-033). Consultivo IA — não
> substitui consultor humano credenciado no dossiê CGCRE pré-acreditação.

## Decisão de fonte do mensurando (P1 — CONFIRMA)

O `Equipamento` NÃO carrega grandeza/faixa estruturados (só `faixa` string livre). A
Calibração também não herda — o RT declara (ADR-0076). Logo o **item de calibração do
orçamento DECLARA o mensurando** (`grandeza_solicitada`, `faixa_solicitada_min/max`,
`unidade_solicitada`). **DONE na Onda 2c-1** (migration 0008 + CHECK + validação fail-fast).

Ajustes aplicados: C1 nomes `*_solicitada` (não `*_calibrada`); C2 obrigatório quando
`tipo_atividade_alvo='calibracao'` (CHECK `ck_orc_item_mensurando_calibracao`); C3 validar
grandeza (`Grandeza`) + faixa/unidade (`FaixaMedicao`) na ENTRADA do item (422 claro).

## Matriz de decisão A/B/C/D (P2 — para a Onda 2c-2)

Por item de calibração, com `data = avaliada_em` (um único `now()` server-side):
- `(cobre_cmc, cmc_reason) = escopos_cmc.cobre(...)` — `cmc_reason=""` se cobre; senão `cmc_fora_do_escopo`/`erro_interno`.
- `(procedimento_ok, proc_dict) = procedimentos.cobre_procedimento(...)` — dict: `procedimento_id, codigo, versao, numero_revisao, hash_anexo`.
- `item_ok = cobre_cmc and procedimento_ok`. `padrao_disponivel` NÃO consultado (GATE-ORC-PADRAO).

| Perfil | Itens | Veredito | Severidade | Efeito |
|---|---|---|---|---|
| indeterminado (`""`) | — | — | — | **422 PerfilIndeterminado** (fail-closed). Não grava análise. |
| **D** | (não avalia) | `desabilitada` | — | Aprova. Grava análise (itens_avaliados=[]). |
| **A** (não suspenso) | algum `item_ok=False` | `reprovada` | — | **422 AnaliseCriticaReprovada** + WORM + `orcamento.analise_critica_reprovada`. Não aprova. |
| **A** (não suspenso) | todos `item_ok=True` | `com_ressalva` | **media** | Ressalva `TEXTO_RESSALVA_PADRAO_INDISPONIVEL` (padrão não verificável — TL-ORC-10). Aprova. |
| **A** (acreditação **suspensa**) | qualquer | `reprovada` | — | 422 + ressalva de suspensão. Não emite RBC durante suspensão (AJUSTE-3). |
| **B** | algum `item_ok=False` | `com_ressalva` | **media** | Ressalva apresentada no GET; POST público exige `ressalvas_confirmadas` (senão 422). Aprova. |
| **B** | todos `item_ok=True` | `aprovada` | — | Aprova. |
| **C** | algum `item_ok=False` | `com_ressalva` | **baixa** | Log interno, sem confirmação do cliente. Aprova. |
| **C** | todos `item_ok=True` | `aprovada` | — | Aprova. |
| **A/B/C/D** | sem item de calibração | `aprovada` | — | Nada metrológico. Grava análise (itens_avaliados=[]) — AJUSTE-1. |

### Implementação (ajustes do parecer)
- **AJUSTE-3 (importante):** ramificar com `obter_perfil_tenant_corrente()` (char A/B/C/D/""),
  NÃO `tenant_perfil_e` (só binário). Server-side, nunca payload. Para perfil A, chamar
  também `tenant_perfil_e({"A"})`; se `tenant_acreditacao_suspensa` → fail-closed (reprovada).
- **AJUSTE-1:** sempre gravar `AnaliseCriticaOrcamento` (envelope sempre tem `analise_critica_id`).
- **AJUSTE-2 — `itens_avaliados[n]`:** equipamento_id, grandeza, faixa_min, faixa_max, unidade,
  cobre_cmc, cmc_codigo_ref?, **cmc_reason**, procedimento_ok, procedimento_id?,
  procedimento_codigo?, procedimento_versao?, **procedimento_revisao** (numero_revisao),
  **procedimento_hash_anexo** (hash_anexo), ressalvas[].
- `avaliada_por`: interno = user_id; público = `"SISTEMA/AUTO:<aprovacao_id>"` (C5).
  `norma_referencia` = `"ISO/IEC 17025:2017 cl. 7.1.1"` (C6).
- `snapshot_hash`: ADR-0029 — `formatar_hash_versionado(VERSAO_HMAC_ATUAL, sha256(canonicalizar_payload_para_hmac(payload)).digest())`.
- Transições: `enviado→aprovado→aprovado_pendente_os`; publica `orcamento.aprovado`
  (envelope `montar_envelope_orcamento_aprovado` — já casa 100% com o consumer da OS) +
  `orcamento.analise_critica_reprovada`/`_com_ressalva` (com `severidade`). Idempotente.
- **Arquitetura:** ports (escopos_cmc/procedimentos) chamadas na VIEW/infra; resultados por item
  passados ao use case `aprovar_orcamento`, que chama função PURA de decisão + persiste WORM +
  transiciona + monta envelope. Perfil/suspensão resolvidos na view (server-side).

### Pendências humanas (não bloqueiam codar)
- Texto verbatim da ressalva de padrão + suspensão de acreditação: revisão humana RBC pré-1º
  tenant A externo (GATE-ORC-CMC-PREENCHIDO / `[RBC-PRE-PROD]`). Rastrear **C-ORC-SUSPENSAO**.
