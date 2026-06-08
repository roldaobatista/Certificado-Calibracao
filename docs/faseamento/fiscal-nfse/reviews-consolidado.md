---
owner: agente-ia
revisado-em: 2026-06-08
proximo-review: 2026-09-08
status: draft
diataxis: explanation
audiencia: [agente, advogado, tech-lead, consultor-rbc, auditor]
frente: fiscal-nfse
tipo: reviews-consolidado-P2
relacionados:
  - docs/faseamento/fiscal-nfse/spec.md
  - docs/faseamento/fiscal-nfse/plan.md
---

# P2 — Revisões consolidadas da spec `fiscal/NFS-e`

> 3 revisores roteados (INV-RITUAL-003): **advogado-saas-regulado** (retenção/LGPD/
> contrato), **tech-lead-saas-regulado** (porta/idempotência/máquina de estados),
> **consultor-rbc-iso17025** (matriz perfil × documento metrológico). **Veredito dos
> 3 = APROVA COM CORREÇÕES.** Nenhum REPROVA; nenhum CRÍTICO de risco bloqueia o
> arranque da Fatia 1a. TL-06 é "crítico de coerência" (predicate no lugar errado vs
> ADR-0073) e é incorporado já no /plan. Total: 26 achados (1 crítico-coerência + 6
> ALTO + 11 MÉDIO + 8 BAIXO/confirmação).

## 1. Convergência forte (3 revisores no mesmo ponto)

A questão aberta §7 da spec (fiscal reconsulta vigência do Tenant **ou** confia no
snapshot do Certificado?) foi respondida igual por tech-lead e consultor-rbc:

> **A trava de perfil combina (a) perfil do Tenant lido server-side via ContextVar
> [defesa L6] + (b) `Certificado.tipo_acreditacao` snapshotado pelo M8 [classificação
> RBC]. Roda DENTRO do `emitir_nfse` (use case), NÃO no permission layer DRF
> [ADR-0073]. NUNCA reconsulta `Tenant.acreditacao_vigencia_fim` — a vigência RBC já
> foi consumada pelo M8 na data de emissão do certificado.**

Isto vira **D-FIS-5** + **INV-FIS-PERFIL-001/002** no /plan + emenda ADR-0008.

## 2. Achados — advogado (FIS-J)

| ID | Sev | Resumo | Destino /plan |
|----|-----|--------|---------------|
| FIS-J-01 | ALTO | Listar as 14 cláusulas mínimas do contrato BaaS (6 da ADR-0008 §5 + 8 complementos) | GATE-FIS-CONTRATO — lista cravada no /plan §Gates |
| FIS-J-02 | MÉDIO | Fundamentação do prazo 5a imprecisa ("art. 173 CTN" é decadência do Fisco) | corrigir citação: art. 173/174 CTN + art. 195 §único CTN + legislação municipal ISS |
| FIS-J-03 | ALTO | Divergência interna: spec "5a+10a prudencial" vs matriz vigente "5a" | **manter 5a como mínimo legal** + nota prudencial até 10a quando XML compõe audit de path sensível; não inventar 10a fiscal autônomo |
| FIS-J-04 | ALTO | Conflito crypto-shredding × retenção não explícito | **INV-FIS-RETENCAO-001**: NFS-e + XML = zona B (ADR-0021); pedido de eliminação do titular = recusa fundamentada art. 16 I LGPD; anonimização só após prazo fiscal |
| FIS-J-05 | MÉDIO | Distinguir payload-ao-provider (PII clara) de evento-WORM (hash) | documentar 2 objetos/2 regimes; check anti-PII-clara no evento |
| FIS-J-06 | MÉDIO | Responsabilidade por erro de emissão não tratada | cláusula limitação resp. (tenant é responsável fiscal pelo conteúdo; Aferê = veículo técnico) — referência cruzada ToS billing-saas |
| FIS-J-07 | MÉDIO | Cadeia LGPD tripla não mapeada (tomador→tenant→Aferê→BaaS) | documentar: tenant=controlador, Aferê=operador (art. 39), BaaS=sub-operador (art. 39 §único) |
| FIS-J-08 | BAIXO | NIT-DICLA-030 N/A — confirmação | registrar "fiscal não cria interface metrológica" |
| FIS-J-09 | BAIXO | Separar DPA Aferê↔BaaS de ToS/DPA Aferê↔tenant | GATE-FIS-CONTRATO cobre só Aferê↔BaaS |

## 3. Achados — tech-lead (TL)

| ID | Sev | Resumo | Destino /plan |
|----|-----|--------|---------------|
| TL-01 | ALTO | Protocol ADR-0008 §1 vaza conceito BR (`chave_acesso_44`, CNAE) | VO agnóstico enxuto; campos BR em `InvoiceResult.metadata`/`raw_response`; tradução BR só no serializer infra; VO não valida formato BR |
| TL-02 | ALTO | "UNIQUE no Idempotency-Key" é redundante; molde usa serviço central | 2 camadas: (a) Idempotency-Key via serviço central reusado M8; (b) UNIQUE de **negócio** `(tenant, origem_id, versao)` + `existe_chave` no use case |
| TL-03 | ALTO | PENDING→AUTHORIZED sem dupla emissão | UNIQUE de negócio fecha: 2º `emitir` da mesma origem em PENDING → 409 retorna nota existente; `consultar` é o único caminho PENDING→terminal |
| TL-04 | MÉDIO | `network_timeout` não é estado da nota; REJECTED terminal | timeout = nenhuma persistência + `falhar_chave` + 503/504; REJECTED terminal (nova tentativa = nova origem) |
| TL-05 | BAIXO | Cancelamento = **Padrão B** (transição de estado + evento WORM append-only) | entidade AUTHORIZED→CANCELED reflete estado atual; imutabilidade vem do evento na cadeia hash + XML canonicalizado; advisory lock `(tenant, nfse_id)` |
| TL-06 | CRÍTICO (coerência) | Predicate especificado em `authz/predicates.py` contradiz ADR-0073 | mover validação metrológica para o **use case** com `Certificado` carregado; DRF só `tenant_perfil_e`; reescrever INV-FIS-PERFIL-001 + emenda PRD §11 |
| TL-07 | MÉDIO | Mock no domínio (ok); breaker na infra (não acopla núcleo) | use case sempre recebe `FiscalProvider` injetado; hook anti-import cobre `pybreaker` também |
| TL-08 | BAIXO | Path raiz própria confirmado (fiscal ≠ metrologia/) | nota no /plan declarando a assimetria (evita auditor-drift) |
| TL-09 | MÉDIO | Faltam ADRs/emendas | ver §5 deste doc |
| TL-dec7 | — | Evento `Fiscal.NFSeEmitida` vai ao **outbox** (consumer contas-receber previsto) | nome lowercase `fiscal.nfse_emitida` (CHECK do `bus_outbox`); seam pronto, drenável |

## 4. Achados — consultor-rbc (RBC)

| ID | Sev | Resumo | Destino /plan |
|----|-----|--------|---------------|
| RBC-01 | ALTO | Fonte de verdade da vigência RBC dupla/mal-fechada (§7) | cravar D-FIS-5 + INV-FIS-PERFIL-002 + emenda ADR-0008: fonte = `Certificado.tipo_acreditacao`, nunca reconsulta Tenant |
| RBC-02 | ALTO | Risco INVERSO: reconsultar rebaixaria NFS-e legitimamente RBC | predicate NÃO reavalia vigência; só compatibilidade perfil↔tipo_acreditacao |
| RBC-03 | MÉDIO | Data de referência não declarada | declarar: vigência avaliada 1x na emissão do certificado; NFS-e herda snapshot (fatura serviço já prestado) |
| RBC-04 | MÉDIO | Falta borda simétrica: perfil A PODE emitir NFS-e de cert NAO_RBC | predicate perfil A exige `certificado_id` vinculado, **não** `tipo_acreditacao==RBC` obrigatório; AC novo |
| RBC-05 | MÉDIO | Flag `em_preparacao_para_rbc` (perfil C) não pode sugerir acreditação | flag = metadado interno; **proibida** na `service_description`/campos impressos; hook `fiscal-anti-rbc-em-descricao` |
| RBC-06 | MÉDIO | Perfil D: descrição não pode nomear ISO 17025/RBC | terminologia "aferição/verificação" (herda M8); proibida palavra "ISO 17025"/"RBC" |
| RBC-07 | BAIXO | `tipo_servico="calibracao_basica"` (perfil D) arriscado | preferir `"afericao"`/`"verificacao"` — **decisão de produto/terminologia → AskUserQuestion ao Roldão** |
| RBC-08 | BAIXO | NIT-DICLA-030 N/A — confirmação | linha em §5 spec |

## 5. ADRs / emendas a cravar no /plan (P3)

- **Emenda ADR-0008** (sem ADR nova): (a) **fronteira fiscal↔M8** — vínculo RBC da
  NFS-e provém exclusivamente do snapshot `Certificado.tipo_acreditacao`; fiscal nunca
  reconsulta `Tenant.acreditacao_vigencia_fim` (RBC-01/02/03); (b) **VO agnóstico** —
  campos BR (`chave_acesso_44`/`numero`) em `metadata`, não atributo nomeado (TL-01);
  (c) **14 cláusulas** mínimas do contrato BaaS (FIS-J-01) substituem as 6 da §5.
- **Emenda PRD §11** — predicate de perfil roda no **use case**, não em
  `authz/predicates.py` (TL-06, coerência ADR-0073). Atualizar AC-FIS-001 (borda
  perfil A + cert NAO_RBC = RBC-04; anti-RBC na descrição = RBC-05/06).
- **ADR-0073** (já existe) — citada como precedente; não reabrir.
- **Sem ADR nova.** Tudo cabe em emenda ADR-0008 + emenda PRD.

## 6. Itens que escalam ao Roldão (decisão de produto)

- **RBC-07 (terminologia perfil D):** `"calibracao_basica"` vs `"afericao"`/
  `"verificacao"` — o cliente lê. Recomendação dos revisores: `"afericao"`. Levar via
  `AskUserQuestion` antes de cravar no /plan (regra #0.5 caso B).

## 7. Itens que escalam a humano licenciado (pré-produção)

- Minuta do contrato BaaS (14 cláusulas) → revisão advogado OAB antes de assinar
  (GATE-FIS-CONTRATO; `project_sem_contratacoes_externas_ate_producao`).
- Drill de chaos no BaaS sandbox (swap primary→fallback sob carga) antes do 1º tenant
  pago (GATE-FIS-SMOKE-TRIMESTRAL — tech-lead).
- 1ª auditoria CGCRE / homologação software → consultor RBC credenciado.

**Próximo:** `AskUserQuestion` (RBC-07) → `plan.md` (P3) incorporando os 26 achados +
numerando INV-FIS + emendas → `/tasks` (T-FIS-NNN) → implement Fatia 1a.
