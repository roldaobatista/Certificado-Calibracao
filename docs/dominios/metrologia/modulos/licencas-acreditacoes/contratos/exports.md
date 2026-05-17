---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/conformidade/comum/fiscal.md
---

# Contratos de Export — Licenças e Acreditações

> Formatos de saída do módulo.

---

## Exports

### Export 1: Relatório consolidado de auditoria (PDF)

**Propósito:** dossiê pra auditoria externa (CGCRE, fisco, ANVISA, cliente).
**Formato:** PDF/A-1 (longa preservação).
**Regulado?:** sim — ISO 17025 4.1 + NIT-DICLA + LGPD art.37 (registro de tratamento).
**Validador externo:** auditor verifica hash SHA-256 + assinatura digital opcional.
**Template/Schema:** `docs/templates/licencas-relatorio-auditoria-v1.html` (a criar).
**Campos obrigatórios:** identificação tenant (razão social, CNPJ), data corte, lista documentos vigentes (tipo, número, órgão, validade, anexo embed), lista vencidos (com histórico), histórico renovações últimos N meses, lista eventos emergenciais, hash SHA-256 do PDF, data/hora geração.
**Campos opcionais:** assinatura digital A3 do admin emissor.
**Assinatura digital:** opcional (A3 via Web PKI Lacuna).
**Imutabilidade pós-emissão:** sim — `INV-022` (registro em WORM).
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md` (mínimo 25 anos por ISO 17025 8.4).

**Exemplo (snippet anonimizado):**
```
RELATÓRIO DE LICENÇAS E ACREDITAÇÕES — Empresa XPTO Ltda
Data corte: 2026-05-17
Documentos vigentes: 7
1. ACREDITAÇÃO CGCRE Nº CRL-0123 — válida até 2030-01-14
   Anexo: SHA-256 abc123...
...
Hash relatório: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

---

### Export 2: CSV de documentos por status

**Propósito:** integração com planilha do admin pra controle interno.
**Formato:** CSV UTF-8 com BOM.
**Regulado?:** não.
**Campos:** `id, tipo, numero, orgao_emissor, data_emissao, data_validade, status, bloqueante, responsavel, dias_pra_vencer`.
**Imutabilidade:** não.
**Retenção:** transitório (não armazenado no servidor).

**Exemplo:**
```
id,tipo,numero,orgao_emissor,data_emissao,data_validade,status,bloqueante,responsavel,dias_pra_vencer
uuid1,ACREDITACAO_CGCRE,CRL-0123,INMETRO/CGCRE,2026-01-15,2030-01-14,VIGENTE,true,Maria Silva,1339
```

---

### Export 3: Anexo individual (PDF/imagem original)

**Propósito:** baixar cópia do documento regulatório original.
**Formato:** PDF ou imagem (formato original).
**Regulado?:** sim — evidência documental.
**Assinatura digital:** preserva assinatura do documento original.
**Imutabilidade:** sim (B2 WORM).
**Retenção:** mesma do documento (mínimo 25 anos).

---

### Export 4: Histórico de eventos emergenciais (CSV/JSON)

**Propósito:** prestação de contas aos auditores sobre acionamentos do modo emergencial.
**Formato:** CSV ou JSON.
**Regulado?:** sim (auditoria interna + externa).
**Campos:** `evento_id, data_hora, admin, operacao_liberada, documento_bloqueante, justificativa, janela_horas, assinatura_a3_thumbprint`.
**Imutabilidade:** sim — origina-se de eventos WORM.

---

## Exports inter-módulos

- Documento "ACREDITACAO_CGCRE" vigente → consumido por módulo **Certificados** pra carimbo RBC.
- Documento "ART/RRT" vigente → consumido por módulo **Calibração** pra autorizar assinatura RT.
- Documento "CERT_DIGITAL_A3" vigente → consumido por módulos com assinatura (Certificados, Fiscal).
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Versionamento de export regulado

- Mudança em template de relatório → ADR + janela 6 meses coexistência v1/v2.
- PDF/A-1 vs PDF/A-3 → ADR se houver migração.

## Como esta lista evolui

- Export novo → adicionar + validar.
- Mudança em formato regulado → ADR + atualizar validador.
- Export descontinuado → `@deprecated`.
