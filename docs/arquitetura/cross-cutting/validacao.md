---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Cross-cutting — validação de entrada

> **Pra quê:** validação acontece em 3 camadas (UI, API, domínio). Mensagens em PT-BR sempre.

---

## 3 camadas

### Camada 1 — UI (HTMX/Flutter)
- Validação imediata (campo obrigatório, formato CPF, range numérico)
- Feedback em PT-BR no próprio campo
- Bloqueia submit se inválido

### Camada 2 — API (DRF serializer + Pydantic)
- Validação após chegada na API
- Reflete regras da camada 1 + regras que não cabem em UI (e.g., unicidade)
- Retorna 400 + mensagens estruturadas:
```json
{"erros": {"cpf": "CPF inválido", "data_emissao": "Data não pode ser futura"}}
```

### Camada 3 — Domínio
- Regras de negócio que não cabem em validação simples
- Levanta `DomainError` (vira 422)
- Exemplos: "certificado só pode ser emitido se OS está fechada"

---

## Princípios

1. **Nunca confiar só na camada 1** — atacante bypassa UI
2. **Nunca repetir regra entre 2 e 3** — regra fica em um lugar; outra camada usa
3. **Mensagens sempre em PT-BR** — Roldão é o leitor final
4. **Erros estruturados** — JSON com `campo: mensagem`, nunca texto livre

---

## Stack (quando código existir)

| Camada | Lib |
|--------|-----|
| UI web | Atributos HTML + Alpine.js + HTMX hx-validate |
| UI mobile | Riverpod + form_validator |
| API | DRF `Serializer` + Pydantic v2 (alguns endpoints) |
| Domínio | Pydantic v2 + custom validators |

---

## Validação de tipos brasileiros

| Tipo | Lib |
|------|-----|
| CPF | `validate-docbr` (Python) + lib equivalente Flutter |
| CNPJ | **Implementação própria** no VO `CNPJ` (`src/domain/shared/value_objects.py`) baseada nos códigos de referência Serpro — aceita alfanumérico a partir de jul/2026 (IN RFB nº 2.229/2024). Ver ADR-0017. `validate-docbr` só quando lançar suporte estável ao novo formato. |
| CEP | `pycep-correios` ou regex + lookup ViaCEP |
| Telefone BR | `phonenumbers` |
| Valor monetário | `decimal.Decimal` + tipo customizado |
| Data BR | dd/mm/aaaa entrada + ISO 8601 internamente |
| NCM | tabela validada |
| Inscrição estadual | tabela por estado |

---

## Validação multi-tenant

Toda entrada que referencia FK de outro registro precisa **validar que o registro pertence ao tenant ativo**:

```python
# ❌ ruim
cliente_id = data["cliente_id"]
cliente = Cliente.objects.get(id=cliente_id)

# ✅ bom (RLS já filtra, mas explícito é melhor)
cliente = Cliente.objects.get(id=cliente_id, tenant=request.tenant)
```

Auditor Segurança verifica.

---

## Sanitização (separada de validação)

- **HTML entrada** (campos de texto livre): `bleach` ou similar — strip de tags
- **SQL**: ORM Django escapa por default (não usar `raw_sql` sem revisão)
- **Path traversal**: lib `pathlib` + verificação que path resolvido está dentro de allowed dir
- **Unicode**: normalizar (NFC) + remover zero-width chars + bloquear homoglyph

Detalhes em `seguranca/agente-input-nao-confiavel.md`.

---

## Hooks / verificação

Auditor Qualidade em pre-commit:
- Endpoint sem serializer / sem validação → FAIL
- `data["x"]` sem validação prévia → CONCERN
- Mensagem de erro hardcoded em inglês ou linguagem técnica vazando pra UX → FAIL (`auditor-produto`)

---

## Referências

- `erro.md` (ValidationError = 400, DomainError = 422)
- `auth-rbac.md`
- `seguranca/agente-input-nao-confiavel.md`
