---
owner: agente-ia
revisado-em: 2026-06-09
proximo-review: 2026-09-09
status: stable
diataxis: reference
audiencia: [agente, tech-lead]
frente: configuracoes-sistema
tipo: plan-faseamento
relacionados:
  - docs/faseamento/configuracoes-sistema/spec.md
  - docs/adr/0080-numeracao-serie-documento-dois-regimes.md
---

# Plano de implementação — frente `configuracoes-sistema` (núcleo)

> Deriva da spec v2 (pós-P2). 3 agregados: `Empresa`/`Filial`, `Imposto`/`RegimeTributario`,
> `SerieDocumento`. Path achatado `src/{domain,application,infrastructure}/configuracoes_sistema/`
> (ADR-0072). Molde: fiscal + metrologia/certificados (numeração gap-less).

## Fatias (ordem de dependência)

### Fatia 1a — Domínio puro (`src/domain/configuracoes_sistema/`)
- `enums.py`: `RegimeTributario` (NORMAL/SIMPLES_NACIONAL/MEI/LUCRO_PRESUMIDO/LUCRO_REAL/IMUNE/ISENTO),
  `TipoImposto` (ICMS/ISS/PIS/COFINS/IRRF/CSLL/INSS), `TipoDocumento` (os/orcamento/fatura/
  certificado/recibo/interno), `RegimeNumeracao` (GAP_LESS/BURACOS_ACEITOS).
- `value_objects.py`: `Cnpj` (reusar/validar ADR-0017 se já houver VO compartilhado), `Aliquota`
  (Decimal 0..100), `JanelaVigencia` (reusar VO comum se existir).
- `entities.py`: `Empresa`, `Filial`, `Imposto` (com `iss_retido_fonte`/`tem_st`/
  `simples_excedeu_sublimite`), `SerieDocumento` (com `regime_numeracao` derivado do tipo).
- `transicoes.py`: `regime_numeracao_do_tipo(tipo)` (GAP_LESS p/ fatura/certificado; BURACOS p/
  resto); `proximo_formatado(serie, numero, ano)`; `imposto_vigente_em(impostos, tipo, filial, data)`;
  `validar_uma_matriz(filiais)`.
- `erros.py`: `NumeroNuncaDiminuiError`, `MatrizAusenteOuDuplicadaError`, `CnpjDuplicadoError`,
  `ImpostoVigenciaSobrepostaError`, `ImpostoImutavelError`, `TipoDocumentoInvalidoError`.
- `repository.py`: Protocols `EmpresaRepository`, `ImpostoRepository`, `SerieDocumentoRepository`.
- **Saída:** testes puros (regime por tipo, vigência determinística, 1 matriz, formato número).

### Fatia 1b — Schema PG (`src/infrastructure/configuracoes_sistema/`)
- `models.py`: `Empresa`, `Filial`, `Imposto`, `SerieDocumento` (+ `numero_documento_reservado`
  p/ gap-less, espelha `numero_certificado_reservado`).
- migrations: 0001 CreateModel + UNIQUE (`Empresa.cnpj` por tenant INV-036; `Filial` 1 matriz
  parcial INV-037; série `(tenant,filial,tipo,prefixo)` INV-028); 0002 RLS v2 todas; 0003 WORM
  Padrão B onde imutável (`Imposto` linha + número confirmado) + **trigger INV-028** (BEFORE UPDATE
  barra decremento de `proximo_numero`) + **trigger INV-CFG-IMPOSTO-IMUTAVEL** (barra UPDATE de
  aliquota/tipo/vigencia_inicio; só vigencia_fim NULL→data); 0004 **exclusion constraint**
  `btree_gist` (INV-CFG-IMPOSTO-SEM-SOBREPOSICAO — habilitar extensão se preciso); 0005 grants;
  0006 seed authz `configuracoes_sistema.*`.
- `mappers.py` + `repositories.py` (Django) + reserva gap-less reusando motor de certificados.
- drill `validar_configuracoes_sistema`.
- **Saída:** testes PG-real (RLS cross-tenant, INV-028 decremento bloqueado, imposto imutável,
  não-sobreposição vigência, 1 matriz, gap-less vs buracos por tipo).

### Fatia 2 — Use cases + REST
- `src/application/configuracoes_sistema/`: `atualizar_empresa`, `adicionar_filial`,
  `cadastrar_imposto`, `encerrar_vigencia_imposto`, `criar_serie`, `reservar_numero` (2 regimes).
- `src/infrastructure/configuracoes_sistema/views.py`: ViewSet por agregado (empresa/filiais/
  series/impostos) + ACTION_MAP authz + Idempotency-Key + perfil server-side + eventos WORM
  `Config.*` (em `ACOES_CONFIG`).
- **Saída:** E2E (editar empresa+evento; 2ª matriz 422; cadastrar imposto sobreposto 422; reservar
  número gap-less sem buraco vs operacional; cross-tenant 404).

### Fatia 3 — P7/P8/P9
- P7: família `INV-CFG-*` em REGRAS (NUM-ATOMICA, IMPOSTO-IMUTAVEL, IMPOSTO-SEM-SOBREPOSICAO) +
  reconciliar `INV-028` (remover `NF` da enumeração — ADV-04) + `TestINV_CFG_*` + hooks
  (`serie-numeracao-regime-check`, `imposto-imutavel-check`) + casos `_test-runner`.
- P8: matriz-reconciliação (molde M7) + promover ADR-0080 proposta→aceito (§11 AGENTS) +
  promover frontmatters draft→stable.
- P9: auditores roteados (seguranca, llm-correctness, produto, qualidade, idempotencia,
  conformidade-lgpd, supplychain se houver dep `btree_gist`).

## Decisões abertas resolvidas no plan
- **Reset anual (TL-07):** SIM para tipos com `{ano}` no formato → contador por `(serie, ano)`
  no gap-less (motor de certificados já tem dimensão de ano); nos buracos-aceitos, `proximo_numero`
  por `(serie, ano)` quando formato tem `{ano}`, senão linear.
- **Extensão `btree_gist`:** verificar habilitada no init do PG (docker init script); senão
  migration `CREATE EXTENSION IF NOT EXISTS btree_gist`.
- **WORM:** só `Imposto` (linha) e número confirmado de série gap-less. `Empresa`/`Filial`/`SerieDocumento`
  (config) são mutáveis com auditoria (não WORM).

## GATEs rastreados (não bloqueiam fechamento do núcleo)
- GATE-CFG-NUM-DRILL-LOCAL: drill gap-less cronometrado PG-real sob concorrência (espelha
  GATE-CER-DRILL-LOCAL) — invariante de consecutividade provado em unit + UNIQUE.
- GATE-CFG-TRIBUTARIO-CONTADOR (pré-prod): conjunto final de regimes/figuras (ADV-01/02/08) =
  validação contador/OAB. Estrutura entregue; humano valida lista.
- GATE-CFG-RETROFIT-SERIE (Wave B): migrar OS/calibração para série central.
