---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
relacionados:
  - ./modelo-de-dominio.md
  - ./conformidade-iso-17025.md
  - ./validacao-software.md
  - ./garantia-validade-7.7.md
  - REGRAS-INEGOCIAVEIS.md (INV-022, INV-CAL-AUD-001, INV-CAL-TXT-001)
---

# Registros técnicos (ISO/IEC 17025 cl. 7.5)

> **Origem:** TEMA-B.3 da auditoria 10 lentes 2026-05-23. Cláusula 7.5 ISO 17025 exige que **todos os registros técnicos** sejam: (a) **identificáveis** (pessoal, equipamento, condições, hora), (b) **rastreáveis** (cadeia até origem), (c) **imutáveis com correções rastreáveis** ("rasura digital"). Faltava doc canônico — auditoria saltava de 7.4 (recebimento — Marco 2) pra 7.7 (garantia validade).

---

## 1. Princípio

Todo registro técnico de calibração tem **2 camadas** de proteção:

1. **Imutabilidade** — após gravação, o registro NÃO pode ser editado nem deletado (trigger PG BLOCK + WORM Backblaze B2 25 anos).
2. **Rastreabilidade de correção** — quando uma correção é **necessária e legítima** (antes da aprovação final), ela é registrada como **NOVO** registro (`LeituraCorrecao` / `OrcamentoCorrecao`) preservando o original. Quem fez, quando, valor original, valor corrigido, razão (≥30 chars, anti-PII).

**Princípio inviolável:** "rasura digital" — nunca-sobrescrever, sempre-anexar.

---

## 2. Mapeamento campo → INV

| Tipo de registro técnico (entidade) | Imutabilidade | Correção legítima | INV aplicável |
|---|---|---|---|
| `Leitura` | Trigger PG `leitura_anti_update_delete_trg` | `LeituraCorrecao` (entidade separada — TEMA-B.3) | INV-022, INV-CAL-AUD-001 |
| `CondicoesAmbientais` | Trigger PG BLOCK | Não permite correção — exige nova `Calibracao` com causation_id | INV-022 |
| `OrcamentoIncerteza` + `ComponenteIncerteza[]` + `OrcamentoPorPonto[]` | Trigger PG BLOCK | Recalcular = novo orçamento + causation_id apontando pro anterior; original preservado pra replay determinístico (garantia-validade-7.7) | INV-004, INV-005, INV-022 |
| `AvaliacaoConformidade` | Trigger PG BLOCK | Nova avaliação com causation_id | INV-006 |
| `RevisaoTecnica` | Imutável após inserido | Re-revisão = novo `RevisaoTecnica` | INV-007 |
| `PadraoUsado.snapshot_padrao_json` | Imutável pós-`EM_REVISAO_1` (INV-CAL-RT-COMP-001) | NÃO permite correção retroativa — TEMA-B.1 | INV-CAL-RT-COMP-001 |
| `Certificado` emitido | INV-001 (hash chain) + WORM | Reemissão = novo Certificado + retificação justificada (cl. 7.8.8) — ver `controle-certificado-emitido.md` | INV-001, INV-017 |

---

## 3. LeituraCorrecao — entidade dedicada (cl. 7.5)

> Implementa a "rasura digital" da cláusula 7.5: valor original preservado + valor corrigido + razão + corretor + timestamp. NUNCA `UPDATE` em `Leitura`.

### Atributos

- `id` (uuid)
- `tenant_id`
- `leitura_id` (FK Leitura — não modifica original)
- `valor_original` (cópia do valor da Leitura no momento da correção — defesa contra hipótese de Leitura ser mutável no futuro)
- `valor_corrigido`
- `razao_correcao` (≥30 chars, anti-PII via INV-CAL-TXT-001)
- `corretor_id_hash` (HMAC tenant)
- `corrigido_em` (timestamp UTC)
- `correlation_id` (herdado da Calibração)

### Quando é permitido corrigir

- **Permitido:** `calibracao.status IN (CONFIGURADA, EM_EXECUCAO)`.
- **Bloqueado após `EM_REVISAO_1`:** correção exige reabertura formal da calibração via `NaoConformidade` (TEMA-B.2 — ciclo CAPA). Trigger PG `leitura_correcao_pos_revisao_trg` bloqueia INSERT.

### Como aparece no certificado

O certificado NÃO mostra o valor original — mostra o valor final usado no cálculo + nota de rodapé "Houve correção pré-aprovação registrada em audit (ver dossiê)" quando aplicável.

### Eventos

- `Calibracao.LeituraCorrigida` — `{tenant_id, calibracao_id, leitura_id, corretor_id_hash, correlation_id, causation_id}`. Consumer: `EventoDeCalibracao` (WORM 25a) + Qualidade (monitora taxa de correção como indicador de competência do executor).

---

## 4. Identificação do pessoal nos registros

Cada registro técnico carrega ator identificado por `*_id_hash` (HMAC tenant) em payload publicado, mas com UUID interno preservado para reconstrução autenticada (quando RT precisa identificar quem fez algo em supervisão CGCRE):

| Campo | Tipo | Onde |
|---|---|---|
| `executor_id` | UUID interno | `Leitura`, `RecepcaoItemCalibracao`, `MedicaoControle` |
| `executor_id_hash` | HMAC tenant | payload publicado (cross-context) |
| `revisor_id` | UUID interno | `RevisaoTecnica` |
| `revisor_id_hash` | HMAC tenant | payload publicado |
| `conferente_id` | UUID interno | `RevisaoTecnica` etapa CONFERENCIA_2 |
| `conferente_id_hash` | HMAC tenant | payload publicado |
| `corretor_id` | UUID interno | `LeituraCorrecao` |
| `corretor_id_hash` | HMAC tenant | payload publicado |
| `ator_id_hash` | HMAC tenant | `EventoDeCalibracao` (sempre hash — audit WORM 25a) |

Resolução `hash → nome real + CRM` só via porta autenticada `consultar_signatario_vigente()` (aplica matriz de anonimização em runtime conforme retenção — TEMA-D em LGPD).

---

## 5. Retenção e WORM

| Registro | Retenção mínima | Local |
|---|---|---|
| `Leitura` | 25 anos quando vinculada a certificado emitido | B2 WORM |
| `LeituraCorrecao` | Igual à Leitura corrigida | B2 WORM |
| `EventoDeCalibracao` | 25 anos quando vinculado a certificado / 5a caso contrário | B2 WORM |
| `OrcamentoIncerteza` + filhas | 25 anos | B2 WORM |

Ver `docs/conformidade/comum/retencao-matriz.md` para a matriz completa.

---

## 6. Defesas técnicas

- **Trigger PG** `leitura_anti_update_delete_trg` em todas as 5 tabelas (`leitura`, `leitura_correcao`, `condicoes_ambientais`, `orcamento_incerteza`, `evento_de_calibracao`).
- **Hook pre-commit** `audit-immutability-check.sh` (já existe Marco 2) — estende-se a tabelas de calibração.
- **Sanitização na escrita** (INV-CAL-AUD-001) — payload de `EventoDeCalibracao` proíbe IDs PII crus.
- **Anti-PII em texto livre** (INV-CAL-TXT-001) — `razao_correcao`, `nota`, `observacoes_gerais`, `motivo_cancelamento`, `descricao_nc`, `causa_raiz`, `acao_corretiva`.
- **Replay determinístico** (`garantia-validade-7.7.md`) — segundo caminho de cálculo + hash de entrada/saída.

---

## 7. Como o RT prova em supervisão CGCRE

> Cenário típico: auditor CGCRE pede "mostre o histórico técnico do certificado XYZ emitido em 2027".

1. Carrega cert → `Certificado.calibracao_id` → carrega Calibração + snapshot equipamento + atividade OS pai.
2. Lista todas `Leitura` da calibração + todas `LeituraCorrecao` (com razão + corretor).
3. Lista `RevisaoTecnica` (REVISAO_1 + CONFERENCIA_2 com revisor/conferente).
4. Lista `NaoConformidade` aberta/fechada (ciclo CAPA documentado).
5. Lista `EventoDeCalibracao` (audit WORM imutável).
6. Resolve `*_id_hash` em nomes reais via porta autenticada (LGPD compliance — log `AcessoDadosCliente`).

Auditor reconstrói TODA a história — quem fez, quando, quais correções, qual causa-raiz, qual ação corretiva, qual eficácia — em <10 minutos.

## 8. Como evolui

- Campo novo em entidade de registro técnico → migration + atualização desta matriz + bump CHANGELOG.
- Cláusula 7.5 ISO atualizada (ABNT publica revisão) → re-revisar este doc + ADR se mudar fluxo.
