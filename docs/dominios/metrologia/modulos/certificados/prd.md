---
owner: roldao
revisado-em: 2026-06-01
proximo-review: 2026-09-01
status: stable
modulo: certificados
dominio: metrologia
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/controle-certificado-emitido.md
  - docs/dominios/metrologia/modulos/calibracao/garantia-validade-7.7.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
  - docs/dominios/metrologia/modulos/procedimentos/prd.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - docs/adr/0009-onde-a3-assina.md
  - docs/adr/0021-anonimizacao-vs-retencao-regulatoria.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0043-calibracao-faturamento-bloqueio-inadimplencia.md
  - docs/adr/0044-exportacao-regulatoria-anvisa-saude.md
  - docs/adr/0045-certificado-recall-suspensao-errata.md
  - docs/adr/0046-ocsp-crl-revogacao-online.md
  - docs/adr/0047-carimbo-tsa-iti-pades-ltv.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
historico:
  - 2026-05-23 — versão draft com US-CER-001..010 + US-CER-013/016..020 (Onda 7 saneamento + ADRs 0021/0043/0044/0045).
  - 2026-05-27 — Onda PRE-A.3 BATCH B1 saneamento perfil ADR-0067 (§6.1 corrigido lê Tenant.perfil_regulatorio do banco — FAIL L6 fraude documental fechada — + matriz por perfil + AC binário GIVEN-WHEN-THEN + emendas ADRs 0009/0044/0045/0047 explicitadas + status promovido para stable).
---

# PRD — Módulo Certificados, Relatórios e Documentos Técnicos

> Módulo dedicado à geração, emissão controlada, distribuição e versionamento de certificados de calibração, relatórios técnicos e documentos derivados. Separado do módulo Calibração porque a emissão tem ciclo de vida e governança próprios (ISO 17025 7.8).

---

## 1. O que este módulo é

Plataforma única de emissão e gestão de documentos técnicos: certificados de calibração com numeração sequencial inviolável, relatórios de serviço, relatórios fotográficos, relatórios de não conformidade, laudos técnicos e etiquetas de identificação. Suporta templates customizáveis (cabeçalho, rodapé, logo, assinatura), assinatura digital A3 do responsável técnico, reemissão controlada com versionamento, envio automático ao cliente e disponibilização no portal.

## 2. Por que este módulo existe (problema a resolver)

Certificado é o produto-final entregue ao cliente — vale dinheiro, vale auditoria, vale CGCRE. Emissão errada (numeração quebrada, dados trocados entre certificados, PDF reemitido sem versionamento) gera não-conformidade na auditoria CGCRE e pode resultar em perda da acreditação. Hoje (mystery shopping Calibre.Software) o concorrente trata isso como afterthought; nosso diferencial é tratar como ciclo de vida primeiro-cidadão.

## 3. Personas

**Persona dominante:** P-MET-02 (responsável técnico RT — emite, assina e supervisiona certificados) + P-OP-05 (cliente final — consulta no portal). Detalhe completo em `personas.md` deste módulo + `../../personas.md` + `docs/comum/personas.md`.

## 3.1 Perfil regulatório do tenant (ADR-0067 — CRÍTICO)

> **Matriz feature × perfil canônica:** `docs/conformidade/comum/matriz-feature-perfil.md` (Sprint 3 SAN-PERFIL-TENANT).
>
> **Atenção L6:** PRD anterior tinha `cert.tipo_acreditacao == "RBC"` no template (§6.1) — campo lido do payload da request, **vetor de fraude documental viável** (qualquer call-site podia mentir o `tipo_acreditacao` e burlar selo RBC). Reescrito 2026-05-27 para `tenant_perfil_e(['A'])` lendo `Tenant.perfil_regulatorio` do banco via ContextVar.

Predicate canônico: **`tenant_perfil_e(perfis_aceitos: list[str])`** em `src/infrastructure/authz/predicates.py`. Lê `Tenant.perfil_regulatorio` (ContextVar `perfil_tenant_context` populada por middleware Sprint 2 SAN-PERFIL-TENANT). **Fail-closed timeout 50ms**, jamais payload.

| US / Feature do módulo | Perfil A — RBC acreditado | Perfil B — Rastreável | Perfil C — Em preparação D→A | Perfil D — Comercial puro |
|---|---|---|---|---|
| **US-CER-001** emitir certificado | ✅ Template RBC obrigatório + selo CGCRE + ILAC-MRA (se aderido) + cert OCSP good | ✅ Template "rastreabilidade declarada (não-acreditado)" obrigatório | ✅ Template "em preparação RBC" + flag `em_preparacao` no envelope | ✅ Documento renomeado para "**Relatório de Aferição/Verificação**" — palavra "ISO 17025" e "RBC" proibidas no PDF (hook `template-perfil-d-anti-iso`) |
| **US-CER-002** assinatura A3 (ADR-0009 emenda perfil) | ✅ OBRIGATÓRIO A3 ICP-Brasil do RT signatário + OCSP good (ADR-0046) | 🟢 RECOMENDADO (A1 aceito) | 🟢 RECOMENDADO em modo treinamento | 🟢 OPCIONAL (assinatura simples aceita) |
| **US-CER-002** carimbo TSA-ITI PAdES-LTV (ADR-0047) | ✅ OBRIGATÓRIO qualificado (25a longa duração) | ⚪ OPCIONAL (ICP-Brasil simples basta) | ⚪ OPCIONAL | ❌ DESABILITADO |
| **US-CER-003** numeração sequencial inviolável | ✅ Tipo `CERT_CALIBRACAO_RBC` separado | ✅ Tipo `CERT_CALIBRACAO` | ✅ Tipo `CERT_CALIBRACAO` (mesma sequência B) | ✅ Tipo `RELATORIO_AFERICAO` (sequência distinta) |
| **US-CER-016/017** export regulatório ANVISA + PDF/A-3 com selo CGCRE (ADR-0044 emenda) | ✅ OBRIGATÓRIO disponível (predicate `tenant_perfil_e(['A'])`) | ❌ DESABILITADO (403 + evento `Certificado.ExportRegulatorioBloqueado`) | ❌ DESABILITADO | ❌ DESABILITADO |
| **US-CER-018** recall com notificação CGCRE em ≤24h (ADR-0045 emenda) | ✅ OBRIGATÓRIO `Certificado.Recalled → NotificacaoCGCRE` síncrona | ⚪ Errata + suspensão (sem recall formal CGCRE) | ⚪ Errata + suspensão em modo treinamento (notificação CGCRE opcional) | ⚪ Errata simples (sem suspensão nem recall) |
| **US-CER-019** suspensão temporária (ADR-0045 emenda) | ✅ DISPONÍVEL | ✅ DISPONÍVEL | ✅ DISPONÍVEL | ❌ DESABILITADO |
| **US-CER-020** errata simples (ADR-0045 emenda) | ✅ DISPONÍVEL + A3 RT + comitê imparcialidade (cl. 4.1) | ✅ DISPONÍVEL | ✅ DISPONÍVEL | ✅ DISPONÍVEL |
| **Retenção PDF + WORM** (ADR-0021 + matriz-feature-perfil §retenção) | 25a B2 WORM | 25a (recomendado preparação A) | 25a | 5a (Receita) + anonimização agressiva |

**Predicate adicional perfil-aware específico do módulo:** `acao_pos_emissao_permitida_por_perfil(tenant_id, acao_enum)` — invocado por US-CER-018/019/020 ANTES de qualquer mudança de estado pós-emissão. Tentativa fora do perfil → 403 + evento `Certificado.AcaoPosEmissaoBloqueada{tenant_id, perfil, acao, motivo}`.

## 4. Escopo (o que ESTÁ neste módulo)

- Geração de certificado de calibração a partir de dados consolidados do módulo Calibração.
- Numeração sequencial por tenant, por tipo de documento, inviolável (gap = incidente auditável).
- Dados cliente + instrumento + padrões utilizados (snapshot — imutável após emissão).
- Resultado das medições + incerteza de medição.
- Declaração de conformidade (quando aplicável + regra de decisão ISO 17025 7.8.6).
- Validade do certificado (período recomendado de recalibração).
- Assinatura digital A3 do responsável técnico (cliente-side via Web PKI Lacuna — ADR-0009).
- Reemissão controlada: nova versão linkada à anterior, motivo obrigatório, ambas ficam visíveis.
- Histórico de versões com diff.
- Envio automático por e-mail ao cliente.
- Download pelo portal do cliente.
- Relatório de serviço (não-calibração — ex: assistência técnica).
- Relatório fotográfico (fotos antes/depois com timestamp + geolocalização).
- Relatório de não conformidade (NC) ligada a OS/calibração.
- Laudos técnicos (parecer técnico avulso).
- Etiquetas de identificação (PDF + impressão térmica) com QR Code linkando ao certificado.
- Modelos PDF customizáveis: cabeçalho, rodapé, logotipo, assinatura escaneada (e/ou A3), variáveis dinâmicas.

## 5. Non-goals (o que NÃO está neste módulo)

- NÃO executa a CALIBRAÇÃO em si — apenas consome dados consolidados do módulo Calibração.
- NÃO emite NF-e nem documento fiscal — isso é módulo Fiscal.
- NÃO gerencia a acreditação CGCRE da empresa — isso é módulo Licenças e Acreditações.
- NÃO substitui Word/Adobe — templates são engine própria (HTML→PDF), sem editor visual de Word.
- NÃO armazena chave privada do A3 — assinatura sempre client-side (ADR-0009).
- NÃO permite editar certificado emitido — só reemissão versionada (INV-001 + INV-034).

## 6. User Stories

### US-CER-001: Gerar certificado a partir de calibração concluída

**Como** responsável técnico, **quero** gerar certificado a partir de uma calibração revisada e aprovada, **para** entregar o resultado ao cliente conforme ISO 17025 7.8.

**Critérios de aceite:**
- **AC-CER-001-1**: GIVEN calibração com status APROVADO AND segunda conferência concluída (perfil A obrigatório; B/C opcional; D N/A — matriz §3.1) AND `Tenant.perfil_regulatorio` resolvido via ContextVar `perfil_tenant_context`, WHEN RT solicita emissão via POST `/api/v1/certificados/{calibracao_id}/emitir`, THEN sistema gera certificado com numeração sequencial próxima (tipo per perfil — §6.1.b), snapshot imutável de dados (cliente, instrumento, padrões, leituras, incerteza), `Certificado.perfil_emissor_no_momento` cravado = `Tenant.perfil_regulatorio` (ADR-0067 §3 snapshot WORM), template aplicado conforme perfil (§3.1) AND publica evento `Certificados.CertificadoReconciliado{cert_id, perfil_emissor_no_momento, reconciliacao_hash, ...}` (emissão metrológica). **Nota terminológica (T-CER-070 — fronteira NC-08):** `status='emitido'` é o estado INTERNO da emissão lógica (snapshot WORM congelado, reconciliação ponto-a-ponto concluída); a **entrega normativa cl. 7.8** (selo RBC distribuível ao cliente) e o evento `Certificados.CertificadoEmitido` só ocorrem na assinatura A3 (Wave A — `DocumentoCertificado`, ADR-0009/0047).
- **AC-CER-001-2**: GIVEN calibração não aprovada (rejeitada/pendente), WHEN tenta emitir, THEN sistema bloqueia com 422 `{erro: "CALIBRACAO_NAO_APROVADA", detalhe: "exige status APROVADO + 2ª conferência (perfil A) ou APROVADO (B/C)"}`.
- **AC-CER-001-3 (perfil-aware — ADR-0067 + ADR-0044 emenda)**: GIVEN tenant `perfil_regulatorio != 'A'` (B, C ou D), WHEN tenta emitir certificado com template RBC ou marcar `tipo_acreditacao=RBC` no payload, THEN predicate `tenant_perfil_e(['A'])` rejeita com 403 `{erro: "PERFIL_NAO_AUTORIZA_RBC", perfil_atual, tentativa: "template_rbc"}` AND publica evento `Certificado.EmissaoBloqueadaPorPerfil{tenant_id, perfil, motivo: "template_rbc_em_perfil_nao_acreditado"}` AND NENHUMA emissão (defesa anti-fraude documental — fecha FAIL L6 SAN-PERFIL-TENANT).
  - **Nota de fronteira (T-CER-080 / PROD-CER-01 — núcleo metrológico desta frente):** na emissão metrológica (sem render), o serializer **não expõe** campo `tipo_acreditacao`/`template` — a "tentativa de marcar RBC no payload" é **estruturalmente impossível** (defesa L6 invertido garantida pela ausência do campo, confirmada pelo auditor-segurança P9). O `tipo_acreditacao` é **derivado server-side** (`perfil_e_acreditado(perfil) and tem_rbc`): perfil B/C/D produz automaticamente `NAO_RBC` (sem 403, porque não há forja a rejeitar). O **403 com gating de template RBC** (escolha visual + selo) materializa-se com a **UI/render — Wave A** (GATE-CER-PDF). A camada A (hook `cert-perfil-rbc-so-A`) é defesa-em-profundidade. Logo: nesta frente o comportamento observado é `NAO_RBC` derivado (não 403), e o 403 do AC permanece válido para a frente de UI.
- **AC-CER-001-4 (perfil A + acreditação CGCRE vencida/suspensa — INV-CER-CGCRE-VIG-001; comportamento DECIDIDO no plan §4 / C-06):** GIVEN tenant `perfil=A` AND `Tenant.acreditacao_vigencia_fim < data_de_emissao` (vencida — vigência inclusiva do último dia, `>=`) **OU** acreditação suspensa na janela `[suspensa_em, suspensa_ate]` na data de emissão, WHEN tenta emitir cert, THEN o sistema **NÃO faz hard-block (não há 409)** — em vez disso **rebaixa todos os pontos a não-RBC** (`cmc_efetivo=None`), de modo que pontos que seriam RBC passam a **exigir decisão explícita do RT** (`EMITIR_NAO_RBC_NO_PONTO` com ressalva, ou `EXCLUIR`); só classifica `RBC_OK` quando perfil A está **ativo E não-suspenso E `acreditacao_vigencia_fim >= data_de_emissao`** (data de emissão, **não** `today`). `acreditacao_vigencia_fim is None` = **fail-open lazy** (GATE-CER-CGCRE-VIG-DATA-POPULAR torna efetivo em Wave A). **Fronteira documentada (NC-09):** esta regra reconcilia a versão original deste AC (que previa 409 hard-block) com a decisão do `consultor-rbc` (2026-06-01) — rebaixamento preserva a possibilidade de emitir certificado não-acreditado válido em vez de travar a operação inteira, mantendo a defesa contra "uso indevido de acreditação" (cl. 8.1.3). Base: ISO 17025 cl. 8.1.3 + NIT-DICLA-005 §7.4 + ADR-0067.
- **AC-CER-001-5 (perfil D — relatório de aferição)**: GIVEN tenant `perfil=D`, WHEN emite, THEN template aplicado é `RELATORIO_AFERICAO` (sem palavra "ISO 17025" nem "RBC" nem "calibração acreditada") AND `Certificado.tipo = RELATORIO_AFERICAO` AND retenção 5a (Receita) — `matriz-feature-perfil.md` §retenção.

**Invariantes:** `INV-032` (acreditação vigente — doc bloqueante vencido impede operação dependente), `INV-034` (numeração sequencial inviolável), `INV-001` (WORM + snapshot imutável), `INV-019` (RT habilitado quando aplicável), `INV-TENANT-001`, **`INV-CER-PERFIL-001`** (novo Onda PRE-A.3: template aplicado MATCH `Tenant.perfil_regulatorio` vigente; mismatch = bloqueio 403 + evento), **`INV-CER-SNAPSHOT-PERFIL-001`** (novo: `Certificado.perfil_emissor_no_momento` cravado no INSERT, imutável pós-emissão — defesa CGCRE retroativa cl. 8.4).

**Dependências:** Bloqueado por: US-CAL (calibração aprovada), US-LIC-003 (bloqueio CGCRE). Predicate `tenant_perfil_e` (ADR-0067 Sprint 2 SAN-PERFIL-TENANT).

---

### US-CER-002: Assinar certificado com A3 do responsável técnico

**Como** RT, **quero** assinar digitalmente o certificado gerado com meu token A3, **para** atender ISO 17025 7.8.2.1 (assinatura autorizada) e LGPD/ICP-Brasil.

**Critérios de aceite:**
- **AC-CER-002-1 (perfil A — A3 obrigatório + OCSP — ADR-0009 emenda + ADR-0046)**: GIVEN certificado em status `PENDENTE_ASSINATURA` AND `tenant_perfil_e(['A'])` AND `documento_a3_obrigatorio_por_perfil(tenant_id, "certificado_rbc") == True` AND `verificar_status_a3_via_ocsp()` retornou `good` (timeout 3s + fallback CRL 1h), WHEN RT inicia assinatura via Web PKI Lacuna, THEN sistema gera hash do PDF, envia nonce + signing-time controlado pelo servidor, recebe assinatura PKCS#7, anexa ao PDF, aplica carimbo TSA-ITI PAdES-LTV (ADR-0047 obrigatório perfil A), marca status `ASSINADO`, publica `Certificado.Assinado{cert_id, perfil_emissor_no_momento, signatario_rt_id, tsa_carimbo_id}`.
- **AC-CER-002-1b (perfil B/C/D — A3 recomendado/opcional)**: GIVEN `Tenant.perfil_regulatorio ∈ {B,C,D}` AND `documento_a3_obrigatorio_por_perfil(tenant_id, "certificado") == False`, WHEN RT assina, THEN sistema aceita A1 (perfil B/C) OU assinatura simples persistida em `Certificado.assinatura_simples` (perfil D) AND carimbo TSA-ITI opcional (B/C) ou desabilitado (D — matriz §3.1).
- **AC-CER-002-2 (replay)**: GIVEN tentativa de replay (mesmo nonce reusado em 24h), WHEN servidor verifica, THEN rejeita com 409 `{erro: "NONCE_REUSED"}` + log incidente segurança SEC-001 + publica `Seguranca.IncidenteReplayDetectado`.
- **AC-CER-002-3 (ART/RRT vencida + OCSP revoked)**: GIVEN ART/RRT do RT vencida E marcada bloqueante (módulo `licencas-acreditacoes` US-LIC-005) OR `verificar_status_a3_via_ocsp()` retornou `revoked` (ADR-0046), WHEN inicia assinatura, THEN sistema bloqueia com 409 `{erro: "RT_BLOQUEADO_PARA_ASSINAR", motivo: "ART_VENCIDA" | "A3_REVOGADO_OCSP"}` AND publica evento correspondente (`A3.RevogacaoDetectada` se OCSP) + escalação P1.
- **AC-CER-002-4 (novo Onda 7 — A1-CAL preservar cert pós-anonimização):** GIVEN cliente em Zona B do `ADR-0021` (anonimização-em-lugar com retenção regulatória), WHEN cliente é anonimizado pós-emissão do cert, THEN sistema:
  - (a) preserva o cert em status `ASSINADO`/`ENVIADO` (vigência inalterada);
  - (b) **mantém `Certificado.cliente_nome_snapshot` imutável** (campo capturado em `gerarCertificado` — fonte única para visualização auditor CGCRE em 2050);
  - (c) imprime selo no PDF "Cliente anonimizado conforme LGPD art. 18 em DD/MM/AAAA — dado preservado para fins de obrigação legal (Receita Federal 5a + ISO 17025 cl. 8.4 25a)";
  - (d) substitui `cliente_id` FK por `ReferenciaPIIAnonimizavel` (`INV-ANON-001`) — backref ao cliente vivo (ou hash quando hard-delete impossível em Zona A propagado);
  - (e) visualização pública (QR Code US-CER-009) NÃO mostra nome do cliente nem snapshot — só nº cert + status (`INV-035` mantida).

**Invariantes:** `INV-019` (RT habilitado quando aplicável), `INV-017` (A3 + carimbo ITI obrigatório em A), `INV-001` (WORM), `INV-CER-ANON-001` (snapshot cliente imutável pós-emissão), `INV-ANON-001` (FK cross-módulo via ReferenciaPIIAnonimizavel), ADR-0009, ADR-0021.

---

### US-CER-003: Numeração sequencial inviolável

**Como** auditor CGCRE, **quero** ver numeração sequencial sem gaps por tenant + tipo + ano, **para** comprovar não-emissão paralela ou supressão.

**Critérios de aceite:**
- **AC-CER-003-1**: GIVEN tenant XYZ + tipo CERT_CALIBRACAO + ano 2026, WHEN sistema emite N-ésimo certificado, THEN número = N (sem gap).
- **AC-CER-003-2**: GIVEN falha no meio da emissão (ex: erro na assinatura), WHEN sistema retoma, THEN número fica reservado pra essa tentativa; NÃO pula sequência.
- **AC-CER-003-3**: GIVEN cancelamento de certificado já numerado, WHEN admin cancela, THEN número não é reusado; certificado fica visível com status CANCELADO + motivo + auditoria.

**Invariantes:** `INV-034` (numeração sequencial inviolável).

---

### US-CER-004: Reemissão controlada com versionamento

**Como** RT, **quero** reemitir certificado quando descubro erro factual (dado do cliente errado, padrão errado), **para** corrigir mantendo histórico auditável.

**Critérios de aceite:**
- **AC-CER-004-1**: GIVEN certificado emitido, WHEN RT solicita reemissão informando motivo (>= 50 chars), THEN sistema gera versão v(N+1) linkada à v(N), marca v(N) como SUBSTITUIDA (visível, não excluída), e v(N+1) cita explicitamente "substitui versão v(N) emitida em DD/MM/AAAA".
- **AC-CER-004-2**: GIVEN versão SUBSTITUIDA, WHEN cliente baixa pelo portal, THEN sistema avisa "esta versão foi substituída por v(N+1) em DD/MM" + link.
- **AC-CER-004-3**: GIVEN tentativa de excluir certificado emitido, WHEN qualquer usuário, THEN sistema bloqueia (INV-001 — WORM).

**Invariantes:** `INV-001` (WORM — snapshot imutável; reemissão versionada), `INV-034` (numeração sequencial inviolável), ISO 17025 7.8.8.

---

### US-CER-005: Envio automático ao cliente

**Como** sistema, **quero** enviar o certificado por e-mail ao cliente ao finalizar assinatura, **para** automatizar a entrega.

**Critérios de aceite:**
- **AC-CER-005-1**: GIVEN certificado ASSINADO, WHEN status muda, THEN sistema dispara e-mail ao contato do cliente (anexo PDF + link portal) e registra evento `Certificados.Enviado`.
- **AC-CER-005-2**: GIVEN falha de envio (e-mail bounce), WHEN detectado, THEN sistema retenta 3x com backoff exponencial; após falha definitiva, notifica RT.
- **AC-CER-005-3**: GIVEN cliente sem e-mail cadastrado, WHEN sistema tenta enviar, THEN registra "envio impossível — cadastrar contato" + notifica RT.

**Invariantes:** `INV-001` (evento de envio gravado em trilha WORM).

---

### US-CER-006: Disponibilizar certificado no portal do cliente

**Como** cliente final, **quero** baixar meus certificados pelo portal, **para** ter acesso 24/7 sem precisar pedir.

**Critérios de aceite:**
- **AC-CER-006-1**: GIVEN cliente autenticado no portal, WHEN consulta seus certificados, THEN sistema lista todos por instrumento + período, marca versão atual e substituídas.
- **AC-CER-006-2**: GIVEN cliente baixa PDF, WHEN clica, THEN sistema serve com headers `Content-Disposition: attachment` e registra evento `Certificados.Baixado` pra auditoria de acesso (LGPD).

**Invariantes:** `INV-001` (WORM em downloads), `INV-013` (confidencialidade cl. 4.2 — log de visualização), `INV-TENANT-001` (cliente só vê seus).

---

### US-CER-007: Relatório fotográfico

**Como** técnico de campo, **quero** anexar fotos antes/depois do serviço com timestamp + geolocalização, **para** comprovar execução.

**Critérios de aceite (revisados em 2026-05-23 — TEMA-D.7 + TEMA-A.4 + INV-OS-GEO-001):**

- **AC-CER-007-1 (revisado):** GIVEN OS em campo, WHEN técnico anexa fotos via app, THEN sistema:
  - **(a) preserva EXIF em metadata interna assinada** (hash imutável SHA-256 + EXIF original → JSONB cifrado por tenant-key — disponível ao RT em supervisão CGCRE);
  - **(b) NO PDF entregue ao cliente / no portal público, EXIF é removido + watermark imprime "data/hora/local resumido"** (município/bairro — INV-OS-GEO-001) — não vaza endereço residencial completo;
  - **(c) gera hash SHA-256 de cada foto + grava em audit**;
  - **(d) detecta rosto identificável** (vision API ou hash perceptual) e força blur ou eliminação se aplicável.
- **AC-CER-007-2 (revisado):** GIVEN relatório fotográfico gerado, WHEN cliente baixa via portal, THEN cada foto tem rodapé "data/hora/local **resumido**" (município/bairro) + nº cert + watermark anti-cópia.
- **AC-CER-007-3 (revisado Onda 7D — NOVO-ALTO-1 produto R2):** GIVEN cliente solicita dispensa de foto (privacidade industrial — direito CC art. 195 LPI + LGPD art. 7º), WHEN atendente cadastra OS, THEN sistema:
  - (a) marca `ChecklistDaAtividade.dispensa_foto: true` no checklist;
  - (b) persiste `motivo_dispensa_hash` (HMAC tenant — INV-OS-TXT-001 sobre texto pré-hash com mín 30 chars anti-PII);
  - (c) cria `AceiteAtividade` específico referenciando texto canônico `docs/conformidade/comum/termos/aceite-atividade-dispensa-foto-v1.0.md` (variante a criar Wave A — GATE-LGPD-DISP-FOTO);
  - (d) bloqueia campo `foto_obrigatoria` no checklist;
  - (e) publica evento `DispensaFotoRegistrada(tenant_id, atividade_id, motivo_hash, aceite_atividade_id, correlation_id)`.

**Invariantes:** `INV-001` (WORM), `INV-OS-GEO-001` (precisão limitada em payload publicado), `INV-EQP-ANOM-001` (anti-PII em texto livre da foto), `INV-CAL-FOTO-001` (EXIF strip + geo limit + detecção de rosto).

---

### US-CER-008: Relatório de não conformidade

**Como** RT, **quero** registrar NC de calibração ou serviço, **para** documentar conforme ISO 17025 7.10 e iniciar ação corretiva.

**Critérios de aceite:**
- **AC-CER-008-1**: GIVEN calibração com resultado fora dos limites OU serviço com defeito identificado, WHEN RT abre NC, THEN sistema cria documento NC numerado, descrição, evidências (fotos/leituras), ação imediata, ação corretiva planejada.
- **AC-CER-008-2**: GIVEN NC aberta, WHEN não fechada em 30 dias, THEN sistema alerta RT + gestor qualidade.

**Invariantes:** `INV-012` (NC abre bloqueio de emissão até resolução documentada), `INV-001` (WORM em NC), ISO 17025 8.7.

---

### US-CER-009: Etiqueta de identificação com QR Code

**Como** RT, **quero** imprimir etiqueta adesiva do certificado com QR Code, **para** colar no instrumento e permitir verificação rápida.

**Critérios de aceite (revisados em 2026-05-23 — TEMA-C.6 + TEMA-C.9 + TEMA-M.4 LGPD):**

- **AC-CER-009-1 (revisado):** GIVEN certificado ASSINADO, WHEN RT solicita etiqueta, THEN sistema gera PDF/PNG no tamanho configurado (padrões: 50x30mm, 80x40mm) com nº cert, validade, QR Code **gerado pelo helper único `gerar_qr_hash_versionado()` com chave dedicada `QR_CERT_HMAC_KEY_REGISTRO`** (SEC-QR-001 pattern Marco 2 — distinta de `QR_HMAC_KEY` equipamentos e `PII_HASH_KEY`) apontando pra URL pública (token opaco HMAC-SHA256 com `tenant_id` no hash, ≥22 chars).
- **AC-CER-009-2 (revisado):** GIVEN QR Code escaneado, WHEN navegador abre URL pública (sem login), THEN exibe página pública verificadora **com rate-limit 60 req/min por IP + lockout após 100 4xx em 1h** (pattern SEC-QR-001 — TEMA-C.9) + **allowlist anti-PII** conforme `docs/conformidade/calibracao/qr-publico-allowlist.md` (a criar Wave A — TEMA-C.6): nº cert, validade, fabricante+modelo do instrumento (sem NS completo), status (vigente/expirado/cancelado/substituído). **Não** mostra nome do cliente, localização, RT signatário em texto. Re-emissão revoga QR anterior automaticamente.
- **AC-CER-009-3 (novo — TEMA-C.9):** GIVEN tentativa de scan de hash inexistente OU de outro tenant, WHEN página resolve, THEN retorna 404 body idêntico ao 404 de hash inválido (P-EQP-S2 anti-oracle cross-tenant Marco 2).

**Invariantes:** `INV-001` (WORM), `INV-035` (página pública verificadora sem PII além do mínimo), `INV-051` (QR Code token opaco HMAC + rate-limit + allowlist), `SEC-QR-001` (helper único + chave dedicada).

---

### US-CER-010: Templates PDF customizáveis

**Como** admin tenant, **quero** customizar cabeçalho, rodapé, logo, cores e assinatura escaneada do template de certificado, **para** entregar com identidade visual da empresa.

**Critérios de aceite:**
- **AC-CER-010-1**: GIVEN admin no editor de template, WHEN faz upload de logo + define cabeçalho/rodapé + cor primária, THEN sistema valida (logo ≤ 1MB, formatos PNG/SVG/JPG) e gera pré-visualização antes de salvar.
- **AC-CER-010-2**: GIVEN template aprovado, WHEN novas emissões acontecem, THEN aplicam template atual; certificados já emitidos preservam template usado na época (snapshot).
- **AC-CER-010-3**: GIVEN template muda, WHEN versionado, THEN sistema mantém histórico v1/v2/v3 + qual cert usou qual.

**Invariantes:** `INV-001` (snapshot imutável WORM — template usado na emissão preservado por certificado).

---

### US-CER-013: Consulta histórica de cert com equipamento baixado (novo Onda 7 — M1-CAL)

**Como** auditor CGCRE ou cliente, **quero** consultar cert emitido para equipamento que posteriormente foi **baixado** (`Equipamento.status=BAIXADO`), **para** atender ISO 17025 cl. 8.4 (retenção de registros independe da disponibilidade do bem).

**Critérios de aceite:**
- **AC-CER-013-1**: GIVEN cert emitido para equipamento EQP-X, WHEN equipamento posteriormente vira `BAIXADO`, THEN cert continua consultável no portal cliente + auditor + QR público, com selo "este certificado se refere a equipamento baixado em DD/MM/AAAA" (snapshot do equipamento no momento da emissão é mostrado).
- **AC-CER-013-2**: GIVEN equipamento baixado, WHEN consulta histórica, THEN sistema usa `Certificado.snapshot_equipamento_json` (imutável — capturado na emissão, paridade `Calibracao.snapshot_equipamento_json` TEMA-E.4); não consulta `Equipamento` mutável atual.
- **AC-CER-013-3**: GIVEN equipamento baixado é candidato a hard-delete (ADR-0021 Zona C), WHEN admin tenta deletar, THEN sistema bloqueia citando "equipamento referenciado em cert emitido — use anonimização-em-lugar (Zona B)".

**Invariantes:** `INV-001` (WORM cert preserva snapshot), `INV-CER-ANON-001`, `INV-CAL-WORM-001`.

---

### US-CER-016: Exportação regulatória ANVISA (novo Onda 7 — C2-CAL / ADR-0044)

**Como** RT de tenant farma/hospital, **quero** marcar cert como destino regulatório (ANVISA/SAÚDE/INMETRO), **para** que sistema gere PDF/A-3 com XML estruturado anexo + carimbo TSA-ITI atendendo RDC 658/2022 + Portaria INMETRO 157/2022.

**Critérios de aceite:**
- **AC-CER-016-1 (perfil A obrigatório — ADR-0044 emenda)**: GIVEN cert em status `ASSINADO` AND `tenant_perfil_e(['A'])` AND `Tenant.acreditacao_vigencia_fim > today` AND tenant declara setor (farma/hospital/inmetro) em onboarding, WHEN RT marca "destino regulatório" via POST `/api/v1/certificados/{id}/export-regulatorio`, THEN sistema gera PDF/A-3 com XML embedded validado contra XSD setorial (`anvisa-ext-v1.xsd`/`inmetro-ext-v1.xsd`/`saude-ext-v1.xsd`) AND aplica selo CGCRE+ILAC-MRA no PDF/A-3.
- **AC-CER-016-1b (perfil != A — bloqueio defesa)**: GIVEN `Tenant.perfil_regulatorio ∈ {B,C,D}`, WHEN tenta marcar destino regulatório, THEN predicate `tenant_perfil_e(['A'])` rejeita com 403 `{erro: "EXPORT_REGULATORIO_EXIGE_PERFIL_A", perfil_atual}` AND publica `Certificado.ExportRegulatorioBloqueado{tenant_id, perfil, cert_id}` (defesa probatória anti-fraude — ADR-0044 emenda §15).
- **AC-CER-016-2**: GIVEN PDF/A-3 gerado, WHEN sistema processa, THEN aplica carimbo TSA-ITI **qualificado** PAdES-LTV (ADR-0047 — latência aceita 1-3s assíncrona) + hash SHA-256 do XML embedded salvo em `Certificado.xml_embedded_hash` (probatório).
- **AC-CER-016-3**: GIVEN cert regulatório sem TSA-ITI carimbado, WHEN tenant tenta marcar como "entregue ao auditor", THEN sistema bloqueia com 412 `{erro: "CertRegulatorioSemTSA"}`.

**Invariantes:** `INV-CER-EXP-001`, `INV-001` (WORM), ADR-0044.

---

### US-CER-017: PDF/A-3 longa duração 25a (novo Onda 7 — C2-CAL / ADR-0044)

**Como** tenant + auditor CGCRE em 2051, **quero** que TODO cert (regulatório ou não) seja PDF/A-3 ISO 19005-3:2012, **para** garantir abertura/legibilidade ao longo de 25 anos de retenção (`INV-010`).

**Critérios de aceite:**
- **AC-CER-017-1**: GIVEN cert gerado em qualquer fluxo (US-CER-001, US-CER-004 reemissão), WHEN sistema produz PDF, THEN formato é PDF/A-3 (não PDF "padrão"). Validação via verificador PDF/A no smoke test do `validar_m4_calibracao` drill.
- **AC-CER-017-2**: GIVEN cert PDF/A-3 + assinatura A3, WHEN persistido, THEN é gravado em B2 bucket WORM `certificados-wormA/<tenant>/<ano>/<cert_id>.pdf` (anti-mutação física); crypto-shredding NÃO aplica (Zona A de ADR-0021).

**Invariantes:** `INV-CER-EXP-001`, `INV-010` (retenção 25a), `INV-001` (B2 WORM).

---

### US-CER-018: Recall de cert por bug do motor de cálculo (novo Onda 7 — C3-CAL / ADR-0045)

**Como** RT/gestor qualidade, **quero** disparar Recall em batch de cert que usaram versão buggy do motor de cálculo, **para** atender ISO 17025 cl. 7.10 + 7.11 + LGPD art. 48.

**Critérios de aceite:**
- **AC-CER-018-1 (perfil A — recall completo — ADR-0045 emenda)**: GIVEN `tenant_perfil_e(['A'])` AND bug confirmado em `versao_motor_calculo=X.Y.Z` via replay determinístico (ADR-0025), WHEN gestor dispara Recall via POST `/api/v1/certificados/recall` + A3 do RT + comitê interno de imparcialidade (cl. 4.1), THEN predicate `acao_pos_emissao_permitida_por_perfil(tenant_id, 'RECALL') == True` AND sistema identifica TODOS os cert com aquela versão + cria evento `Certificado.Recalled{certificado_id, motivo_bug, replay_validacao_id, correlation_id, perfil_no_evento}` por cert.
- **AC-CER-018-1b (perfil B/C/D — recall bloqueado)**: GIVEN `Tenant.perfil_regulatorio ∈ {B,C,D}`, WHEN tenta disparar recall, THEN predicate `acao_pos_emissao_permitida_por_perfil(tenant_id, 'RECALL') == False` AND retorna 403 `{erro: "RECALL_EXIGE_PERFIL_A", alternativa: "use_errata_us_cer_020 OR suspensao_us_cer_019"}` AND publica `Certificado.AcaoPosEmissaoBloqueada`.
- **AC-CER-018-2 (notificação cliente — todos os perfis com recall ativo)**: GIVEN evento `Certificado.Recalled` publicado, WHEN consumer `notificar-cliente-recall` recebe, THEN envia notificação ao cliente em ≤24h (canal preferencial + e-mail — ADR-0060 `EmailTemplateProvider`) + audit no `EventoDeCertificado`.
- **AC-CER-018-3 (notificação CGCRE — perfil A apenas, síncrona ≤24h)**: GIVEN evento `Certificado.Recalled` AND `tenant_perfil_e(['A'])`, WHEN consumer `notificar-cgcre-recall` recebe, THEN dispara `NotificacaoCGCRE` síncrona em ≤24h via canal regulatório + audit imutável (ADR-0045 emenda).
- **AC-CER-018-4 (notificação ANPD)**: GIVEN bug afetou decisão sobre titular (cert farma usado pra liberar lote — `impacto_titular=true`), WHEN consumer `notificar-anpd-recall` recebe, THEN notifica ANPD em ≤24h via canal LGPD `docs/conformidade/comum/incidente-anpd-modelo.md`.
- **AC-CER-018-5 (QR público)**: GIVEN Recall ativo, WHEN página pública (US-CER-009) resolve QR Code, THEN exibe "este cert foi objeto de Recall em DD/MM/AAAA — contate o laboratório emissor" + nº cert + status `RECALL_ATIVO`.
- **AC-CER-018-6 (dossiê CGCRE perfil A em ≤30d)**: GIVEN `tenant_perfil_e(['A'])` AND notificação CGCRE precisa ser formal em ≤30d, WHEN gestor qualidade dispara via UI, THEN gera dossiê via `consultor-rbc-iso17025` template + audit imutável.

**Invariantes:** `INV-CER-RECALL-001`, `INV-CAL-WORM-001`, `INV-005` (incidente ANPD em ≤3d quando aplicável), ADR-0045.

---

### US-CER-019: Suspensão temporária de cert (novo Onda 7 — C3-CAL / ADR-0045)

**Como** RT/gestor qualidade, **quero** suspender cert temporariamente quando padrão usado é descoberto descalibrado retroativo, **para** investigar sem cancelar definitivamente.

**Critérios de aceite:**
- **AC-CER-019-1**: GIVEN cert ASSINADO + padrão usado descoberto descalibrado, WHEN RT dispara `suspenderCertificado(cert_id, suspenso_ate, motivo_padrao_descalibrado)`, THEN status vira `SUSPENSO` + vigência paralisa (relógio para; `dias_suspensao_acumulada` zera-se 0 e contabiliza dias).
- **AC-CER-019-2**: GIVEN cert SUSPENSO, WHEN investigação fecha sem Recall, THEN RT dispara `levantarSuspensaoCertificado(cert_id, justificativa ≥50 chars)` + vigência retoma do ponto onde parou (não é prorrogação, é "tempo morto" descontado).
- **AC-CER-019-3**: GIVEN cert SUSPENSO, WHEN cliente acessa portal, THEN sistema mostra "este cert está em verificação pelo lab — vigência paralisada" + nº cert.

**Invariantes:** `INV-CER-SUSP-001`, `INV-CAL-WORM-001`, ADR-0045.

---

### US-CER-020: Errata simples de cert (novo Onda 7 — C3-CAL / ADR-0045)

**Como** RT, **quero** emitir errata em campo descritivo do cert (typo no nome cliente, endereço errado) sem reemitir o cert inteiro, **para** corrigir display sem inflar numeração.

**Critérios de aceite:**
- **AC-CER-020-1**: GIVEN cert ASSINADO + typo em campo descritivo da allowlist (`cliente_endereco`, `instrumento_serie_str`, `data_recebimento_label`, `observacoes_gerais` — definido em `errata-campos-permitidos.md` Wave A), WHEN RT dispara `emitirErrataCertificado(cert_id, campo, valor_novo, justificativa ≥30 chars anti-PII)`, THEN sistema cria "apêndice PDF" anexo ao cert original + incrementa `errata_seq` + assinatura A3 do RT autor.
- **AC-CER-020-2**: GIVEN tentativa de errata em campo **técnico** (`valor_lido`, `U_expandida`, `decisao`, `padroes_usados`, `regra_decisao`), WHEN RT submete, THEN sistema bloqueia com 422 `ErrataProibidaEmCampoTecnico` citando que mudança técnica exige reemissão (US-CER-004).
- **AC-CER-020-3**: GIVEN cert com erratas aplicadas, WHEN cliente baixa portal ou auditor consulta, THEN sistema entrega cert original + lista cronológica de erratas (`errata_seq`, campo, valor anterior, novo, RT autor, justificativa).

**Invariantes:** `INV-CER-ERRATA-001`, `INV-001` (cert original imutável), `INV-CAL-TXT-001` (anti-PII na justificativa), ADR-0045.

---

## 6.1 Campos do certificado — por perfil regulatório do tenant (corrigido Onda PRE-A.3 — fecha FAIL L6 SAN-PERFIL-TENANT)

> **Mudança crítica 2026-05-27:** este documento **NÃO LÊ MAIS `cert.tipo_acreditacao` do payload da request** (era vetor de fraude documental — qualquer call-site podia mentir). A condicional do template lê o **perfil regulatório do tenant persistido no banco** (`Tenant.perfil_regulatorio`) via predicate canônico `tenant_perfil_e(['A'])` consumido pelo helper de template.
>
> Tabela canônica de quais campos aparecem no PDF, condicional ao `Tenant.perfil_regulatorio` vigente. Templates US-CER-010 usam esta tabela como contrato e validam que `template.perfil_alvo == tenant.perfil_regulatorio` ANTES de renderizar.

| Campo | Perfil A (RBC) | Perfil B (rastreável) | Perfil C (em preparação) | Perfil D (comercial puro) | Observação |
|---|---|---|---|---|---|
| Selo CGCRE com nº acreditação | ✅ Obrigatório | ❌ Proibido | ❌ Proibido | ❌ Proibido | A sem selo = NC supervisão; B/C/D com selo = fraude documental (bloqueio 403) |
| Declaração ILAC-MRA | ✅ Obrigatório se `tenant.ilac_mra_aderido=TRUE` | ❌ Proibido | ❌ Proibido | ❌ Proibido | Matriz §3.1 |
| Bloco "Certificado com rastreabilidade declarada (não-acreditado)" | ❌ Proibido | ✅ Obrigatório | ✅ Obrigatório | ❌ Proibido (renomeação para "Relatório de Aferição") | Diferenciação visual obrigatória |
| Selo "EM PREPARAÇÃO RBC" | ❌ Proibido | ❌ Proibido | ✅ Obrigatório | ❌ Proibido | Flag `em_preparacao` |
| Documento renomeado para "Relatório de Aferição/Verificação" + palavra "ISO 17025" proibida + "RBC" proibida | ❌ | ❌ | ❌ | ✅ Obrigatório (hook `template-perfil-d-anti-iso`) | Perfil D |
| Número da acreditação CGCRE | ✅ Obrigatório (`Tenant.acreditacao_cgcre_numero`) | ❌ N/A | ❌ N/A | ❌ N/A | NULL em B/C/D |
| Escopo CGCRE da grandeza | ✅ Obrigatório | — | — | — | Cita ID e versão do escopo aprovado |
| Declaração de rastreabilidade ao SI | ✅ Obrigatório | ✅ Recomendado | ✅ Recomendado | ⚪ Opcional | Cadeia INMETRO → padrão usado |
| Resultado de medição | ✅ | ✅ | ✅ | ✅ | Núcleo técnico |
| Incerteza de medição (U, k, nível confiança) | ✅ | ✅ | ✅ | ⚪ Opcional | NIT-DICLA-030 rev. 15 item 8.2.6 |
| Regra de decisão (ADR-0024) | ✅ Obrigatório quando declarada | ⚪ Opcional quando declarada | ⚪ Opcional | ❌ Desabilitado | Matriz §3.1 |
| Condições ambientais | ✅ Obrigatório | ✅ Recomendado | ✅ Recomendado | ⚪ Opcional | cl. 7.5 |
| Padrões utilizados (cadeia + cert externo) | ✅ Obrigatório | ✅ Recomendado | ✅ Recomendado | ⚪ Opcional | cl. 6.5 |
| Validade da recalibração (sugestão) | ⚪ Opcional (cliente decide) | ⚪ Opcional | ⚪ Opcional | ⚪ Opcional | Não é obrigatória cl. 7.8 |
| Assinatura A3 ICP-Brasil | ✅ Obrigatório RT signatário + OCSP good | 🟢 Recomendado | 🟢 Recomendado treinamento | 🟢 Opcional | INV-017 + ADR-0009 emenda perfil |
| Carimbo TSA-ITI PAdES-LTV qualificado | ✅ Obrigatório (25a longa duração) | ⚪ Opcional | ⚪ Opcional | ❌ Desabilitado | ADR-0047 |

### Regra do template (US-CER-010) — versão pós-correção L6

- Template Jinja2 tem fields condicionais **`{% if tenant_perfil_e(['A']) %}`** (helper canônico injetado pelo motor de template) — controla blocos selo+declaração RBC. **Não usa `cert.tipo_acreditacao` nunca.**
- **Pre-flight check em `emitir_certificado`** (ADR-0067 §8): valida que `template.perfil_alvo == tenant.perfil_regulatorio_vigente` ANTES de renderizar; mismatch → 403 `{erro: "TEMPLATE_PERFIL_MISMATCH"}` + evento `Certificado.EmissaoBloqueadaPorPerfil`.
- Tentativa de gerar cert com template RBC em tenant `perfil != A` bloqueia com 403 (predicate `tenant_perfil_e(['A'])` rejeita — `INV-CER-PERFIL-001`).
- Tentativa de gerar cert perfil A sem `Tenant.acreditacao_cgcre_numero` NOT NULL OU `Tenant.acreditacao_vigencia_fim > today` bloqueia com 412 (`INV-032`).
- Tentativa de inserir selo RBC em template não-A bloqueia em validação de template (US-CER-010 AC-3) — defesa em profundidade.
- **Hook `payload-tipo-acreditacao-obsoleto-check`** (Sprint 2 SAN-PERFIL-TENANT) bloqueia commit que reintroduza `tipo_acreditacao` lido do payload.

---

## 6.2 Política de numeração (novo Onda 7 — A4-CAL)

> Detalha `INV-CER-NUM-001` + `INV-034`. Aplica VO `NumeroCertificado` da `src/domain/metrologia/value_objects.py`.

### Regras

1. **Formato:** `<TENANT_SLUG>-<YYYY>-<NNNNNN>` (zero-padded 6 dígitos).
2. **Virada anual:** em **1º jan 00:00 BRT** do ano novo, `NNNNNN` reseta para `000001`. Job `job_certificado_virada_anual` (00:01 BRT) materializa o reset por tenant; trigger PG `BEFORE INSERT` valida que `YYYY` confere com `extract(year from emitido_em)`.
3. **Sequência:** absoluta por **tenant + tipo + ano**. Tipos não dividem sequência (CERT_CALIBRACAO, CERT_CALIBRACAO_RBC, RELATORIO_SERVICO, NC, LAUDO_TECNICO têm contadores separados).
4. **Gap-detection:** job noturno `job_certificado_gap_detection` (03:00 BRT) varre `MAX(seq) - COUNT(*)` por tenant/tipo/ano; gap dispara alerta P1 + cria `IncidenteCertNumero` para investigação manual (auditor CGCRE pode pedir explicação).
5. **Cancelamento preserva número:** cert `CANCELADO` mantém o número; auditor vê `CANCELADO` na lista + motivo + audit. Número NÃO é reusado (`INV-034`).
6. **Reserva com TTL:** transação que aborta no meio (ex: falha na assinatura A3) reserva o número via entidade `NumeroReservado`:
   - **Atributos:** `numero` (PK composta com tenant+tipo+ano), `certificado_id` (FK, NULL enquanto reservado), `reservado_em` (timestamp UTC), `ttl_segundos` (default 300).
   - **Ciclo:** INSERT com `certificado_id NULL` reserva; UPDATE com `certificado_id` finaliza emissão; após `reservado_em + ttl_segundos`, job `job_certificado_liberar_reservas` (a cada 60s) libera o número de volta ao pool E publica audit (auditor CGCRE vê tentativa abortada).
   - **Rationale:** evita "buraco visível" em cert; toleramos buraco invisível ≤5min com audit cobrindo.

### Invariante

- **INV-CER-NUM-002 (novo Onda 7 — A4-CAL):** numeração de cert respeita virada anual + tenant/tipo separados + reserva TTL 5min + gap-detection diário. Tentativa de reuso de número via INSERT (após cancelamento ou expiração de reserva) bloqueia com erro PG.

---

## 7. Métricas de sucesso (inline + detalhe em `metricas.md`)

- **Zero gaps de numeração** (target: 100%) — `INV-034` + `INV-CER-NUM-002`.
- **Tempo médio emissão → assinatura ≤ 5 min** (mediana); p95 ≤ 15 min.
- **Taxa de entrega de e-mail ≥ 98%** (US-CER-005 — ADR-0060).
- **Tempo médio QR público p95 < 800ms** (US-CER-009 + SEC-QR-001).
- **% certificados perfil A com TSA-ITI ≥ 99,9%** (ADR-0047 cl. 8.4 longa duração).
- **% recall notificado a cliente em ≤24h = 100%** (perfil A — ADR-0045 emenda).
- **Drift de perfil (tentativa de emissão `template_rbc` em tenant não-A) = 0/mês** (defesa L6 SAN-PERFIL-TENANT).

## 8. NFR

- **Performance:** geração PDF < 3s p95; assinatura A3 (round-trip) < 10s p95; OCSP verify < 3s + fallback CRL 1h (ADR-0046).
- **Disponibilidade:** 99.9% (certificado pendente é dinheiro parado).
- **Segurança:** SEC-001, SEC-002; A3 cliente-side (ADR-0009); URL pública verificadora não expõe PII além do mínimo (allowlist `docs/conformidade/calibracao/qr-publico-allowlist.md` Wave A).
- **Acessibilidade:** WCAG AA (ADR-0057); certificado PDF tagueado (PDF/UA).
- **Retenção (matriz-feature-perfil §retenção):** perfil A/B/C 25a B2 WORM; perfil D 5a (Receita) + anonimização agressiva.

## 8.1 Não-objetivos (Wave A — explícitos)

- NÃO executa a CALIBRAÇÃO em si — apenas consome dados consolidados do módulo `metrologia/calibracao`.
- NÃO emite NF-e nem documento fiscal — isso é módulo `financeiro/fiscal` (consumer downstream).
- NÃO gerencia a acreditação CGCRE da empresa — isso é módulo `metrologia/licencas-acreditacoes`.
- NÃO substitui Word/Adobe — templates são engine própria (Jinja2 → HTML → PDF), sem editor visual de Word.
- NÃO armazena chave privada do A3 — assinatura sempre client-side (ADR-0009).
- NÃO permite editar certificado emitido — só reemissão versionada (`INV-001` + `INV-034`) ou errata em campo descritivo allowlist (US-CER-020).
- NÃO emite cert RBC em tenant não-A — bloqueio defesa em profundidade (`INV-CER-PERFIL-001`).
- **Editor visual WYSIWYG de template** — Wave B (V2).
- **OCR de PDF externo pra extrair leitura** — Wave B.
- **Assinatura por múltiplos signatários simultâneos no mesmo cert** — Wave B (V2 — multi-sig).
- **Reabertura de certificado emitido para edição** — proibido permanentemente (`INV-001` WORM).

## 9. Dependências (ADRs + módulos)

**Módulos consumidos:**

- `metrologia/calibracao` — fornece `Calibracao.aprovada()` + dados de medição (US-CER-001).
- `metrologia/licencas-acreditacoes` — fornece `Tenant.acreditacao_cgcre_*` + ART/RRT do RT (US-CER-001/002).
- `seguranca/certificados-digitais` (ADR-0048) — porta `verificar_status` OCSP/CRL (ADR-0046).
- `infrastructure/tenant` — fornece `Tenant.perfil_regulatorio` via ContextVar (ADR-0067).
- `metrologia/responsabilidade-tecnica` (ADR-0022) — competência RT por grandeza.

**Módulos consumers downstream:**

> **Nota de evento (T-CER-070 / NC-08):** os consumers fiscais abaixo consomem o evento **normativo** `Certificados.CertificadoEmitido` (cl. 7.8 — disparado na **assinatura A3, Wave A**), não o `Certificados.CertificadoReconciliado` da emissão metrológica desta frente. Faturar antes do certificado assinado seria NC; por isso a integração fiscal é **Wave A** e escuta o evento normativo.

- `financeiro/fiscal` (**Wave A**) — consome o evento normativo `Certificados.CertificadoEmitido` (cl. 7.8, assinatura A3) → gera NFS-e (INV-FIS-CR-001).
- `financeiro/contas-receber` (**Wave A**) — consome o evento normativo `Certificados.CertificadoEmitido` (cl. 7.8, assinatura A3) → cria título (ADR-0043 emenda perfil — grace D+45/20/30/7).
- `notificacoes/cliente` — consumer US-CER-005 + US-CER-018 (ADR-0060 `EmailTemplateProvider`).

**ADRs aceitas Onda 2/PRE-A.2:**

- **ADR-0009** — A3 cliente-side via Web PKI Lacuna (emenda 2026-05-27 perfil A obrigatório).
- **ADR-0021** — anonimização vs retenção (3 zonas — preserva `cliente_nome_snapshot` imutável pós-emissão).
- **ADR-0022** — RT do tenant + competência por grandeza.
- **ADR-0024** — regra de decisão ISO 17025 cl. 7.8.6 (3 modos).
- **ADR-0025 v2** — validação software ISO 17025 cl. 7.11 (URS/IQ/OQ/PQ + replay determinístico). Wave A planeja URS/IQ/OQ/PQ específicos do módulo certificados — incluir testes de regressão de template + replay de geração de PDF.
- **ADR-0029** — canonicalização texto probatório (UTF-8 NFC + LF + sem BOM).
- **ADR-0044** — exportação regulatória ANVISA/SAÚDE/INMETRO (emenda 2026-05-27 perfil A único — `tenant_perfil_e(['A'])` no export).
- **ADR-0045** — recall + suspensão + errata (emenda 2026-05-27 perfil-aware — predicate `acao_pos_emissao_permitida_por_perfil`).
- **ADR-0046** — OCSP/CRL revogação online (timeout 3s + fallback CRL 1h).
- **ADR-0047** — TSA-ITI PAdES-LTV qualificado 25a (perfil A obrigatório).
- **ADR-0048** — cadastro segregado A3 (e-CNPJ + e-CPF RT + demais).
- **ADR-0054** — `OutboundWebhookProvider` HMAC para integrações.
- **ADR-0057** — Acessibilidade WCAG 2.1 AA.
- **ADR-0060** — `EmailTemplateProvider` (US-CER-005 + US-CER-018).
- **ADR-0061** — canal do titular + DPO (US-CER-018 notificação ANPD).
- **ADR-0067** — perfil regulatório do tenant entidade temporal (canônico — fonte L6 fix).

## 10. Glossário

Ver `glossario.md` do módulo + `docs/comum/glossario.md`. Termos canônicos adicionados nesta sanação:

- **Perfil regulatório do tenant:** atributo `Tenant.perfil_regulatorio` enum `{A_ACREDITADO_RBC, B_RASTREAVEL, C_EM_PREPARACAO, D_COMERCIAL_PURO}` — fonte ÚNICA consultada por templates e predicates do módulo (ADR-0067).
- **Predicate `tenant_perfil_e(perfis_aceitos)`:** função canônica `src/infrastructure/authz/predicates.py` que lê `Tenant.perfil_regulatorio` via ContextVar `perfil_tenant_context`. Fail-closed timeout 50ms.
- **Predicate `acao_pos_emissao_permitida_por_perfil(tenant_id, acao_enum)`:** função decisora de US-CER-018/019/020 — recall/suspensão/errata por perfil (ADR-0045 emenda).
- **Predicate `documento_a3_obrigatorio_por_perfil(tenant_id, tipo_doc)`:** função decisora de US-CER-002 (assinatura A3 — ADR-0009 emenda).
- **ContextVar `perfil_tenant_context`:** variável Python isolada por request — populada por middleware Sprint 2 SAN-PERFIL-TENANT.
- **`Certificado.perfil_emissor_no_momento`:** coluna `CHAR(1) NOT NULL` cravada no INSERT — snapshot WORM imutável pós-emissão (ADR-0067 §3 + `INV-CER-SNAPSHOT-PERFIL-001`).
- **`Tenant.acreditacao_cgcre_numero` / `acreditacao_vigencia_inicio/fim`:** campos preenchidos apenas em perfil A (ADR-0067 §1).
- **Relatório de Aferição/Verificação:** documento renomeado para perfil D — palavra "ISO 17025" e "RBC" PROIBIDAS (hook `template-perfil-d-anti-iso`).
- **TSA-ITI qualificado:** carimbo de tempo emitido por Autoridade de Carimbo de Tempo do ITI — obrigatório perfil A para longa duração 25a (ADR-0047).
- **OCSP `good` / `revoked` / `unknown`:** estados de verificação online de certificado digital (ADR-0046).
- **Errata vs Reemissão:** errata = correção de campo descritivo (allowlist) sem reemitir (US-CER-020); reemissão = nova versão completa (US-CER-004).

## 11. Como este PRD evolui

- US nova → próximo `US-CER-NNN`.
- US deprecada → `@deprecated` + ADR.
- Mudança no template default → ADR + janela.
- Mudança em campo da §6.1 (perfil × campo) → emenda ADR-0067 + atualização `matriz-feature-perfil.md` + hook `feature-perfil-matriz-validator` valida.
