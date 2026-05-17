---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/suporte-plataforma/README.md
  - REGRAS-INEGOCIAVEIS.md
---

# PRD — Módulo Gestão Documental

> Biblioteca central de documentos do tenant. Pastas por entidade (cliente, equipamento, OS, contrato, fornecedor), versionamento, aprovação, vigência, assinatura eletrônica, validade, OCR, busca por conteúdo, retenção, compartilhamento com cliente.

---

## 1. O que este módulo é

ECM (Enterprise Content Management) leve embarcado no Aferê. Armazena, versiona, aprova, assina, expira e descobre documentos de qualquer entidade do sistema (clientes, equipamentos, OS, contratos, fornecedores, calibrações). Não substitui WORM regulado de calibração (esse fica em `metrologia/`), mas é o repositório operacional do dia a dia.

## 2. Por que este módulo existe

Empresas técnicas trabalham com laudos, certificados, contratos, manuais, ARTs, fotos, notas fiscais e evidências. Hoje fica em pastas dispersas (Drive, e-mail, WhatsApp, papel). Sem versão, sem validade, sem rastreabilidade.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Biblioteca central de documentos com upload, download, preview.
- Pastas virtuais por entidade (cliente / equipamento / OS / contrato / fornecedor).
- Controle de versão (v1, v2, v3) com diff de metadados.
- Workflow de aprovação configurável.
- Status vigente / obsoleto / em revisão.
- Assinatura eletrônica (simples e avançada — A3 fica no módulo de Assinatura).
- Controle de validade + notificação de vencimento.
- Modelos de documento (templates reutilizáveis).
- Controle de acesso granular por documento (ACL).
- Trilha de auditoria de todas as ações (`INV-001`).
- Busca por conteúdo (full-text) + OCR para digitalizados.
- Política de retenção configurável.
- Compartilhamento externo com cliente via link.

## 5. Non-goals (o que NÃO está neste módulo)

- NÃO emite certificado de calibração (módulo `metrologia/certificacao/`).
- NÃO armazena trilha imutável WORM de eventos regulados (módulo `comum/auditoria/` + Backblaze B2).
- NÃO faz assinatura A3 client-side (delegado a Web PKI Lacuna — ADR-0009).
- NÃO substitui DMS jurídico avançado (sem cluster semântico, sem retenção legal hold court-order).
- NÃO faz colaboração em tempo real estilo Google Docs.

## 6. User Stories

### US-DOC-001: Upload de documento vinculado a entidade

**Como** usuário operacional, **quero** fazer upload de um arquivo vinculado a um cliente/OS/equipamento, **para** centralizar evidências.

**AC:**
- **AC-DOC-001-1**: GIVEN entidade selecionada, WHEN upload é concluído, THEN documento é gravado com `tenant_id`, `entidade_tipo`, `entidade_id`, `versao=1`, `status=vigente`.
- **AC-DOC-001-2**: GIVEN arquivo > 50MB, WHEN upload tentado, THEN sistema rejeita com mensagem clara.

**Invariantes:** `INV-001` (audit trail de toda criação), `INV-TENANT-001` (tenant em toda query).

---

### US-DOC-002: Controle de versão

**Como** responsável técnico, **quero** substituir documento mantendo histórico, **para** rastrear evolução.

**AC:**
- **AC-DOC-002-1**: GIVEN documento v1 existente, WHEN substituído, THEN v1 vira `status=obsoleto`, v2 vira `status=vigente`, ambos consultáveis.
- **AC-DOC-002-2**: GIVEN nova versão, WHEN gravada, THEN trilha registra autor, motivo, data.

**Invariantes:** `INV-001`.

---

### US-DOC-003: Workflow de aprovação

**Como** gestor, **quero** que documento crítico exija aprovação antes de virar vigente, **para** governança.

**AC:**
- **AC-DOC-003-1**: GIVEN documento marcado "requer aprovação", WHEN criado, THEN entra em `status=em_revisao`.
- **AC-DOC-003-2**: GIVEN aprovador autorizado, WHEN aprova, THEN status vira `vigente` + evento `documento.aprovado` disparado.

---

### US-DOC-004: Assinatura eletrônica simples

**Como** cliente externo, **quero** assinar documento via link, **para** formalizar aceite.

**AC:**
- **AC-DOC-004-1**: GIVEN link de assinatura gerado, WHEN cliente assina, THEN registro inclui IP, user-agent, hash do doc, timestamp.

---

### US-DOC-005: Controle de validade + notificação

**Como** responsável, **quero** que documento com data de validade me notifique antes de vencer, **para** renovar a tempo.

**AC:**
- **AC-DOC-005-1**: GIVEN documento com `data_validade`, WHEN faltam 30/15/7 dias, THEN notificação disparada pra responsável.
- **AC-DOC-005-2**: GIVEN data passada, WHEN consultado, THEN status muda para `vencido` automaticamente.

---

### US-DOC-006: Modelo de documento

**Como** administrador, **quero** criar templates reutilizáveis, **para** padronizar saída.

**AC:**
- **AC-DOC-006-1**: GIVEN template com variáveis, WHEN instanciado em entidade, THEN variáveis são preenchidas automaticamente.

---

### US-DOC-007: Controle de acesso por documento

**Como** gestor, **quero** restringir acesso a documento sensível, **para** confidencialidade.

**AC:**
- **AC-DOC-007-1**: GIVEN documento com ACL restrita, WHEN usuário não autorizado tenta acessar, THEN 403 + evento de tentativa registrado.

**Invariantes:** `INV-001`.

---

### US-DOC-008: Busca por conteúdo + OCR

**Como** usuário, **quero** buscar termo dentro de documentos (incluindo PDFs escaneados), **para** encontrar rápido.

**AC:**
- **AC-DOC-008-1**: GIVEN PDF digitalizado, WHEN ingerido, THEN OCR roda assíncrono e texto fica indexado em até 5min.
- **AC-DOC-008-2**: GIVEN busca por termo, WHEN executada, THEN retorna em < 2s p95 e respeita ACL.

---

### US-DOC-009: Política de retenção

**Como** compliance officer, **quero** configurar retenção por tipo de documento, **para** atender LGPD + ISO 17025.

**AC:**
- **AC-DOC-009-1**: GIVEN política "manter 5 anos", WHEN documento atinge prazo, THEN entra em fila de descarte revisado.

---

### US-DOC-010: Compartilhamento com cliente

**Como** atendente, **quero** gerar link público temporário, **para** entregar documento ao cliente sem e-mail.

**AC:**
- **AC-DOC-010-1**: GIVEN link gerado com TTL, WHEN expirado, THEN retorna 410 Gone.
- **AC-DOC-010-2**: GIVEN cada acesso, WHEN ocorre, THEN registrado em trilha (`INV-001`).

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- % documentos com versão única (sem duplicatas) > 95%.
- Tempo médio de busca p95 < 2s.

## 8. NFR

- **Performance:** upload até 50MB < 30s; busca p95 < 2s; OCR assíncrono SLA 5min.
- **Disponibilidade:** SLO 99.5%.
- **Segurança:** SEC-001 (criptografia at-rest), SEC-002 (TLS in-transit), ACL granular.
- **Acessibilidade:** WCAG AA.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

US nova → próximo ID livre (`US-DOC-NNN`). US deprecada → `@deprecated` + ADR.
