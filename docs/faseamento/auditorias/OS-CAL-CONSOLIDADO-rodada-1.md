---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente
escopo: Wave A Marco 3 (OS) + Marco 4 (Calibração) + Marco 5 (Certificados)
tipo: auditoria-10-lentes-pre-marco-3
relacionados:
  - docs/dominios/operacao/modulos/os/prd.md
  - docs/dominios/operacao/modulos/os/modelo-de-dominio.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/modelo-de-dominio.md
  - docs/dominios/metrologia/modulos/certificados/prd.md
  - docs/adr/0023-os-com-atividades.md
---

# Auditoria 10 lentes — Domínios OS + Calibração + Certificados (rodada 1)

> **Solicitada por Roldão em 2026-05-23**, após decisão ADR-0023 (OS com Atividades).
> Greenfield — ainda não tem código de OS, Calibração ou Certificados. Auditoria sobre
> PRDs + modelo-de-domínio + ADRs + integrações inter-modulares.
>
> **Objetivo:** identificar GAPs **antes** do ritual Spec Kit do Marco 3 começar, evitando
> retrabalho como aconteceu em Foundation F-A/F-B antes da consolidação de 2026-05-19.

---

## Sumário executivo

10 lentes despachadas em paralelo. **Veredito agregado: FAIL severo** — 28 CRÍTICO + 53 ALTO + 67 MÉDIO + 31 BAIXO. Não dá pra arrancar Marco 3 com este nível de drift entre ADR-0023 (aceita 2026-05-23) e o resto dos docs.

Causa-raiz comum em ~70% dos achados: **PRDs e modelo-de-domínio foram escritos antes do aprendizado consolidado em Marco 1 + Marco 2** (padrões `*_hash` em payload, EXIF strip, INV-EQP-LOC-001, INV-EQP-VERSAO-002, snapshot imutável, RLS pattern v2). Não é falta de conhecimento — é retrofit pendente.

---

## Distribuição por lente

| # | Lente | Veredito | CRÍT | ALTO | MÉD | BAIXO |
|---|---|---|---|---|---|---|
| 1 | tech-lead-saas-regulado (arquitetura/integrações) | **FAIL** | 6 | 8 | 10 | 3 |
| 2 | advogado-saas-regulado (LGPD/contratos) | **FAIL** | 3 | 5 | 5 | 3 |
| 3 | consultor-rbc-iso17025 (ISO 17025 / CGCRE) | **FAIL** | 3 | 5 | 6 | 3 |
| 4 | corretora-seguros-saas (risco/cobertura) | **FAIL** | 5 | 4 | 3 | 1 |
| 5 | auditor-produto (AC binários / non-goals) | **FAIL** | 5 | 5 | 7 | 2 |
| 6 | auditor-drift-docs (consistência docs) | **FAIL** | 2 | 5 | 8 | 5 |
| 7 | auditor-llm-correctness (coerência interna) | **FAIL** | 4 | 7 | 10 | 6 |
| 8 | auditor-conformidade-lgpd (PII / base legal) | **CONCERN** | 0 | 4 | 5 | 2 |
| 9 | auditor-seguranca (multi-tenant / authz) | **FAIL** | 3 | 5 | 5 | 3 |
| 10 | auditor-observabilidade (trilha / correlation_id) | **FAIL** | 0 | 2 | 5 | 3 |
| | **Total agregado** | | **28** | **53** | **67** | **31** |

---

## GAPs agrupados por tema (consolidado)

### TEMA A — ADR-0023 propagada parcialmente (drift estrutural)

Confirmado pelas lentes **drift-docs, produto, llm-correctness, tech-lead, observabilidade**.

| ID | Gap | Severidade |
|---|---|---|
| TEMA-A.1 | `os/glossario.md:16` ainda lista 5 tipos legados ("calibração / manutenção / instalação / verif INMETRO / vistoria") em vez dos 6 da ADR-0023 (manutenção corretiva + preventiva separadas). | CRÍTICO |
| TEMA-A.2 | `os/contratos/api.md:23-33` aceita `"tipo": "calibracao"` no POST /v1/os — modelo legado anterior à ADR-0023; endpoints `/iniciar` `/concluir` operam em OS, não em atividade. Faltam endpoints `iniciarAtividade`/`concluirAtividade`/`adicionarAtividade`. | ALTO |
| TEMA-A.3 | `os/metricas.md` mede só OS atômica — KPI "Tempo médio RASCUNHO→CONCLUIDA por tipo" usa `tipo` da OS que sumiu. Falta métrica de atividade. | ALTO |
| TEMA-A.4 | Calibração ainda aponta `Calibracao.ordem_servico_id` (FK em OS) — deveria ser `atividade_os_id` (FK em AtividadeDaOS). | CRÍTICO |
| TEMA-A.5 | INV-OS-ATIV-001/002/003/004 prometidas pela ADR-0023 **não estão em `REGRAS-INEGOCIAVEIS.md`**. | CRÍTICO |
| TEMA-A.6 | US-OS-001..010 sem AC binário (GIVEN/WHEN/THEN explícito). Em especial US-OS-009 (combinada) e US-OS-010 (atividade em andamento) — recém-criadas pela ADR. | CRÍTICO |
| TEMA-A.7 | Glossário OS não tem `AtividadeDaOS`, `EstadoAtividade`, `TipoAtividade`, `tipo_predominante`, `sequencia`, `link_modulo_tecnico`. | CRÍTICO |

### TEMA B — Conformidade ISO 17025 / CGCRE (gaps de modelo regulatório)

Confirmado pelas lentes **consultor-rbc-iso17025, advogado, segurança**.

| ID | Gap | Severidade |
|---|---|---|
| TEMA-B.1 | Snapshot retroativo de padrão (cl. 6.5 + 7.7.1.f): `PadraoUsado.snapshot_padrao_json` é imutável, mas falta `snapshot_capturado_at` cravando que snapshot foi feito *no momento do uso*, não retroativamente. | CRÍTICO |
| TEMA-B.2 | Ciclo CAPA fechado (cl. 7.10 + 8.7): INV-012 só bloqueia emissão; faltam estados `CONTIDA → ACAO_CORRETIVA_DEFINIDA → ACAO_EXECUTADA → EFICACIA_VERIFICADA → FECHADA` + `causa_raiz`/`responsavel_acao`/`eficacia_verificada_por`. CGCRE pede em toda supervisão. | CRÍTICO |
| TEMA-B.3 | Cl. 7.5 (registros técnicos imutáveis com rasura digital): não existe doc canônico; salta de 7.4 pra 7.7. Falta `LeituraCorrecao` para correções pré-aprovação rastreáveis. | CRÍTICO |
| TEMA-B.4 | Cl. 7.4 (recebimento de item do cliente para calibração): falta entidade `RecepcaoItemCalibracao` com avaliação de aptidão + foto + aceite. Marco 2 cobriu equipamentos, calibração não reusa. | ALTO |
| TEMA-B.5 | Cl. 7.6 (incerteza): `OrcamentoIncerteza.componentes_json` é blob — NIT-DICLA-030 rev. 15 exige orçamento ponto-a-ponto. Falta `ComponenteIncerteza` 1:N + `OrcamentoPorPonto` 1:N. | ALTO |
| TEMA-B.6 | Cl. 7.7.1 (gráfico de controle): falta US + entidade `MedicaoControle` (X-R/CUSUM) com alerta automático 2σ/3σ. | ALTO |
| TEMA-B.7 | Cl. 7.8.3.1.b (certificado): falta declaração explícita "resultados se aplicam apenas ao item calibrado tal como recebido" + "certificado não pode ser reproduzido parcialmente". CGCRE marca como NC documental. | ALTO |
| TEMA-B.8 | Cl. 6.2.5 (exceção revisor=executor): texto frouxo em US-CAL-007 AC-007-3. Falta política objetiva + limite de % exceções/mês. | ALTO |
| TEMA-B.9 | Cl. 8.3 (controle de documentos): falta página `/manual-qualidade` no produto listando documentos vigentes por tenant. | MÉDIO |
| TEMA-B.10 | Cl. 6.6 (subcontratação): PRD não declara se aceita subcontratar calibração fora do escopo CMC pra outro lab — non-goal ou Wave A? | MÉDIO |

### TEMA C — Segurança multi-tenant + Auditoria imutável

Confirmado pelas lentes **segurança, observabilidade, conformidade-lgpd**.

| ID | Gap | Severidade |
|---|---|---|
| TEMA-C.1 | RLS policy não declarada nos modelos-de-domínio. Marco 2 (INV-TENANT-003) obriga policy RLS na mesma migration da CREATE TABLE — modelos PRD não citam, gerador spec→código pode produzir tabela sem policy. | CRÍTICO |
| TEMA-C.2 | `reabrirOS` clona atividades pra OS-filha sem invariante explícito `OS-filha.tenant_id = OS-mãe.tenant_id`. Paralelo do INV-050 cross-tenant (Marco 2). | CRÍTICO |
| TEMA-C.3 | Anti-fraude A3: faltam validação server-side de que `certificado_a3_subject_cn.cpf == sessao.usuario.cpf`. Hoje RT pode usar A3 de outro RT (token físico esquecido). | CRÍTICO |
| TEMA-C.4 | INV-AUTHZ-001 ausente nos 34 comandos sensíveis (OS + Calibração + Certificados) — modelos citam "RBAC genérico" mas não referenciam `AuthorizationProvider.can(action, resource, tenant_id, purpose)` (porta F-B). | ALTO |
| TEMA-C.5 | `EventoDeOS` declarado "append-only" mas sem trigger PG nem `# audit-immutability` declarado. Calibração nem tem entidade equivalente (só eventos publicados em bus, log volátil). | ALTO |
| TEMA-C.6 | SEC-QR-001 + INV-051 (Marco 2) **não citados** no QR Code da etiqueta de calibração (US-CAL-001) nem no QR de verificação pública (US-CER-009). Risco de mineração cross-tenant. | ALTO |
| TEMA-C.7 | Sync mobile sem `client_event_id`/Idempotency-Key obrigatório em `iniciarAtividade`/`concluirAtividade` — replay 2x gera evento duplicado + calibração duplicada (IDEMP-001 + IDEMP-002). | ALTO |
| TEMA-C.8 | RT desligado: INV-INT-002 (revogar sessões + bloquear emissões em ≤2s) **não citado** em PRDs/modelo. Sem consumer `Colaborador.Desligado`, signatário fica `ativo=true` post-desligamento. | ALTO |
| TEMA-C.9 | Endpoints públicos de portal-cliente + verificador de certificado sem rate-limit declarado (paralelo a SEC-QR-001). Mineração de hashes adjacentes viável. | MÉDIO |
| TEMA-C.10 | Textos livres (`razao_cancelamento`, `razao_nao_conformidade`, `observacoes_gerais`, `decisao_manual_se_zona`, `nota_revisao`) sem regex anti-PII + limite — paralelo a INV-EQP-LOC-001 / INV-EQP-VERSAO-001. | MÉDIO |
| TEMA-C.11 | `EventoDeOS.payload` jsonb sem proibição de PII + sanitização **na escrita** (SEC-SANITIZE-001). Repete bug-classe de 2026-05-19. | MÉDIO |
| TEMA-C.12 | Eventos `OSAberta/Concluida/Cancelada` + `AtividadeIniciada/Concluida` + `Calibracao.Recepcionada/Aprovada` carregam `cliente_id`/`tecnico_id`/`revisor_id` UUID cru. Padrão Marco 1+2 obriga `*_hash` HMAC-tenant. | ALTO |

### TEMA D — LGPD / Direitos do titular / Contratual

Confirmado pelas lentes **advogado, conformidade-lgpd**.

| ID | Gap | Severidade |
|---|---|---|
| TEMA-D.1 | Geolocalização em OS sem **RIPD aprovada** — PRD cita RAT-07 mas RAT-07 não existe canonicamente em REGRAS-INEGOCIAVEIS.md. | CRÍTICO |
| TEMA-D.2 | Retenção de OS **só-manutenção** não coberta na matriz (que cobre cert 25a e foto OS 5a, mas não OS manutenção pura/cancelada). | CRÍTICO |
| TEMA-D.3 | Termo de aceite cliente não-versionado / sem hash + IP + texto canônico. Lei 14.063/2020 art. 4º exige vínculo signatário ↔ manifestação. | CRÍTICO |
| TEMA-D.4 | INV-CER-COMP-001 ausente: validar competência do RT **na data da execução**, não da emissão (ADR-0022 aceita mas não enforced). | ALTO |
| TEMA-D.5 | Substituição de RT mid-calibração: comando `trocarRevisorOuConferente` ausente do modelo — CGCRE marca NC. | ALTO |
| TEMA-D.6 | Retificação de certificado confunde correção administrativa vs recálculo técnico (ISO 17025 §7.8.8). Hoje RT sozinho pode reemitir qualquer natureza. | ALTO |
| TEMA-D.7 | EXIF + geo em foto (US-CER-007 "preserva EXIF") contradiz matriz que exige EXIF strip em fotos com PII de estabelecimento. | ALTO |
| TEMA-D.8 | Conflito eliminação LGPD vs OS em andamento: ADR-0021 não cobre cliente PF com OS aberta pedindo eliminação. | ALTO |
| TEMA-D.9 | Cliente pode recusar foto (privacy industrial): falta `ChecklistDaAtividade.dispensa_foto: bool + motivo + assinatura_cliente_hash`. | MÉDIO |
| TEMA-D.10 | 4-party data (tenant→cliente_PJ→contato_PF) sem mapeamento DPA padrão. | MÉDIO |
| TEMA-D.11 | Anti-fraude checklist: técnico_executor ≠ usuário autenticado deveria bloquear, hoje só audit. INV-OS-ATIV-005 a criar. | MÉDIO |

### TEMA E — Integrações inter-modulares + Eventos

Confirmado pelas lentes **tech-lead, observabilidade, llm-correctness**.

| ID | Gap | Severidade |
|---|---|---|
| TEMA-E.1 | `AtividadeIniciada/Concluida/NaoConforme` **ausentes do catálogo de eventos v9** (`docs/comum/integracoes-inter-modulos.md`). Catálogo precisa virar v10. | CRÍTICO |
| TEMA-E.2 | Catálogo v9 ainda lista `OS.Concluida → calibração` (modelo antigo). Pós-ADR-0023 calibração dispara por `AtividadeIniciada filter tipo=calibracao`, **não** OS.Concluida (que vem depois). Inversão lógica. | CRÍTICO |
| TEMA-E.3 | `link_modulo_tecnico` em AtividadeDaOS é string genérica sem FK tipada nem RLS. Quebra INV-TENANT-001. Inverter: `Calibracao.atividade_os_id` FK explícita. | CRÍTICO |
| TEMA-E.4 | Calibração não consome `Equipamento.perfil_tenant_snapshot` (ADR-0022). Equipamento muda de cliente/RT mid-calibração → certificado com dados errados. | CRÍTICO |
| TEMA-E.5 | Cadeia `correlation_id`/`causation_id` ausente em todas as entidades (OS, AtividadeDaOS, Calibracao, Certificado, NotaFiscal) e em todos os payloads de evento. Trilha forense quebrada. | ALTO |
| TEMA-E.6 | `AtividadeNCResolvida` ausente: NAO_CONFORME→CONCLUIDA não publica evento → certificado fica bloqueado eternamente. | ALTO |
| TEMA-E.7 | `Calibracao.Aprovada` payload `{calibracao_id, decisao}` não inclui `atividade_os_id` nem `os_id` — certificado consumer precisa query extra. | MÉDIO |
| TEMA-E.8 | Certificados.Cancelado sem consumer `fiscal` — se cert virou base de NFS-e, fiscal precisa CC-e. | MÉDIO |
| TEMA-E.9 | Falta porta `PhotoStorageProvider`/`EXIFExtractor` na anti-corrosion v3 (US-CER-007 lê EXIF). | MÉDIO |
| TEMA-E.10 | Reabertura não especifica quais atividades clonar (todas? só do tipo da reabertura?) nem estado inicial. | ALTO |

### TEMA F — ADRs estruturantes faltantes

Confirmado pelas lentes **tech-lead, RBC, segurança**.

| ID | Gap | Severidade |
|---|---|---|
| TEMA-F.1 | **ADR-0024 — Regra de decisão ISO 17025 7.8.6 (banda de guarda)**: PRD lista 3 regras + zona de incerteza mas decisão estrutural sem ADR. | ALTO |
| TEMA-F.2 | **ADR-0025 — Validação de software ISO 17025 7.11**: `validacao-software.md` existe mas é doc operacional, não ADR. | ALTO |
| TEMA-F.3 | **ADR-0026 — 2ª conferência + independência RT**: política de exceção sem ADR. | ALTO |
| TEMA-F.4 | **ADR-0027 — Sync mobile com merge por atividade**: ADR-0004 (proposta) não foi atualizada pós-ADR-0023. | ALTO |
| TEMA-F.5 | **ADR-0028 — Mapa de coberturas Wave A** (E&O + Cyber + D&O + BPT + extensão veicular UMC): GAP-SEG-01..05 antes do briefing corretora. | CRÍTICO |
| TEMA-F.6 | Aceitar **ADR-0022** (RT do tenant, hoje "proposta") antes de Marco 4 — sem isso INV-CER-COMP-001 não tem onde se ancorar. | ALTO |

### TEMA G — Seguros / risco assegurável

Confirmado pela lente **corretora-seguros-saas**. **Todos os 5 CRÍTICOS são GATEs Wave A pré-1º tenant externo + 1 ativo já em dogfooding (BPT)**.

| ID | Gap | Severidade |
|---|---|---|
| TEMA-G.1 | BPT (custódia física de instrumento no laboratório) ausente do mapa de coberturas — ADR-0019 só fala E&O+cyber. Capital sugerido: R$ 500k-2M. **GATE imediato** (Balanças Solution dogfooding já recebe instrumento de cliente). | CRÍTICO |
| TEMA-G.2 | Atividade `vistoria` gera laudo civil sem cobertura E&O dimensionada pra parecer técnico humano. | CRÍTICO |
| TEMA-G.3 | Garantia metrológica do certificado (cliente farma usa cert pra liberar lote → recall) sem cobertura explícita "consequential regulatory damages". Capital: R$ 2-5M. | CRÍTICO |
| TEMA-G.4 | Cyber não cobre comprometimento de chave A3 do RT (phishing). Cláusula `third-party credential abuse`/`social engineering coverage` obrigatória. | CRÍTICO |
| TEMA-G.5 | Transferência de equipamento mid-OS (Marco 2) deixa segurado BPT indefinido. Cláusula DPA + apólice BPT com `named insured by date of loss`. | CRÍTICO |
| TEMA-G.6 | App técnico mobile sem extensão veicular pra UMC + padrão F1 (R$ 15-80k no carro). | ALTO |
| TEMA-G.7 | Cyber subdimensionada pra acervo de fotos (NS visível, layout fábrica do cliente). LGPD art. 46 + segredo industrial. | ALTO |
| TEMA-G.8 | Disputa civil pós-NC com cobrança (US-OS-005) sem cobertura defesa jurídica `billing dispute legal defense`. | ALTO |
| TEMA-G.9 | DR de calibração não-emitida (perda de dados pré-WORM) sem cobertura `dependent business interruption`. | ALTO |

---

## Bloqueios pra arrancar Marco 3

Sob INV-RITUAL-001 (MÉDIO+ bloqueia), nenhum dos 4 marcos seguintes pode começar P1 (spec FORWARD) sem zerar pelo menos os **28 CRÍTICOS**. Lista priorizada de pré-requisitos:

### Antes de Marco 3 (OS) começar ritual Spec Kit

1. **TEMA-A inteiro** — propagação completa da ADR-0023 (glossário OS + contratos/api.md + metricas.md + AC binários US-OS-001..010 + INV-OS-ATIV-001..004 promovidos a REGRAS-INEGOCIAVEIS).
2. **TEMA-C.1, C.2, C.3** — RLS policy declarada nos modelos + INV-OS-ATIV-005 cross-tenant em `reabrirOS` + AC anti-fraude A3.
3. **TEMA-D.1, D.2, D.3** — RIPD geo-OS + matriz retenção +4 linhas atividade não-calibração + entidade `AceiteAtividade` versionada.
4. **TEMA-E.1, E.2, E.3, E.4** — catálogo v10 inclui eventos AtividadeDaOS + inversão consumer calibração + FK tipada `Calibracao.atividade_os_id` + snapshot equipamento em calibração.
5. **TEMA-G.1** (BPT dogfooding) — apólice antes do próximo cliente trazer instrumento.

### Antes de Marco 4 (Calibração) começar ritual Spec Kit

6. **TEMA-B.1, B.2, B.3** — snapshot retroativo de padrão + ciclo CAPA fechado + cl. 7.5 registros técnicos com `LeituraCorrecao`.
7. **TEMA-F.1, F.2, F.3, F.4, F.6** — 4 ADRs novas + aceite ADR-0022 RT do tenant.

### Antes de 1º tenant externo pago

8. **TEMA-G.2..G.5** — apólice E&O ampliada + cyber A3 + BPT named insured by date of loss + garantia metrológica.

---

## Próximo passo recomendado

Recomendo **NÃO arrancar Marco 3 ainda**. Em vez disso:

1. **Sprint de retrofit pré-Marco 3** (2-5 dias) — atacar TEMA-A + TEMA-C.1..3 + TEMA-D.1..3 + TEMA-E.1..4 em paralelo com os 4 humano-substitutos (tech-lead + advogado + RBC + corretora).
2. **Criar 5 ADRs** (TEMA-F) — propostas + revisão dos 4 subagentes + aceite Roldão antes da spec FORWARD do Marco 3.
3. **Briefing corretora SUSEP humana** com base no doc da corretora-saas → emitir BPT no curto prazo + as outras 4 modalidades antes do 1º tenant externo.
4. **Após retrofit + ADRs + apólice BPT** → arrancar P1 do Marco 3 (spec FORWARD) com base sólida.

Sem isso, Marco 3 vai entrar em loop de auditoria iguzinho ao que aconteceu na Foundation antes de 2026-05-19 — alto custo, baixo aprendizado.

---

## Em linguagem de produto (pro Roldão)

A auditoria com 10 olhares achou 179 problemas (28 graves, 53 importantes, 67 médios, 31 leves). 70% deles vêm do mesmo motivo: você decidiu "OS com Atividades" ontem, mas só 2 dos ~20 documentos relacionados foram atualizados.

**O que tá pegando, em resumo:**

- **Decisão ADR-0023** ficou no PRD da OS e no modelo, mas o glossário, os contratos de API, as métricas e as user stories ainda falam do modelo antigo.
- **6 documentos da calibração** referenciam "OS" quando deveriam referenciar "Atividade da OS".
- **Modelo de calibração** ainda está com práticas antes do Marco 1+2 — falta tudo o que aprendemos com clientes e equipamentos (esconder dados pessoais nos eventos, tirar EXIF de foto, hash em vez de UUID).
- **Conformidade ISO 17025** tem 3 buracos sérios que CGCRE detecta em auditoria: snapshot de padrão pode ser feito retroativamente, ciclo de não-conformidade não tem "verificação de eficácia", e falta documento da cláusula 7.5 (registros técnicos imutáveis).
- **Seguro** está parcialmente coberto pelo ADR-0019, mas faltam 5 modalidades — incluindo BPT (custódia do instrumento) que já deveria existir hoje na Balanças Solution.

**Sugestão:** antes de codar OS, fazer 1 semana de "limpeza" — atacar os 28 críticos. Sem isso, Marco 3 vai ter mais retrabalho que aproveitamento.
