---
owner: roldao
revisado-em: 2026-05-29
status: draft
fase: M6-escopos-cmc
ritual: plan-reviews
depende-de: docs/faseamento/M6-escopos-cmc/plan.md
---

# Consolidação das revisões do plan — M6 `metrologia/escopos-cmc`

> 2 subagentes (roteamento INV-RITUAL-003: tech-lead + RBC são os essenciais para
> módulo metrológico) revisaram `plan.md` v1 (2026-05-29). **Nenhum BLOQUEIA
> total** (ambos APROVAM COM CORREÇÕES), mas há **2 CRÍTICO + 6 ALTO** que
> bloqueiam `/tasks` (INV-RITUAL-001). Disparam **plan v2 + 3 ADRs novas
> (0073/0074/0075) + emenda ADR-0066**.

## Vereditos

| Subagente | Veredito | Itens |
|---|---|---|
| tech-lead-saas-regulado | APROVA COM CORREÇÕES | C-01..C-11 (2 CRÍTICO, 3 ALTO, 4 MÉDIO, 2 BAIXO) |
| consultor-rbc-iso17025 | APROVA COM CORREÇÕES | NC-01..NC-08 (1 CRÍTICO, 3 ALTO, 2 MÉDIO, 2 BAIXO) |

## Correções obrigatórias antes de `/tasks`

### Bloqueantes CRÍTICO

- **TL-C-01 (tech-lead — ADR-0073): ponto de invocação do `cmc_cobre` real.**
  `get_authz_resource(request)` roda na fase de PERMISSÃO DRF (`permissions.py:93-97`),
  só recebe `request`; a Calibracao persistida ainda não foi carregada → não há de
  onde derivar grandeza/faixa server-side. O "drop-in" não é trivial. **Decisão:
  mover a validação de cobertura metrológica para DENTRO do use case**
  `configurar_calibracao` (chamada explícita à porta, 412 do domínio), tirando-a do
  permission layer. Vale para `procedimento_vigente_para` (módulo irmão) também. →
  **ADR-0073**.
- **RBC-NC-01 (RBC — ADR-0074): regra `U ≥ CMC` é invariante obrigatória, não
  refinamento futuro.** ILAC-P14:09/2020 §5.5 + NIT-DICLA-021 (verificar rev.):
  laboratório acreditado NÃO pode reportar incerteza menor que a CMC declarada —
  não-conformidade nº 1 em auditoria CGCRE. Como `cmc_cobre` roda na configuração
  (antes do U existir), exige **2ª porta** `cmc_para(grandeza, faixa, data) ->
  Decimal` consultada na EMISSÃO/aprovação (US-CAL-007/008/cert) → 412
  `IncertezaAbaixoDoCMC`. Normalizar unidade/forma (absoluta vs `a+b·X`). →
  **INV-ECMC-009 + ADR-0074**.

### Bloqueantes ALTO

- **TL-C-02 (CRÍTICO→tratado junto C-01): drop-in lê chave no topo.** O bloco
  `predicates_calibracao.py:170-178` e o STUB leem `resource.get("grandeza")` no
  topo, mas a allowlist anti-PII (`django_provider.py:82`) só não-recursa dentro de
  `escopo`. Grandeza no topo = `ValueError`. **Adaptar para `resource['escopo'][...]`**
  (ou eliminado se ADR-0073 mover pro use case — neste caso a checagem nem usa o
  resource DRF). Resolvido por ADR-0073.
- **TL-C-04 (ALTO): singleton `escopo_repo` diverge do molde M5.** M5 expõe porta
  cross-módulo como FUNÇÕES DE MÓDULO sem estado (`padroes/query_service.py:71`),
  não singleton stateful. **Expor `cobre()` e `cmc_para()` como funções de módulo
  em `escopos_cmc/query_service.py`**; ajustar o drop-in/uso para importar a função.
  (Reabre §9 Q do dossiê: decisão = função de módulo, NÃO singleton.)
- **TL-C-05 (ALTO): contradição fail-open vs fail-closed do vínculo RT.** Plan diz
  "escopo sem RT competente → bloqueia" (fail-closed) E "fail-open lazy até retrofit
  ADR-0022 v2" (R3). No MVP `RTCompetencia` só tem `grandeza` (sem método+faixa).
  **Cravar inequívoco:** no MVP o vínculo RT↔escopo é **fail-open lazy** (não
  bloqueia por RT) + GATE rastreado + teste nomeado; bloqueio real entra com
  ADR-0022 v2. → emenda ADR-0066 + **GATE-ECMC-RT-VINCULO**.
- **RBC-NC-02 (ALTO — ADR-0075): terminologia "CMC" para não-A é uso indevido de
  acreditação** (ISO 17025 cl. 8.1.3). Modelagem está certa (`rbc_acreditado=false`
  forçado); o risco é de RÓTULO. **Separar:** perfil A = "CMC (menor incerteza
  declarada)" + "Escopo CGCRE nº XXXX"; perfis B/C/D = "Capacidade interna
  declarada (sem acreditação RBC)" + badge "NÃO ACREDITADO". → **ADR-0075**.
- **RBC-NC-03 (ALTO): uma CMC por faixa.** Múltiplos métodos na mesma grandeza+faixa
  → CMC efetiva publicada/oposta ao cliente é a **MENOR** entre métodos
  (NIT-DICLA-012, verificar rev.). Não deixar usar a "pior" CMC para passar no
  U≥CMC. **Sub-regra de INV-ECMC-005/009.** → entra em ADR-0074.
- **RBC-NC-04 (ALTO): GATE individualizado do vínculo RT.** Fail-open só dogfooding;
  bloqueio real (escopo sem RT competente vivo → DENY uso RBC) obrigatório antes do
  1º tenant RBC externo. → **GATE-ECMC-RT-VINCULO** (junto com TL-C-05).

### Ajustes MÉDIO (entram no plan v2)

- **TL-C-03 (investigação — regra #0): estado real da suíte M4 sob perfil A.** Hoje
  a view `configurar` não passa grandeza/faixa no resource; investigar se algum
  teste M4 de `configurar` com perfil A passa (e como) ANTES do `/tasks`. Determina
  o tamanho real do wire-in. Transição em 2 etapas (canal de dados com STUB True;
  troca real depois) — nunca relaxar assert M4.
- **TL-C-06 (eventos probatórios): revogação/revisão na cadeia hash central.**
  `registrar_auditoria` com `action="escopos_cmc.revogado"/"...revisado"` ancorado
  na cadeia hash HMAC central `auditoria` (molde M5 `action="padrao.*"`). Não precisa
  tabela nova; o audit trail padrão JÁ é hash-chain. Declarar explícito.
- **TL-C-07 (trigger WORM): revisão = INSERT nova versão, não UPDATE in-place.**
  Trigger BEFORE UPDATE bloqueia mutação de campos metrológicos de linha CONFIRMADA
  exceto transição one-shot `revogado_em` (molde `recal_externo_padrao_worm_check`).
  Sem GUC.
- **TL-C-08 (semântica de cobertura): não reusar `_faixa_intersecta` (escopo.py:55-71)
  para BLOQUEAR.** Interseção serve p/ LISTAR (query M4); `cobertura.py` implementa
  **contenção total** isolada. Fronteira explícita no `/tasks`.
- **TL-C-09 (fatiamento): Fatia 1 (~32 tarefas) acima da faixa INV-RITUAL-002.**
  Dividir em **Fatia 1a** (domínio puro + cobertura.py + Protocols) e **Fatia 1b**
  (schema + migrations + RLS + WORM + repo + drill). 5 fatias no total.
- **RBC-NC-05 (redução de escopo CGCRE): bloqueio prospectivo, sem invalidar
  retroativo.** Revisão que reduz escopo (tira grandeza/faixa em supervisão) →
  `vigencia_fim` na versão antiga + bloqueia novas calibrações a partir da nova
  vigência; certificados já emitidos sob a versão antiga permanecem válidos (snapshot
  congelado sustenta). Sub-regra de INV-ECMC-003/006.
- **RBC-NC-06 (snapshot EscopoUsado): conteúdo mínimo probatório.** Enriquecer o VO
  com `versao` do escopo + CMC-da-época com forma (abs vs `a+b·X`) + comparação U×CMC
  + RT competente da época + `perfil_no_evento`. Lista completa em §6 do parecer RBC.
  Refina INV-ECMC-008.

### Ajustes BAIXO

- **TL-C-10:** `apps.py` com `label="escopos_cmc"` explícito.
- **TL-C-11:** índice parcial `WHERE estado='CONFIRMADO' AND revogado_em IS NULL`.
- **RBC-NC-07:** não preencher `U = CMC` cego (erro oposto ILAC-P14); U sempre do
  orçamento de incerteza; CMC é só o piso. Teste anti-cópia.
- **RBC-NC-08:** validar números/revisões das NIT citadas (NIT-DICLA-021/031/012/016)
  com consultor humano credenciado antes do dossiê CGCRE. Não bloqueia código.

## Saída

- **plan v2** incorporando TL-C-01..11 + RBC-NC-01..08 (§ deltas no plan.md).
- **3 ADRs novas:** **0073** (validação metrológica no use case, não no permission
  layer), **0074** (cobertura RBC tridimensional: faixa ⊆ escopo + U ≥ CMC +
  menor-CMC-por-faixa), **0075** (capacidade não-acreditada ≠ CMC acreditada —
  separação terminológica) — escrever ANTES de `/tasks`.
- **Emenda ADR-0066** (formalizar transição fail-open→fail-closed do `cmc_cobre` +
  fail-open lazy do vínculo RT).
- **2 GATEs novos:** `GATE-ECMC-RT-VINCULO` (TL-C-05/RBC-NC-04) + `GATE-ECMC-U-MAIOR-CMC`
  (consumo da 2ª porta na emissão — pode ser parcialmente diferido ao módulo
  `certificados` Wave A).
- **INV nova: INV-ECMC-009** (U ≥ CMC) em REGRAS no `/implement` + `TestINV_ECMC_009`.
- **Decisão de terminologia (RBC-NC-02) reportada ao Roldão** — A=CMC, B/C/D=capacidade
  interna; refinamento da decisão L/O dele, com base normativa cl. 8.1.3 (veto aberto).
- **NADA de código até plan v2 + ADRs aprovados** (INV-RITUAL-001).

## Limites declarados pelos revisores

- **RBC:** não tem credencial CGCRE — parecer consultivo deixa o trabalho ~80%
  pronto p/ consultor humano credenciado; números de NIT marcados "verificar";
  dossiê cl. 7.11 do módulo exige assinatura credenciada pré-produção (diferido —
  `project_sem_contratacoes_externas_ate_producao`).
- **Tech-lead:** (a) se a suíte M4 passa hoje sob perfil A no `configurar` só fecha
  rodando o ambiente (TL-C-03); (b) vazamento de contexto de tenant no caminho
  permissão→use case sob RLS só fecha em drill PG real (GATE-ECMC-DRILL-LOCAL) +
  pentest externo pré-1º tenant (lição incidente 733 tenants).
