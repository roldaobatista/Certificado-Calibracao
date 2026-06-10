---
owner: agente-ia
revisado-em: 2026-06-09
proximo-review: 2026-09-09
status: stable
diataxis: reference
audiencia: [agente, auditor, advogado, tech-lead]
frente: configuracoes-sistema
tipo: spec-faseamento
relacionados:
  - docs/faseamento/configuracoes-sistema/T-CFG-000-investigacao.md
  - docs/faseamento/plano-dependencia-sistema.md
  - docs/dominios/suporte-plataforma/modulos/configuracoes-sistema/prd.md
  - docs/dominios/suporte-plataforma/modulos/configuracoes-sistema/modelo-de-dominio.md
  - docs/adr/0080-numeracao-serie-documento-dois-regimes.md
  - docs/adr/0008-fiscal-pluggable.md
  - docs/adr/0017-cnpj-alfanumerico.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
---

# Spec de faseamento — frente `configuracoes-sistema` (núcleo: cadastro + tributário + numeração)

> **v2 (2026-06-09)** — incorpora P2 (tech-lead TL-01..09 + advogado ADV-01..08), ambos
> **APROVA COM CORREÇÕES**. Log de incorporação em §10.
>
> **Escopo:** núcleo da central de configurações do tenant que destrava a **cadeia de
> preço** — três agregados: **`Empresa`+`Filial`** (cadastro base, INV-036/037),
> **`Imposto`+`RegimeTributario`** (catálogo tributário versionado e imutável por linha,
> INV-CFG-IMPOSTO-*) e **`SerieDocumento`** (numeração local em **dois regimes por tipo**,
> ADR-0080). RBAC, feature-flags, workflows, campos obrigatórios, modelos PDF, A3,
> integrações/credenciais, notificações, regras comerciais, SLA, config operacional fina
> e backup/retenção fina ficam **DIFERIDOS** (têm dono existente ou são pós-núcleo). Base:
> `T-CFG-000-investigacao.md` (regra #0; greenfield confirmado).

## 1. Por que agora (dependency-first)

Frente **#1** do `plano-dependencia-sistema.md`: raiz da cadeia de preço. Consumidores
diretos — `produtos-pecas-servicos`, `precificacao`, `orcamentos`, `estoque` — não
funcionam sem catálogo tributário + cadastro da empresa. **Correção regra #0 (T-CFG-000 §2):**
a justificativa "dívida de numeração do fiscal" caiu (NFS-e é numerada pelo BaaS/município;
OS/calibração já numeram com sequence própria ADR-0056). A frente é #1 pela via **tributária
+ cadastro base**, não pela numeração.

## 2. Seam pronto / o que NÃO reconstruir (T-CFG-000 §3)

| US-CFG (PRD) | Tema | Dono existente | Decisão |
|--------------|------|----------------|---------|
| US-CFG-004 | RBAC papéis/permissões (INV-029) | `authz` (ADR-0012, ACTION_MAP, seed) ✅ | **NÃO reconstruir** — fora do núcleo |
| US-CFG-014 | Feature flags do tenant (INV-030) | `feature_flag` (ADR-0006) ✅ | **NÃO reconstruir** — fora do núcleo |
| US-CFG-005/006 | Workflows/status (INV-038), campos obrigatórios | config fina diferida | fora do núcleo |
| US-CFG-013 | Retenção fina (INV-039) | matriz `retencao-matriz.md` (+linhas ADV-05) | config fina diferida; matriz emendada agora |
| US-CFG-009 | Credenciais de integração | KMS (SEC-KMS-001) + `webhook_out` ✅ | reusar quando entrar (diferido) |
| Idempotência (IDEMP-001) / RLS v2 / authz ACTION_MAP / observabilidade / VO CNPJ (ADR-0017) | infra/F-C | ✅ | molde — reusar, zero padrão novo |
| Motor de reserva gap-less (TTL + consecutividade) | `metrologia/certificados` (`numeracao.py` + `numero_certificado_reservado`) ✅ | **REUSAR** para séries fiscais (TL-02) — não reescrever |
| Path infra achatado `src/{domain,application,infrastructure}/configuracoes_sistema/` | molde fiscal | ✅ | ADR-0072 — módulo raiz consumido por todos |

## 3. Escopo — US do PRD cobertas (núcleo)

| US do PRD | O que entra AGORA | O que difere |
|-----------|-------------------|--------------|
| **US-CFG-001** dados da empresa e filiais | agregados `Empresa` + `Filial`; use cases criar/atualizar empresa, adicionar/editar filial; AC-001-1 (edita+evento `Config.EmpresaAtualizada`), AC-001-2 (filial CNPJ próprio + 1 matriz), AC-001-3 (auditoria antes/depois) | edição em massa UI; upload logo B2 (stub) |
| **US-CFG-003** impostos | agregado `Imposto` versionado+imutável por linha + VO `RegimeTributario` (CFG dono único) + figuras fiscais (ISS retido, ST, sublimite, imune/isento); use cases cadastrar/encerrar-vigência; AC-003-1 (campos por regime), AC-003-2 (alíquota nova só vale p/ futuros — INV-026 via imutabilidade da linha) | cálculo de imposto (consumidor fiscal/precificacao); CFOP/NCM por operação |
| **US-CFG-002** numeração e séries | agregado `SerieDocumento` em **dois regimes (ADR-0080)**: gap-less (fatura/certificado-local) via reserva-TTL; buracos-aceitos (os/orcamento/recibo/interno) via UPDATE atômico; AC-002-1 (config série), AC-002-2 (não diminuir — INV-028), AC-002-3 reescrito (ver §6 D-CFG-2) | **tipo `nf`/`nfse` NÃO entra** (BaaS é dono); retrofit de OS/calibração p/ série central = Wave B |

## 4. Non-goals (núcleo) — diferidos + mapa de INVs órfãos (TL-08)

Diferidos: US-CFG-005..013 (exceto retenção-matriz emendada), retrofit de emissores
existentes (OS/calibração/fiscal) para `SerieDocumento` central.

**INVs associados ao módulo no PRD que NÃO são do núcleo (dono declarado):**
`INV-029` (≥1 admin) → `authz`; `INV-030` (flag não burla plano) → `feature_flag`;
`INV-038` (não excluir entidade em uso) → config fina diferida; `INV-039` (retenção ≥ legal)
→ config-retenção fina diferida (matriz já cobre o prazo).

## 5. Entidades + invariantes do núcleo

- **`Empresa`** — id, tenant_id, razao_social, cnpj (VO ADR-0017), ie, endereco,
  regime_tributario_id (FK ou VO); opcionais im/logo_url/site/telefone. **INV-036** (CNPJ
  único por tenant — UNIQUE), INV-TENANT-001 (RLS). *Nota LGPD (ADV-06): MEI=CPF no CNPJ,
  telefone/endereço podem ser PII de PF — base legal art. 7º II/V LGPD + minimização
  (opcionais); declarar no RAT.*
- **`Filial`** — id, tenant_id, empresa_id, cnpj, nome, endereco, eh_matriz; opcionais
  ie/im/telefone. **INV-037** (exatamente 1 matriz por empresa — UNIQUE parcial
  `WHERE eh_matriz`; e não-ausência quando ≥1 filial). CNPJ único por tenant.
- **`Imposto`** — id, tenant_id, filial_id (nullable), tipo (ICMS/ISS/PIS/COFINS/IRRF/
  CSLL/INSS), aliquota, vigencia_inicio; opcionais cfop_padrao/ncm_padrao/vigencia_fim/
  observacoes; **atributos de figura fiscal (ADV-02/03):** `iss_retido_fonte` (bool),
  `tem_st` (bool — substituição tributária do ICMS; NÃO é regime), `simples_excedeu_sublimite`
  (bool). **INV-CFG-IMPOSTO-IMUTAVEL** (TL-04 — trigger Padrão B: bloqueia UPDATE de
  `aliquota`/`tipo`/`vigencia_inicio`; só `vigencia_fim` one-shot NULL→data; mudar alíquota =
  nova linha). **INV-CFG-IMPOSTO-SEM-SOBREPOSICAO** (TL-05 — exclusion constraint `btree_gist`
  sobre `(tenant, tipo, filial, daterange(inicio,fim) &&)`). INV-026 fecha-se no **consumidor**
  (carimbo de `imposto_id`/`aliquota` no snapshot do documento — seam, fora do núcleo).
- **`SerieDocumento`** — id, tenant_id, filial_id (nullable=global), tipo, prefixo,
  proximo_numero (ou contador por `(serie, ano)` se reset anual — TL-07), formato, padding,
  `regime_numeracao` (GAP_LESS|BURACOS_ACEITOS, derivado do tipo — ADR-0080). **INV-028**
  (proximo_numero nunca diminui — trigger BEFORE UPDATE) por chave **`(tenant, filial_id,
  tipo, prefixo)`** (TL-06). **INV-CFG-NUM-ATOMICA** (TL-01 — reserva atômica sem duplicata;
  gap-less para fiscal/cert via motor reserva-TTL reusado; buraco-por-rollback aceito nos
  operacionais). NÃO confundir com IDEMP-001 (Idempotency-Key de request).
- **`RegimeTributario`** — VO enum {NORMAL, SIMPLES_NACIONAL, MEI, LUCRO_PRESUMIDO,
  LUCRO_REAL, **IMUNE, ISENTO**} (ADV-01; `ST_INDICADOR` REMOVIDO → virou `Imposto.tem_st`,
  ADV-03). **CFG é dono único e original** (TL-03 — fiscal NÃO tem enum de regime no código;
  greenfield, sem divergência a tolerar).

Transversais: INV-TENANT-001 (RLS v2 todas as tabelas), SEC-005 (auditoria de mudança via
trilha central, payload antes/depois sanitizado), ADR-0067 (snapshot `perfil_no_evento` nos
eventos WORM; sem gating de perfil no núcleo — config é admin do tenant).

## 6. Decisões cravadas (D-CFG-*, pós-P2)

- **D-CFG-1** Estrutura achatada `src/{domain,application,infrastructure}/configuracoes_sistema/` (ADR-0072).
- **D-CFG-2** **Numeração em dois regimes por tipo (ADR-0080):** (a) **gap-less** para
  `fatura`/`certificado` (local) — reusar o motor `metrologia/certificados` (reserva TTL +
  confirmação one-shot na transação + consecutividade `{1..N}` densa); (b) **buracos-aceitos**
  para `os`/`orcamento`/`recibo`/`interno` — `UPDATE ... SET proximo_numero = proximo_numero+1
  RETURNING` (row-lock exclusivo basta; advisory por consistência de molde). **AC-002-3
  reescrito:** "sem gap **proposital**; buraco por rollback aceito nos tipos operacionais;
  sem duplicata em nenhum tipo; cancelamento não reusa número" (alinha texto real de INV-028).
- **D-CFG-3** `Imposto` versionado por vigência; consulta "vigente em D" determinística
  (garantida pela exclusion constraint TL-05); imutabilidade da linha por trigger (TL-04);
  encerrar vigência = `vigencia_fim` NULL→data one-shot.
- **D-CFG-4** `Empresa.cnpj` único por tenant (INV-036); `Filial` 1 matriz via UNIQUE parcial
  (INV-037); ambos validam VO CNPJ (ADR-0017).
- **D-CFG-5** `RegimeTributario` VO no domínio CFG = **dono único e original** (TL-03 —
  nenhum módulo o possui hoje; não há retrofit a diferir).
- **D-CFG-6** `tipo` de `SerieDocumento` exclui `nf`/`nfse` (BaaS é dono — ADV-04); inclui
  os/orcamento/fatura/certificado/recibo/interno. Chave UNIQUE `(tenant, filial_id, tipo,
  prefixo)`; decidir reset anual no plan (contador por ano se sim — TL-07).
- **D-CFG-7** Auditoria de config via trilha central (`registrar_auditoria`) payload
  antes/depois sanitizado; WORM Padrão B onde a imutabilidade é exigida (`Imposto`, número
  confirmado de série gap-less).
- **D-CFG-8** ViewSet por agregado (empresa/filiais/series/impostos) com ACTION_MAP authz +
  Idempotency-Key + perfil server-side; **seed authz `configuracoes_sistema.*` na mesma
  migration de criação** (TL-09, molde fiscal `0005_seed_authz`); eventos `Config.*` em
  `ACOES_CONFIG`.
- **D-CFG-9 (ADV-02/03)** Figuras fiscais como atributos do `Imposto`: `iss_retido_fonte`
  (LC 116/2003 art. 6º), `tem_st` (ST do ICMS), `simples_excedeu_sublimite`. Lista final de
  regimes/figuras = `[OAB/contador-PRE-PROD]` (estrutura pronta; humano valida o conjunto).
- **D-CFG-10 (ADV-07)** "Sem gap" é **exigência legal** só para `fatura`/`certificado`
  (fiscal + ISO 17025); para `os`/`orcamento`/`recibo`/`interno` é boa-prática auditável, não
  imposição fiscal — coerente com D-CFG-2.

## 7. ADR nova exigida pela P2

**ADR-0080 — Numeração de `SerieDocumento` em dois regimes por tipo** (gap-less via
reserva-TTL reusando `metrologia/certificados` para fiscal/regulatório; buracos-aceitos
`UPDATE...RETURNING` estilo ADR-0056 para operacional). Proposta criada com esta spec;
promover a aceito no fechamento P8.

## 8. Dependências

- **Pré-requisitos (✅):** infra (tenant/RLS, authz, audit/WORM, idempotência,
  observabilidade), VO CNPJ (ADR-0017), motor de numeração gap-less (`metrologia/certificados`),
  extensão PG `btree_gist` (exclusion constraint — verificar habilitada).
- **Consumidores a jusante (greenfield — seam, não bloqueia):** produtos-pecas-servicos,
  precificacao, orcamentos, estoque, futuros emissores de doc local.

## 9. Critérios de pronto (núcleo)

Domínio puro + schema PG (models + migrations RLS v2 + WORM Padrão B + exclusion constraint +
triggers INV-028/imposto-imutável + grants + seed authz) + use cases + REST (4 grupos) + drill
`validar_configuracoes_sistema` + testes (puros + PG-real: INV-028 gap-less vs buracos por tipo,
imposto imutável, não-sobreposição vigência, INV-036/037, E2E) + família INV-CFG-* em REGRAS +
hooks dos invariantes não-óbvios + emendas (PRD AC-CFG-002-3, modelo-de-dominio drift, retenção
+3 linhas, RAT) + ADR-0080 aceita + matriz-reconciliação + P9 auditores roteados. ruff/mypy
limpos, makemigrations limpo, `_test-runner` verde.

## 10. P2 — revisões incorporadas (tech-lead + advogado, ambos APROVA COM CORREÇÕES)

| Achado | Sev | Incorporação |
|--------|-----|--------------|
| TL-01 | CRÍT | `INV-006` (DPO/LGPD) trocado por `INV-CFG-NUM-ATOMICA`; corrigir PRD AC-CFG-002-3 (tarefa P3) |
| TL-02 / ADV-07 | CRÍT/BAIXO | Numeração dois regimes por tipo → **ADR-0080**; D-CFG-2/D-CFG-10; AC-002-3 reescrito |
| TL-03 | ALTO | `RegimeTributario` dono único CFG (D-CFG-5) — fiscal não tem enum |
| TL-04 | ALTO | `INV-CFG-IMPOSTO-IMUTAVEL` (trigger); INV-026 fecha no consumidor (snapshot) |
| TL-05 | ALTO | `INV-CFG-IMPOSTO-SEM-SOBREPOSICAO` (exclusion constraint btree_gist) |
| TL-06/07 | MÉD | Chave série `(tenant,filial,tipo,prefixo)`; decidir reset anual no plan |
| TL-08/09 | MÉD | §4 mapeia INV-029/030/038/039; seed authz na migration de criação |
| ADV-01 | ALTO | +IMUNE/ISENTO no `RegimeTributario` [conjunto final OAB/contador-pre-prod] |
| ADV-02 | ALTO | Figuras `iss_retido_fonte`/`tem_st`/`simples_excedeu_sublimite` (D-CFG-9) |
| ADV-03 | MÉD | `ST_INDICADOR` deixa de ser regime → `Imposto.tem_st` |
| ADV-04 | MÉD | Drift: remover `nf` + alinhar enum no `modelo-de-dominio.md` (tarefa P3) |
| ADV-05 | ALTO | +3 linhas na `retencao-matriz.md` (Imposto/SerieDocumento/Empresa-Filial) + nota CTN art.195 + DRILL-RET-CFG-01 (tarefa P3) |
| ADV-06 | MÉD | Nota LGPD base legal/finalidade PII Empresa/Filial → RAT (tarefa P3) |
| ADV-08 | BAIXO | Uso de `fatura` (duplicata vs interno) = `[contador-pre-prod]` |

**Edições cross-doc pendentes (P3/tasks):** PRD AC-CFG-002-3 (INV-006→INV-CFG-NUM-ATOMICA);
`modelo-de-dominio.md` (remover `nf`, alinhar enum regime, ST como atributo); `retencao-matriz.md`
(+3 linhas + DRILL-RET-CFG-01); `lgpd-rat.md` (PII Empresa/Filial); `REGRAS-INEGOCIAVEIS.md`
(INV-028 cita `NF` — reconciliar; nascer família INV-CFG-*).

## 11. Pendências para humano licenciado (pré-produção, não bloqueiam núcleo dogfooding)

`[OAB/contador-PRE-PROD]`: conjunto final exigível de regimes/figuras fiscais para empresa de
calibração (ADV-01/02); uso de `fatura` como duplicata (ADV-08); consolidação do RAT (ADV-06).
Estrutura de dados entregue pronta pelo agente; humano só valida/ajusta a lista.
