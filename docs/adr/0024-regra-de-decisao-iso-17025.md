---
adr: 0024
titulo: Regra de decisão ISO/IEC 17025 cl. 7.8.6 — 3 modos + override por cliente
status: aceito
data: 2026-05-23
aceito-em: 2026-05-23 (Onda 6 saneamento — destravar Marco 4 calibração)
proposto-por: agente (auditoria 10 lentes — TEMA-F.1)
revisado-por: consultor-rbc-iso17025 + tech-lead-saas-regulado
bloqueia-fase: Wave A Marco 4 (calibracao)
depende-de: ADR-0023 (OS com Atividades)
---

# ADR-0024 — Regra de decisão ISO/IEC 17025 cl. 7.8.6

## Contexto

US-CAL-006 + AC-CAL-006-1..3 já documentam 3 regras de decisão (Aceitação Simples / Banda de Guarda 30% / Risco Compartilhado) + zona de incerteza. Mas **decisão estrutural não tem ADR** — auditor CGCRE em supervisão pede justificativa documentada de por que essas 3 + parametrização por cliente + lock após emissão.

Auditoria 10 lentes (consultor-rbc-iso17025 — TEMA-F.1) marcou como ALTO antes de Marco 4 começar.

## Decisão

**Adotar 3 modos de regra de decisão**, parametrizáveis por cliente, com lock pós-emissão:

| Modo | Quando aplicar | Como calcular | Norma de referência |
|---|---|---|---|
| **Aceitação Simples** (default) | Cliente sem requisito específico | Resultado vs especificação direta; incerteza informada mas não amplia bandas | ILAC G8 §4.2 |
| **Banda de Guarda 30%** | Cliente farma / regulatório que exige risco controlado de aceitação errada (PFA ≤ 5%) | Banda de aceitação = `[LSL + 0.3·U, USL − 0.3·U]` (k=2 → 95.45%) | ILAC G8 §4.4 |
| **Risco Compartilhado** | Cliente pede declaração de probabilidade explícita | Cálculo de PFA + PRA (false acceptance + false rejection); cliente decide threshold | ILAC G8 §4.3 + JCGM 106 |

### Override por cliente

- `Tenant` define regra padrão (`Tenant.regra_decisao_default`).
- `Cliente.regra_decisao_override` pode mudar para clientes específicos (ex: tenant default = Aceitação Simples; cliente farma X = Banda de Guarda 30%).
- Override registrado em audit + cláusula contratual obrigatória do tenant↔cliente.

### Lock pós-emissão

Após `Calibracao.status = APROVADA` + certificado EMITIDO, a regra de decisão usada fica **imutável** no snapshot do certificado. Mudar regra no `Tenant`/`Cliente` no futuro NÃO afeta certificados emitidos.

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| Adotar só Aceitação Simples (mais simples) | Inviabiliza cliente farma/regulatório que exige Banda de Guarda — perda de mercado |
| Permitir tenant criar regra customizada (4º modo, 5º modo) | Customização do fluxo regulatório por tenant = NC em supervisão CGCRE (ANTI-11). Reservado a ADR futura |
| Regra dinâmica por calibração (sem default tenant) | Carga cognitiva no metrologista; risco de inconsistência tenant |

## Consequências

### Positivas

- ISO 17025 §7.8.6 documentada com base normativa.
- Cliente farma / regulatório atendido sem fork de código.
- Audit trail completo da escolha + override.
- Lock pós-emissão impede fraude retroativa.

### Negativas (mitigáveis)

- Complexidade adicional no UI (P-OP-02 metrologista escolhe modo + parâmetros).
- Treinamento do tenant na escolha do modo.

## Non-goals

- NÃO permite tenant criar 4ª regra customizada.
- NÃO aplica regra retroativamente a certs emitidos.
- NÃO altera ZONA_INCERTEZA — continua exigindo decisão explícita do metrologista (AC-CAL-006-2).

## Invariantes novas

- **INV-CAL-DEC-001:** toda calibração carrega `regra_decisao` snapshot (não-FK ao Cliente — congelado).
- **INV-CAL-DEC-002:** override de cliente exige cláusula contratual ativa do tenant↔cliente.
- **INV-CAL-DEC-003:** após `Calibracao.status = APROVADA`, `regra_decisao` é imutável (trigger PG).

## Implicações pro faseamento

- Marco 4 `calibracao` implementa as 3 regras + override + lock.
- Marco N `clientes` (se necessário) expõe `Cliente.regra_decisao_override` no UI.

## Status

Proposta — aguarda aceite Roldão + parecer consultor-rbc-iso17025 humano antes de Marco 4 começar.
