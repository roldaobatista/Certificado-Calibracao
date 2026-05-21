---
owner: consultor-rbc-iso17025 (consultivo — não substitui credenciado CGCRE)
revisado-em: 2026-05-20
status: stable
---

# Review RBC/ISO 17025 — US-CLI-006 (T-CLI-114..120)

Veredito: **AJUSTAR** (3 BLOQ).

## R1 — Matriz eliminação×anonimização (T-CLI-116)

3 zonas de dado por cliente vinculado a certificado emitido:

| Zona | Campo | Tratamento LGPD | Base ISO 17025 |
|---|---|---|---|
| **A — Identificação titular** | CPF, RG, e-mail, telefone | Hash SHA-256 + salt tenant | LGPD art. 16 II |
| **B — Identificação fiscal PJ** | CNPJ, razão social, IE, endereço fiscal | **MANTER** 25a | ISO §7.8.2.1 + §8.4.2 |
| **C — Vínculo titular↔cliente PJ** | nome contato, cargo, assinatura | Pseudonimizar (hash) preservando rastreabilidade | NIT-DICLA-021 |

## R2 — Signatário humano (ISO cl. 6.2 + NIT-DICLA-021)

NUNCA entra em eliminação enquanto certificado emitido por ele estiver dentro de 25a. Texto de bloqueio padrão:

> "Mantido por obrigação ISO/IEC 17025 §8.4 + NIT-DICLA-021 até [data emissão + 25a do último certificado assinado]."

## R3 — Art. 37 LGPD × §8.4 ISO

**Não há conflito.** Registros independentes, mesma trilha B2 WORM com tags distintas. Retenção = max(25a, prazo LGPD do tenant).

## BLOQs

- **BLOQ-R1**: ADR-0021 (Anonimização vs retenção regulatória) — abrir agora.
- **BLOQ-R2**: texto de bloqueio cita base **art. 7º II Lei 9.933/99 INMETRO** (dogfooding pré-RBC); pós-credencial muda pra **art. 16 IV LGPD**.
- **BLOQ-R3**: consultor RBC humano credenciado assina antes da 1ª CGCRE real. R$ 5-10k pontual.
