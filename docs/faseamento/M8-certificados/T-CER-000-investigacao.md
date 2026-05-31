---
owner: agente-ia
revisado-em: 2026-05-31
status: stable
diataxis: reference
audiencia: [agente, tech-lead, consultor-rbc]
marco: M8-certificados
tipo: investigacao-p0
---

# T-CER-000 — Investigação P0 do seam de emissão (regra #0)

> Mapa do que JÁ existe (PRONTO) vs o que FALTA, para a emissão metrológica do
> certificado. Base da `spec.md` §2. Investigado 2026-05-31 (subagente Explore + leitura direta).

## PRONTO (seam consumível agora)

| SEAM | Arquivo:linha | Nota |
|------|---------------|------|
| Estado terminal `APROVADA` (terminal, imutável; trigger PG 0002) | `domain/metrologia/calibracao/enums.py` (~30) | fluxo 2 etapas |
| 1ª conferência (revisor) `EM_REVISAO_1→AGUARDANDO_2A_CONFERENCIA` | `application/metrologia/calibracao/aprovar_revisao.py` (~103) | snapshot competência revisor |
| 2ª conferência (conferente) `→APROVADA` + ADR-0026 | `application/metrologia/calibracao/aprovar_2a_conferencia.py` (~120) | INV-CAL-FRAUDE-CONF-001 (conferente≠revisor≠executor) |
| Pontos medidos `LeituraSnapshot` (`ponto_calibracao`, `valor_lido`, `unidade`, `numero_repeticao`, `timestamp`) | `domain/metrologia/calibracao/entities.py` (~259) | WORM; SEM U na leitura |
| `repo.obter_leituras_por_calibracao(calibracao_id)` | `infrastructure/calibracao/repositories.py` | |
| Incerteza `OrcamentoIncertezaSnapshot` (`U_expandida`, `k`, `nivel_confianca`, `versao_motor_calculo`) | `domain/metrologia/calibracao/entities.py` (~200) | **1 por orçamento** (Q1 da spec) |
| Faixa declarada `grandeza_calibrada` + `faixa_calibrada_declarada` (ADR-0076) | `domain/metrologia/calibracao/entities.py` (~162) | preenchida na configuração; ambas None ou ambas preenchidas |
| `FaixaMedicao.contem(valor)` | `domain/metrologia/value_objects.py` (~101) | reconciliação pontos⊆declarada |
| Porta `cmc_para(*, tenant_id, grandeza, ponto, data) -> Decimal\|None` | `infrastructure/metrologia/escopos_cmc/query_service.py` (~77) | menor CMC no ponto; None bloqueia RBC |
| `cobertura.avaliar_u_cmc(u_reportada, cmc_no_ponto) -> (bool,str)` + `menor_cmc_por_faixa` | `domain/metrologia/escopos_cmc/cobertura.py` | INV-ECMC-009 |
| Snapshot `EscopoUsado` (campos `u_reportada`/`cmc_no_ponto`/`u_atende_cmc` preenchidos na emissão) | `domain/metrologia/escopos_cmc/entities.py` (~92) | ADR-0074 cond. 2 |
| Snapshot `ProcedimentoUsado` (`.snapshot_minimo()` = codigo/versao/numero_revisao/hash_anexo) | `domain/metrologia/procedimentos_calibracao/entities.py` (~77) | congelado na configuração |
| VO `NumeroCertificado` (`^[A-Z0-9]{2,16}-\d{4}-\d{6}$`) | `domain/metrologia/value_objects.py` (~213) | NIT-DICLA-021 |
| Stub `Certificado` (id/tenant/equipamento/status RASCUNHO/EMITIDO/REVOGADO + trigger imutabilidade equipamento) | `infrastructure/certificados/models.py` (~51) | **estender** sem quebrar trigger |
| Evento bus `calibracao.aprovada` (MAPA 23 eventos) | `domain/metrologia/calibracao/entities.py` (~452) | M8 consome |
| Padrão WORM `append_evento_calibracao` (advisory lock + `sequencia_local` + `evento_hash` v<NN>$base64) | `application/metrologia/calibracao/append_evento_calibracao.py` (~107) | replicar p/ EventoDeCertificado |
| Numeração inviolável M4 (`calibracao_numero_seq_global` + trigger `numero_exibido`) | `application/metrologia/calibracao/criar_calibracao.py` | molde p/ sequence cert |
| Perfil `tenant_perfil_e` + snapshot `perfil_no_evento` | `infrastructure/authz/predicates.py` + middleware | ADR-0067 |

## FALTA (diferido — Wave A / infra externa)

| Componente | GATE rastreado |
|------------|----------------|
| Sequence PG `certificado_numero_seq` + `NumeroReservado` + trigger virada anual | constrói nesta frente (Fatia 1b) |
| Motor PDF/A-3 (Jinja2→HTML→PDF ISO 19005-3) | GATE-CER-PDF Wave A |
| A3/Lacuna (assinatura client-side ADR-0009) | GATE-CER-A3 Wave A |
| OCSP/CRL (ADR-0046) + TSA-ITI (ADR-0047) | GATE-CER-OCSP / GATE-CER-TSA Wave A |
| Portal do cliente (US-CER-006) + QR público (US-CER-009) | GATE-CER-PORTAL / GATE-CER-QR Wave A |
| E-mail (ADR-0060 EmailTemplateProvider, US-CER-005/018) | GATE-CER-EMAIL Wave A |
| Export ANVISA/PDF-A3 (US-CER-016/017) | GATE-CER-EXPORT Wave A |
| Recall/suspensão/errata (US-CER-018/019/020) | GATE-CER-POSEMISSAO Wave A |
| `metrologia/licencas-acreditacoes` (bloqueio CGCRE/ART vencida) | módulo #5 da ordem |

## Conclusão

A emissão LÓGICA (reconciliação + snapshot + numeração + perfil + WORM) é construível
AGORA, sem nenhuma infra externa. Fecha `GATE-CAL-EMISSAO-RECONCILIA-FAIXA` +
`GATE-ECMC-U-MAIOR-CMC`. PDF/assinatura/distribuição plugam depois sobre o snapshot
imutável.
