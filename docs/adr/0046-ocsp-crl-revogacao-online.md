---
owner: roldao
revisado-em: 2026-05-23
status: proposta
diataxis: explanation
audiencia: agente
relacionados:
  - docs/adr/0009-onde-a3-assina.md
  - docs/adr/0047-carimbo-tsa-iti-pades-ltv.md
  - docs/adr/0048-a3-ecpf-rt-cadastro.md
  - docs/dominios/seguranca/modulos/certificados-digitais/prd.md
---

# ADR-0046 — Verificação OCSP/CRL online em cada assinatura

> **Status:** PROPOSTA (2026-05-23). Detectado pela auditoria Onda 8 (auditor regulatório 7): assinatura de certificado de calibração e emissão de NF não verificam **status de revogação** do A3/A1 contra a AC emissora. Cert revogado pela AC ICP-Brasil (titular perdeu, comprometeu PIN, AC suspendeu) seguiria assinando até alguém perceber manualmente.

## Contexto

ICP-Brasil exige (MP 2.200-2/2001 + ITI DOC-ICP-15.03) que cada **uso** de certificado verifique status de revogação contra a AC emissora. Mecanismos:
- **OCSP (Online Certificate Status Protocol):** consulta HTTP em tempo real ao OCSP Responder da AC (URL no `AIA` do cert). Retorna `good`/`revoked`/`unknown`. Latência típica 100-800ms; timeout recomendado 3s.
- **CRL (Certificate Revocation List):** lista publicada pela AC (URL no `CDP` do cert), baixada periodicamente. Snapshot local — pode estar desatualizada.

Estado atual no projeto: nenhum dos dois implementado. ADR-0009 cobre **onde** o A3 assina (cliente-side via Lacuna), mas não cobre verificação de revogação. INV-017 só exige "A3 obrigatório", sem revogação online.

Impacto regulatório: cert revogado emitindo certificado de calibração RBC = certificado **sem valor legal** (titularidade inválida) + Cgcre nota em supervisão (R-018 score 25 reabre).

## Decisão

Criar porta `CertificadoDigital.verificar_status(cert_id) → {status, verificado_em, fonte}` no módulo `certificados-digitais` (PRD do mesmo nome). Verificação obrigatória em:

1. **Cadastro** de A3 novo (US-CER-DIG-002/003) — rejeita se já revogado
2. **Cada assinatura** de certificado de calibração (US-CER-002 — módulo `metrologia/certificados`)
3. **Cada emissão de NF** com cert A3 do tenant (US-FIS-001 — módulo `fiscal`)
4. **Job diário** varre todos certs ativos do tenant, atualiza `status_local`, alerta revogações

### Mecânica

- **OCSP primeiro** — HTTP POST ao Responder URL (extraído do `AIA`). Timeout 3s.
- **Fallback CRL** se OCSP timeout/erro — consulta CRL local (cache atualizado a cada 1h por cert + diário 02:00 BRT).
- **Cert RBC (calibração):** se nem OCSP nem CRL atual (≤1h) disponíveis, **bloqueia hard** com 503 `VERIFICACAO_INDISPONIVEL`. Cgcre exige controle demonstrável.
- **Cert não-RBC (NF, declaração):** permite com flag `verificacao_degraded=true` em audit. Trade-off operacional aceito (NF não pode parar; risco mitigado por job diário).
- **OCSP `revoked`:** bloqueia 409 + publica `A3.RevogacaoDetectada` + escalação P1 ao dono Aferê + marca `status_local=revogado` (subsequentes não chamam OCSP).
- **OCSP `unknown`:** trata como `degraded` (Responder não conhece o cert — pode ser cert de AC não cadastrada; sinaliza pra investigação).

### Cache + invalidação

- Resposta OCSP cacheada por 1h (alinhado com `nextUpdate` típico). Cert RBC força fresh fetch.
- CRL baixada a cada 1h por cert ativo + diário 02:00 BRT consolidado. Persistida em tabela `cert_crl_snapshots` por AC.
- `status_local=revogado` é **sticky** — nunca volta pra `vigente` automaticamente (titular renova = nova entrada).

## Alternativas consideradas

1. **Só validar `valido_ate`** — REJEITADA. Cert revogado tem `valido_ate` no futuro; passa despercebido. Exatamente o gap detectado pela auditoria.
2. **Só CRL diária, sem OCSP** — REJEITADA. Janela de 24h entre revogação na AC e detecção no Aferê é gap regulatório inaceitável pra cert RBC.
3. **OCSP sem fallback CRL** — REJEITADA. Responders ICP-Brasil têm SLA variável; sem fallback, emissões param.
4. **Deixar verificação no Web PKI Lacuna (ADR-0009)** — REJEITADA. Lacuna assina client-side; verificação de revogação precisa ser server-side e auditável (Aferê precisa do registro do `verificado_em` em WORM, não confiar no que o navegador relatou).

## Consequências

### Positivas
- Cert revogado bloqueia uso em < 1h (OCSP cacheado) ou em tempo real (cert RBC força fresh)
- Audit WORM completo: `quem usou qual cert quando, status OCSP retornou X`
- R-018 (Cgcre supervisão) score baixa de 25 → ≤10
- INV-A3-OCSP-001 satisfeita

### Negativas
- Latência adicional 100-800ms em cada assinatura (mitigado por cache)
- Dependência externa nova (OCSP Responder ICP-Brasil) — risco SLA upstream (mitigado por CRL fallback)
- Custo operacional: monitorar Responder downtime e CRL stale por AC

## Itens a fazer

- [ ] Implementar porta `CertificadoDigital.verificar_status()` em `certificados-digitais`
- [ ] Job Celery diário `atualizar_crl_acs` + on-demand 1h por cert ativo
- [ ] Hook semgrep: chamadas a `assinar_certificado()` / `emitir_nf()` exigem `verificar_status()` imediatamente antes
- [ ] Teste E2E: revoga cert na AC sandbox → próxima emissão bloqueia em < 1h
- [ ] INV-A3-OCSP-001 em REGRAS-INEGOCIAVEIS.md
- [ ] Dashboard "saúde OCSP/CRL por AC" pra operação Aferê

## Aprovação

- [ ] Roldão (decisor)
- [ ] Auditor-segurança
- [ ] Consultor-RBC-ISO17025

## Referências

- MP 2.200-2/2001 art. 10
- ITI DOC-ICP-15.03 (verificação de revogação)
- RFC 6960 (OCSP)
- RFC 5280 (CRL)
- ADR-0009, ADR-0047, ADR-0048
- INV-017 (REGRAS-INEGOCIAVEIS.md)
