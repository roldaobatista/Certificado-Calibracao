---
owner: roldao
revisado-em: 2026-05-23
status: minuta
aguarda-revisao-oab: true
selo: "MINUTA — REQUER VALIDAÇÃO OAB ANTES DE EXECUÇÃO/PUBLICAÇÃO"
---

# DPIA — Módulo Certificados (Marco 5)

> Plataforma Aferê — LGPD art. 38 + Res. CD/ANPD 18/2024.
> **MINUTA — REQUER VALIDAÇÃO OAB**.

---

## 1. Descrição da Operação

1.1. **Módulo:** Certificados — emissão, assinatura A3 ICP-Brasil, distribuição, custódia long-tail.
1.2. **Marco:** Marco 5 (pós Marco 4 `calibracao`).
1.3. **Operações:**
- geração de PDF/A do certificado de calibração;
- assinatura A3 client-side via Lacuna Web PKI;
- selo de tempo (signing-time server-controlled + nonce anti-replay);
- gravação em trilha WORM (Backblaze B2 Object Lock compliance);
- distribuição ao Cliente Final (e-mail, portal);
- validação posterior (verificação ICP-Brasil OCSP + integridade hash).

---

## 2. Finalidade

- `signatario_a3`
- `obrigacao_regulatoria_iso17025`
- `auditoria_cgcre`
- `responsavel_tecnico_tenant`
- `defesa_em_juizo`
- `comunicacao_servico_titular`

---

## 3. Necessidade e Proporcionalidade

3.1. **Necessidade:** assinatura A3 é exigência regulatória para validade jurídica/metrológica. Sem CPF e dados ICP-Brasil do signatário, certificado não é válido.

3.2. **Proporcionalidade:**
- A3 assinada **client-side**, material de chave nunca tramita no servidor;
- coletados apenas elementos exigidos pela MP 2.200-2/2001 e ICP-Brasil;
- distribuição limitada a destinatários autorizados pelo Tenant.

---

## 4. Titulares e Dados

| Titular | Dados |
|---|---|
| Cliente Final | Razão social, CNPJ/CPF, e-mail, endereço |
| Signatário A3 | Nome, CPF, dados certificado ICP-Brasil (serial AC, vigência), signing-time, nonce |
| Responsável Técnico (RT) | Nome, CPF, registro conselho |
| Padrões | Metadados técnicos (sem PII) |

---

## 5. Bases Legais

| Dado | Base | Justificativa |
|---|---|---|
| Signatário A3 | art. 7º II (MP 2.200-2/2001) | Obrigação legal para validade |
| RT | art. 7º II + 11 II "a" | NIT-DICLA-021 |
| Cliente Final | art. 7º V + VI | Contrato + defesa |
| E-mail Cliente para envio | art. 7º V | Comunicação transacional |

---

## 6. Retenção

6.1. **~25 anos** vinculada ao certificado (ISO 17025 cl. 8.4 + 5 anos prescricional + life cycle do equipamento).
6.2. WORM Object Lock em modo **compliance** — não removível antes do prazo.
6.3. Pedido de eliminação Titular signatário desligado: Zona C (anonimização em lugar) preservando validade jurídica do certificado já emitido — ADR-0021.

---

## 7. Garantias de Segurança

- A3 **client-side** (ADR-0009) — chave privada nunca toca servidor;
- nonce + signing-time **server-controlled** + one-shot — defesa anti-replay;
- WORM Object Lock compliance — imutabilidade total;
- ciclo de chave KMS Multi-Region anual;
- OCSP ICP-Brasil em validação posterior;
- hash SHA-256 do PDF assinado em trilha;
- RLS multi-tenant + middleware tenant_id;
- INV-CER-FRAUD-A3-001 (anti-fraude assinatura).

---

## 8. Riscos Identificados

| # | Risco | Probabilidade | Impacto |
|---|---|---|---|
| R1 | Signatário A3 comprometido (certificado roubado/expirado usado) | Muito baixa | Crítico |
| R2 | Contestação judicial de assinatura (alegação não-repúdio falha) | Baixa | Alto |
| R3 | Custódia long-tail (~25 anos) — perda de mídia/migração | Média (no horizonte) | Crítico |
| R4 | Trilha WORM violada (ataque ao Backblaze) | Muito baixa | Crítico |
| R5 | Distribuição a destinatário errado (e-mail trocado) | Baixa | Médio |
| R6 | Replay de assinatura (mesmo nonce reutilizado) | Muito baixa | Crítico |
| R7 | RT desligado sem registro assinando certificado | Baixa | Alto |

---

## 9. Mitigação

- **R1:** OCSP ICP-Brasil obrigatório pré-assinatura; INV-CER-FRAUD-A3-001; revogação imediata em incidente; trilha de quem assinou.
- **R2:** signing-time server-controlled + nonce + hash PDF em WORM constitui evidência robusta de não-repúdio.
- **R3:** Multi-Region (AWS sa-east-1 ↔ us-east-1 KMS) + Backblaze WORM + verificação periódica (GATE-1 Wave A: verificação periódica + checksum); plano de migração de mídia decenal.
- **R4:** Object Lock compliance + verificação periódica de integridade; provedor B (Magalu/Oracle/AWS) para DR.
- **R5:** confirmação dupla de destinatário; UI mostra preview antes de envio.
- **R6:** one-shot nonce server-controlled; reutilização bloqueada por unique constraint.
- **R7:** ADR-0022 imutabilidade pós-INSERT RT + EXCLUDE GIST vigência + consumer ANPD/CGCRE em desligamento (GATE-EQP-RT-NOTIF).

---

## 10. Consulta a Titulares

10.1. Não exigida (B2B regulado); canal DPO público.

---

## 11. Conclusão

11.1. **Veredito:** operação proporcional; riscos críticos mitigados por defesa em profundidade (cliente-side A3 + WORM + KMS Multi-Region + ciclo chave + OCSP).
11.2. **Pendências pré-Marco 5 produção:**
- aceite ADR-0009;
- GATE-1 Wave A (B2/WORM verificação periódica) operacional;
- GATE-EQP-RT-NOTIF operacional;
- validação OAB.

11.3. **Revisão:** anual ou em mudança regulatória ICP-Brasil/ITI.

---

**FIM DPIA-CERT v1.0 — MINUTA**
