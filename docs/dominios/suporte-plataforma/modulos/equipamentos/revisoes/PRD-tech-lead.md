---
owner: tech-lead-saas-regulado (subagente)
revisado-em: 2026-05-18
status: stable
escopo: PRD draft equipamentos — review pré-STABLE
---

# Tech Lead Review — PRD `equipamentos` (DRAFT → STABLE)

## (A) Veredito geral

**REPROVADO PARA STABLE** — subir como está produz dívida regulatória e operacional. PRD está sólido na intenção e bem fatiado, mas tem **6 BLOQUEADORES** que precisam ser endereçados antes de promover para STABLE, e **9 CONCERNS** com gravidade média/alta. Recomendação: aplicar as correções de seção (D), abrir **1 mini-ADR** (item E) e re-revisar.

Comparativamente ao módulo `clientes` Marco 1 (referência), `equipamentos` está em estágio menos maduro — falta invariância de TAG, falta porta para módulos ausentes (certificados/OS), e tem ambiguidade crítica no endpoint público de QR.

---

## (B) BLOQUEADORES

### B1. BLOQUEADOR — Não existe invariante para "TAG única por tenant"
INV-024 cobre cliente (CPF/CNPJ). `prd.md §2` afirma "TAG única" e `api.md §POST /v1/equipamentos` lista erro 409 "TAG duplicada no tenant", mas **não há ID em `REGRAS-INEGOCIAVEIS.md`** que crave isso. Sem INV, não tem hook de validação, não tem teste obrigatório (TST-004), e a unicidade vira convenção informal — mesmo problema que o módulo `clientes` resolveu com INV-024.

**Correção:** criar **INV-049** (próximo ID livre) — ver texto em (D1).

### B2. BLOQUEADOR — Endpoint `GET /v1/qr/{hash}` "público autenticado" colide com INV-AUTHZ-001
`api.md §90-92` declara o endpoint como "público autenticado" sem qualificar. INV-AUTHZ-001 exige que **toda** decisão passe por `AuthorizationProvider.can(user_id, action, resource, tenant_id, purpose)`. Hoje:
- Não há `user_id` definido para chamada do QR (cliente final escaneou no chão de fábrica)
- Não há `tenant_id` derivável do hash sem antes resolver a tabela
- Não há `purpose` LGPD declarado

Isso é o **mesmo problema** que o módulo `certificados` resolveu com a página verificadora pública (INV-035 — token opaco + campos mínimos). Equipamentos precisa de tratamento equivalente, mas atualmente abre brecha cross-tenant.

**Correção:** ver (D2) — 2 modos de leitura (público mínimo vs interno autenticado) + action `equipamento.ler_via_qr` + `purpose='leitura_publica_pos_scan'`.

### B3. BLOQUEADOR — Hash do QR sem especificação criptográfica + sem proteção anti-enumeração
`modelo-de-dominio.md §32-34` cita `hash_assinatura` sem detalhar algoritmo, sem `tenant_id` no payload do hash, sem comprimento mínimo. URL `/v1/qr/{hash}` é enumerável se o hash for curto/previsível — **risco de mineração cross-tenant**.

**Correção:** ver (D3) — HMAC-SHA256(`equipamento_id|tenant_id|emitido_em`, KMS_secret), token base64url ≥22 chars, rate-limit por IP.

### B4. BLOQUEADOR — Proibição de transferência cross-tenant não está cravada
`prd.md §29` permite "transferência de equipamento entre clientes" e `api.md §POST /transferir` aceita `novo_cliente_id`. **Não há regra explícita** dizendo que `novo_cliente_id` precisa ser do **mesmo tenant** que o `cliente_id_original`.

**Correção:** ver (D4) — criar **INV-050** + AC explícito + teste.

### B5. BLOQUEADOR — Porta `CertificadoQueryService` / `OSQueryService` ausente do modelo de domínio
Ficha 360° declara que retorna "histórico cert. + OS abertas". Esses módulos **não existem ainda**. Sem porta domain definida com stub, agente que implementar US-EQP-003 vai inventar acesso direto ao banco do módulo certificados/os (viola ADR-0007) OU retornar vazio e "esquecer de plugar depois" (débito permanente).

**Correção:** ver (D5) — definir 2 portas em `src/domain/suporte_plataforma/equipamentos/ports/` + adapter stub default + hook `port-binding-validator`.

### B6. BLOQUEADOR — `EquipamentoEvento` versus `Equipamento.*` eventos publicados — duplicação ambígua
Modelo define `EquipamentoEvento` (log interno append-only) e 4 eventos publicados no bus. PRD não explica relação. Auditor de Qualidade vai bater nessa ambiguidade. Padrão clientes Marco 1: gravar evento em `auditoria` (WORM, hash chain) — fonte única de verdade.

**Correção:** ver (D6) — alinhar com padrão `clientes`: `EquipamentoEvento` REMOVIDO; auditoria é fonte.

---

## (C) CONCERNS

### C1. CONCERN ALTA — Campos imutáveis inconsistentes entre os 3 documentos
`modelo-de-dominio.md §16`, `api.md §61` e `glossario.md:24` listam imutáveis pós-cert de formas diferentes. Padronizar nos 3 docs.

### C2. CONCERN ALTA — `cliente_id_original` vs `cliente_atual_id` — snapshot de versão incompleto
`EquipamentoVersao` snapshot JSONB não inclui `cliente_atual_id` no momento. Auditor pergunta "quem era cliente_atual em 2026-03-15?" — resposta vem indireta via `EquipamentoEvento.transferido`. Incluir `cliente_atual_id_no_momento` no snapshot.

### C3. CONCERN ALTA — `snapshot_atributos_versionaveis` JSONB sem índice/schema
GIN index + Pydantic schema mínimo + validação na camada application.

### C4. CONCERN ALTA — Tela 5 (Scanner QR mobile) é ADR-0003-dependent
PWA + BarcodeDetector com fallback jsQR (Chrome Android nativo; iOS Safari fallback) — entrega sem bloquear ADR-0003. Ver (E) mini-ADR.

### C5. CONCERN ALTA — Performance ficha 360° p95 ≤ 1.5s
Índice composto `(tenant_id, equipamento_id, created_at DESC)` em `EquipamentoEvento` e `EquipamentoVersao`. NÃO implementar cache em Marco 1 — medir primeiro.

### C6. CONCERN MÉDIA — Persona "almoxarife" em `api.md` mas não em `personas.md`
Adicionar persona ou remover de api.md. Recomendo adicionar (P-OP-03 Almoxarife).

### C7. CONCERN MÉDIA — Spec-as-source ADR-0007: como expressar "imutável pós-cert" em YAML
Ver (D8) — snippet YAML.

### C8. CONCERN MÉDIA — Payload mínimo dos 4 eventos não está no catálogo v8
Ver (D9) — payload por evento.

### C9. CONCERN MÉDIA — Re-emissão de QR Code não revoga anterior automaticamente
Re-emissão revoga automaticamente; flag opcional `manter_anterior_valido` para casos de impressão em lote.

---

## (D) Recomendações prontas (texto sugerido)

### D1. INV-049 — TAG única por tenant
```
| INV-049 | TAG do equipamento é única por tenant. Não permite duplicar TAG no cadastro de equipamentos do mesmo tenant. Bloqueio em INSERT/UPDATE. (Origem: equipamentos US-EQP-001) | Boa prática + INV-024 análoga + audit | Constraint UNIQUE (tenant_id, tag) na tabela equipamento; UI mostra "TAG já existe" antes do submit; resposta 409 não pode vazar cross-tenant | Absoluta (todos perfis) | Equipamento duplicado, etiqueta colidindo, certificado emitido com referência ambígua |
```

### D2. Endpoint `GET /v1/qr/{hash}` — 2 modos
```
Modo A — usuário com sessão autenticada no MESMO tenant do equipamento:
- AuthorizationProvider.can(user_id, "equipamento.ler", {equipamento_id, tenant_id}, purpose="operacao_normal")
- Retorna 302 redirect para ficha 360° completa.

Modo B — anônimo OU sessão de tenant diferente:
- AuthorizationProvider.can(SYSTEM_USER, "equipamento.ler_via_qr", {equipamento_id, tenant_id}, purpose="leitura_publica_pos_scan")
- Retorna 200 com payload MÍNIMO LGPD (INV-051): { tag, modelo, status, proxima_calibracao_em }. Sem NS, sem cliente, sem localização, sem histórico.

Erros: 404 (hash inválido/revogado/equip. removido).
Rate limit: 60 req/min por IP (não só por usuário).
Invariantes: INV-051, INV-AUTHZ-001, INV-TENANT-001.
```

### D3. QrCode value object — HMAC-SHA256
```
- Atributos: equipamento_id, tenant_id, hash, emitido_em, revogado_em (nullable)
- Hash: base64url( HMAC-SHA256( "<equipamento_id>|<tenant_id>|<emitido_em_iso8601>", KMS_qr_secret ) ) — 22+ chars (≥128 bits entropia)
- KMS_qr_secret: chave dedicada em AWS KMS MRK, rotacionada anualmente; rotação não invalida hashes existentes
- Re-emissão: automaticamente seta revogado_em = now() no QR anterior. Flag manter_anterior_ativo=true em rota explícita para casos de re-impressão em lote
- Invariantes: INV-051
```

### D4. INV-050 + US novo
```
| INV-050 | Transferência de equipamento entre clientes é restrita ao mesmo tenant. Equipamento.cliente_atual_id só pode ser atualizado para cliente cujo tenant_id é igual ao Equipamento.tenant_id. Tentativa cross-tenant bloqueia hard. (Origem: equipamentos transferência) | INV-TENANT-001 + LGPD art. 6º V | Hook BEFORE UPDATE em equipamento.cliente_atual_id: valida novo_cliente.tenant_id = equipamento.tenant_id; teste de fuzzing cross-tenant | Absoluta (todos perfis) | Vazamento cross-tenant; cliente de tenant A "recebe" equipamento de tenant B |
```

US-EQP-004 (transferência intra-tenant) com AC explícito de bloqueio cross-tenant.

### D5. Portas CertificadoQueryService / OSQueryService stub
Definir interface + adapter `EmptyCertificadoQueryService` / `EmptyOSQueryService` retornando lista vazia. Selecionado em runtime via `settings.PORT_BINDINGS`. Hook `port-binding-validator.sh` bloqueia release prod se binding apontar para Empty* em settings.production.

### D6. `EquipamentoEvento` REMOVIDO
Padrão Marco 1 clientes: eventos do equipamento gravam em `audit_trail.eventos` (tabela global WORM com hash chain — INV-001) com `action` lowercase dot-notation:
- `equipamento.cadastrado`
- `equipamento.editado`
- `equipamento.versao_criada`
- `equipamento.transferido`
- `equipamento.sucateado`

Quando Procrastinate entrar (Wave A late), relay publica no bus a partir do `audit_trail.eventos` via outbox.

### D7. EquipamentoVersao — esquema JSONB
```python
class SnapshotAtributosVersionaveis(BaseModel):
    modelo: str
    faixa_medicao: str
    classe_exatidao: str
    descricao: str | None
    localizacao_fisica: str | None
    cliente_atual_id_no_momento: UUID
```
Índices: `(equipamento_id, versao_n DESC)` UNIQUE; GIN parcial se busca virar hot path (medir primeiro).

### D8. Snippet spec-as-source ADR-0007
```yaml
entidade: Equipamento
campos:
  - nome: tag
    tipo: string
    imutavel_pos: ["primeira_emissao_certificado"]
    invariante: INV-049
  - nome: numero_serie
    tipo: string
    imutavel_pos: ["primeira_emissao_certificado"]
    invariante: INV-025
  - nome: modelo
    tipo: string
    versionavel: true
    invariante: INV-025
```

### D9. Payload dos eventos
Envelope padrão (catálogo v8): `event_id`, `tenant_id`, `published_at`, `correlation_id`, `causation_id`, `actor_user_id`, `_schema_version`.

```
Equipamento.Cadastrado: { equipamento_id, tag, cliente_id_original_hash }
Equipamento.VersaoCriada: { equipamento_id, versao_n, campos_alterados[] }
Equipamento.Sucateado: { equipamento_id, motivo, ts_marcacao }
Equipamento.Transferido: { equipamento_id, cliente_anterior_id, cliente_novo_id, motivo }
```

Não logar NS em claro no payload (preferir resolver via tabela).

---

## (E) Mini-ADR a abrir antes da Wave A

### ADR-0018 — Estratégia de scanner QR em PWA até Flutter chegar

**Status:** proposta — abrir agora, fechar antes de implementar US-EQP-003.
**Decisão proposta:** PWA com BarcodeDetector API nativo (Chrome Android) + fallback jsQR (iOS Safari + browsers antigos). Mesma URL `/v1/qr/{hash}` resolvida pelo backend — quando Flutter chegar (Wave B), reusa endpoint.
**Trade-offs:**
- ✅ Não bloqueia Wave A
- ✅ Não joga código fora — PWA continua útil para clientes finais mesmo após app Flutter
- ❌ iOS Safari pré-17 sem BarcodeDetector nativo — jsQR é ~45KB gzip
- ❌ Performance câmera ativa em browser inferior a app nativo (uso esporádico)
