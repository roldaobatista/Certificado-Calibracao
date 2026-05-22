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

**Invariantes:** `INV-019` (RT habilitado quando aplicável), `INV-017` (A3 + carimbo ITI obrigatório em A), `INV-001` (WORM), ADR-0009.

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
