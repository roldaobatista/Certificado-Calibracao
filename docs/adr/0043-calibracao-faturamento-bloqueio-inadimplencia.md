---
adr: 0043
titulo: Integração Certificado.Emitido → Financeiro + bloqueio de emissão por inadimplência dura
status: aceito
data: 2026-05-23
aceito-em: 2026-05-27
proposto-por: agente (Onda 7 — auditor 6, achado C1-CAL)
revisado-por: tech-lead-saas-regulado + advogado-saas-regulado + consultor-rbc-iso17025
bloqueia-fase: Wave A Marco 4 (calibracao) + Wave A `certificados` + 1º tenant externo pago
depende-de: ADR-0015 (lifecycle tenant — inadimplência), ADR-0023 (OS com atividades), ADR-0067 (perfil regulatório), INV-CLI-BLOQ-001
---

# ADR-0043 — Faturamento de certificado + bloqueio de emissão por inadimplência dura

> **Emenda 2026-05-27 (Onda PRE-A.2 auditoria 10 lentes pré-Wave A — L10#4):** política de bloqueio dura por inadimplência é **perfil-aware** (ADR-0067):
> - **Perfil A (RBC acreditado):** grace period D+45 antes do bloqueio (perda de janela CGCRE é catastrófico — risco regulatório > recuperação de R$). Notificação obrigatória D+30 e D+45 antes do bloqueio.
> - **Perfil B (rastreável):** grace D+20.
> - **Perfil C (em preparação):** grace D+30 (igual A em vigência, mas sem CGCRE risk).
> - **Perfil D (comercial puro):** grace D+7 (bloqueio agressivo aceito — sem risco regulatório).
>
> Override A3 do dono Aferê (Roldão) pode estender grace caso-a-caso até D+90 — registrado em `OverrideBloqueio.justificativa` + A3 obrigatório + auditoria WORM.

## Contexto

Marco 4 calibração + Marco 5 certificados não cobrem o disparo financeiro nem a defesa contra cliente inadimplente continuar consumindo certificado:

1. **Sem disparo Financeiro:** RT emite certificado → cliente recebe PDF → tenant nunca cobra. Vazamento de receita silencioso. Auditoria fiscal vê NF-e desalinhada de cert emitido.
2. **Sem bloqueio por inadimplência:** cliente com >30 dias e >1 título vencido continua pedindo cert. Tenant trabalha de graça, perde dinheiro, descobre quando vai cobrar e o cliente desapareceu.
3. **Sem override governado:** bloquear duro sem válvula de escape gera caso de borda (cliente VIP em discussão amigável de fatura) que vira corrida ao suporte. Precisa ser exceção auditada, não bypass.

CDC art. 6º III/IV + Lei 14.181/2021 exigem comunicação prévia antes de bloqueio comercial — alinhado com `INV-CLI-BLOQ-001` que já trata régua D+30/60/89 do cliente.

## Decisão

### 1. Consumer Financeiro reage a `Certificado.Emitido`

- Evento publicado pelo módulo Certificados quando `Certificado.status` vira `ASSINADO` (não em `RASCUNHO` nem `PENDENTE_ASSINATURA`).
- Consumer `criar_titulo_a_partir_de_certificado_handler` no módulo Financeiro:
  - Idempotente por `certificado_id` (chave natural; reentrega não duplica título).
  - Cria `ContasReceber` com vencimento = `Certificado.emitido_em + Cliente.condicoes_pagamento.prazo_dias` (default 30).
  - Valor = `Certificado.valor_servico_snapshot` (snapshot capturado no momento da emissão — não acompanha mudança de tabela de preço pós-emissão; respeita `INV-026`).
  - Publica `ContasReceber.TituloEmitido(certificado_id, conta_id, valor, vencimento, correlation_id)` em transactional outbox (`INV-INT-010`).

### 2. Bloqueio duro de emissão por inadimplência

- Estado `Cliente.situacao_financeira` derivado:
  - `EM_DIA` — sem títulos vencidos.
  - `ATRASO_LEVE` — 1 título vencido, ≤30 dias.
  - `INADIMPLENCIA_BRANDA` — >1 título OU >30 dias (apenas alerta, NÃO bloqueia).
  - `INADIMPLENCIA_DURA` — >1 título vencido E >30 dias do mais antigo.
- Predicate `cliente_pode_receber_novo_certificado(cliente_id)`:
  - Bloqueia se `situacao_financeira == INADIMPLENCIA_DURA` E `Tenant.bloqueio_inadimplencia_calibracao_habilitado == true`.
  - Tenant flag começa `false` (Marco 4) — ativa Wave A pós régua D+30/60/89 (`INV-CLI-BLOQ-001`).
- Resposta no endpoint de emissão quando bloqueado:
  - HTTP 409 `EmissaoBloqueadaInadimplenciaDura`.
  - Mensagem inclui número e vencimento dos títulos vencidos (sem outros dados sensíveis).
  - Audit `EventoDeCertificado.BloqueioEmissaoInadimplencia(cliente_id_hash, titulos_vencidos_count, correlation_id)`.

### 3. Override gerencial auditado

- Entidade nova `OverrideEmissaoCertificado`:
  - `id`, `tenant_id`, `certificado_id` (FK criado APÓS override), `cliente_id`, `motivo` (≥100 chars, anti-PII via `INV-CAL-TXT-001`), `gerente_id`, `audit_event_id`, `criado_em`, `assinatura_a3_id` (FK obrigatória — `INV-017` carimbo ITI).
- Fluxo:
  - Usuário com `papel.gerente_financeiro` ou `papel.admin_tenant` requisita override → assina A3 → backend cria override → libera emissão única do cert → certificado nasce com FK `Certificado.override_emissao_id`.
- Restrições:
  - Override é por cert (não por cliente — não vira passe livre).
  - Limite 5%/mês de cert overrideados por tenant (mesma política do `ADR-0026`); estouro vira alerta P1 + bloqueia novos overrides.

## Caminhos alternativos considerados

| Alternativa | Por que NÃO |
|---|---|
| Bloqueio na assinatura ao invés da emissão | RT já gastou tempo configurando + executando — bloquear no fim é frustração total |
| Sem bloqueio, só alerta | Não resolve vazamento de receita — Roldão (founder is customer) detectou em dogfooding |
| Override por cliente (passe livre) | Vira bypass silencioso; auditor financeiro perde rastro caso-a-caso |
| Cobrança pré-paga | Quebra modelo B2B brasileiro (faturamento mensal) |

## Consequências

### Positivas

- Receita rastreada cert→título→NF-e (cumpre `INV-026`).
- Defesa contra free-rider que vira churn forçado.
- Override governado preserva caso VIP sem virar bypass.
- Comunicação CDC respeitada via régua D+30/60/89 (`INV-CLI-BLOQ-001`).

### Negativas (mitigáveis)

- Complexidade no fluxo de emissão (gerente precisa estar disponível para override).
- Risco de tenant "esquecer" de habilitar flag → mitigado por checklist onboarding Wave A.

## Non-goals

- NÃO altera cálculo de preço — snapshot de `valor_servico_snapshot` é fora desta ADR.
- NÃO bloqueia consulta/download de cert já emitidos — só nova emissão.
- NÃO trata cliente em discussão judicial (Wave B — módulo `juridico-cobranca`).

## Invariantes novas

- **INV-CAL-FIN-001:** evento `Certificado.Emitido` dispara `ContasReceber.TituloEmitido` em consumer idempotente por `certificado_id`.
- **INV-CAL-FIN-002:** emissão bloqueia com 409 quando `cliente.situacao_financeira == INADIMPLENCIA_DURA` E flag tenant habilitada; override via `OverrideEmissaoCertificado` exige A3 + motivo ≥100 chars.

## Implicações pro faseamento

- Marco 4 calibração + Marco 5 certificados implementam predicate + consumer + entidade override.
- Wave A módulo `comunicacao-omnichannel` entrega régua D+30/60/89 → tenant habilita flag.
- GATE-CAL-FIN-1: dashboard tenant mostra `Cliente.situacao_financeira` antes de iniciar nova OS (UX preventivo).

## Status

Proposta — aguarda aceite Roldão pré-Marco 4. Bloqueia abertura ao 1º tenant externo pago.
