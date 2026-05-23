---
owner: Roldão
revisado-em: 2026-05-23
status: draft
modulo: padroes
dominio: metrologia
versao: 1
---

# Modelo de domínio — Padrões metrológicos do laboratório

> **v1 (draft 2026-05-23):** criado na Onda 5 saneamento. ADR-0040
> separa padrão de equipamento do cliente. VOs metrológicos
> existentes em `src/domain/metrologia/value_objects.py` (Grandeza,
> FaixaMedicao, IncertezaExpandida) reusados.

## Entidades

### PadraoMetrologico (agregado raiz)

**Atributos imutáveis após primeiro uso em calibração:**
- `numero_serie` (UNIQUE por tenant — INV-PAD-001)
- `fabricante`
- `modelo`

**Atributos versionáveis (UPDATE direto até primeiro uso; depois cria
`PadraoVersao` espelhando padrão `EquipamentoVersao` do M2):**
- `descricao` (≤500 chars, regex anti-PII)
- `localizacao_lab` (≤200 chars, regex anti-PII)
- `intervalo_recal_meses` (configurável por classe)

**Atributos operacionais (mutáveis controlados):**
- `grandezas: list[Grandeza]` (≥1 — VO existente)
- `faixas: list[FaixaMedicao]` (≥1 — VO existente)
- `incertezas_certificado: list[IncertezaExpandida]` (≥1; só atualiza
  via evento `padrao.recal_externo_concluido` — INV-PAD-006)
- `vinculacao: enum {BIPM, INMETRO, RBC, INTERNACIONAL}` (cadeia ao SI)
- `cert_externo_storage_key: string` (chave opaca `FotoStorageService`;
  EXIF/metadata strip; rotacionada a cada recal)
- `validade_certificado_rastreabilidade: date`
- `proximo_recal: date` (computado = `validade - margem_seguranca_dias`;
  margem default 30 dias por classe)
- `classe: enum {E1, E2, F1, F2, M1, M2, M3, OUTRA}` (OIML R111 para
  massa; análogos por grandeza)
- `estado: enum {EM_USO, EM_RECAL_EXTERNO, INTERCOMPARACAO_PT_EM_CURSO,
  BAIXADO, SUCATEADO}`
- `vigencia_inicio: timestamp` + `revogado_em: timestamp NULL` +
  `motivo_revogacao: text NULL ≥10 chars` (ADR-0030 — INV-VIG-001..004)

**Padrão soft-delete: B — revogado_em (WORM)** (ADR-0031;
INV-SOFT-002). DELETE direto bloqueado por trigger PG.

**Ciclo de vida:** criada em `EM_USO` → vai e volta entre `EM_USO` ↔
`EM_RECAL_EXTERNO` ↔ `INTERCOMPARACAO_PT_EM_CURSO` → terminal em
`BAIXADO` (reversível com avaliação técnica) ou `SUCATEADO` (terminal
duro).

**Invariantes:** INV-PAD-001..006, INV-VIG-001..004, INV-SOFT-001/002,
INV-021..023, INV-TENANT-001.

### RecalExternoPadrao (entidade filha)

- `padrao_id: FK`
- `enviado_em: timestamp`
- `lab_externo: string` (nome do lab destinatário — sem PII direta)
- `responsavel_envio: usuario_id` (audit)
- `numero_protocolo_lab_externo: string NULL`
- `retornado_em: timestamp NULL`
- `cert_externo_novo_storage_key: string NULL` (chave opaca)
- `incertezas_novas: list[IncertezaExpandida] NULL`
- `validade_nova: date NULL`
- `valor_convencional_novo: Decimal NULL`
- `status: enum {ENVIADO, RETORNADO, EXTRAVIADO_NO_TRANSPORTE,
  RECUSADO_PELO_LAB}`

**Imutável após `retornado_em IS NOT NULL`.** Evento
`padrao.recal_externo_concluido` dispara update transacional em
`PadraoMetrologico.incertezas_certificado` +
`validade_certificado_rastreabilidade`.

### VerificacaoIntermediaria (entidade filha — INV-022)

- `padrao_id: FK`
- `data_vi: timestamp`
- `executor: usuario_id`
- `metodo: text` (procedimento aplicado — anti-PII; ≤500 chars)
- `resultado: enum {APROVADO, REPROVADO, INCONCLUSIVO}`
- `desvio_observado: Decimal NULL` (em unidade do padrão)
- `acao_corretiva: text NULL` (≥30 chars se REPROVADO)
- `criado_em: timestamp` (imutável)

**WORM** (INV-CAL-WORM-001 estendido).

### IntercomparacaoPT (entidade filha — INV-023, perfil A)

- `padrao_id: FK`
- `lab_organizador: string`
- `protocolo: string`
- `data_inicio: timestamp`
- `data_resultado: timestamp NULL`
- `resultado: enum {APROVADO, REJEITADO, SOB_REVISAO} NULL`
- `zeta_score: Decimal NULL`
- `relatorio_pt_storage_key: string NULL`
- `nao_conformidade_id: FK NULL` (referência ao módulo `nao-conformidades`
  se REJEITADO — Wave B+)

**WORM.**

## Agregados (DDD)

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| PadraoMetrologico | RecalExternoPadrao, VerificacaoIntermediaria, IntercomparacaoPT | INV-PAD-001..006, INV-021..023, INV-VIG-001..004, INV-SOFT-002 |

## Portas consumidas e expostas

### Porta exposta `PadraoMetrologicoQueryService` (consumida por Marco 4)

```python
class PadraoMetrologicoQueryService(Protocol):
    def buscar_disponivel_para_calibracao(
        self, tenant_id: UUID, grandeza: Grandeza, faixa: FaixaMedicao
    ) -> list[PadraoSummary]: ...

    def snapshot_para_uso(
        self, padrao_id: UUID, tenant_id: UUID, em_data: datetime
    ) -> PadraoUsadoSnapshot: ...

    def padrao_bloqueado_para_uso(
        self, padrao_id: UUID, tenant_id: UUID
    ) -> tuple[bool, str | None]: ...
```

Retorna VO imutável `PadraoUsadoSnapshot` com todos os campos do
padrão no momento da seleção (INV-CAL-SNAP-001). Marco 4
(`calibracao`) congela isso em `PadraoUsado.snapshot_padrao_json`.

### Adapter default Wave A inicial

`EmptyPadraoMetrologicoQueryService` retorna `[]` / lança
`NotImplementedError` em `snapshot_para_uso` — bloqueia release até
`padroes` cravar.

## Eventos publicados (em `audit_trail.eventos`)

| Action | Payload mínimo | Consumers |
|---|---|---|
| `padrao.cadastrado` | `{padrao_id, numero_serie_hash, vinculacao, classe, grandezas, validade}` | Metrologia, Dashboard CGCRE |
| `padrao.recal_externo_iniciado` | `{padrao_id, lab_externo, enviado_em, protocolo}` | Dashboard recal, Comercial (gera OS interna) |
| `padrao.recal_externo_concluido` | `{padrao_id, validade_anterior, validade_nova, valor_convencional_novo}` | Marco 4 (revalida calibrações abertas), Dashboard |
| `padrao.verificacao_intermediaria_registrada` | `{padrao_id, resultado, desvio_observado}` | Marco 4 (bloqueia se REPROVADO), Qualidade |
| `padrao.intercomparacao_iniciada` | `{padrao_id, lab_organizador, protocolo, data_inicio}` | Dashboard PT |
| `padrao.intercomparacao_concluida` | `{padrao_id, resultado, zeta_score}` | Marco 4, Qualidade (abre NC se REJEITADO) |
| `padrao.baixado` | `{padrao_id, motivo, tipo}` | Marco 4 (revoga seleção em calibrações abertas) |
| `padrao.sucateado` | `{padrao_id, motivo}` | Marco 4 |

**Não logar em payload:** localização_lab em claro; cert externo
PDF em claro; responsável envio em UUID cru (só hash).

## Schema físico

Migration inicial em `src/infrastructure/metrologia/padroes/migrations/0001_initial.py`
(Wave A — a criar). Inclui:
- `padrao_metrologico` + UNIQUE `(tenant_id, numero_serie)` + RLS
- `recal_externo_padrao` + RLS
- `verificacao_intermediaria` + RLS + trigger WORM
- `intercomparacao_pt` + RLS + trigger WORM
- Trigger PG `padrao_incertezas_so_via_recal_evento` (INV-PAD-006)
- Trigger PG `padrao_block_delete` (INV-SOFT-002)

## Como evolui

- Nova grandeza/faixa → atualização do VO em
  `src/domain/metrologia/value_objects.py` + revisão `consultor-rbc`.
- Nova vinculação (ex: ANM) → ADR.
- Nova classe → atualização enum + revisão `consultor-rbc`.
