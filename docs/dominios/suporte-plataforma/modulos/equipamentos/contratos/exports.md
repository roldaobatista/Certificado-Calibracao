---
owner: Roldão
revisado-em: 2026-05-18
status: stable
modulo: equipamentos
dominio: suporte-plataforma
versao: 2
---

# Contratos de Export — Equipamentos do cliente

> **v2 (2026-05-18):** Etiqueta separada em duas (RBC C2 — identificação permanente vs selo de calibração re-emitido a cada calibração). Adição de PDF de termo de transferência e PDF de termo de devolução.

## Exports

### Export 1a: Etiqueta de identificação permanente (PDF)

**Propósito:** etiqueta física durável colada no instrumento — TAG + QR (estável).
**Formato:** PDF (A6 default; label 50x80mm opcional).
**Material recomendado (configurável por tenant em perfil A):** poliéster laminado (durabilidade ≥5 anos exposta) ou metálica alumarca.
**Regulado:** não.
**Campos obrigatórios:** QR (URL assinada — INV-051), TAG, NS, logo do tenant.
**Campos opcionais:** modelo, faixa, cliente (em tenants que escolhem expor).
**Assinatura digital:** não.
**Imutabilidade pós-emissão:** não (re-emissão revoga QR anterior — janela 90 dias se `manter_anterior_ativo=true`).
**Retenção:** ver `../../../conformidade/comum/retencao-matriz.md` linha "Cadastro de equipamento (ativo)".

**Exemplo (mock):**
```
+---------------+
|  [QR Code]    |
|  TAG: BAL-001 |
|  NS:  ABC123  |
|  [logo tenant]|
+---------------+
```

---

### Export 1b: Selo de calibração (PDF) — entregue pelo módulo `certificados`

**Propósito:** etiqueta complementar com nº de certificado vigente + data calibração + data próxima — re-emitida a cada calibração.
**Formato:** PDF.
**Responsável:** módulo `certificados` (Wave A+) — não é responsabilidade direta deste módulo.
**Integração:** este módulo expõe `Equipamento.numero_etiqueta_calibracao_atual` (FK) que o módulo `certificados` atualiza via porta inversa quando um cert é emitido.

---

### Export 2: Ficha do equipamento (PDF para impressão/envio ao cliente)

**Propósito:** entregar ficha do equipamento ao cliente final — só no Modo A (mesmo tenant).
**Formato:** PDF.
**Regulado:** não.
**Campos obrigatórios:** dados cadastrais + histórico de calibração (datas + nº certificado) + próxima calibração.
**Campos opcionais:** OS abertas, fotos do equipamento (sem rosto identificável — política RAT-EQP-FOTO).
**Assinatura digital:** não (Wave futura — assinatura do RT).
**Retenção:** ver matriz.

---

### Export 3: Lista de equipamentos (CSV/XLSX)

**Propósito:** export operacional para auditoria interna ou migração.
**Formato:** CSV / XLSX.
**Regulado:** não.
**Campos:** TAG, NS, fabricante, modelo, faixa, classe, cliente, status, perfil_tenant_no_cadastro, última calibração, próxima calibração.
**Filtros aplicáveis:** mesmos da Tela 1 (com escopo restritivo por papel — advogado C3).
**Autorização:** `equipamento.exportar_lista` — perfil admin_tenant ou metrologista.

---

### Export 4: Termo de transferência (PDF — US-EQP-004 / advogado D2)

**Propósito:** gerar PDF do termo de transferência assinado entre cedente e cessionário pra arquivo do tenant + cliente.
**Formato:** PDF.
**Regulado:** boa prática civil (Lei 14.063/2020).
**Campos obrigatórios:** TAG, NS, fabricante, modelo, motivo_categoria, hashes dos clientes, timestamps de aceite, IP hash dos aceitantes, versão do texto.
**Assinatura digital:** Lei 14.063/2020 art. 4º I (simples — MVP-1) ou A3 (V2 configurável).
**Imutabilidade:** PDF gravado em Backblaze B2 WORM com hash; reabertura cria nova OS de transferência + novo termo.
**Retenção:** 5 anos pós-término do vínculo cedente (matriz fiscal).

---

### Export 5: Termo de devolução do equipamento (PDF — US-EQP-006)

**Propósito:** comprovante de devolução do equipamento ao cliente após calibração; cliente assina recebimento.
**Formato:** PDF.
**Campos obrigatórios:** TAG, NS, data de entrada, data de devolução, condição visual chegada × devolução, foto chegada × devolução, número do certificado vigente, assinatura do recebedor (cliente).
**Assinatura:** eletrônica simples via portal cliente OU física no momento da retirada (digitalizada).
**Retenção:** 5 anos (audit + execução contrato).

---

### Export 6: Foto do equipamento (JPEG/PNG — RAT-EQP-FOTO)

**Propósito:** evidência visual do estado do equipamento (cadastro, recebimento, devolução).
**Formato:** JPEG/PNG, ≤5MB.
**Processamento server-side obrigatório:**
- **EXIF removido** (GPS, timestamp do device, modelo do celular) — anti-PII indireta.
- (V2) Detecção facial automática + blur sugerido se rosto identificável.
- Validação tamanho/formato.
**Storage:** Backblaze B2 com chave KMS por tenant (crypto-shredding).
**Retenção:** vigência equipamento + 5 anos pós-sucateamento; 25 anos se compõe evidência ISO 17025 cl. 7.4.4.

---

## Exports inter-módulos

- Lista de equipamentos consumida pelo módulo **Calibração** (Metrologia) ao iniciar OS — via porta `CertificadoQueryService` reversa quando módulo certificados nascer.
- Lista de equipamentos do cliente consumida por **Cliente 360°** (Comercial) — via API `GET /v1/equipamentos?cliente_id=...`.
- Termo de transferência (Export 4) consumido pelo módulo **portal-cliente** quando cessionário acessa aceite (Tela 8 — advogado E4).

## Versionamento

- Mudança de layout da etiqueta → bump CHANGELOG; etiquetas antigas continuam válidas (QR é estável; hash não muda com layout).
- Mudança no termo de transferência → bump `texto_versao_id`; termos antigos continuam imutáveis (impressos em WORM).

## Como evolui

- Export novo → adicionar + linkar US-EQP-NNN.
- Layout de etiqueta com QR → coordenar com módulo de impressão (Wave A+).
- Adição de campo PII num export → revisar com subagente `advogado-saas-regulado` antes de mergear.
