---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: equipamentos
dominio: suporte-plataforma
---

# Modelo de domínio — Equipamentos do cliente

## Entidades

### Equipamento (agregado raiz)

- **Atributos imutáveis pós-emissão (INV-025):** `tag`, `numero_serie`, `fabricante`, `cliente_id_original`
- **Atributos versionáveis:** `modelo`, `faixa_medicao`, `classe_exatidao`, `descricao`, `localizacao_fisica`
- **Atributos operacionais (mutáveis sempre):** `status` (ativo/inativo/sucata/em_calibracao), `cliente_atual_id`
- **Invariantes:** `INV-025` (imutabilidade pós-cert), `INV-TENANT-001` (presença de tenant em toda query)
- **Ciclo de vida:** criada no cadastro → ativa → versões geradas a cada edição pós-cert → sucateada (terminal).

### EquipamentoVersao (entidade filha)

- **Atributos:** `equipamento_id`, `versao_n`, `snapshot_atributos_versionaveis (JSONB)`, `motivo_mudanca`, `criado_em`, `criado_por`
- **Imutável após criada.** Cada certificado referencia `(equipamento_id, versao_n)` que existia no momento da emissão.

### EquipamentoEvento (log imutável)

- **Atributos:** `equipamento_id`, `tipo_evento` (cadastrado/editado/calibrado/transferido/sucateado), `payload (JSONB)`, `usuario_id`, `timestamp`
- **Append-only.**

### QrCode (value object)

- `equipamento_id`, `url`, `hash_assinatura`, `emitido_em`
- Imutável. Re-emitir gera novo registro mas o anterior permanece válido até `revogado_em`.

---

## INV-025 — Imutabilidade pós-emissão (detalhe)

**Regra:** assim que o equipamento tem ≥1 `Certificado.status = emitido`:
1. **Campos imutáveis** (`tag`, `numero_serie`, `fabricante`, `cliente_id_original`): qualquer tentativa de UPDATE retorna erro 422 com mensagem em PT ("não é possível alterar TAG após emissão de certificado").
2. **Campos versionáveis**: UPDATE NÃO altera o registro original. Em vez disso, cria `EquipamentoVersao` nova com `versao_n+1` e snapshot dos novos valores. Certificados anteriores continuam pointando pra versão antiga.
3. **Histórico (`EquipamentoEvento`)**: append-only — nenhum delete permitido, nenhum update permitido.
4. **Validação**: hook de banco + validação na camada de aplicação.

---

## Agregados (DDD)

| Agregado raiz | Entidades incluídas | Invariantes |
|---|---|---|
| Equipamento | EquipamentoVersao, EquipamentoEvento, QrCode | `INV-025`, `INV-TENANT-001` |

---

## Eventos publicados

| Evento | Quando dispara | Consumidores |
|---|---|---|
| `Equipamento.cadastrado` | Após INSERT | Metrologia (pré-aloca padrão), Comercial (visão 360° cliente) |
| `Equipamento.versao_criada` | Após nova `EquipamentoVersao` | Metrologia (revalida calibrações abertas) |
| `Equipamento.sucateado` | Status → sucata | Comercial, Operação (cancela OS abertas) |
| `Equipamento.transferido` | `cliente_atual_id` muda | Comercial |

---

## Comandos

| Comando | Origem | Pré-condição | Pós-condição |
|---|---|---|---|
| `cadastrarEquipamento` | UI/API | cliente existente, TAG única no tenant | Equip. + QR criados; evento publicado |
| `editarAtributoVersionavel` | UI/API | equip. existe | Se há cert. emitido → nova `EquipamentoVersao`; senão UPDATE direto |
| `sucatear` | UI/API | sem OS aberta | Status=sucata; evento publicado |
| `transferirParaCliente` | UI/API | novo cliente existe | `cliente_atual_id` atualizado; evento publicado |

---

## Schema físico

Ver `../schema-banco.md` quando criado.

## Como evolui

- Novo atributo → migration + decidir se é imutável ou versionável.
- Mudança em INV-025 → ADR obrigatório.
