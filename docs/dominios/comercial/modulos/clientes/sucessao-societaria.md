---
owner: Roldão
revisado-em: 2026-05-22
status: draft
modulo: clientes
dominio: comercial
diataxis: explanation
audiencia: agente
---

# Sucessão Societária — Módulo Clientes

> Fluxo de transferência de cadastro + equipamentos + certificados + histórico financeiro entre clientes PJ em eventos societários: **fusão**, **cisão**, **incorporação** (com ou sem CNPJ novo). Origem: Onda 4 saneamento Marco 1 — CRÍTICO C3-CLI.

## Por que existe

Cliente PJ não é estático. Eventos legais reorganizam a base:

- **Fusão:** 2 PJ se unem em 1 nova (Cias A + B → C). Equipamentos/certificados de A e B migram para C.
- **Cisão:** 1 PJ se divide em 2+ (Cia A → A' + B'). Equipamentos são distribuídos por contrato societário.
- **Incorporação:** PJ A incorpora PJ B (B deixa de existir, A absorve patrimônio). Equipamentos de B viram de A.
- **Incorporação com CNPJ novo:** raro, mas acontece em reestruturação grande — sucessor nasce fora do tenant atual e precisa ser provisionado.

Sem fluxo formal, soluções no improviso quebram:
- **Certificado emitido para B** (cliente fundido) precisa apontar para sucessor C **mas preservar quem foi o tomador na data de emissão** (ISO 17025 cl. 7.8 + Receita Federal — auditor fiscal vê NF emitida com CNPJ B; sistema diz "B não existe mais" = inconsistência).
- **Equipamento físico** (balança, termômetro) é da mesma máquina — não muda dono pela operação societária, muda só o CNPJ no registro.
- **Histórico financeiro** (títulos a receber emitidos contra B) segue em B até liquidação; novos títulos vão pra sucessor.

## Decisão de design

### Entidade `SucessaoSocietaria`

```python
class SucessaoSocietaria:
    id: UUID
    tenant_id: UUID
    predecessor_cliente_id: UUID    # quem desapareceu/cindiu (FK Cliente, on_delete=PROTECT)
    sucessor_cliente_id: UUID       # quem absorve/herda (FK Cliente, on_delete=PROTECT)
    tipo: enum {FUSAO, CISAO, INCORPORACAO, INCORPORACAO_CNPJ_NOVO}
    data_evento: date               # data do ato societário (NÃO data de inserção no sistema)
    fundamento_legal: text          # "Lei 6.404/76 art. 228" ou similar (≥10 chars)
    ato_societario_anexo_id: UUID   # FK AnexoDocumento (escritura de fusão, contrato de cisão, ata de incorporação)
    ato_aprovacao_id: UUID          # FK Usuario — quem do tenant aprovou a operação no sistema
    criado_em: datetime
    criado_por: UUID
    observacoes: text NULL
```

Pode existir N `SucessaoSocietaria` para o mesmo `predecessor_cliente_id` (cisão gera múltiplos sucessores; cada par predecessor→sucessor = 1 linha).

### Relação com `cliente_canonico_id` (INV-CLI-001)

`SucessaoSocietaria` **NÃO substitui** `cliente_canonico_id`. Diferença:

| Cenário | Mecanismo | Justificativa |
|---|---|---|
| Cadastro duplicado por erro (dedup) | `cliente_canonico_id` aponta para vencedor; perdedor `deletado_em` | INV-CLI-001 + US-CLI-005 dedup |
| Sucessão societária real (fusão/cisão/incorporação) | `SucessaoSocietaria` registra evento; **predecessor NÃO é deletado** (`deletado_em IS NULL`) — fica em estado `ARQUIVADO_POR_SUCESSAO`; `cliente_canonico_id` continua apontando para si mesmo | Predecessor era entidade fiscal real; auditor Receita precisa ler "cliente B existia até 2026-08-15"; deletar = fraude documental |

### Fluxos por tipo

#### 1. Fusão (2 → 1)

```
predecessor A + predecessor B → sucessor C (novo cadastro)
```

Passos no sistema:
1. Usuário cadastra C como cliente novo (estado `ATIVO`).
2. Wizard "registrar fusão" pede: predecessores (A, B), data evento, ato societário (PDF), fundamento legal.
3. Sistema cria 2 linhas em `SucessaoSocietaria` (A→C, B→C).
4. A.estado = B.estado = `ARQUIVADO_POR_SUCESSAO`.
5. Equipamentos físicos: para cada Equipamento de A/B, criar evento `Equipamento.SucessaoSocietaria(de=B, para=C, sucessao_id=...)`. `Equipamento.cliente_atual_id` atualiza para C (INV-050 mantida — só dentro do mesmo tenant). **Certificados emitidos preservam snapshot** do cliente original (INV-025 + ADR-0021 Zona B).
6. Títulos financeiros: títulos em aberto de A/B podem ser repactuados para C via wizard separado (módulo `contas-receber` — fora desta ADR); títulos quitados ficam históricos com cliente original.
7. Publica `Cliente.SucessaoSocietariaRegistrada(predecessor_ids=[A,B], sucessor_id=C, tipo=FUSAO, sucessao_ids=[...])` para consumers (operação, financeiro, BI).

#### 2. Cisão (1 → 2+)

```
predecessor A → sucessor A' + sucessor B'
```

Passos:
1. Usuário cadastra A' e B' (A' pode reusar mesmo CNPJ se cisão parcial mantém raiz; B' é CNPJ novo).
2. Wizard "registrar cisão" pede: predecessor (A), sucessores ([A', B']), data evento, ato societário, **mapeamento equipamento→sucessor** (escolha equipamento por equipamento ou em lote por TAG/setor).
3. Sistema cria N linhas `SucessaoSocietaria` (A→A', A→B', ...).
4. A.estado = `ARQUIVADO_POR_SUCESSAO` (se cisão total) ou permanece `ATIVO` (se cisão parcial — A continua existindo).
5. Equipamentos: cada um migra para o sucessor escolhido (`Equipamento.SucessaoSocietaria`).
6. Títulos: fica com A até o usuário transferir manualmente (não há regra automática — exige contrato societário pra distribuir passivo).

#### 3. Incorporação (A absorve B)

```
sucessor A (mantém CNPJ) ← predecessor B (desaparece)
```

Passos:
1. A já existe (não cria novo). B existe.
2. Wizard "registrar incorporação" pede: incorporada (B), incorporadora (A), data evento, ato.
3. Cria 1 linha `SucessaoSocietaria(B → A, tipo=INCORPORACAO)`.
4. B.estado = `ARQUIVADO_POR_SUCESSAO`.
5. Equipamentos de B migram para A.
6. Títulos: idem cisão (manual).

#### 4. Incorporação com CNPJ novo (raro)

```
predecessor A + predecessor B → sucessor C com CNPJ inédito (não existe no tenant)
```

Diferença vs fusão simples: sucessor C **não existe** no tenant antes do evento. Pode ser que C esteja sob **outro tenant** (Cia comprou outra Cia e quer consolidar no tenant do comprador).

Passos:
1. Se C está fora do tenant atual: **bloqueio hard** — sistema não permite sucessão entre tenants (INV-TENANT-001/002 + INV-CLI-SUCESSAO-001). Caminho: provisionar C no tenant correto, depois fazer migração assistida via canal suporte (procedimento separado — fora desta ADR).
2. Se C estará no mesmo tenant: cadastra C, segue fluxo "Fusão" §1.

### Invariantes (REGRAS-INEGOCIAVEIS.md)

- **INV-CLI-SUCESSAO-001:** Sucessão societária só ocorre **dentro do mesmo tenant**. Tentativa cross-tenant retorna 422 genérico (sem oracle). Equipamento físico migra sempre (transferência completa de `Equipamento.cliente_atual_id`); certificados imutáveis mantêm snapshot do predecessor (INV-025 + ADR-0021 Zona B).
- **INV-CLI-SUCESSAO-002:** Predecessor em sucessão societária **NÃO pode ser hard-deleted nem anonimizado** (LGPD art. 16 III + Receita 5 anos). Estado `ARQUIVADO_POR_SUCESSAO` é terminal (não volta para `ATIVO`).
- **INV-CLI-SUCESSAO-003:** `SucessaoSocietaria` exige `ato_societario_anexo_id NOT NULL` + `fundamento_legal` com ≥10 chars. Sem evidência documental, registro bloqueia.

### Eventos publicados

| Evento | Payload | Consumidores |
|---|---|---|
| `Cliente.SucessaoSocietariaRegistrada` | `{predecessor_ids[], sucessor_id, tipo, data_evento, sucessao_ids[]}` | equipamentos, contas-receber, contas-pagar, certificados, BI |
| `Equipamento.SucessaoSocietaria` | `{equipamento_id, de_cliente_id, para_cliente_id, sucessao_id}` | calibracao, os, certificados (snapshot) |

(detalhe de payload completo entra no catálogo de eventos quando Onda 1 fechar — esta doc só declara existência)

### UI

Tela `/clientes/{id}/sucessao-societaria`:
- Lista de sucessões em que cliente participa (como predecessor ou sucessor).
- Botão "registrar sucessão" abre wizard com 3 passos (tipo → predecessores/sucessores → ato societário + confirmação).
- Visualização da árvore: predecessor → sucessor com data + tipo + link para ato.

### Auditoria

Toda mudança grava em `audit_trail` com `causation_id` ligando à `SucessaoSocietaria.id`. Auditor fiscal/CGCRE consulta trilha completa.

---

## Non-goals

- **Sucessão entre tenants** — bloqueio hard. Migração entre tenants é procedimento administrativo (canal suporte Aferê + assinatura A3 dono CNPJ).
- **Transferência automática de títulos a receber/pagar** — fora desta doc. Módulo `financeiro/*` decide.
- **Reversão de sucessão** — ato societário é imutável; estado `ARQUIVADO_POR_SUCESSAO` é terminal.
- **Sucessão para PF** (transferência de equipamento de PJ pra sócio que virou autônomo) — fora do MVP. Workaround: cadastra PF, transfere equipamento manualmente.

---

## Referências

- Lei 6.404/76 art. 227-229 (incorporação, fusão, cisão)
- INV-CLI-001 (cliente_canonico_id) — REGRAS-INEGOCIAVEIS.md
- INV-025 (equipamento imutável pós-certificado) — REGRAS-INEGOCIAVEIS.md
- INV-050 (transferência equipamento same-tenant) — REGRAS-INEGOCIAVEIS.md
- ADR-0021 (anonimização Zona A/B/C)
- ADR-0032 (FK cross-módulo + anonimização)
