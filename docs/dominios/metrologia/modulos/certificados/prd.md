---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/controle-certificado-emitido.md
  - docs/dominios/metrologia/modulos/calibracao/garantia-validade-7.7.md
  - docs/dominios/metrologia/modulos/licencas-acreditacoes/prd.md
  - docs/dominios/metrologia/modulos/procedimentos/prd.md
  - docs/adr/0021-anonimizacao-vs-retencao-regulatoria.md
  - docs/adr/0043-calibracao-faturamento-bloqueio-inadimplencia.md
  - docs/adr/0044-exportacao-regulatoria-anvisa-saude.md
  - docs/adr/0045-certificado-recall-suspensao-errata.md
---

# PRD — Módulo Certificados, Relatórios e Documentos Técnicos

> Módulo dedicado à geração, emissão controlada, distribuição e versionamento de certificados de calibração, relatórios técnicos e documentos derivados. Separado do módulo Calibração porque a emissão tem ciclo de vida e governança próprios (ISO 17025 7.8).

---

## 1. O que este módulo é

Plataforma única de emissão e gestão de documentos técnicos: certificados de calibração com numeração sequencial inviolável, relatórios de serviço, relatórios fotográficos, relatórios de não conformidade, laudos técnicos e etiquetas de identificação. Suporta templates customizáveis (cabeçalho, rodapé, logo, assinatura), assinatura digital A3 do responsável técnico, reemissão controlada com versionamento, envio automático ao cliente e disponibilização no portal.

## 2. Por que este módulo existe (problema a resolver)

Certificado é o produto-final entregue ao cliente — vale dinheiro, vale auditoria, vale CGCRE. Emissão errada (numeração quebrada, dados trocados entre certificados, PDF reemitido sem versionamento) gera não-conformidade na auditoria CGCRE e pode resultar em perda da acreditação. Hoje (mystery shopping Calibre.Software) o concorrente trata isso como afterthought; nosso diferencial é tratar como ciclo de vida primeiro-cidadão.

## 3. Personas

Ver `personas.md` deste módulo + `../../personas.md` + `docs/comum/personas.md`.

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
- **AC-CER-001-1**: GIVEN calibração com status APROVADO e segunda conferência concluída, WHEN RT solicita emissão, THEN sistema gera certificado com numeração sequencial próxima, snapshot de dados (cliente, instrumento, padrões, leituras, incerteza), template aplicado.
- **AC-CER-001-2**: GIVEN calibração não aprovada (rejeitada/pendente), WHEN tenta emitir, THEN sistema bloqueia com mensagem "calibração precisa estar aprovada + 2ª conferência".
- **AC-CER-001-3**: GIVEN acreditação CGCRE vencida e marcada bloqueante (módulo Licenças), WHEN tenta emitir certificado RBC, THEN sistema bloqueia citando documento bloqueante.

**Invariantes:** `INV-032` (acreditação vigente — doc bloqueante vencido impede emissão), `INV-034` (numeração sequencial inviolável), `INV-001` (WORM + snapshot imutável), `INV-019` (RT habilitado quando aplicável), `INV-TENANT-001`.

**Dependências:** Bloqueado por: US-CAL (calibração aprovada), US-LIC-003 (bloqueio CGCRE).

---

### US-CER-002: Assinar certificado com A3 do responsável técnico

**Como** RT, **quero** assinar digitalmente o certificado gerado com meu token A3, **para** atender ISO 17025 7.8.2.1 (assinatura autorizada) e LGPD/ICP-Brasil.

**Critérios de aceite:**
- **AC-CER-002-1**: GIVEN certificado gerado em status PENDENTE_ASSINATURA, WHEN RT inicia assinatura, THEN sistema gera hash do PDF, envia nonce + signing-time controlado pelo servidor pro Web PKI Lacuna, recebe assinatura PKCS#7, anexa ao PDF, marca status ASSINADO.
- **AC-CER-002-2**: GIVEN tentativa de replay (mesmo nonce reusado), WHEN servidor verifica, THEN rejeita + log incidente segurança.
- **AC-CER-002-3**: GIVEN ART/RRT do RT vencida (módulo Licenças), WHEN inicia assinatura, THEN sistema bloqueia.
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
- **AC-CER-016-1**: GIVEN cert em status ASSINADO + tenant declara setor (farma/hospital/inmetro) em onboarding, WHEN RT marca "destino regulatório", THEN sistema gera PDF/A-3 com XML embedded validado contra XSD setorial (`anvisa-ext-v1.xsd`/`inmetro-ext-v1.xsd`/`saude-ext-v1.xsd`).
- **AC-CER-016-2**: GIVEN PDF/A-3 gerado, WHEN sistema processa, THEN aplica carimbo TSA-ITI (latência aceita 1-3s assíncrona) + hash SHA-256 do XML embedded salvo em `Certificado.xml_embedded_hash` (probatório).
- **AC-CER-016-3**: GIVEN cert regulatório sem TSA-ITI carimbado, WHEN tenant tenta marcar como "entregue ao auditor", THEN sistema bloqueia com 412 `CertRegulatorioSemTSA`.

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
- **AC-CER-018-1**: GIVEN bug confirmado em `versao_motor_calculo=X.Y.Z` via replay determinístico (ADR-0025), WHEN gestor dispara Recall, THEN sistema identifica TODOS os cert com aquela versão + cria evento `CertificadoRecallEmitido(certificado_id, motivo_bug, replay_validacao_id, correlation_id)` por cert.
- **AC-CER-018-2**: GIVEN evento publicado, WHEN consumer `notificar-cliente-recall` recebe, THEN envia notificação ao cliente em ≤24h (canal preferencial + e-mail) + audit no `EventoDeCertificado`.
- **AC-CER-018-3**: GIVEN bug afetou decisão sobre titular (cert farma usado pra liberar lote), WHEN flag `impacto_titular=true`, THEN consumer `notificar-anpd-recall` notifica ANPD em ≤24h via canal LGPD `docs/conformidade/comum/incidente-anpd-modelo.md`.
- **AC-CER-018-4**: GIVEN Recall ativo, WHEN página pública (US-CER-009) resolve QR Code, THEN exibe "este cert foi objeto de Recall em DD/MM/AAAA — contate o laboratório emissor" + nº cert + status `RECALL_ATIVO`.
- **AC-CER-018-5**: GIVEN notificação CGCRE em ≤30d, WHEN gestor qualidade dispara, THEN gera dossiê via `consultor-rbc-iso17025` template + audit imutável.

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

## 6.1 Campos do certificado — RBC vs não-RBC (novo Onda 7 — A2-CAL)

> Tabela canônica de quais campos aparecem no PDF condicional ao escopo de acreditação. Templates US-CER-010 usam esta tabela como contrato.

| Campo | RBC obrigatório | Não-RBC | Observação |
|---|---|---|---|
| Selo CGCRE com nº acreditação | Sim | Não | RBC sem selo = NC supervisão |
| Declaração ILAC-MRA | Sim | Não | Cabeçalho do PDF |
| Número da acreditação CGCRE | Sim | Não | Vinculado a `Tenant.acreditacao_cgcre_id` (módulo Licenças) |
| Escopo CGCRE da grandeza | Sim | Não | Cita ID e versão do escopo aprovado (Marco 5 módulo Licenças) |
| Declaração de rastreabilidade ao SI | Sim | Recomendado | Cadeia INMETRO → padrão usado |
| Resultado de medição | Sim | Sim | Núcleo técnico |
| Incerteza de medição (U, k, nível confiança) | Sim | Sim | NIT-DICLA-030 rev. 15 item 8.2.6 |
| Regra de decisão (ADR-0024) | Sim (quando declarada) | Sim (quando declarada) | ILAC G8 |
| Condições ambientais | Sim | Recomendado | cl. 7.5 |
| Padrões utilizados (cadeia + cert externo) | Sim | Recomendado | cl. 6.5 |
| Validade da recalibração (sugestão) | Opcional (cliente decide) | Opcional | Não é obrigatória cl. 7.8 |
| Selo "NÃO RBC" | Não | Sim | Diferenciação visual obrigatória |
| Assinatura A3 + carimbo ITI | Sim | Sim | INV-017 |

**Regra do template (US-CER-010):**
- Template tem fields condicionais `{% if cert.tipo_acreditacao == "RBC" %}` que controlam blocos de selo+declaração.
- Tentativa de gerar cert RBC sem `Tenant.acreditacao_cgcre_id` vigente bloqueia com 412 (`INV-032`).
- Tentativa de gerar cert não-RBC com selo RBC no template bloqueia em validação de template (US-CER-010 AC-3).

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

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Zero gaps de numeração (target: 100%).
- Tempo médio emissão→assinatura ≤ 5 min.
- Taxa de entrega de e-mail ≥ 98%.

## 8. NFR

- **Performance:** geração PDF < 3s p95; assinatura A3 (round-trip) < 10s p95.
- **Disponibilidade:** 99.9% (certificado pendente é dinheiro parado).
- **Segurança:** SEC-001, SEC-002; A3 cliente-side; URL pública verificadora não expõe PII além do mínimo.
- **Acessibilidade:** WCAG AA; certificado PDF tagueado (PDF/UA).

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo `US-CER-NNN`.
- US deprecada → `@deprecated` + ADR.
- Mudança no template default → ADR + janela.
