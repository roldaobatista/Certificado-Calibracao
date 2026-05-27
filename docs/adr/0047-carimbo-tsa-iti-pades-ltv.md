---
owner: roldao
revisado-em: 2026-05-27
status: aceito
aceito-em: 2026-05-27
diataxis: explanation
audiencia: agente
relacionados:
  - docs/adr/0009-onde-a3-assina.md
  - docs/adr/0046-ocsp-crl-revogacao-online.md
  - docs/dominios/metrologia/modulos/certificados/prd.md
---

# ADR-0047 — Carimbo do tempo TSA-ITI + PAdES-LTV obrigatório em certificado de calibração

> **Status:** PROPOSTA (2026-05-23). Detectado pela auditoria Onda 8 (auditor regulatório 7): INV-017 exige "carimbo ITI", mas não cobre como o PDF do certificado de calibração mantém validade **25 anos** (ISO 17025 cl. 8.4 + INV-010) se cert A3 do RT expira em 1-3 anos. Sem **PAdES-LTV (Long-Term Validation)**, validação retroativa falha após 1ª expiração.

## Contexto

ICP-Brasil + Lei 14.063/2020 + ITI DOC-ICP-15 exigem carimbo do tempo de TSA acreditada pra assinatura ter validade legal de longo prazo. Padrão técnico recomendado pra documentos de retenção longa: **PAdES-LTV** (PDF Advanced Electronic Signature - Long-Term Validation), perfil ETSI TS 102 778-4.

PAdES-LTV embute no PDF:
- Cadeia de cert do signatário até a AC raiz (ICP-Brasil)
- Respostas OCSP/CRL da hora da assinatura (prova "estava vigente naquele momento")
- Carimbo do tempo de TSA acreditada (prova **quando** foi assinado, sem confiar no relógio do signatário)
- Periodicamente, **re-timestamps** com nova TSA pra estender validade além da expiração da TSA original (DSS — Document Security Store)

Cert de calibração tem retenção ISO 17025 8.4: ciclo de calibração do cliente + 1 ciclo (~5-25 anos). RT assina com A3 que expira em 1-3 anos. Sem LTV, em ano 4 a validação falha — "não consigo provar que cert estava vigente em 2026 quando assinou".

Provedores TSA acreditados ICP-Brasil: ITI (próprio), Serpro, Certisign, AC SAFEWEB, AC SOLUTI. Aferê adota **TSA-ITI como default** (governamental, gratuito até limite de uso, alinhado com ITI DOC-ICP-15); fallback ICP-Brasil comercial (Certisign/Serpro) se TSA-ITI timeout > 5s.

## Decisão

1. **Toda emissão de certificado de calibração** (US-CER-002) gera PDF assinado em formato **PAdES-LTV** (perfil B-LTA — Long-Term with Archive timestamps).
2. **Provedor TSA default:** TSA-ITI (https://timestamp.iti.gov.br). Configurável por tenant pra fallback comercial.
3. **DSS embutido:** PDF carrega respostas OCSP da hora da assinatura + cadeia de cert completa até AC raiz.
4. **Re-timestamp anual:** job Celery anual varre certs emitidos há > 1 ano sem re-timestamp, gera nova camada DSS+timestamp (preserva validação além da expiração da TSA original).
5. **Validação no consumo:** ao gerar PDF de visualização/download, sistema valida cadeia + LTV. Se inválida, marca certificado com flag `validacao_ltv_falhou` + alerta P1 (não bloqueia download — auditoria precisa do registro).
6. **NF-e fiscal NÃO exige LTV** (NF tem ciclo 5 anos + WORM XML; LTV é trade-off custo TSA × benefício longevidade).

## Alternativas consideradas

1. **PAdES-B (básico, sem LTV)** — REJEITADA. Validação falha após expiração do A3 do signatário (1-3 anos). Cgcre questiona aos 2 anos.
2. **PAdES-T (com timestamp único, sem DSS)** — REJEITADA. TSA também expira; sem re-timestamp, validação cai em ~10 anos.
3. **Manter só carimbo ITI sem perfil PAdES-LTV** — REJEITADA. Sem DSS + re-timestamp anual, retenção ISO 8.4 (25 anos) é inviável.
4. **Carimbo do tempo opcional configurável** — REJEITADA. INV-017 já cobra obrigatório; aqui só refina o formato.

## Consequências

### Positivas
- Cert calibração validável por 25+ anos sem depender de A3 do RT estar vigente
- ISO 17025 8.4 + Lei 14.063/2020 atendidos
- INV-CER-LTV-001 satisfeita
- Auditoria retroativa Cgcre: PDF prova "RT X assinou em DD/MM/YYYY com A3 fingerprint Y vigente, OCSP good, carimbo TSA-ITI"

### Negativas
- Custo TSA: TSA-ITI gratuita até limite (~10k req/dia); acima disso fallback comercial custa ~R$0,01-0,05/timestamp
- PDF cresce ~15-50KB por LTV (cadeia + OCSP + timestamp); negligível
- Job anual re-timestamp adiciona custo operacional (1x/cert/ano) — para 100k certs/ano, ~100k timestamps/ano (~R$5k/ano se cair em comercial)
- Dependência TSA externa (mitigada por fallback multi-provedor)

## Itens a fazer

- [ ] Implementar geração PAdES-LTV no módulo `metrologia/certificados` (lib `pyhanko` ou similar)
- [ ] Configurar TSA-ITI como provedor default + fallback Serpro/Certisign
- [ ] Job Celery anual `re_timestamp_certificados_calibracao`
- [ ] AC US-CER-002 (`metrologia/certificados/prd.md`) — adicionar exigência LTV + provider TSA
- [ ] INV-CER-LTV-001 em REGRAS-INEGOCIAVEIS.md
- [ ] Teste E2E: emitir cert → validar PAdES-LTV; mock expiração A3 → validação ainda passa via DSS
- [ ] Dashboard "saúde TSA por provedor" (latência, falhas, custos)

## Aprovação

- [ ] Roldão (decisor)
- [ ] Auditor-segurança
- [ ] Consultor-RBC-ISO17025

## Referências

- ETSI TS 102 778-4 (PAdES-LTV)
- ITI DOC-ICP-15 + DOC-ICP-15.03
- Lei 14.063/2020 + MP 2.200-2/2001
- ISO 17025 cl. 8.4
- ADR-0009, ADR-0046, ADR-0048
- INV-010, INV-017, INV-CER-LTV-001 (REGRAS-INEGOCIAVEIS.md)
