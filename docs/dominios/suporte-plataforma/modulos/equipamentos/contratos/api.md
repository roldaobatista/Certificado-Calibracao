---
owner: Roldão
revisado-em: 2026-05-18
status: stable
modulo: equipamentos
dominio: suporte-plataforma
versao: 2
---

# Contratos de API — Equipamentos do cliente

> **v2 (2026-05-18):** revisão dos 4 subagentes endereçou bloqueadores B2/B3 (QR dual-mode + HMAC), B4 (transferência intra-tenant + aceite duplo), B5 (porta stub), B6 (audit unificado). Endpoints novos: `/recebimentos`, `/devolucoes`. Autorização sempre via `AuthorizationProvider.can()` (INV-AUTHZ-001).

## Convenções

- Versionamento via path (`/v1/`).
- Auth via Bearer token. Tenant via header `X-Tenant-ID` (INV-TENANT-001).
- Erros formato RFC 7807 (`application/problem+json`).
- Mutações aceitam `Idempotency-Key` (TTL 7 dias default; mutações destrutivas — sucatear/transferir — recusam reuso após 24h com 409).
- Toda decisão de autorização passa por `AuthorizationProvider.can(user_id, action, resource, tenant_id, purpose)` (INV-AUTHZ-001).
- Respostas 404/422 são **indistinguíveis** entre "não existe" e "existe em outro tenant" (sem oracle de enumeração).

---

## Endpoints

### `POST /v1/equipamentos` — cadastrar equipamento

**Action:** `equipamento.criar`
**Autorização:** metrologista, almoxarife (P-OP-03), atendente, admin.

**Request:**
```json
{
  "cliente_id": "uuid",
  "tag": "BAL-001",
  "numero_serie": "ABC123",
  "fabricante": "Toledo",
  "modelo": "9094",
  "faixa_medicao": "0-30kg",
  "classe_exatidao": "III",
  "descricao": "string ≤500 chars",
  "localizacao_fisica": "string ≤200 chars (regex anti-PII)",
  "material_etiqueta": "poliester_laminado|vinil_termico|metalica_alumarca",
  "intervalo_recalibracao_meses": 12
}
```

**Response 201:** equipamento + URL do QR + `perfil_tenant_no_momento_cadastro` congelado.

**Erros:**
- `409` TAG duplicada no tenant (INV-049) — mensagem genérica sem vazar quais TAGs existem.
- `422` cliente não encontrado neste tenant (INV-TENANT-001).
- `400` `localizacao_fisica` contém PII (INV-EQP-LOC-001).

**Invariantes:** INV-049, INV-051, INV-EQP-LOC-001, INV-TENANT-001, INV-AUTHZ-001.
**US:** US-EQP-001.
**Eventos:** `equipamento.cadastrado`.

---

### `GET /v1/equipamentos/{id}` — ficha 360°

**Action:** `equipamento.ler`
**Autorização:** mesmo tenant; perfis com escopo controlado (RBC C8):
- `admin_tenant`, `metrologista`: tudo.
- `atendente`, `almoxarife`: dados cadastrais + próxima calibração + histórico certs (sem fotos de chegada + sem decisao_apos_anomalia).
- `tecnico_campo`: cadastro + histórico certs (mesma de atendente).

**Response 200:** equipamento + versões + histórico certs (via porta `CertificadoQueryService`) + OS abertas (via porta `OSQueryService`) + eventos (filtrados de `audit_trail.eventos`).

**Performance:** p95 ≤ 1.5s mesmo com 200+ certs (NFR — RBC C3 índice composto).

**Invariantes:** INV-AUTHZ-001, INV-TENANT-001, INV-013 (log visualização).
**US:** US-EQP-003.

---

### `GET /v1/equipamentos?busca=&status=&cliente_id=` — listagem

**Action:** `equipamento.listar`
**Autorização escopo restritivo (advogado C3):**
- `admin_tenant`, `metrologista`: lista qualquer cliente.
- `atendente`: lista apenas clientes com OS aberta ou últimos 90d de atividade (necessidade LGPD art. 6º III).
- `tecnico_campo`: lista apenas equipamentos de OSs atribuídas a ele.

**Response 200:** paginação cursor.

---

### `PATCH /v1/equipamentos/{id}` — editar atributo

**Action:** `equipamento.editar`
**Autorização:** metrologista, admin (mesmo tenant).

**Request:**
```json
{
  "modelo": "string?",
  "faixa_medicao": "string?",
  "classe_exatidao": "string?",
  "descricao": "string?",
  "localizacao_fisica": "string?",
  "intervalo_recalibracao_meses": "int?",
  "motivo_mudanca": "correcao_cadastro_inicial|reparo_reclassificou|recalibracao_revelou_drift_permanente|troca_componente_principal|reidentificacao_fabricante|outros",
  "motivo_detalhe": "string (≥100 chars se motivo=outros)",
  "assinatura_a3_token": "string? (obrigatório em perfil A se altera classe/faixa)"
}
```

**Comportamento:**
- Tenta alterar `tag`, `numero_serie`, `fabricante`, `cliente_id_original_hash`, `perfil_tenant_no_momento_cadastro` → 422 "campo imutável" (INV-025).
- Campo versionável + cert emitido → cria `EquipamentoVersao` nova.
- Campo versionável + sem cert → UPDATE direto.
- Perfil A + altera `classe_exatidao`/`faixa_medicao` → exige `assinatura_a3_token` válida; ausente → 422.
- `motivo_mudanca=outros` → exige `motivo_detalhe` ≥100 chars + aprovação gestor qualidade (workflow async — Marco 2 retorna 202 "aguardando aprovação").
- `localizacao_fisica` com PII → 400 (INV-EQP-LOC-001).

**Erros:** 422, 404, 403, 400.
**Invariantes:** INV-025, INV-EQP-LOC-001, INV-AUTHZ-001.
**US:** US-EQP-002.
**Eventos:** `equipamento.editado` ou `equipamento.versao_criada`.

---

### `POST /v1/equipamentos/{id}/sucatear` — sucatar com notificação

**Action:** `equipamento.sucatear`
**Autorização:** metrologista, admin (mesmo tenant).

**Request:**
```json
{
  "motivo": "string ≤500 chars",
  "foto_evidencia_url": "URL? (corretora C1 — recomendado)",
  "confirmacao_dupla": "boolean (obrigatório true se há cert vigente)"
}
```

**Pré:** sem OS aberta (consulta porta `OSQueryService`).

**Comportamento:**
- Cert vigente (`CertificadoQueryService.equipamento_tem_certificado_vigente()`) + `confirmacao_dupla=false` → 412 "confirmação dupla obrigatória — equipamento tem certificado vigente".
- Sucata é estado terminal.

**Erros:** 409 (OS aberta), 412 (confirmação dupla pendente).
**Invariantes:** INV-AUTHZ-001.
**US:** US-EQP-005.
**Eventos:** `equipamento.sucateado` OU `equipamento.sucateado_com_certificado_vigente`.

---

### `POST /v1/equipamentos/{id}/transferir` — transferir intra-tenant com aceite duplo

**Action:** `equipamento.transferir`
**Autorização:** atendente, metrologista, admin (mesmo tenant).

**Request:**
```json
{
  "novo_cliente_id": "uuid",
  "motivo_categoria": "venda|comodato|doacao|correcao_cadastral|outro",
  "motivo_detalhe": "string ≤500 chars (regex anti-PII)",
  "aceite_origem": {
    "via": "portal|presencial|email_confirmado",
    "texto_versao_id": "uuid",
    "evidencia_id": "uuid?"
  },
  "aceite_destino": {
    "via": "portal|presencial|email_confirmado",
    "texto_versao_id": "uuid",
    "evidencia_id": "uuid?"
  }
}
```

**Comportamento:**
- `novo_cliente.tenant_id != equipamento.tenant_id` → 422 "cliente não encontrado neste tenant" (INV-050 — mensagem genérica, sem oracle).
- Cliente cedente bloqueado OU tem fatura aberta referente ao equipamento → 412 "regularize antes de transferir".
- Aceite ausente → 400.
- `motivo_detalhe` com PII → 400.

**Erros:** 422 (cross-tenant ou ausência de PII), 412 (bloqueio cedente), 400 (validação).
**Invariantes:** INV-050, INV-025, INV-TENANT-001, INV-AUTHZ-001.
**US:** US-EQP-004.
**Eventos:** `equipamento.transferido` (payload sanitizado — hashes).

---

### `POST /v1/equipamentos/{id}/recebimentos` — registrar entrada física no lab (US-EQP-006)

**Action:** `equipamento.receber_no_lab`
**Autorização:** almoxarife (P-OP-03), metrologista, admin.

**Request (multipart/form-data):**
```
condicao_visual_chegada: integro|amassado|lacre_violado|contaminado|sem_acessorios|outros
anomalias_observadas: string
decisao_apos_anomalia: prosseguir|contatar_cliente_aguardando|recusar_devolver|prosseguir_com_ressalva
justificativa_decisao: string (≥30 chars se decisao != prosseguir)
lacre_chegada: string?
fotos: file[] (≥1 obrigatória em perfil A; EXIF removido server-side; ≤5MB cada)
```

**Response 201:** `EquipamentoRecebimento` criado; `status_fluxo_lab=recebido_pendente_inspecao`.

**Erros:** 422 (perfil A sem foto), 400 (validação).
**Invariantes:** INV-AUTHZ-001, ISO 17025 cl. 7.4.4.
**US:** US-EQP-006.
**Eventos:** `equipamento.recebido_no_lab` + `equipamento.anomalia_recebimento` se condição != integro.

---

### `PATCH /v1/equipamentos/{id}/recebimentos/{recebimento_id}` — avançar status_fluxo_lab

**Action:** `equipamento.avancar_fluxo_lab`
**Autorização:** metrologista, admin.

**Request:** `{ "novo_status": "em_inspecao_visual|aguardando_calibracao|...|devolvido", "observacoes": "string?" }`

**Comportamento:** valida transição na máquina de estados. Transição inválida → 422.

**US:** US-EQP-006.

---

### `POST /v1/equipamentos/{id}/recebimentos/{recebimento_id}/devolucoes` — registrar devolução ao cliente

**Action:** `equipamento.devolver`
**Autorização:** almoxarife, metrologista, admin.

**Request (multipart/form-data):**
```
condicao_visual_devolucao: enum
fotos_devolucao: file[]
termo_devolucao_assinado_url: string? (URL portal cliente)
```

**Response 200:** `data_hora_devolucao` setado; `status_fluxo_lab=devolvido`.
**US:** US-EQP-006.
**Eventos:** `equipamento.devolvido_ao_cliente`.

---

### `GET /v1/equipamentos/{id}/qr` — gerar PDF da etiqueta

**Action:** `equipamento.imprimir_etiqueta`
**Autorização:** almoxarife, metrologista, atendente.

**Response 200:** PDF da etiqueta (A6 ou label 50x80mm; material conforme `material_etiqueta`).

---

### `POST /v1/equipamentos/{id}/qr/reemitir` — re-emitir QR Code

**Action:** `equipamento.reemitir_qr`
**Autorização:** metrologista, admin.

**Request:**
```json
{ "manter_anterior_ativo": false }
```

**Comportamento:** novo hash HMAC-SHA256; QR anterior recebe `revogado_em = now()` (salvo flag explícita — válido por mais 90 dias para re-impressão em lote).

**Eventos:** `equipamento.qr_reemitido`.

---

### `GET /v1/qr/{hash}` — resolver QR (dual-mode — INV-051)

**Action:** decidida via `AuthorizationProvider.can(user, "equipamento.ler_via_qr" | "equipamento.ler", resource, tenant_id, purpose)`.

**Modo A — sessão autenticada no MESMO tenant do equipamento:**
- `can("equipamento.ler", purpose="operacao_normal")` → 302 redirect para `/equipamentos/{id}` (ficha 360° completa).

**Modo B — sessão autenticada em OUTRO tenant:**
- `can("equipamento.ler_via_qr", purpose="leitura_publica_pos_scan")` → 200 com payload mínimo Escopo B (allowlist em `docs/conformidade/equipamentos/qr-publico-allowlist.md`):
```json
{
  "tipo": "ativo_aferê",
  "fabricante": "string|null",
  "modelo": "string|null",
  "status": "ativo|inativo|sucata|em_calibracao_lab",
  "proxima_calibracao_em": "YYYY-MM-DD|null",
  "faixa_medicao": "string|null",
  "classe_exatidao": "string|null",
  "mensagem": "Este ativo pertence a outro tenant. Detalhes protegidos por confidencialidade."
}
```

**Modo C — anônimo ou sem sessão:**
- 200 com payload mínimo Escopo C:
```json
{
  "tipo": "ativo_aferê",
  "fabricante": "string|null",
  "modelo": "string|null",
  "status": "ativo|inativo|sucata|em_calibracao_lab",
  "mensagem": "Este ativo está cadastrado no Aferê. Para acessar detalhes técnicos, entre em contato com o laboratório responsável.",
  "afere_url_institucional": "https://afere.com.br"
}
```

**Erros:** 404 (hash inválido / revogado / equip removido — indistinguível entre os casos).

**Rate limit:**
- 60 req/min/usuário autenticado.
- 60 req/min/IP (independente de autenticação).
- 100+ respostas 4xx do mesmo IP em 1h → bloqueio 24h + alerta P2.

**Cache:** `Cache-Control: private, no-store` (payload varia por escopo).

**Invariantes:** INV-051, INV-AUTHZ-001, INV-TENANT-001.
**US:** US-EQP-003.
**Eventos:** `equipamento.qr_scanned` (todos escopos — IP hash + UA hash + decisão).

---

## Rate limits

| Endpoint | Limite por usuário | Limite por IP |
|---|---|---|
| `GET /v1/qr/*` | 60 req/min | 60 req/min |
| Demais (autenticados) | 120 req/min | 120 req/min |
| `POST` mutações destrutivas (sucatear, transferir) | 10 req/min | 10 req/min |

## Versionamento

v1 e v2 coexistem por 6 meses. Quebra de contrato → ADR + janela de migração.

## Como evolui

- Endpoint novo → linkar US-EQP-NNN.
- Quebra de contrato → ADR.
- Action nova → registrar em catálogo de ações do `AuthorizationProvider` + seed migration.
