---
owner: roldao
revisado-em: 2026-05-23
status: stable
diataxis: reference
audiencia: agente
relacionados:
  - REGRAS-INEGOCIAVEIS.md
  - .claude/hooks/seed-anti-pii-real.sh
  - docs/adr/0021-anonimizacao-vs-retencao-regulatoria.md
---

# Dados sintéticos canônicos — fixtures e seeds

> **Pra quê:** auditor LGPD apontou (Onda 0 plano-v2) que agente IA pode colar CPF/CNPJ/e-mail/telefone reais em `tests/fixtures/` por desatenção. Lista canônica + hook `seed-anti-pii-real.sh` previne isso.
>
> **Aplica a:** `tests/fixtures/**`, `**/seeds/**`, `tests/factories/**`, `tests/conftest*.py`, qualquer arquivo `.py`/`.json`/`.csv`/`.yaml` em `tests/` que carregue dados.

## Princípios

1. **Nunca** usar CPF, CNPJ, RG, e-mail real, telefone real, CEP real em fixture/seed.
2. Usar **só** os valores desta lista. Hook `seed-anti-pii-real.sh` reconhece padrões reais (DV válido) e bloqueia commit; reconhece valores desta lista como sintéticos e libera.
3. Se precisar de novo valor sintético, **adicionar nesta lista primeiro**, depois usar.

## CPFs sintéticos (formato canônico — todos com DV inválido propositalmente)

| Valor | Uso recomendado |
|---|---|
| `000.000.000-00` | placeholder genérico |
| `111.111.111-11` | placeholder usuário 1 |
| `222.222.222-22` | placeholder usuário 2 |
| `333.333.333-33` | placeholder usuário 3 |
| `444.444.444-44` | placeholder usuário 4 |
| `555.555.555-55` | placeholder RT |
| `666.666.666-66` | placeholder técnico |
| `777.777.777-77` | placeholder cliente PF 1 |
| `888.888.888-88` | placeholder cliente PF 2 |
| `999.999.999-99` | placeholder cliente PF 3 |
| `123.456.789-09` | CPF do INSS público (mantido por compatibilidade Receita — verificar com hook) |

**Regra:** CPF com DV válido fora desta lista = bloqueio do hook.

## CNPJs sintéticos

| Valor | Uso |
|---|---|
| `00.000.000/0000-00` | placeholder genérico |
| `11.111.111/1111-11` | placeholder PJ 1 |
| `22.222.222/2222-22` | placeholder PJ 2 |
| `33.333.333/3333-33` | placeholder PJ 3 |
| `44.444.444/4444-44` | placeholder PJ 4 |
| `12.345.678/0001-95` | CNPJ exemplo Receita (DV válido — só permitido com tag `# fixture-cnpj-canonico`) |

## CNPJs alfanuméricos (ADR-0017 — vigência jul/2026)

| Valor | Uso |
|---|---|
| `AA.AAA.AAA/AAAA-00` | placeholder alfanumérico genérico |
| `12.ABC.345/01DE-35` | placeholder alfanumérico com dígitos misturados |

## E-mails sintéticos

**Domínios permitidos em fixtures:**

- `@example.com` / `@example.org` / `@example.net` (RFC 2606 — reservados para exemplo)
- `@test` (RFC 2606 TLD reservado)
- `@afere.local` (TLD `.local` — RFC 6762 reservado para mDNS)
- `@invalid` (RFC 2606 TLD reservado)

**Valores canônicos:**

| Valor | Uso |
|---|---|
| `tecnico@example.com` | técnico genérico |
| `gerente@example.com` | gerente genérico |
| `rt@example.com` | responsável técnico |
| `cliente@example.com` | cliente genérico |
| `admin@afere.local` | admin de teste |
| `a@b.com` | placeholder mínimo (legado em testes existentes — manter compatível) |

**Domínios bloqueados (qualquer ocorrência em fixture = bloqueio):**

- `@gmail.com`, `@outlook.com`, `@hotmail.com`, `@yahoo.com`, `@protonmail.com`, `@icloud.com`
- `@balancas-solution.com.br` (cliente dogfooding — usar `@example.com` em teste, mesmo sendo o próprio)
- Qualquer TLD não-reservado fora da lista acima

## Telefones sintéticos

**Formato BR canônico:** `(11) 9XXXX-XXXX` ou `(11) XXXX-XXXX`.

**Valores canônicos:**

| Valor | Uso |
|---|---|
| `(11) 90000-0000` | celular placeholder 1 |
| `(11) 91111-1111` | celular placeholder 2 |
| `(11) 4002-8922` | fixo genérico (referência cultural, sem assinante real) |
| `(00) 00000-0000` | telefone nulo padronizado |

**Bloqueado:** qualquer DDD válido (11..99) com 9 dígitos começando com 9 fora desta lista — risco de bater em assinante real.

## RGs sintéticos

| Valor | Uso |
|---|---|
| `00.000.000-0` | placeholder |
| `11.111.111-1` | placeholder 1 |
| `MG-00.000.000` | placeholder com órgão emissor |

## CEPs sintéticos

| Valor | Uso |
|---|---|
| `00000-000` | placeholder |
| `01310-100` | CEP genérico SP (Av. Paulista — endereço público, sem morador) |
| `99999-999` | placeholder "fim" |

## Datas sintéticas

- Sem regra fixa, mas **preferir** datas no passado dentro da janela 2020-01-01 a `data atual` para evitar conflito com validações de "data futura proibida".
- Para "data futura": usar `2099-12-31` como sentinela canônica.

## Como o hook `seed-anti-pii-real.sh` valida

1. Verifica se o arquivo está em path coberto (`tests/**`, `**/seeds/**`, etc.).
2. Lê o conteúdo e procura padrões reais:
   - CPF com DV válido E fora desta lista → bloqueio.
   - CNPJ com DV válido E fora desta lista → bloqueio.
   - E-mail com domínio fora da allowlist → bloqueio.
   - Telefone com DDD+9 dígitos fora desta lista → bloqueio.
   - RG fora desta lista → bloqueio (regex tolerante).
   - CEP real (com prefixo de cidade conhecida fora da lista) → bloqueio.
3. Allowlist via comentário inline: `# fixture-cpf-canonico`, `# fixture-cnpj-canonico`, etc.
4. Allowlist por arquivo (caso especial): `# seed-anti-pii: skip -- <razão ≥10 chars>`.

## Quando adicionar novo valor

Pull request neste arquivo + revisão do `auditor-conformidade-lgpd`. Adicionar valor sem PR = drift.
