---
owner: Roldão
revisado-em: 2026-05-18
status: stable
modulo: equipamentos
dominio: suporte-plataforma
versao: 3
---

# Modelo de domínio — Equipamentos do cliente

> **v2 (2026-05-18 manhã):** revisão pelos 4 subagentes endereçou 16 bloqueadores. `EquipamentoEvento` removido (usa `audit_trail.eventos`), `cliente_id_original` separado em hash + UUID nullable, `perfil_tenant_no_momento_cadastro` snapshot imutável, `RecebimentoEquipamento` entidade nova, motivo de versionamento enum, portas stub para módulos certificados/OS.
>
> **v3 (2026-05-18 noite):** revisão de 12 planos de US endereçou ressalvas finas: (a) `fotos_chegada`/`fotos_devolucao` guardam `storage_key` (não URL — tech-lead US-006), (b) `recebimento_aberto_id` materializado no `Equipamento` resolve ambiguidade `status=em_calibracao_lab` com múltiplos recebimentos, (c) `consentimento_compartilhamento_historico_em_transferencia` migrou para `TransferenciaEquipamentoAceite` (imutável no aceite) + flag derivada `mostrar_historico_anterior` no `Equipamento`, (d) entidade nova `RecebimentoProvisorio` (separada de `EquipamentoRecebimento` — decisão Roldão Caminho A).

## Entidades

### Equipamento (agregado raiz)

**Atributos imutáveis pós-cert (INV-025 + INV-049):**
- `tag` (UNIQUE por tenant — INV-049)
- `numero_serie`
- `fabricante`
- `cliente_id_original_hash: bytes(32)` — SHA-256 salgado por tenant (mesmo salt do hash de PII de clientes — Marco 1). Sobrevive ao crypto-shredding do cliente original.
- `perfil_tenant_no_momento_cadastro: enum {A,B,C,D}` — snapshot anti-downgrade (RBC B4)

**Atributos versionáveis (criam `EquipamentoVersao` se há ≥1 cert emitido):**
- `modelo`
- `faixa_medicao`
- `classe_exatidao` (em perfil A exige A3 RT)
- `descricao` (≤500 chars)
- `localizacao_fisica` (≤200 chars, regex anti-PII — INV-EQP-LOC-001)
- `procedimento_calibracao_aplicavel: FK opcional` (preenchido na 1ª calibração; versionável após)
- `intervalo_recalibracao_meses: integer`

**Atributos operacionais (mutáveis sempre):**
- `status: enum {ativo, inativo_temporario, aposentado, em_calibracao_lab, sucata, orfao_pendente_decisao, extraviado}`
- `cliente_atual_id: FK NULL` (FK com `ON DELETE SET NULL` — espelho LGPD)
- `cliente_id_original: FK NULL` (referência mutável "viva" enquanto cliente original existir; vira NULL quando shredded — par com `cliente_id_original_hash`)
- `foto_principal_storage_key: string NULL` — chave opaca no `FotoStorageService` (NÃO URL — URL é regenerada via signed URL TTL curto; v3 tech-lead US-006); imutável após primeira foto; EXIF removido no upload
- `material_etiqueta: enum {poliester_laminado, vinil_termico, metalica_alumarca}` (default `poliester_laminado` em perfil A)
- `numero_etiqueta_calibracao_atual: FK opcional` ao selo vigente (módulo `certificados` quando chegar)
- `mostrar_historico_anterior: boolean` (derivada — flag espelho do consentimento dado no último aceite de transferência. **Imutabilidade do consentimento está em `TransferenciaEquipamentoAceite`**, não aqui. Default true se nunca houve transferência. v3 tech-lead US-004)
- `recebimento_aberto_id: FK NULL` (materializado via trigger — aponta para `EquipamentoRecebimento` ativo se há um; NULL quando não há. Resolve ambiguidade do `status=em_calibracao_lab` com múltiplos recebimentos. v3 tech-lead US-006)

**Ciclo de vida:** criada no cadastro → ativa → versões geradas a cada edição pós-cert → sucateada (terminal) / aposentada (reversível com avaliação técnica) / extraviada (alerta).

**Invariantes:** INV-025, INV-049, INV-051, INV-EQP-LOC-001, INV-TENANT-001.

### EquipamentoVersao (entidade filha)

- `equipamento_id: FK`
- `versao_n: integer` (UNIQUE com `equipamento_id` DESC)
- `snapshot_atributos_versionaveis: JSONB` (esquema Pydantic abaixo)
- `motivo_mudanca: enum` (controlado — RBC B7):
  - `correcao_cadastro_inicial`
  - `reparo_reclassificou`
  - `recalibracao_revelou_drift_permanente`
  - `troca_componente_principal`
  - `reidentificacao_fabricante`
  - `outros` (exige justificativa ≥100 chars + aprovação gestor qualidade)
- `motivo_detalhe: text` (≥100 chars se motivo=outros)
- `exige_assinatura_a3_rt: boolean` (true em perfil A para mudanças em classe_exatidao / faixa_medicao)
- `assinatura_a3_hash: text NULL`
- `criado_em: timestamp`
- `criado_por: usuario_id`

**Imutável após criada.** Cada certificado referencia `(equipamento_id, versao_n)` que existia no momento da emissão.

**Esquema JSONB validado em camada application:**
```python
class SnapshotAtributosVersionaveis(BaseModel):
    modelo: str
    faixa_medicao: str
    classe_exatidao: str
    descricao: str | None
    localizacao_fisica: str | None
    procedimento_calibracao_aplicavel_id: UUID | None
    intervalo_recalibracao_meses: int | None
    cliente_atual_id_no_momento: UUID | None  # tech-lead C2 — preserva cliente histórico
```

**Índices:** `(equipamento_id, versao_n DESC)` UNIQUE; GIN parcial em `snapshot` se ficha 360° virar hot path (não criar agora — medir primeiro).

### EquipamentoRecebimento (entidade nova — ISO 17025 cl. 7.4)

> RBC B1/B2 — registrar cada entrada física no laboratório.

- `equipamento_id: FK`
- `numero_entrada_lab: string` (identificador sequencial — TAG provisória de bancada, formato `{LAB}-{ANO}-{SEQ}`)
- `data_hora_recebimento: timestamp`
- `recebido_por: usuario_id`
- `condicao_visual_chegada: enum {integro, amassado, lacre_violado, contaminado, sem_acessorios, outros}`
- `fotos_chegada: array<string>` — array de `storage_key` opacos do `FotoStorageService` (NÃO URL — v3 tech-lead US-006); ≥1 obrigatória em perfil A; opcional B/C/D; EXIF removido no upload
- `anomalias_observadas: text`
- `decisao_apos_anomalia: enum {prosseguir, contatar_cliente_aguardando, recusar_devolver, prosseguir_com_ressalva}` (exigido se condição != integro)
- `justificativa_decisao: text` (≥30 chars se decisao != prosseguir)
- `lacre_chegada: text NULL` (id do lacre, se houver)
- `status_fluxo_lab: enum` (máquina de estados — RBC B3):
  - `aguardando_recebimento → recebido_pendente_inspecao → em_inspecao_visual → aguardando_calibracao → em_calibracao → aguardando_aprovacao_tecnica → aguardando_devolucao → devolvido`
  - Caminhos alternativos terminais: `nao_conformidade_recebimento`, `nao_conformidade_calibracao`
- `data_hora_devolucao: timestamp NULL`
- `condicao_visual_devolucao: enum` (mesmo conjunto)
- `fotos_devolucao: array<string>` — `storage_key` opacos (EXIF removido; v3 tech-lead US-006)
- `termo_devolucao_assinado_storage_key: string NULL` (comprovante de devolução assinado — v3 advogado US-006 R2 — qualificado como documento particular CPC art. 411 III, não Lei 14.063/2020; Wave B+ com portal-cliente migra pra art. 4º I Lei 14.063/2020)

**Invariantes:** INV-AUTHZ-001, ISO 17025 cl. 7.4.4 + 7.4.5 + 7.10.

### RecebimentoProvisorio (entidade nova v3 — decisão Roldão Caminho A)

> Almoxarife recebe equipamento físico sem cadastro prévio (cliente trouxe instrumento novo). Tabela SEPARADA de `EquipamentoRecebimento` para não exigir migration NULL→NOT NULL em `Equipamento.cliente_atual_id` futuramente (tech-lead US-006 R1).

- `id: UUID`
- `tenant_id: FK`
- `numero_provisorio_lab: string` (TAG provisória de bancada, formato `{LAB}-PROV-{ANO}-{SEQ}`)
- `data_hora_recebimento: timestamp`
- `recebido_por: usuario_id`
- `cliente_id_provisorio: FK NULL` (preenchido se almoxarife identifica cliente; vazio se desconhecido)
- `descricao_aparelho: text` (texto livre — almoxarife descreve o que recebeu — regex anti-PII INV-EQP-LOC-001)
- `fabricante_declarado: text NULL`
- `numero_serie_declarado: text NULL`
- `fotos_chegada: array<string>` — storage_key opacos; obrigatório em perfil A
- `condicao_visual_chegada: enum {integro, amassado, lacre_violado, contaminado, sem_acessorios, outros}`
- `anomalias_observadas: text` — regex anti-PII INV-EQP-ANOM-001
- `decisao_apos_anomalia: enum` (mesmas opções de EquipamentoRecebimento)
- `justificativa_decisao: text` — INV-EQP-ANOM-002
- `status: enum {aguardando_promocao, promovido, recusado, devolvido_sem_promocao}`
- `promovido_para_equipamento_id: FK NULL` (preenchido após promoção)
- `promovido_em: timestamp NULL`

**Não emite cert e não participa de OS até ser promovido** (INV-EQP-PROV-001). Promoção dispara evento `equipamento.promovido_de_provisorio` com payload `{provisorio_id, equipamento_id, perfil_tenant_no_momento_cadastro}`. Trigger PG `bloquear_fk_certificado_para_provisorio` impede INSERT em `certificado` referenciando `RecebimentoProvisorio.id`.

### QrCode (value object)

- `equipamento_id: FK`
- `tenant_id: FK`
- `hash: text` — `base64url( HMAC-SHA256( "<equipamento_id>|<tenant_id>|<emitido_em_iso8601>", KMS_qr_secret ) )` com ≥22 chars (≥128 bits entropia)
- `emitido_em: timestamp`
- `revogado_em: timestamp NULL`
- `manter_anterior_ativo: boolean` (default false; flag explícita em rota dedicada de re-impressão em lote)

**KMS_qr_secret:** chave dedicada em AWS KMS MRK (sa-east-1 ↔ us-east-1); rotação anual; rotação NÃO invalida hashes existentes (validação consulta tabela, não recomputa).

**Re-emissão:** automaticamente seta `revogado_em = now()` no QR anterior (janela de 90 dias se `manter_anterior_ativo=true` para re-impressão em lote — advogado C2).

**Trade-off opaco vs JWT:** opaco escolhido (não precisa cliente decodificar; revogação imediata via UPDATE; sem PII no payload mesmo cifrado).

**Invariantes:** INV-051.

---

## INV-025 — Imutabilidade pós-emissão (detalhe)

**Regra:** assim que o equipamento tem ≥1 `Certificado.status = emitido`:
1. **Campos imutáveis** (`tag`, `numero_serie`, `fabricante`, `cliente_id_original_hash`, `perfil_tenant_no_momento_cadastro`): qualquer tentativa de UPDATE retorna 422 com mensagem PT.
2. **Campos versionáveis**: UPDATE NÃO altera o registro original. Em vez disso, cria `EquipamentoVersao` nova com `versao_n+1` + snapshot + motivo (enum) + assinatura A3 se exigida.
3. **Histórico (`audit_trail.eventos`)**: append-only — nenhum delete, nenhum update.
4. **Anti-downgrade (RBC B4):** equipamento criado em perfil A NÃO pode ter sua história editada se tenant rebaixar pra B depois — `perfil_tenant_no_momento_cadastro` congela o regime.
5. **Validação**: trigger PG + camada application + hook pre-commit `equipamento-imutabilidade-check.sh` (a criar Wave A Marco 2).

---

## Agregados (DDD)

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| Equipamento | EquipamentoVersao, EquipamentoRecebimento, QrCode | INV-025, INV-049, INV-051, INV-EQP-LOC-001, INV-TENANT-001 |

---

## Portas consumidas (ADR-0007 — anti-corrosion layer)

### Porta `CertificadoQueryService` (consumida — módulo `certificados` ainda não existe)

**Localização:** `src/domain/suporte_plataforma/equipamentos/ports/certificado_query_service.py`

**Interface:**
```python
class CertificadoQueryService(Protocol):
    def buscar_por_equipamento(
        self, equipamento_id: UUID, tenant_id: UUID, limite: int = 10
    ) -> list[CertificadoSummary]: ...

    def equipamento_tem_certificado_emitido(
        self, equipamento_id: UUID, tenant_id: UUID
    ) -> bool: ...

    def equipamento_tem_certificado_vigente(
        self, equipamento_id: UUID, tenant_id: UUID
    ) -> CertificadoSummary | None: ...
```

DTO `CertificadoSummary(numero: str, emitido_em: date, validade: date, status: str)`.

**Adapter default Wave A Marco 2:** `EmptyCertificadoQueryService` retorna `[]` / `False` / `None` — equipamento ainda não tem certificados até módulo nascer.

**Adapter Wave A+:** `DjangoCertificadoQueryService` consulta módulo `certificados` quando entrar.

**Selecionado em runtime:** via `settings.PORT_BINDINGS["CertificadoQueryService"]`.

### Porta `OSQueryService` (consumida — módulo `os` ainda não existe)

**Localização:** `src/domain/suporte_plataforma/equipamentos/ports/os_query_service.py`

**Interface:**
```python
class OSQueryService(Protocol):
    def buscar_abertas_por_equipamento(
        self, equipamento_id: UUID, tenant_id: UUID
    ) -> list[OSSummary]: ...

    def equipamento_tem_os_aberta(
        self, equipamento_id: UUID, tenant_id: UUID
    ) -> bool: ...
```

**Adapter default:** `EmptyOSQueryService`.

### Porta `NotificacaoClienteService` (consumida — usada em US-EQP-005 sucatar + US-EQP-006 contatar cliente)

**Localização:** `src/domain/suporte_plataforma/equipamentos/ports/notificacao_cliente_service.py`

**Interface:**
```python
class NotificacaoClienteService(Protocol):
    def notificar_sucatamento_com_cert_vigente(
        self, equipamento_id: UUID, tenant_id: UUID, certificado: CertificadoSummary
    ) -> None: ...

    def notificar_anomalia_recebimento(
        self, recebimento_id: UUID, tenant_id: UUID, anomalia: str
    ) -> None: ...
```

**Adapter default:** `EmptyNotificacaoClienteService` (loga warning, não envia nada — `comunicacao-omnichannel` ainda não existe). Marco 2 entrega evento publicado em `audit_trail.eventos` action=`equipamento.sucateado_com_certificado_vigente` para consumer futuro processar.

### Anti-débito: hook obrigatório

Hook `port-binding-validator.sh` (a criar Wave A Marco 2) bloqueia release pra produção se alguma porta `domain/.../ports/*.py` tiver binding apontando para classe `Empty*` em `settings.production`. Garante que "esqueci de plugar quando módulo nasceu" vire erro de build, não bug silencioso.

---

## Eventos publicados (gravados em `audit_trail.eventos` — fonte única)

> Padrão Marco 1 clientes: nenhuma tabela `EquipamentoEvento` separada. Todo evento vai pra `audit_trail.eventos` (WORM + hash chain — INV-001) com `action` lowercase dot-notation. Relay assíncrono pro bus entra com Procrastinate (Wave A late).

**Envelope padrão (catálogo v8 — `docs/comum/integracoes-inter-modulos.md`):** `event_id`, `tenant_id`, `published_at`, `correlation_id`, `causation_id`, `actor_user_id`, `_schema_version`.

| Action | Quando dispara | Payload mínimo | Consumers |
|---|---|---|---|
| `equipamento.cadastrado` | INSERT | `{ equipamento_id, tag, cliente_id_original_hash, perfil_tenant_no_momento_cadastro }` | Metrologia (pré-aloca padrão), Comercial (visão 360° cliente) |
| `equipamento.editado` | UPDATE direto (pré-cert) | `{ equipamento_id, campos_alterados[] }` | — |
| `equipamento.versao_criada` | Nova `EquipamentoVersao` (pós-cert) | `{ equipamento_id, versao_n, campos_alterados[], motivo_mudanca, assinou_a3 }` | Metrologia (revalida calibrações abertas), Qualidade |
| `equipamento.sucateado` | Status → sucata | `{ equipamento_id, motivo, ts_marcacao }` | Comercial, Operação (cancela OS abertas) |
| `equipamento.sucateado_com_certificado_vigente` | Sucata + cert vigente (US-EQP-005) | `{ equipamento_id, certificado_numero, cert_validade, cliente_atual_id_hash }` | comunicacao-omnichannel (notifica), Comercial |
| `equipamento.transferido` | `cliente_atual_id` muda (US-EQP-004) | `{ equipamento_id, cliente_anterior_id_hash, cliente_novo_id_hash, motivo_categoria, motivo_texto_hash, aceite_origem_ts, aceite_destino_ts }` | Comercial |
| `equipamento.qr_scanned` | Cada scan (escopo A/B/C) | `{ equipamento_id, escopo, ip_hash, user_agent_hash, decisao }` | Analytics (heatmap), Segurança (anomalia geo) |
| `equipamento.qr_reemitido` | Re-emissão QR | `{ equipamento_id, hash_anterior, hash_novo, manter_anterior_ativo }` | — |
| `equipamento.recebido_no_lab` | Entrada física (US-EQP-006) | `{ equipamento_id, recebimento_id, condicao_visual, decisao_apos_anomalia }` | Metrologia, Comercial |
| `equipamento.devolvido_ao_cliente` | Devolução física | `{ equipamento_id, recebimento_id, condicao_devolucao }` | Comercial, Financeiro (gatilho fatura) |
| `equipamento.anomalia_recebimento` | Condição != integro + decisão tomada | `{ equipamento_id, recebimento_id, anomalia, decisao }` | Qualidade (abre NC se grave), Comercial (notifica cliente) |
| `equipamento.orfao_detectado` | Job diário identifica cliente inativo >12m | `{ equipamento_id }` | Suporte tenant, Dashboard |
| `equipamento.extraviado_reportado` | Cliente reporta perda/roubo | `{ equipamento_id, motivo }` | Comercial, Dashboard alerta |

**Não logar em payload:** NS em claro, nome/CPF/CNPJ/e-mail/telefone cliente em claro, localização_fisica. Sempre hashes salgados por tenant ou IDs (que são opacos).

---

## Comandos (camada application)

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `cadastrar_equipamento` | UI/API | cliente existente no mesmo tenant; TAG única no tenant (INV-049); localização sem PII | Equip + QR criados; `perfil_tenant_no_momento_cadastro` congelado; evento `equipamento.cadastrado` |
| `editar_atributo_versionavel` | UI/API | equip existe; motivo enum; A3 RT se classe/faixa em perfil A | Se há cert emitido → nova `EquipamentoVersao`; senão UPDATE direto |
| `sucatear_equipamento` | UI/API | sem OS aberta (porta `OSQueryService`) | Status=sucata; evento `equipamento.sucateado` OU `equipamento.sucateado_com_certificado_vigente` se há cert vigente |
| `transferir_para_cliente` | UI/API | novo_cliente.tenant_id = equip.tenant_id (INV-050); aceite duplo; cedente não bloqueado | `cliente_atual_id` atualizado; evento `equipamento.transferido` |
| `registrar_recebimento` | UI/API (US-EQP-006) | equip existe ou cadastro provisório | `EquipamentoRecebimento` criado; status_fluxo_lab=`recebido_pendente_inspecao`; foto EXIF removido |
| `registrar_devolucao` | UI/API | recebimento existe; status_fluxo_lab in últimas fases | `data_hora_devolucao` setado; `termo_devolucao_assinado_url` registrado |
| `reemitir_qr` | UI/API | equip ativo | Novo QR ativo + anterior `revogado_em = now()` (salvo flag explícita) |
| `marcar_orfao` | Job diário | cliente_atual_id aponta pra cliente inativo > 12m | Status=`orfao_pendente_decisao`; evento |
| `marcar_extraviado` | UI/API | equip ativo; cliente reportou | Status=`extraviado`; alerta se QR escaneado depois |

---

## Spec-as-source (ADR-0007) — snippet futuro

Quando codegen Wave A entrar:
```yaml
entidade: Equipamento
agregado_raiz: true
invariantes: [INV-025, INV-049, INV-051, INV-EQP-LOC-001]
campos:
  - nome: tag
    tipo: string
    unique_por: tenant_id
    imutavel_pos: ["primeira_emissao_certificado"]
    invariante: INV-049
  - nome: numero_serie
    tipo: string
    imutavel_pos: ["primeira_emissao_certificado"]
    invariante: INV-025
  - nome: fabricante
    tipo: string
    imutavel_pos: ["primeira_emissao_certificado"]
    invariante: INV-025
  - nome: modelo
    tipo: string
    versionavel: true
    invariante: INV-025
  - nome: localizacao_fisica
    tipo: string
    max_chars: 200
    validacao: regex_anti_pii
    invariante: INV-EQP-LOC-001
  - nome: perfil_tenant_no_momento_cadastro
    tipo: enum
    valores: [A, B, C, D]
    imutavel: true
```

Gerador (ADR-0007) materializa: model Django + serializer DRF + trigger PG anti-mutation + teste regressão + Pydantic boundary.

## Schema físico

Migration inicial em `src/infrastructure/equipamentos/migrations/0001_initial.py` (Wave A Marco 2 — a criar). Inclui:
- `equipamento` + UNIQUE `(tenant_id, tag)` + RLS policy
- `equipamento_versao` + UNIQUE `(equipamento_id, versao_n)` + RLS
- `equipamento_recebimento` + RLS
- `qrcode` + UNIQUE `hash` + RLS
- Trigger PG `bloquear_update_imutaveis_equipamento` (INV-025) com permissão `# rls-policy: external 0002` se vier em migration separada
- Trigger PG `bloquear_update_revogado_em_para_null` (QR não volta a ser válido)

## Como evolui

- Novo atributo → migration + decidir se é imutável, versionável ou operacional.
- Mudança em INV-025 → ADR obrigatório.
- Novo evento → cataloga em `docs/comum/integracoes-inter-modulos.md` v9+.
- Nova porta → bloqueia release até hook `port-binding-validator` confirmar binding non-Empty em prod.
