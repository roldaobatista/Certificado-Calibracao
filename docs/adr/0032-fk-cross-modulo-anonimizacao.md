---
adr: 0032
titulo: FK cross-módulo + VO ReferenciaPIIAnonimizavel (propagação Zona A/B/C ADR-0021)
status: aceito
data: 2026-05-23
proposto-por: agente (auditoria projeto-inteiro 10 lentes — lente 10 modelo dados C-DT-04 + lente 1 ALTO #1)
revisado-por: tech-lead-saas-regulado + advogado-saas-regulado
aceito-em: 2026-05-23 (Onda 2 saneamento pré-Marco 3 OS)
bloqueia-fase: Wave A Marco 3 (`os`) + retrofit Equipamento/Certificado pra propagação Zona ADR-0021
depende-de: ADR-0021 (anonimização vs retenção), ADR-0030 (vigência canônica)
---

# ADR-0032 — FK cross-módulo + anonimização propagável

## Contexto

ADR-0021 (anonimização vs retenção) define 3 zonas para entidades que carregam PII:

- **Zona A** — eliminação efetiva possível (LGPD art. 18 VI) sem prejuízo regulatório.
- **Zona B** — anonimização in-place obrigatória (retenção regulatória Receita/ISO impede eliminação).
- **Zona C** — anonimização campo-a-campo (alguns campos podem ser anonimizados, outros não).

Matriz `retencao-matriz.md` lista 27 categorias de dado com prazo + ação fim-de-prazo. Mas auditoria 2026-05-23 (lente 10 C-DT-04) detectou:

1. **`certificados/models.py:66-70`** — `Certificado.equipamento = FK(Equipamento, on_delete=PROTECT)`. Cliente referenciado indiretamente via `Equipamento.cliente_atual_id`. Quando LGPD pedir hard-delete cliente (Zona A), `PROTECT` impede ou cascateia incorretamente.
2. **Nenhuma migration cria `cliente_id_original_hash`** em `Equipamento`/`Certificado` (matriz retenção §2 prevê — drift).
3. **Não há evento `Cliente.Anonimizado`** no catálogo v10 — anonimização não propaga para módulos que carregam ref ao cliente.

Cenário concreto que falha hoje: Marco 4 emite `Certificado(cliente_id=X, equipamento_id=Y)`. Cliente X exerce art. 18 VI → modelo `Cliente` é anonimizado (Zona A). `Certificado.cliente_id` continua apontando para registro vazio; `Equipamento.cliente_atual_id` idem; matriz §2 diz "deve restar `cliente_id_original_hash`" — mas o campo não existe.

## Decisão

### Parte 1 — VO `ReferenciaPIIAnonimizavel`

**`src/domain/shared/value_objects.py` ganha VO:**

```python
@dataclass(frozen=True)
class ReferenciaPIIAnonimizavel:
    """Referência a entidade PII que pode ser anonimizada/eliminada.

    Carrega 2 campos pareados:
    - uuid_atual_id: FK viva enquanto entidade existe; NULL se entidade foi eliminada (Zona A).
    - hash_original: HMAC-tenant(uuid_no_momento_da_referencia), NOT NULL desde a criação.

    Permite:
    - Query operacional: JOIN via uuid_atual_id (rápido).
    - Query auditoria/regulatória: agrupar por hash_original (preservado mesmo pós-eliminação).
    - Reconciliação: "qual cliente original esse cert foi emitido a?" via hash.

    Não exposto em endpoints públicos. Hash usa salt por tenant (mesma estratégia
    INV-AUTHZ-001 — KMS-managed via `pii_referencia_key_id`).
    """

    uuid_atual_id: UUID | None
    hash_original: str

    @classmethod
    def from_uuid(cls, uuid: UUID, tenant_id: UUID, key_id: str) -> "ReferenciaPIIAnonimizavel":
        from src.domain.shared.pii_hash import hash_referencia
        h = hash_referencia(uuid=uuid, tenant_id=tenant_id, key_id=key_id)
        return cls(uuid_atual_id=uuid, hash_original=h)

    def eliminada(self) -> bool:
        return self.uuid_atual_id is None
```

### Parte 2 — Modelo Django

Toda FK cross-módulo para entidade Zona A/B/C **deixa de ser FK simples** e vira par:

```python
# ANTES (drift):
class Certificado(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)

# DEPOIS (ADR-0032):
class Certificado(models.Model):
    cliente_atual = models.ForeignKey(
        Cliente, on_delete=models.SET_NULL, null=True,
        related_name="certificados_emitidos",
    )
    cliente_referencia_hash = models.CharField(
        max_length=128, null=False,  # HMAC hex
        help_text="ReferenciaPIIAnonimizavel.hash_original — preserva identidade pós-anonimização",
    )
    cliente_referencia_key_id = models.CharField(
        max_length=32, null=False,
        help_text="key_id do HMAC pra rotação ADR-0030 ciclo chave PII",
    )
    # ... demais campos
```

### Parte 3 — Evento `Cliente.Anonimizado` (catálogo v11)

Schema v1 (Onda 3 implementa):

```yaml
event_name: "Cliente.Anonimizado"
_schema_version: 1
payload:
  cliente_id: UUID  # uuid_atual_id que será apagado (Zona A) ou anonimizado (Zona B/C)
  cliente_referencia_hash: string  # HMAC original — consumers usam pra reconciliação
  zona_anonimizacao: "A" | "B" | "C"
  campos_anonimizados: list[string]  # ['nome', 'cpf', 'email', 'telefone'] — Zona C usa subset
  campos_eliminados: list[string]  # Zona A enche aqui
  motivo: string  # "art_18_vi" | "retencao_expirada" | "consentimento_revogado"
  ocorrido_em: datetime
```

**Consumers:**
- `metrologia/equipamentos` — atualizar `Equipamento.cliente_atual_id` para NULL se Zona A; preservar `cliente_referencia_hash`.
- `metrologia/certificados` — não muta certificado (INV-CER-WORM-001 — imutável); apenas registra evento `acessos_dados_cliente` com motivo "anonimização propagada".
- `operacao/os` — fechar OSes em andamento + transição para `estado='cliente_anonimizado'`; bloquear novas OS pra esse cliente_id.
- `financeiro/contas-receber` — manter `Cobranca` (Receita 5 anos Zona B) mas anonimizar campos `nome_pagador`, `email`, `telefone` (Zona C).
- `comercial/comunicacao-omnichannel` (Wave B) — limpar contatos.

### Parte 4 — Matriz retenção retrofitada (Onda 2)

`docs/conformidade/comum/retencao-matriz.md` ganha coluna estruturada `Zona ADR-0021 (A|B|C)` + `Ação física` (eliminação | anonimização in-place | crypto-shredding | manter) por cada uma das 27+ categorias. (Trabalho Onda 2.)

## Regras invariantes

- **INV-ANON-001:** Toda FK cross-módulo para `Cliente`/`Usuario`/`ResponsavelTecnicoTenant` em entidade regulatória (Padrão B do ADR-0031) **deve** usar VO `ReferenciaPIIAnonimizavel` (par hash+uuid). Hook valida.
- **INV-ANON-002:** Evento `Cliente.Anonimizado` **deve** ser publicado em transação atômica com mutação no `Cliente` (transactional outbox — Onda 3).
- **INV-ANON-003:** Hash `cliente_referencia_hash` usa KMS com `key_id` versionado (rotação anual GATE-1 F-A).
- **INV-ANON-004:** Consumer que recebeu `Cliente.Anonimizado` e mutou seu estado **deve** registrar audit em `acessos_dados_cliente` com motivo `anonimizacao_propagada`.

## Hook validador

`fk-pii-anonimizavel-check.sh` (Onda 4) — bloqueia `models.ForeignKey(Cliente)` ou `models.ForeignKey(Usuario)` em entidade decorada com `@padrao_soft_delete("B")` (ADR-0031) sem o par `*_referencia_hash` + `*_referencia_key_id`. Allow via `# fk-pii-anonimizavel: skip -- <razão>`.

## Alternativas

- **CASCADE em FK** — rejeitado: viola INV-CER-WORM-001 (cert imutável); apaga histórico regulatório.
- **Soft-delete `Cliente` (Padrão C apenas)** — insuficiente: não atende art. 18 VI nem permite eliminação efetiva Zona A.
- **Não modelar — usar ad-hoc por módulo** — rejeitado: drift garantido (já está acontecendo no `certificados`).
- **`uuid_atual_id` NOT NULL** — rejeitado: Zona A exige NULL pra eliminação efetiva.

## Consequências

**Boas:** Marco 3 OS, Marco 4 calibração, certificados Wave A nascem com FKs anonimizáveis; matriz retenção fica acionável; consumers reagem coerentemente; advogado humano valida fluxo cross-módulo.

**Ruins:** migration retrofit em `Certificado` (Marco 2 — alterar FK + adicionar 2 colunas); cada consumer precisa handler `Cliente.Anonimizado` (Onda 3); KMS key rotation (GATE-1) vira pré-requisito mais visível.

## Status

Aceita 2026-05-23. VO + migration `certificados/00XX_fk_anonimizavel.py` + retrofit matriz em Onda 2; evento + consumers em Onda 3; hook em Onda 4.
