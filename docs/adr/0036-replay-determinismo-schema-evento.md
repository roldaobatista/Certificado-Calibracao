---
adr: 0036
titulo: Replay determinístico + versionamento fim-a-fim de schema de evento
owner: roldao
revisado-em: 2026-05-22
status: proposta
proposto-por: agente (auditoria projeto-inteiro 10 lentes — Onda 1 transversal, A-INT-03 + A-INT-10)
revisado-por: tech-lead-saas-regulado
bloqueia-fase: Wave A Marco 4 (calibração — replay forense exigido por cl. 7.11)
depende-de: ADR-0033 (idempotência consumer), ADR-0025 (validação software ISO 17025)
---

# ADR-0036 — Replay determinístico + versionamento de schema

## O QUE

1. Cravar **política única** de versionamento de `_schema_version` no envelope de evento (já obrigatório em integracoes-inter-modulos v8) com regras claras de breaking change + janela de tolerância.
2. Garantir que **replay** de eventos (forense ISO 17025 cl. 7.11 + recall por motor de cálculo) produz **mesmo resultado** — handlers determinísticos por versão de schema.

## PORQUE

- Hoje envelope tem `_schema_version` (v8) mas regras de mudança não estão escritas. Cada Marco está implementando do seu jeito.
- ISO 17025 cl. 7.11.2 (software) exige reprodutibilidade — calibração emitida em 2027 com motor v3.2 precisa ser reproduzível em 2032 mesmo com motor v5 em produção.
- Auditoria Onda 1 A-INT-03 detectou: "versionamento schema fim-a-fim sem política — handler arrisca quebrar produção".
- Auditoria Onda 1 A-INT-10 detectou: "replay determinístico de schemas sem ADR".

## COMO

### Política de `_schema_version`

- Forma: `v1`, `v2`, ... (inteiro). **Sem semver** no envelope (semver fica em libs internas, não em contrato de evento).
- **Breaking change** (campo removido, semântica alterada, tipo mudou) → **nova versão**. Versão anterior **continua publicada por 90 dias** (janela de tolerância).
- **Non-breaking** (campo opcional novo, alargamento de enum em consumer que tolera) → **mesma versão**. Handlers existentes ignoram campos extras.
- **Janela de tolerância:** handler suporta `versao_atual` + `versao_atual - 1` simultaneamente (toleram 2 versões). Versão `-2` cai para `dead_letter_events` (ADR-0033) com motivo `schema_obsoleto`.

### Catálogo de versões — onde mora

`events/catalogo.yaml` (Wave A) gera schemas Python (Pydantic) por versão:

```yaml
events:
  Cliente.Anonimizado:
    v1:
      campos:
        cliente_id: UUID
        cliente_referencia_hash: string
        zona_anonimizacao: Literal["A","B","C"]
        # ...
      breaking_change_em: null
    # v2 entraria aqui quando necessário
```

Hook `bus-envelope-validator` (estendido Onda 4) valida que evento publicado bate com schema da versão declarada.

### Replay determinístico

- Cada handler recebe `(payload, schema_version)` — **não** assume "última versão". Função pura por versão.
- Estado externo (clock, random, ID generation) é injetado — no replay, é mockado a partir do registro original.
- **Versão do motor de cálculo** (INV-CAL-VERSAO-001 — ADR-0025) é parte do payload do evento de calibração. Replay reconstrói com motor `versao_original`, não atual.
- Tabela `replay_executions` registra cada replay forense: `(id, evento_original_id, executor_id, motivo, resultado_hash, executado_em)`.

### Procedimento operacional de breaking change

1. PR adiciona `events/catalogo.yaml` com `v(n+1)` ao lado de `vn`. Marca `vn.breaking_change_em: <data>`.
2. Produtor publica `v(n+1)` (default) **e** `vn` em paralelo por 90 dias (fan-out interno).
3. Consumers atualizados gradualmente — auditor `auditor-llm-correctness` valida handler novo cobrir versão nova.
4. Após 90 dias, produtor para de publicar `vn`. Eventos `vn` ainda em fila caem em `dead_letter_events` se chegarem.

## ID

- **INV-BUS-SCHEMA-001** — todo evento publicado declara `_schema_version: vN` literal no envelope (ADR-0033 envelope obrigatório).
- **INV-BUS-SCHEMA-002** — breaking change exige PR criando `v(N+1)` no `events/catalogo.yaml` + manter `vN` por 90 dias.
- **INV-BUS-SCHEMA-003** — handler de evento implementa pelo menos 2 versões (`atual` e `atual-1`); versão `-2` cai para dead-letter.
- **INV-BUS-REPLAY-001** — replay forense (ISO 17025 cl. 7.11) registra entrada em `replay_executions` com hash do resultado; hash idêntico ao original = passou.

## NON-GOAL

- **Não** prevê migração automática de versão (transformer `vN → v(N+1)`) — agente humano (admin Aferê) faz quando útil.
- **Não** versiona payload de banco interno — só o envelope publicado entre módulos.
- **Não** garante replay de fluxo cross-módulo inteiro automático em V1 — apenas handler individual. Replay end-to-end de saga = V2.

## Consequências

**Boas:** breaking change deixa de ser "torcer" — tem procedimento + ferramenta + janela; replay forense ganha base normativa para auditor CGCRE; gap A-INT-03 + A-INT-10 fechados.

**Ruins:** custo de manter 2 versões em paralelo; PR de breaking change vira "obra" de 90 dias.

## Referências cruzadas

- ADR-0025 (validação software ISO 17025 — origem do requisito replay)
- ADR-0033 (idempotência + dead-letter — destino de eventos obsoletos)
- INV-CAL-VERSAO-001 (versão motor cálculo no certificado)
- `events/catalogo.yaml` (a criar Wave A)
