---
owner: roldao
revisado-em: 2026-05-23
status: minuta
aguarda-revisao-oab: true
selo: "MINUTA — REQUER VALIDAÇÃO OAB ANTES DE EXECUÇÃO/PUBLICAÇÃO"
---

# DPIA — Módulo Calibração (Marco 4)

> Plataforma Aferê — conformidade LGPD art. 38 + Res. CD/ANPD 18/2024.
> **MINUTA — REQUER VALIDAÇÃO OAB**.

---

## 1. Descrição da Operação

1.1. **Módulo:** Calibração metrológica conforme ISO/IEC 17025:2017.
1.2. **Marco:** Marco 4 (pós Marco 3 `os`).
1.3. **Operações:**
- registro de calibração de equipamento;
- aplicação de método (procedimento técnico);
- cálculo de incerteza expandida;
- aplicação da regra de decisão ISO 17025 cl. 7.8.6 (ADR-0024);
- 2ª conferência obrigatória (cl. 6.2.5 — ADR-0026);
- emissão de certificado vinculado ao módulo `certificados` (Marco 5);
- validação de software cl. 7.11 (ADR-0025).

---

## 2. Finalidade

- `obrigacao_regulatoria_iso17025`
- `auditoria_cgcre`
- `responsavel_tecnico_tenant`
- `signatario_a3`
- `defesa_em_juizo`

**Objetivo:** prover ao Tenant laboratório acreditado meios de executar calibração rastreável com defensabilidade técnica/jurídica perante CGCRE e contraprova judicial.

---

## 3. Necessidade e Proporcionalidade

3.1. **Necessidade:** sem identificação de RT, signatário, técnico executor e padrões usados, certificado é inválido perante CGCRE. Sem cálculo auditável, certificado não defensável.

3.2. **Proporcionalidade:**
- coleta restrita a dados exigidos por NIT-DICLA-005 e 030;
- nenhum dado pessoal de Cliente Final além de identificação da PJ titular do equipamento;
- 2º caminho de cálculo (ADR-0025) protege Titular contra erro IA.

---

## 4. Titulares e Dados

| Titular | Dados |
|---|---|
| Cliente Final (Tenant do Tenant) | Razão social, CNPJ/CPF, endereço de uso do equipamento |
| Responsável Técnico (RT) | Nome, CPF, registro conselho, vigência, grandezas autorizadas |
| Signatário A3 | Nome, CPF, dados certificado ICP-Brasil, signing-time, nonce |
| Técnico executor da calibração | Nome, CPF, função, evidência de competência |
| Padrões/instrumentos | Sem dado pessoal (metadados técnicos) |

---

## 5. Bases Legais

| Dado | Base | Justificativa |
|---|---|---|
| RT, signatário, técnico | art. 7º II + 11 II "a" | ISO 17025 + NIT-DICLA |
| Cliente Final identificação | art. 7º V + VI | Contrato + defesa |
| Signatário A3 | art. 7º II (MP 2.200-2/2001) | Validade jurídica do documento |
| Trilha cálculo | art. 7º II + VI | Regulatório + defesa |

---

## 6. Retenção

6.1. **~25 anos** vinculada ao life cycle do certificado (ISO 17025 cl. 8.4 + 5 anos prescricional).
6.2. **Não há eliminação antecipada** salvo decisão judicial; pedido de Titular técnico desligado segue Zona C (anonimização em lugar — ADR-0021) preservando integridade do certificado.

---

## 7. Garantias de Segurança

- RLS multi-tenant (INV-TENANT-003);
- trilha imutável WORM;
- A3 assinada client-side (ADR-0009);
- KMS Multi-Region Key (sa-east-1 / us-east-1);
- 2º caminho de cálculo independente (ADR-0025);
- replay determinístico para auditoria (ADR-0025);
- 2ª conferência por pessoa distinta (ADR-0026).

---

## 8. Riscos Identificados

| # | Risco | Probabilidade | Impacto |
|---|---|---|---|
| R1 | Erro de cálculo por IA (alucinação em fórmula) | Média | Crítico |
| R2 | Regra de decisão (7.8.6) aplicada divergente da pactuada com cliente | Baixa | Alto |
| R3 | Software não validado cl. 7.11 → CGCRE suspende acreditação | Baixa | Crítico |
| R4 | RT desligado sem registro, assinou certificado pós-saída | Baixa | Alto |
| R5 | Signatário A3 comprometido (certificado roubado) | Muito baixa | Crítico |
| R6 | Pedido de eliminação Titular x exigência ISO 17025 25 anos (conflito Zona A vs C) | Média | Médio |

---

## 9. Mitigação

- **R1:** ADR-0025 — 2º caminho determinístico de cálculo + replay; IA jamais decide cálculo final sozinha; hook revisão obrigatória.
- **R2:** ADR-0024 — 3 modos pré-pactuados + override por cliente + lock pós-emissão.
- **R3:** ADR-0025 URS/IQ/OQ/PQ; suite regressão obrigatória; auditor-llm-correctness no pipeline.
- **R4:** ADR-0022 imutabilidade pós-INSERT do RT + EXCLUDE GIST vigência; consumer ANPD/CGCRE em desligamento.
- **R5:** WORM + ciclo de chave + revogação imediata; ICP-Brasil OCSP; INV-CER-FRAUD-A3-001.
- **R6:** ADR-0021 Zona C anonimiza em lugar preservando validade certificado.

---

## 10. Consulta a Titulares

10.1. Não exigida por se tratar de B2B regulado; canal DPO público.
10.2. Tenant piloto (Balanças Solution) consultado em dogfooding.

---

## 11. Conclusão

11.1. **Veredito:** operação compatível com finalidade regulatória; riscos críticos têm mitigação dedicada via ADRs 0022/0024/0025/0026.
11.2. **Pendências pré-Marco 4 produção:** aceite ADRs 0024/0025/0026; auditor-llm-correctness rodando bloqueante; validação OAB deste DPIA.
11.3. **Revisão:** anual ou em mudança material (nova versão NIT-DICLA, nova ISO).

---

**FIM DPIA-CAL v1.0 — MINUTA**
