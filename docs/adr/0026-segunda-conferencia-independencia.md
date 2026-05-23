---
adr: 0026
titulo: 2ª conferência + independência RT (ISO 17025 cl. 6.2.5 + 7.7) — política de exceção objetiva
status: aceito
data: 2026-05-23
aceito-em: 2026-05-23 (Onda 6 saneamento — destravar Marco 4 calibração)
proposto-por: agente (auditoria 10 lentes — TEMA-F.3)
revisado-por: consultor-rbc-iso17025 + advogado-saas-regulado
bloqueia-fase: Wave A Marco 4 (calibracao)
depende-de: ADR-0022 (RT do tenant), ADR-0023 (OS com Atividades)
---

# ADR-0026 — 2ª conferência + independência RT

## Contexto

ISO/IEC 17025 §6.2.5 exige independência entre executor da calibração e revisor (1ª conferência) e entre revisor e conferente (2ª conferência). US-CAL-007 AC-007-3 e US-CAL-008 AC-008-3 documentam **exceção** "quando único RT habilitado" — texto frouxo, sem critério objetivo, sem limite quantitativo, sem revisão periódica. CGCRE em supervisão pergunta o "como objetivo".

Auditoria 10 lentes (consultor-rbc-iso17025 — TEMA-F.3) marcou como ALTO antes de Marco 4 começar.

`responsabilidade-tecnica.md §3.1` já cravou política operacional em 2026-05-23 (sessão atual). Esta ADR **promove a decisão estrutural** que respalda a política.

## Decisão

**Política de independência RT em 3 níveis** + exceção objetiva controlada:

### Nível 1 — Independência total (preferencial)

`executor != revisor != conferente`. 3 pessoas distintas. Aplica-se a calibrações RBC + cliente farma + alta criticidade.

### Nível 2 — Independência parcial (aceitável)

`executor != revisor`; `revisor == conferente` (1 pessoa faz 1ª e 2ª conferência separadas no tempo, mas mesma pessoa). Aceitável em laboratórios pequenos (< 3 RT ativos). Registro obrigatório.

### Nível 3 — Exceção (ÚLTIMO RECURSO)

`executor == revisor == conferente`. Permitido SÓ quando **todas as 4 condições cumulativas** (cravadas em `responsabilidade-tecnica.md §3.1`):

1. Único RT habilitado ATIVO na grandeza/faixa específica.
2. Calibração tem prazo regulatório que não pode esperar (≤7 dias úteis).
3. Tentativa documentada de subcontratar a 2ª conferência a outro lab.
4. Justificativa registrada ≥100 chars + anti-PII.

**Limite quantitativo:** máximo **5% das calibrações/mês**. Hook `politica-excecao-revisor-check.sh` conta + alerta.

**Audit no PDF:** rodapé "Conformidade ISO/IEC 17025 §6.2.5 — exceção registrada em audit ref. NC-####"

### Revisão periódica

- **Trimestral:** gestor de qualidade revisa todas exceções.
- **Anual:** taxa apresentada ao auditor CGCRE.
- **Excedeu 5%/mês 2x consecutivas:** NC automática + revisão obrigatória.

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| Bloqueio absoluto da exceção | Inviabiliza laboratórios pequenos com 1 RT ativo + cert do cliente vencendo |
| Permitir exceção sem limite quantitativo | Vira regra na prática → quebra cl. 6.2.5 |
| Critério subjetivo "RT julga necessário" | CGCRE marca como NC documental (sem critério objetivo) |

## Consequências

### Positivas

- Critério objetivo de exceção (4 condições + 5%/mês).
- Audit explícito no PDF do certificado (transparência ISO §7.8).
- Revisão trimestral + anual cravadas como obrigação operacional.
- Hook mecânico + alerta automático.

### Negativas (mitigáveis)

- Carga operacional do gestor de qualidade (revisão trimestral).
- Possíveis prejuízos comerciais se exceder 5% (cliente espera).

## Non-goals

- NÃO substitui contratação de 2º RT em laboratório que cresce.
- NÃO aplica retroativamente — calibrações existentes não viram NC.

## Invariantes novas

- **INV-CAL-IND-001:** exceção `executor == revisor` só com as 4 condições + justificativa ≥100 chars anti-PII.
- **INV-CAL-IND-002:** taxa de exceção/mês > 5% por 2 meses consecutivos → NC automática.
- **INV-CAL-IND-003:** PDF de certificado emitido sob exceção carrega rodapé padronizado.

## Implicações pro faseamento

- Marco 4 implementa validação das 4 condições + hook + audit no PDF.
- Wave A: dashboard exceções pra gestor de qualidade.
- V2 (RT vendor): revisão anual da política.

## Status

Proposta — política operacional já em `responsabilidade-tecnica.md §3.1`. ADR cristaliza decisão estrutural — aguarda aceite Roldão antes de Marco 4 começar.
