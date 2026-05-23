---
adr: 0044
titulo: Exportação regulatória de certificado (ANVISA / SAÚDE / INMETRO) — PDF/A-3 com XML embedded
status: proposta
data: 2026-05-23
proposto-por: agente (Onda 7 — auditor 6, achado C2-CAL)
revisado-por: tech-lead-saas-regulado + advogado-saas-regulado + consultor-rbc-iso17025
bloqueia-fase: Wave A Marco 5 (certificados) + 1º tenant setorial regulado (farma/hospital/medicamento)
depende-de: ADR-0007 (camada domínio + gerador spec→código), ADR-0009 (A3 client-side), ADR-0029 (canonicalização texto probatório)
---

# ADR-0044 — Exportação regulatória ANVISA/SAÚDE/INMETRO — PDF/A-3 longa duração

## Contexto

Cert PDF "padrão" hoje é HTML→PDF com assinatura A3 PKCS#7. Atende cliente comum, NÃO atende três setores regulados que são alvo de Wave A:

1. **ANVISA (farma + hospital):** RDC 658/2022 + RDC 16/2013 exigem dossiê de calibração com schema XML estruturado anexo ao PDF + retenção 25 anos.
2. **SAÚDE (hospital):** auditores estaduais pedem dados em formato consumível por sistema próprio (não scrapping de PDF).
3. **INMETRO (lacre + balança comercial):** Portaria INMETRO 157/2022 exige formato compartilhável entre OSCBM (Organismo de Calibração e Bal. Metrológica), CGCRE e Rede Brasileira de Calibração.

Sem formato canônico:
- Tenant farma rejeita Aferê na cotação ("seu sistema não exporta XML estruturado").
- Auditor de campo pede planilha manual → tenant trabalha 4h por auditoria.
- Em 5/10/25 anos, cert PDF "padrão" pode não abrir (Acrobat sumiu, fonte desabilitada). PDF/A-3 garante leitura ISO 19005-3:2012.

## Decisão

### 1. Formato canônico = PDF/A-3 com XML embedded

- Geração via WeasyPrint config `pdfa=3` (já usado no projeto desde Marco 2 com mitigação CVE-2025-68616).
- XML anexo ao PDF/A-3 como `EmbeddedFile`:
  - Schema raiz: `iso17025-cert-v1.xsd` (definido pela RBC; Aferê mantém cópia versionada em `docs/dominios/metrologia/modulos/certificados/schemas/`).
  - Extensões setoriais opcionais conforme tenant declara setor:
    - `anvisa-ext-v1.xsd` (cliente_cnpj, anvisa_aut_func, hospital_cnes, etc.)
    - `inmetro-ext-v1.xsd` (lacre_numero, balancao_modelo_inmetro, etc.)
    - `saude-ext-v1.xsd` (cnes_unidade, ministerio_saude_codigo_servico).
- Hash SHA-256 do XML embedded gravado em `Certificado.xml_embedded_hash` (probatório — referencia `ADR-0029`).

### 2. Carimbo TSA-ITI obrigatório

- TSA (Time-Stamp Authority) do ITI carimba o PDF/A-3 final.
- Implementação detalhada em ADR futura (Onda 8 GATE-TSA-ITI-1). Esta ADR define **requisito**: cert exportado regulatório SEM carimbo TSA-ITI é inválido para fins regulatórios.
- Pré-Onda 8, cert nasce com carimbo TSA-ITI placeholder + flag `aguardando_tsa_iti=true` — Wave A endurece bloqueio.

### 3. Retenção 25 anos + WORM B2

- PDF/A-3 + XML embedded vai pra Backblaze B2 bucket WORM (`certificados-wormA/<tenant>/<ano>/<cert_id>.pdf`).
- Crypto-shredding por tenant (LGPD direito ao esquecimento) NÃO aplica a cert regulatórios — referencia `ADR-0021` Zona A (eliminação efetiva proibida; anonimização-em-lugar do snapshot do cliente apenas).

### 4. US novas

- **US-CER-016 (exportação ANVISA):** RT marca cert como "destino ANVISA" → sistema gera PDF/A-3 + XML com `anvisa-ext-v1.xsd` + carimbo TSA-ITI. Disponível no portal cliente com flag `regulatorio`.
- **US-CER-017 (PDF/A-3 longa duração 25a):** todo cert nasce PDF/A-3 (não só regulatórios) — garante abertura 2026→2051. WORM B2 obrigatório.

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| PDF "padrão" + planilha CSV separada | Tenant precisa entregar 2 arquivos; auditor reclama de "pacote frouxo" |
| JSON-LD ao invés de XML | ANVISA/INMETRO ainda exigem XML; JSON-LD vira segundo fork |
| PDF/A-1 (mais antigo, sem embedded) | Não permite anexar XML estruturado → não atende ANVISA |
| XAdES ao invés de PKCS#7 + TSA-ITI | XAdES é em XML separado; conflita com modelo "cert é PDF assinado" |

## Consequências

### Positivas

- Atende 3 setores regulados (farma, hospital, INMETRO) sem fork por setor.
- Cert legível em 2051 (PDF/A-3 ISO 19005-3:2012).
- TSA-ITI fecha vetor de fraude "regredir clock do servidor".
- B2 WORM cumpre `INV-001` (trilha imutável) + retenção 25a (`INV-010`).

### Negativas (mitigáveis)

- WeasyPrint custom `url_fetcher` precisa estender pra suportar `EmbeddedFile` — débito Wave A.
- TSA-ITI tem latência (round-trip 1-3s) → adicionar fila assíncrona com retry.
- Custo B2 cresce ~3x (PDF/A-3 + XML é maior que PDF puro) — aceitável (5GB/tenant/ano estimado).

## Non-goals

- NÃO define schema XML em detalhe — esta ADR cria **requisito** + referencia XSDs (a serem versionados Wave A).
- NÃO trata exportação para sistemas estrangeiros (FDA, EMA) — fora do escopo MVP-1.
- NÃO altera cert "padrão" não-regulatório — ele também vira PDF/A-3 (US-CER-017) mas sem extensões setoriais nem TSA-ITI obrigatório (na verdade ele recebe TSA-ITI por default Wave A).

## Invariantes novas

- **INV-CER-EXP-001:** todo cert regulatório (US-CER-016/017) é PDF/A-3 + XML embedded validado contra XSD + carimbo TSA-ITI + persistido em B2 WORM. Cert regulatório SEM os 4 elementos = inválido.

## Implicações pro faseamento

- Wave A Marco 5 implementa US-CER-016 + US-CER-017 + URS-CAL-EXP-001.
- ADR Onda 8 trava implementação concreta de TSA-ITI (GATE-TSA-ITI-1).
- GATE-CER-EXP-XSD: XSDs versionados em `docs/dominios/metrologia/modulos/certificados/schemas/` antes de codar.

## Status

Proposta — aguarda aceite Roldão + parecer consultor-rbc-iso17025 antes de 1º tenant setorial regulado.
