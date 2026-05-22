---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente
escopo: Wave A Marco 3 (OS) + Marco 4 (Calibração) + Marco 5 (Certificados)
tipo: auditoria-10-lentes-rodada-2-pos-retrofit
relacionados:
  - OS-CAL-CONSOLIDADO-rodada-1.md
  - OS-CAL-RESOLUCAO-rodada-1.md
---

# Auditoria 10 lentes — Domínios OS + Calibração + Certificados (rodada 2)

> **Solicitada por Roldão em 2026-05-23**, após as 6 ondas de retrofit (commits `7dff26c` → `a107f3e`). Mesmas 10 lentes da rodada 1, agora validando se a resolução foi correta + caça a gaps NOVOS introduzidos pelo retrofit.
>
> **Objetivo:** dar parecer GO/NO-GO para arrancar Marco 3 P1 (spec FORWARD do módulo OS).

---

## Sumário executivo

10 lentes despachadas em paralelo. **Veredito agregado: CONCERN com 5 bloqueadores antes de Marco 3 P4** (codificação).

- 128/179 achados da rodada 1 confirmados como RESOLVIDOS (corretos).
- **5 NOVOS CRÍTICOS introduzidos pelo retrofit** (concentração em LLM-correctness ID-colisão + LGPD biometria + tech-lead dupla FK).
- **20+ ALTOS/MÉDIOS NOVOS** rastreados como pendência ou GATE Wave A.
- **3 vereditos GO** (Segurança, Produto, RBC com condições); 7 com CONCERN/FAIL.

Marco 3 OS pode arrancar **P1 spec FORWARD** (5 críticos R1 resolvidos), **mas precisa de Onda 7 pré-P4** (~3-5h de retrofit fino) pra zerar os 5 críticos R2.

---

## Distribuição por lente — rodada 2

| # | Lente | R1 | RESOLVIDOS R1 | CRÍT NOVO R2 | ALTO NOVO R2 | MÉD NOVO R2 | BAIXO NOVO R2 | Veredito |
|---|---|---|---|---|---|---|---|---|
| 1 | tech-lead | 6+8+10+3 | 5 CRÍT + ~17 outros | **1** (CRT-3 dupla FK) | 3 | 2 | 0 | APROVA COM CORREÇÕES |
| 2 | advogado-saas-regulado | 3+5+5+3 | 16 itens | **1** (texto canônico AceiteAtividade) | 3 | 4 | 2 | CONCERN |
| 3 | consultor-rbc-iso17025 | 3+5+6+3 | 3 CRÍT + 5 ALTO + 6 MÉD | 0 | 0 | 3 | 1 | PASS condicionado |
| 4 | corretora-seguros-saas | 5+4+3+1 | 6 GAP-SEG | 0 | 1 | 2 | 1 | OK + 3 GATEs novos |
| 5 | auditor-produto | 5+5+7+2 | 5 CRÍT + 12 outros | 0 | 1 | 2 | 1 | GO M3 / NO-GO M4 sem Onda 7 |
| 6 | auditor-drift-docs | 2+5+8+5 | 7 itens | **1** (frontmatter v10) | 3 | 5 | 2 | CONCERN |
| 7 | auditor-llm-correctness | 4+7+10+6 | 5 itens | **3** (INV-007/006/022 colididos não-resolvidos) | 5 | 8 | 4 | **FAIL** |
| 8 | auditor-conformidade-lgpd | 0+4+5+2 | 8 itens | **1** (assinatura_base64 biometria) | 2 | 2 | 2 | CONCERN |
| 9 | auditor-seguranca | 3+5+5+3 | 11 itens | 0 | 0 | 3 | 4 | CONCERN |
| 10 | auditor-observabilidade | 0+2+5+3 | 7 itens | 0 | 1 (cal/metricas.md) | 4 | 3 | CONCERN |
| | **Total NOVO R2** | | | **6** | **19** | **35** | **20** | |

> Nota: tech-lead lista "1 CRÍT R1 mal fechado" — somado como CRÍT NOVO porque exige correção antes de Marco 3 P4.

---

## Os 6 CRÍTICOS NOVOS (bloqueadores P4)

### NOVO-CRIT-1 — Dupla FK `link_modulo_tecnico` × `Calibracao.atividade_os_id` (tech-lead)

`os/modelo-de-dominio.md:29` ainda descreve `link_modulo_tecnico` como "id do registro no módulo correspondente" (string); linha 80 chama "FK polimórfica"; glossário linha 33 diz "FK tipada". Calibração já tem `atividade_os_id` (FK tipada reversa). **CRT-3 da rodada 1 foi resolvido só pela metade** — temos as duas pontas, FK redundante e ambígua. Decisão: manter apenas `Calibracao.atividade_os_id`, remover `link_modulo_tecnico` do modelo OS. Arquivos: `os/modelo-de-dominio.md`, `os/glossario.md`, ADR-0023 §"Implicações".

### NOVO-CRIT-2 — Texto canônico do AceiteAtividade não existe (advogado)

Modelo OS L59 referencia `docs/conformidade/comum/termos/aceite-atividade-vN.md` "a criar Wave A". **Sem o texto v1.0 versionado, `hash_texto_termo` é hash de nada** → prova Lei 14.063 art. 4º cai. Já invalidada em jurisprudência TJSP. Bloqueia P4 Marco 3 (codificar `AceiteAtividade`).
**Remediação:** redigir minuta `aceite-atividade-v1.0.md` antes do P4 — advogado humano OAB ratifica pré-1º tenant externo.

### NOVO-CRIT-3 — `assinatura_base64` touch é dado biométrico LGPD art. 11 (conformidade-lgpd)

Modelo OS L57: `assinatura_base64 (touch)` armazenada em claro, sem categorização como **dado pessoal sensível** (LGPD art. 5º II + art. 11 + ANPD NT 2/2023). Traçado de assinatura manuscrita digital é biometria comportamental.
**Remediação:** INV-OS-ACEITE-BIO-001 novo; cifrar `assinatura_base64` com `BIOMETRIA_KEY_*` (chave KMS dedicada); DPIA `docs/conformidade/comum/dpia-assinatura-touch.md`; matriz retenção: anonimizar traçado após 5a (preservar hash + metadata). **Bloqueia codificação direta.**

### NOVO-CRIT-4/5/6 — Sistema paralelo de IDs INV-007/006/022 NÃO resolvido (llm-correctness)

REGRAS define INV-007=NF-e, INV-006=DPO, INV-022=verificação intermediária. PRD calibração e modelo continuam usando INV-007=2ª conferência, INV-006=regra decisão 7.8.6, INV-022=WORM (16 ocorrências de INV-022 sozinho). Hooks automatizados validariam o INV errado.
**Remediação:** renomeação em massa em `calibracao/prd.md` + `calibracao/modelo-de-dominio.md`:
- `INV-005 → INV-CAL-VERSAO-001`
- `INV-006 → INV-CAL-DEC-001`
- `INV-007 → INV-CAL-CONF-001` (já proposto)
- `INV-008 → INV-CAL-RAST-001`
- `INV-014 → INV-CAL-SNAP-001`
- `INV-019 → INV-CAL-RT-001`
- `INV-022 → INV-CAL-WORM-001`

Promover todos em REGRAS-INEGOCIAVEIS.md numa única migration.

---

## ALTOS NOVOS (rastreáveis ou bloqueadores)

| ID | Lente | Descrição | Bloqueia |
|---|---|---|---|
| NOVO-ALTO-1 | tech-lead | `OS` e `AtividadeDaOS` precisam coluna `correlation_id` persistida (hoje só em payload de evento). | P4 Marco 3 |
| NOVO-ALTO-2 | tech-lead | US-OS-004 AC fala "aceite quando exigido pelo tipo" sem tabela `tipo → exige_aceite`. | P4 Marco 3 |
| NOVO-ALTO-3 | tech-lead | INV-OS-ATIV-005(a) cita "delegação só explícita com audit" mas não há entidade `DelegacaoExecucao`. | P4 Marco 3 |
| NOVO-ALTO-4 | advogado | Zona D ADR-0021 usa "15 dias úteis" sem âncora LGPD art. 18 §3/§4. | P4 Marco 3 |
| NOVO-ALTO-5 | advogado | SHA-256 do texto do termo: canonicalização não declarada (LF vs CRLF, NFC vs NFD). Sugere ADR-0029. | P4 Marco 3 |
| NOVO-ALTO-6 | advogado | DPA cl. 4.7 referencia ADR-0021 em status `proposta` — fragilidade probatória. | 1º DPA externo |
| NOVO-ALTO-7 | corretora | `instalacao` em ambiente periculoso (Ex/ATEX, farma) — falta RC Operacional R$ 1-3M. | 1º tenant industrial |
| NOVO-ALTO-8 | drift-docs | `integracoes-inter-modulos.md` frontmatter desatualizado (`revisado-em: 2026-05-17`, `status: draft`) com conteúdo v10 dentro. | P1 Marco 3 |
| NOVO-ALTO-9 | drift-docs | `certificados/prd.md` frontmatter `revisado_em: 2026-05-17` mas US-CER-007/009 reescritas na Onda 6. | P1 Marco 3 |
| NOVO-ALTO-10 | drift-docs | 5 docs canônicos (`os/prd.md`, `os/glossario.md`, `controle-certificado-emitido.md`, `responsabilidade-tecnica.md`, `registros-tecnicos-7.5.md`) ainda `status: draft`. | P1 Marco 3 |
| NOVO-ALTO-11 | llm | `OS.Faturada`/`OS.Paga` não publicados no catálogo v10, mas estados existem na máquina de estados. Consumers (financeiro, fiscal) sem sinal. | P4 Marco 3 |
| NOVO-ALTO-12 | llm | Duplicação `Atividade.NaoConforme` (catálogo) × `NaoConformidade.Aberta` (calibração) — mesmo trigger, dois eventos, risco double-CAPA. | P4 Marco 3 |
| NOVO-ALTO-13 | llm | `Calibracao.Rejeitada` consumer declarado como "OS consumer Atividade.NaoConforme" — inversão lógica (Atividade.NaoConforme é PUBLICADO pela OS, não consumido). | P4 Marco 3 |
| NOVO-ALTO-14 | llm | Faltam INVs canônicas pra "rastreabilidade padrão", "2ª conferência", "WORM calibração genérico", "snapshot padrão externo". | P4 Marco 4 |
| NOVO-ALTO-15 | observabilidade | `calibracao/metricas.md` ficou pra trás do retrofit (sem tenant_id, sem correlation_id, sem ciclo CAPA, sem alertas novos). **OBS-002 violado em path crítico**. | P1 Marco 4 |
| NOVO-ALTO-16 | conformidade-lgpd | Evento `Calibracao.LeituraCorrigida` ausente do catálogo v10 — cadeia forense quebrada vs INV-CAL-AUD-001. | P4 Marco 4 |
| NOVO-ALTO-17 | conformidade-lgpd | INV-CAL-TXT-001 não enumera `NaoConformidade.{descricao,causa_raiz,acao_corretiva}` — hook não vai pegar PII em texto livre. | P4 Marco 4 |
| NOVO-ALTO-18 | corretora | Sublimite cyber "imagens confidenciais de cliente do tenant" — cadeia vendor↔tenant↔cliente final. | 1º tenant farma/regulado |
| NOVO-ALTO-19 | corretora | Endosso `contractual liability` na E&O pra cobrir disputa cobrança vendor↔tenant. | 1º tenant externo |

---

## MÉDIOS NOVOS (35 itens — agrupados)

### Drift/coerência (12)

- Frontmatter v9 → v10 catálogo eventos.
- Total eventos v9 (267) vs v10 (273).
- ADR-0026 `status: proposta` mas `responsabilidade-tecnica.md §3.1` já enforce política.
- `papeis-lgpd-multi-tenant.md` `relacionados:` aponta docs não-criados.
- `AGENTS.md` header de status × `CURRENT.md` (Marco 1 P5 reauditoria vs Marco 2 FECHADO).
- `os/contratos/api.md` L169 "ADR-0027 a criar" — já criada.
- INV-INT numeração 010 vs 013.
- Glossário OS L22 "EstadoOS tem 6 valores" mas lista 7.
- INV-027 em REGRAS L57 desatualizada (sem CANCELADA, sem ADR-0023).
- `EventoDeOS` retenção 25a × RAT-08 discrepância para OS calibração sem cert.
- `tipo_predominante` sem trigger de recálculo definido.
- `os/modelo-de-dominio.md` L23 não cita explicitamente INV-OS-ATIV-004.

### Conformidade/segurança (9)

- INV-OS-AUTHZ-001 ausente em comandos.
- Contagem RLS calibração: header 17 vs lista 21.
- `AceiteAtividade.ip_hash` política NÃO-LOG do IP cleartext em access.log não documentada.
- `MedicaoControle` WORM/mutável não declarado.
- `LeituraCorrecao` sem trigger PG BLOCK explícito.
- Geo cleartext em payload de `/atividades/{aid}/iniciar` sem arredondamento server-side.
- `RecepcaoItemCalibracao.fotos_anexo_ids` sem INV-OS-GEO-001 explicitado.
- Chave HMAC 10a × audit metrológico 25a (`MedicaoControle`/`PadraoUsado`/`EventoDeCalibracao`).
- Touch signature qualidade mínima (rabisco vazio).

### Produto/AC (6)

- AC-CAL-007-3 mantém "registra exceção" sem citar ADR-0026.
- Persona Auditor CGCRE ausente em `calibracao/personas.md`.
- US-CER-002/005 não citam evento publicado.
- `Calibracao.Aprovada` payload no PRD desatualizado.
- US-CAL-001-1 não declara consumer trigger `Atividade.Iniciada(tipo=calibracao)`.
- US-OS-010 falta AC-OS-010-4 bloqueando sequência ≤ menor terminal.

### Observabilidade (4)

- Métrica ciclo CAPA (CONTIDA→FECHADA) ausente.
- SLO regulatório CGCRE não marcado como SLO (% RBC fora escopo, padrões fora vigência).
- Cópia hourly B2 dos audit WORM não declarada (lag export PG→B2).
- Hook `correlation-chain-validator.sh` prometido mas inexistente.

### Calibração metrológica (3)

- Transição NaoConformidade REABERTA → ACAO_CORRETIVA_DEFINIDA pula CONTIDA (cl. 8.7.2).
- Retorno do status `NAO_CONFORME`/`PENDENTE_RESOLUCAO_NC` ambíguo.
- OrcamentoPorPonto vs orçamento agregado constante: coexistência sem invariante (cl. 7.6.3).

### Seguro/contratual (1)

- RT vendor V2 endosso `additional insured` ou apólice E&O profissional dedicada.

---

## BAIXOs NOVOS (20 — não bloqueiam, viram GATE)

- 7 itens drift cosmético (underscore vs hífen residual, `RTSubstituido` evento citado mas não no catálogo, etc.).
- 4 itens segurança (chave HMAC QR cert vs equipamento docs, `LeituraCorrecao` qualidade).
- 4 itens produto (Auditor CGCRE no glossário OS, AC-CER-007-3 binário, etc.).
- 3 itens observabilidade (`certificados/metricas.md` stub, KPI atividade reabertura).
- 2 itens LGPD/biometria (RIPD touch, BIOMETRIA_KEY).

---

## Veredito GO/NO-GO

| Pergunta | Resposta |
|---|---|
| Marco 3 OS pode arrancar **P1 (spec FORWARD)**? | **SIM** — 28 CRÍTICOS R1 resolvidos; AC binários robustos; modelo de domínio coerente. |
| Marco 3 OS pode arrancar **P4 (codificação)**? | **NÃO** — bloqueado por 6 CRÍTICOS R2: dupla FK, biometria, sistema paralelo INV. Onda 7 obrigatória pré-P4. |
| Marco 4 Calibração pode arrancar **P1**? | **NÃO** — `calibracao/metricas.md` desatualizado + sistema paralelo INV bloqueia + 4 MÉD novos calibração. |
| Apólice BPT (GATE-SEG-BPT-1) | EMERGENCIAL — independente das rodadas. |

---

## Onda 7 — escopo proposto (~3-5h)

**Pré-requisito de P4 Marco 3:**

1. **Resolver dupla FK** (NOVO-CRIT-1) — remover `link_modulo_tecnico` do `os/modelo-de-dominio.md` + glossário; manter só `Calibracao.atividade_os_id`. ADR-0023 §"Implicações" atualizada.
2. **Redigir `aceite-atividade-v1.0.md`** (NOVO-CRIT-2) — minuta versionada + canonicalização SHA-256 documentada.
3. **Biometria touch** (NOVO-CRIT-3) — INV-OS-ACEITE-BIO-001 + DPIA + matriz retenção biometria + chave KMS dedicada.
4. **Renomear INVs colididos** (NOVO-CRIT-4/5/6) — 7 renomeações em massa no PRD/modelo calibração; promover 7 INVs em REGRAS.
5. **ADR-0029 canonicalização texto probatório** (NOVO-ALTO-5).
6. **Coluna `correlation_id` persistida** em OS + AtividadeDaOS (NOVO-ALTO-1).
7. **Fix drift docs** (NOVO-ALTO-8, 9, 10) — frontmatter `integracoes-inter-modulos.md` + `certificados/prd.md` + status `stable` em 5 docs.
8. **`OS.Faturada`/`OS.Paga` no catálogo** (NOVO-ALTO-11) ou remover estados.
9. **Resolver duplicação `Atividade.NaoConforme` × `NaoConformidade.Aberta`** (NOVO-ALTO-12) — encadeamento, não duplicação.
10. **`AGENTS.md` header sincronizado com `CURRENT.md`**.

**Pré-requisito de P1 Marco 4:**

11. **Retrofit `calibracao/metricas.md`** (NOVO-ALTO-15) — tenant_id + correlation_id + ciclo CAPA + alertas.
12. **Zona D ADR-0021 prazo** (NOVO-ALTO-4) — "15 dias corridos + prorrogação art. 18 §4º".

**Resíduo MÉDIO+BAIXO** (~55 itens) — viram GATE-* Wave A rastreados, não bloqueiam.

---

## Em linguagem de produto (pro Roldão)

A rodada 2 confirmou que **128 dos 179 problemas da rodada 1 foram bem resolvidos** (71% de acerto). Mas o retrofit deixou **6 buracos críticos novos** + ~20 graves que precisam ser endereçados antes de começar a codar OS.

Os 6 críticos novos se concentram em:

1. **Dupla FK** entre OS e Calibração — falta limpar uma das pontas (CRT-3 ficou pela metade).
2. **Falta o texto canônico do "termo de aceite v1.0"** — `AceiteAtividade` guarda hash de um texto que ainda não existe.
3. **Assinatura touch (rabisco do cliente no mobile) é dado biométrico LGPD art. 11** — exige chave KMS dedicada + DPIA específica + classificação sensível.
4-6. **Sistema de IDs paralelo na calibração** (INV-007/006/022 etc.) — PRD usa IDs com significado divergente do catálogo central. Precisa renomeação em massa.

**Não bloqueia começar o ritual de spec FORWARD do Marco 3** (P1) — esse pode arrancar amanhã. Bloqueia começar a **codar o módulo** (P4), que viria 3-5 dias depois.

**Recomendação:** rodar uma **"Onda 7" curta** (~3-5h) atacando esses 6 críticos + ~10 altos antes de codar. Os outros ~75 médios/baixos viram GATEs rastreados Wave A — entram naturalmente quando cada módulo for codado.

**Ainda EMERGENCIAL:** apólice BPT — independente dessa auditoria.
