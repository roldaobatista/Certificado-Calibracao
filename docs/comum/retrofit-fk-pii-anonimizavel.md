---
owner: roldao
revisado-em: 2026-05-22
status: stable
finalidade: lista 8 FKs cross-módulo a entidades PII que devem migrar para o par `ReferenciaPIIAnonimizavel` (ADR-0032).
relacionados:
  - ADR-0032 (FK cross-módulo + anonimização)
  - ADR-0021 (anonimização vs retenção)
  - ADR-0030 (vigência canônica)
  - `docs/comum/modelo-de-dominio-transversal.md` §4
---

# Retrofit FK PII Anonimizável

> **Pra quê:** ADR-0032 define que toda FK cross-módulo para entidade PII (`Cliente`, `Usuario`, `ResponsavelTecnicoTenant`) em entidade Padrão B do ADR-0031 usa par `(uuid_atual_id NULL, hash_original NOT NULL)`. Marcos anteriores criaram FK simples — esta doc lista as 8 FKs que precisam virar para o padrão novo, com plano por onda.

---

## Tabela das 8 FKs alvo

| # | Origem (módulo.entidade.campo) | FK aponta para | Status atual | Padrão soft-delete da origem | Onda retrofit | Justificativa |
|---|---|---|---|---|---|---|
| 1 | `metrologia/equipamentos.Equipamento.cliente_atual_id` | `comercial/clientes.Cliente` | `parcial` — Marco 2 tem FK simples + ON DELETE PROTECT | A (estado-máquina) | Marco 3 onda inicial | Equipamento pode mudar de cliente (transferência INV-050); precisa preservar hash do dono original na época de cada cert emitido. |
| 2 | `operacao/os.OS.cliente_id` | `Cliente` | `inexistente` (Marco 3 nasce com canônico) | A (estado-máquina) | Marco 3 P4 | OS é Padrão A; cliente atual é operacional. Hash preserva quem solicitou (probatório). |
| 3 | `fiscal.NotaFiscal.cliente_id` | `Cliente` | `inexistente` (Wave A) | B (revogado_em — NF imutável) | Wave A `fiscal` | NF é WORM Receita 5 anos — Zona B retenção. FK precisa do par. |
| 4 | `financeiro/contas-receber.Cobranca.cliente_id` | `Cliente` | `inexistente` (Wave A) | B (Cobranca lançada é imutável) | Wave A `financeiro` | Receita 5 anos + INV-026 (preço não retroage). Hash preserva pagador na época. |
| 5 | `comunicacao-omnichannel.Comunicacao.destinatario_id` | `Cliente` (ou `Usuario`/`Contato`) | `inexistente` (Wave B) | C (deletado_em) — config mutável | Wave B `comunicacao-omnichannel` | Comunicação enviada vira registro probatório (LGPD opt-in/opt-out). Hash necessário pós-anonimização. |
| 6 | `audit_trail.Audit.actor_id` | `Usuario` | `parcial` — Marco 2 tem `actor_id` direto + audit imutável | B (WORM por construção) | Wave A `audit` retrofit | Trilha imutável tem que sobreviver a anonimização do usuário (LGPD ANPD pode auditar 25 anos depois). |
| 7 | `financeiro/comissoes.Comissao.vendedor_id` | `Usuario` (colaborador) | `inexistente` (Wave A) | B (Comissão calculada é imutável fiscal) | Wave A `comissoes` | Vendedor pode sair da empresa e exercer art. 18 VI; comissão fica probatória 5 anos Receita. |
| 8 | `metrologia/equipamentos.RecebimentoProvisorio.cliente_id_provisorio` | `Cliente` (tenant suspeita) | `parcial` — Marco 2 (INV-EQP-PROV-001) tem campo + audit | A (estado-máquina; promoção a Equipamento) | Marco 3 onda saneamento | Cliente provisório pode nunca virar definitivo; LGPD permite eliminação Zona A. Hash necessário para audit do recebimento. |

---

## Padrão de migração

```python
# Padrão ADR-0032 §2 — exemplo para origem #1 (Equipamento.cliente_atual)
operations = [
    # 1. adicionar colunas pareadas
    migrations.AddField('Equipamento', 'cliente_referencia_hash',
        models.CharField(max_length=128, null=True)),
    migrations.AddField('Equipamento', 'cliente_referencia_key_id',
        models.CharField(max_length=32, null=True)),

    # 2. backfill com KMS key vigente
    migrations.RunPython(backfill_equipamento_hash, reverse_code=migrations.RunPython.noop),

    # 3. NOT NULL + CHECK
    migrations.AlterField('Equipamento', 'cliente_referencia_hash',
        models.CharField(max_length=128, null=False)),
    migrations.AlterField('Equipamento', 'cliente_referencia_key_id',
        models.CharField(max_length=32, null=False)),

    # 4. mudar on_delete de PROTECT para SET_NULL
    migrations.AlterField('Equipamento', 'cliente_atual',
        models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True)),
]
```

## Critério de saída por FK

- Migration aplicada (2 colunas + CHECK + on_delete=SET_NULL ou conforme padrão).
- Hook `fk-pii-anonimizavel-check.sh` passa (Onda 4).
- Suite anti-regressão: criar entidade → hash preenchido; anonimizar cliente (Zona A) → uuid_atual_id NULL + hash preservado; query operacional por hash funciona; consumer registra `acessos_dados_cliente` com motivo `anonimizacao_propagada` (INV-ANON-004).

## Mapeamento Zona ADR-0021 → política

| Zona | Ação no `Cliente.Anonimizado` recebido | Origens afetadas (FKs) |
|---|---|---|
| A — eliminação efetiva | `uuid_atual_id = NULL`, preservar hash | #1, #2, #5 (operacionais) |
| B — anonimização in-place | mantém uuid (linha do Cliente preservada com campos PII zerados); hash continua válido | #3, #4, #6, #7 (WORM) |
| C — anonimização campo-a-campo | uuid preservado; hash idem; campos individuais zerados conforme `campos_anonimizados[]` | #5 (parcial), #8 |

---

## Dependências cruzadas

- Hook `fk-pii-anonimizavel-check.sh` (Onda 4) — bloqueia `ForeignKey(Cliente)` em entidade Padrão B sem o par hash+key_id. Allow via `# fk-pii-anonimizavel: skip -- <razão>`.
- Evento `Cliente.Anonimizado` (catálogo v11 — Onda 3, ver `docs/comum/integracoes-inter-modulos.md`).
- KMS `pii_referencia_key_id` versionada (GATE-1 F-A — ciclo chave PII anual).
