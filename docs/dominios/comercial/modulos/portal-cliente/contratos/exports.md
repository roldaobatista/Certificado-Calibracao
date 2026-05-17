---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/conformidade/comum/lgpd-rat.md
---

# Contratos de Export — Módulo Portal do Cliente

> Saídas que o cliente baixa pelo portal. Inclui REGULADOS (NF-e XML, certificado RBC) que o portal apenas **reentrega** (não gera).

---

## Princípio

O Portal **NÃO emite documento regulado** — ele **reentrega** documentos já emitidos pelos módulos competentes (Financeiro emite NF-e, Metrologia emite certificado). Toda emissão original fica no módulo de origem; o Portal só:
1. Verifica permissão (cliente correto + flag visível ao cliente).
2. Gera URL temporária para download.
3. Registra evento de auditoria (`Portal.CertificadoBaixado`, `Portal.SegundaViaGerada`).

---

## Exports

### Export 1: Boleto bancário (2ª via)

**Propósito:** cliente baixa boleto de fatura em aberto.
**Formato:** PDF.
**Regulado?:** Não (boleto não é fiscal; é financeiro). Mas tem regras FEBRABAN.
**Origem:** módulo Financeiro/Cobranças gera; Portal reentrega.
**Campos obrigatórios:** linha digitável, código de barras, valor, vencimento, beneficiário, sacado, banco.
**Imutabilidade pós-emissão:** boleto vencido → nova 2ª via é OUTRO boleto (com juros/multa); o anterior fica em histórico.
**Assinatura digital:** não.
**Retenção:** Backblaze B2 — boletos pagos 5 anos (matriz fiscal); URLs temporárias geradas pelo portal expiram em 24h.
**Eventos:** `Portal.SegundaViaGerada` na entrega.

---

### Export 2: QR Code Pix (cópia-e-cola)

**Propósito:** alternativa moderna à 2ª via.
**Formato:** imagem PNG + string `pix-copia-e-cola` em JSON.
**Regulado?:** Não (instrumento de pagamento BCB).
**Origem:** Financeiro gera (provider pagamentos); Portal exibe.
**Imutabilidade:** QR Pix vencido = inválido; novo Pix = novo QR.

---

### Export 3: Fatura PDF

**Propósito:** cópia digital da fatura (não confundir com NF-e).
**Formato:** PDF.
**Regulado?:** Não (fatura é comercial).
**Conteúdo:** itens, valores, condições, totais.

---

### Export 4: NF-e (XML + DANFE PDF)

**Propósito:** cliente PJ baixa XML para escrituração + DANFE para conferência visual.
**Formato:** XML (assinado SEFAZ) + PDF DANFE.
**Regulado?:** **SIM** — schema SEFAZ + assinatura digital obrigatória.
**Origem:** módulo Financeiro/NF-e (FiscalProvider — ADR-0008) gera e assina; Portal apenas reentrega arquivo já existente.
**Validador externo:** portal da SEFAZ-UF do tenant.
**Imutabilidade:** NF-e autorizada é imutável (CC-e/cancelamento são outros documentos).
**Retenção:** 5 anos (Receita Federal) — ver `../../../conformidade/comum/fiscal.md` e `../../../conformidade/comum/retencao-matriz.md`.
**Eventos:** `Portal.NFeBaixada` (a definir).

---

### Export 5: Certificado de Calibração PDF (regulado RBC/ISO 17025)

**Propósito:** cliente baixa certificado emitido pelo laboratório.
**Formato:** PDF.
**Regulado?:** **SIM** — ISO/IEC 17025 cláusula 7.8.
**Origem:** módulo Metrologia/Calibração emite e assina (Lacuna A3 — ADR-0009); Portal só reentrega.
**Validador externo:** QR Code embutido no PDF apontando para validador RBC/INMETRO.
**Imutabilidade pós-emissão:** **TOTAL** — `INV-001` (WORM no certificado RBC) + `INV-034` (numeração sequencial inviolável). Anulação cria certificado novo com selo "ANULA O ANTERIOR".
**Assinatura digital:** A3 (cert ICP-Brasil) embutida no PDF.
**Retenção:** 25 anos (ISO 17025 cláusula 8.4 — alinhada à matriz `../../../conformidade/comum/retencao-matriz.md`).
**Eventos:** `Portal.CertificadoBaixado` (trilha ISO 17025 + LGPD).

---

### Export 6: Relatório técnico / laudo de OS

**Propósito:** cliente baixa relatório de uma OS concluída.
**Formato:** PDF (gerado pelo módulo OS).
**Regulado?:** Depende do tipo (laudo metrológico = regulado; relatório de visita técnica = não).
**Origem:** módulo Operação/OS.
**Visibilidade:** flag `visivel_cliente` no anexo.

---

### Export 7: Histórico de OS / Faturas / Certificados em CSV (LGPD — portabilidade)

**Propósito:** atender direito de **portabilidade** do cliente (LGPD Art. 18 V).
**Formato:** CSV UTF-8 BOM, separador `;`.
**Regulado?:** LGPD (direito do titular).
**Disparo:** cliente solicita via tela "Perfil > LGPD > Exportar meus dados" (US a criar — recomendado adicionar em V2).
**Conteúdo:** todos os dados pessoais do cliente armazenados pelo tenant, em formato estruturado.
**Retenção do arquivo gerado:** 7 dias na URL temporária.

---

### Export 8: Aceite de termos (PDF — comprovante)

**Propósito:** quando cliente aprova orçamento, gera PDF de comprovante imutável.
**Formato:** PDF.
**Conteúdo:** dados do orçamento + ts + IP + identidade + texto do termo aceito (versionado).
**Imutabilidade:** WORM em Backblaze B2 (trilha auditoria).
**Retenção:** mesma do orçamento (geralmente 5 anos — matriz Receita).

---

## Exports inter-módulos

- **Portal → Auditoria:** todo download relevante gera evento em WORM (`Portal.CertificadoBaixado`, `Portal.SegundaViaGerada`, `Portal.NFeBaixada`).
- **Portal → Notificações:** comprovantes de aprovação podem ser enviados por e-mail (anexo).

## Versionamento de export regulado

- Mudança em schema NF-e SEFAZ → ADR + janela definida pela SEFAZ.
- Mudança em layout certificado RBC → ADR + janela CGCRE/INMETRO.

## Como esta lista evolui

- Export novo → adicionar + definir retenção.
- Mudança em formato regulado → ADR + validar com auditor (advogado-saas-regulado ou consultor-rbc-iso17025).
- Export deprecado → `@deprecated`.

## Notas de segurança

- TODAS URLs de download são **assinadas + temporárias** (≤ 24h para boleto, ≤ 7 dias para CSV LGPD).
- Cross-tenant rigorosamente bloqueado por `INV-TENANT-001..004`.
- Logs de download em WORM (atende ISO 17025 + LGPD rastreabilidade).
- Arquivos contendo CPF/CNPJ seguem `SEC-*` (criptografia repouso + trânsito).
