---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
us: US-CLI-003
---

# Plano US-CLI-003 — Importação 1-clique (Cali/Bling/CSV)

> Story em `docs/dominios/comercial/modulos/clientes/prd.md` §6 US-CLI-003 (2 ACs).

## ACs

- **AC-CLI-003-1**: GIVEN arquivo válido WHEN upload THEN preview com 10 primeiras linhas + mapeamento sugerido.
- **AC-CLI-003-2**: GIVEN confirmação WHEN executa THEN cria clientes em lote, dedup automático, relatório final (criados/atualizados/rejeitados).

## Escopo realista pra Marco 1

- **CSV** primeiro (Cali/Bling exigem parsers específicos — Wave A).
- **Síncrono no Marco 1** (sem Procrastinate worker rodando — job enfileirado entra em Wave A).
- **Lote limite 1000 linhas** por chamada (proteção mem + DoS).
- **Dedup automático**: usa UNIQUE INDEX parcial do Marco 1 (US-CLI-005 R4) — se cliente ativo existe com mesmo CPF/CNPJ, atualiza; soft-deleted reativa via dedup do create.
- **Aceite LGPD em lote**: importação registra `aceite_lgpd_origem="importacao"` + `aceite_lgpd_dispensa_motivo="pj_sem_pf_associada"` pra PJ ou pula linha exigindo aceite explícito pra PF.

## Sequência de tasks

- **T-CLI-041**: endpoint `POST /api/v1/clientes/importar-preview/` recebe arquivo, lê 10 primeiras linhas, devolve mapeamento sugerido.
- **T-CLI-042**: endpoint `POST /api/v1/clientes/importar-executar/` recebe arquivo + mapeamento confirmado + opções (skip_invalid, update_existing). Retorna relatório.
- **T-CLI-043**: lógica em `src/application/comercial/clientes/importar_clientes.py` — use case puro recebendo Repository + InadimplenciaSource (não, só Repository).
- **T-CLI-044**: adapter Django implementa `bulk_create_or_update` em `src/infrastructure/clientes/repositories.py`.
- **T-CLI-045**: limite 1000 linhas + validação tamanho upload no settings.
- **T-CLI-046**: audit `cliente.importacao_executada` com totais + nenhuma PII.
- **T-CLI-047**: migration seed `clientes.importar` autorização (admin_tenant apenas — TL7 padrão).
- **T-CLI-048**: testes — 8:
  - `test_preview_devolve_10_linhas_e_mapeamento`
  - `test_executar_cria_clientes_pj_em_lote`
  - `test_executar_atualiza_existente_quando_documento_bate`
  - `test_executar_relatorio_separa_criados_atualizados_rejeitados`
  - `test_executar_rejeita_linha_com_cnpj_invalido`
  - `test_executar_limite_1000_linhas_excedido_400`
  - `test_executar_audita_cliente_importacao_executada`
  - `test_importar_exige_perfil_admin_tenant`

## Non-goals

- Cali/Bling parsers (Wave A — adapters específicos).
- Excel/XLSX (Wave A — pandas).
- Async (Procrastinate worker — Wave A).
- Importação de PF com aceite individual (cada linha precisaria do aceite — diferido pra V2; PF em lote rejeita ou exige flag de "aceite presencial").
- Resolução de conflitos manual (sobre-escrita campo-a-campo) — Wave A.

## Subagentes a consultar

- `tech-lead-saas-regulado`: tamanho de upload + DoS + dedup em lote (transaction.atomic + cursor + serialização).
- `advogado-saas-regulado`: aceite LGPD em lote (especialmente PF), retenção do arquivo importado, RAT da importação.
