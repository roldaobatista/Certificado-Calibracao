---
adr: 0045
titulo: Ciclo de vida pós-emissão — Recall, Suspensão, Errata (além de Reemissão/Cancelamento)
status: proposta
data: 2026-05-23
proposto-por: agente (Onda 7 — auditor 6, achado C3-CAL)
revisado-por: tech-lead-saas-regulado + advogado-saas-regulado + consultor-rbc-iso17025
bloqueia-fase: Wave A Marco 5 (certificados) + 1º tenant externo pago
depende-de: ADR-0021 (anonimização vs retenção), ADR-0025 (validação software ISO 17025), ADR-0029 (canonicalização texto probatório), INV-CAL-VERSAO-001
---

# ADR-0045 — Recall, Suspensão e Errata de certificado

## Contexto

US-CER-004 (reemissão) + US-CER-003 AC-3 (cancelamento) cobrem 2 cenários só. Faltam 3 cenários que viram NC crítica em supervisão CGCRE quando não existem:

1. **Recall por bug do motor de cálculo** (ISO 17025 cl. 7.10 + 7.11 + EA-4/02):
   - Bug descoberto em `versao_motor_calculo=1.2.3` afeta 47 cert emitidos em jan/2026.
   - Sem Recall formal: tenant manda e-mail ad-hoc, cliente abre processo, CGCRE encontra cert nulo "vivo" → suspensão da acreditação.
2. **Suspensão temporária** (ISO 17025 cl. 7.10):
   - Padrão descoberto descalibrado retroativo → cert depende daquele padrão precisa ficar "em quarentena" enquanto investiga. NÃO é cancelamento (pode voltar).
3. **Errata simples** (boa prática — typo no nome do cliente, data trocada):
   - Reemissão por typo é fora de proporção (numeração nova + assinatura A3 + envio). Errata permite ajuste de campo descritivo sem mudar resultado técnico.

Cada um tem evento próprio, regras de notificação (ANPD/CGCRE/cliente) e impacto distinto no `status` do cert.

## Decisão

### 1. Recall (cl. 7.10 + 7.11)

- Comando `recallCertificadoPorBug(cert_id, motivo_bug, replay_validacao_id)`:
  - Disparado quando bug em `versao_motor_calculo` é confirmado via replay determinístico (ADR-0025 — 2º caminho de cálculo).
  - Identifica TODOS os cert que usaram a versão buggy → batch recall.
- Evento `CertificadoRecallEmitido(certificado_id, motivo_bug, replay_validacao_id, correlation_id)`:
  - Notifica cliente em **24h** (CDC art. 6º + LGPD art. 9º) — canal preferencial cliente + e-mail backup.
  - Notifica ANPD em **24h** se dados foram usados em decisão que afetou titular (LGPD art. 48).
  - Notifica CGCRE em **30d** (ISO 17025 cl. 7.10 + NIT-DICLA-021 política de incidente).
- Status do cert → `RECALL_ATIVO`. Visualização pública (QR Code) mostra "este certificado foi objeto de recall em DD/MM/AAAA — entre em contato com o laboratório emissor".
- Recall NÃO retira cert do WORM (preservação probatória — `INV-CAL-WORM-001`); marca status.

### 2. Suspensão

- Comando `suspenderCertificado(cert_id, suspenso_ate, motivo_padrao_descalibrado)`:
  - Estado intermediário não-cancelado.
  - Disparado quando padrão usado é descoberto descalibrado retroativo (cl. 7.10) ou quando NC aberta investiga uso técnico.
- Evento `CertificadoSuspenso(certificado_id, suspenso_ate, motivo_padrao_descalibrado, correlation_id)`.
- Status cert → `SUSPENSO`. Vigência **paralisada** (validade do recalibração não corre durante suspensão — relógio para; retoma se voltar).
- Comando `levantarSuspensaoCertificado(cert_id, justificativa)` quando investigação fecha sem necessidade de recall.
- Visualização pública mostra "este certificado está em verificação pelo laboratório — pode estar suspenso temporariamente".

### 3. Errata

- Comando `emitirErrataCertificado(cert_id, campo_corrigido, valor_anterior, valor_novo, justificativa)`:
  - Aplica APENAS a campos descritivos: `cliente_endereco`, `instrumento_serie_str` (typo), `data_recebimento_label` (typo de display), `observacoes_gerais`.
  - **Proibido** errata em campos técnicos: `valor_lido`, `U_expandida`, `decisao`, `padroes_usados`, `regra_decisao`. Mudança técnica = reemissão (US-CER-004).
  - Sequência incremental por cert: `errata_seq=1, 2, 3, ...`
- Evento `CertificadoErrataEmitida(certificado_id, errata_seq, campo_corrigido, justificativa, correlation_id)`.
- Errata gera "apêndice" PDF anexo ao cert original (não substitui o PDF original — preservação probatória). Visualização pública mostra cert + lista de erratas.
- Numeração de cert NÃO muda; assinatura A3 do RT autor da errata é capturada no apêndice.

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| Reemissão pra tudo (typo + bug + padrão) | Inflate numeração + faz cliente baixar cert novo a cada typo |
| Cancelamento + reemissão pra Recall | Quebra rastreabilidade ("certificado N existe?" — sim, com status RECALL — auditor consegue rastrear) |
| Recall sem notificar ANPD | Quando bug afetou decisão sobre titular (cliente farma usou cert pra liberar lote), risco ANPD existe |
| Errata em campo técnico | Vira porta de fraude — "errata" pra mudar U_expandida sem audit |

## Consequências

### Positivas

- Cobre 3 cenários que CGCRE pesquisa em supervisão.
- Errata desinfla numeração de cert.
- Suspensão preserva vigência durante investigação (paralisa relógio — defensável legalmente).
- Recall em batch via `versao_motor_calculo` ativa workflow de "incidente metrológico" inteiro.

### Negativas (mitigáveis)

- 5 estados a mais no cert (`RECALL_ATIVO`, `SUSPENSO`, `ERRATA_APLICADA` flag). UI precisa explicar.
- ANPD notification em 24h exige consumer rápido — usar `procrastinate` com priority alta.

## Non-goals

- NÃO trata Recall por mudança de regulação (ex: NIT-DICLA-021 muda em 2027 e cert antigos viram "obsoletos"). Esse cenário é Wave B (módulo `obsolescencia-regulatoria`).
- NÃO trata garantia comercial cert ("validade comercial expirou" ≠ "recall"). Vigência expirada continua sendo status `EXPIRADO`.

## Invariantes novas

- **INV-CER-RECALL-001:** cert objeto de Recall preserva trilha WORM + status `RECALL_ATIVO`; notificação cliente em 24h + ANPD em 24h (quando aplicável) + CGCRE em 30d são obrigatórias (consumers idempotentes).
- **INV-CER-SUSP-001:** cert `SUSPENSO` paralisa vigência (relógio para). Levantamento de suspensão retoma vigência do ponto onde parou; campo `dias_suspensao_acumulada` registra para auditoria.
- **INV-CER-ERRATA-001:** Errata aplica APENAS a campos descritivos da allowlist (`docs/dominios/metrologia/modulos/certificados/errata-campos-permitidos.md` — a criar Wave A). Tentativa de errata em campo técnico bloqueia com 422.

## Implicações pro faseamento

- Wave A Marco 5 implementa US-CER-018/019/020.
- Consumers `notificar-cliente-recall`, `notificar-anpd-recall`, `notificar-cgcre-recall` versionados.
- Allowlist `errata-campos-permitidos.md` criada Wave A com aceite advogado.
- GATE-CER-RECALL-NOTIF: drills trimestrais de Recall (mensagem-modelo + tempo SLA) — referência `runbook-incidente-metrologico.md` (a criar Wave A).

## Status

Proposta — aguarda aceite Roldão + parecer consultor-rbc-iso17025 + advogado-saas-regulado antes de Marco 5 codar.
