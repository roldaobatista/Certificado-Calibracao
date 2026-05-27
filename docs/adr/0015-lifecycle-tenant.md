# ADR-0015 — Lifecycle de Tenant: provisioning atômico + sincronização plano-features + bloqueio inadimplência

> **Status:** **ACEITO** (2026-05-27 noite — auditoria 10 lentes pré-Wave A, Onda PRE-A.2). Estava em proposta desde 17/05/2026. Emenda Sprint 3 SAN-PERFIL-TENANT adicionou etapa 0 `COLETA_PERFIL_REGULATORIO` (ADR-0067). Resolve 4 gaps críticos comerciais identificados pela auditoria de 10 agentes (Auditores G, H, A, B): provisioning de novo tenant não atômico, sincronização ADR-0013↔ADR-0006 ausente, suspensão por inadimplência não desliga features, cliente inadimplente não bloqueia OS/orçamento/agenda.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Auditoria de integrações inter-modulares 17/05/2026 madrugada.
> **Depende de:** ADR-0001, ADR-0002 (multi-tenant), ADR-0006 (feature flags), ADR-0007 (outbox), ADR-0012 (autorização), ADR-0013 (pricing composicional), ADR-0014 (transições regulatórias), ADR-0067 (perfil regulatório do tenant).
> **Bloqueia:** Wave A (sem provisioning atômico, novo tenant pode pagar e ficar sem acesso).
> **Aceito-em:** 2026-05-27 (Onda PRE-A.2 auditoria 10 lentes pré-Wave A — Roldão decidiu "resolver TUDO").

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Lifecycle de tenant** | "Ciclo de vida do cliente" — desde a hora que ele paga até quando cancela. Cada etapa precisa acontecer numa ordem certa, sem furo. |
| **Provisioning** | "Preparação" — quando cliente novo paga, sistema precisa criar a "casa" dele: usuário admin, espaço no banco, features liberadas, e-mail de boas-vindas. |
| **Atômico** | "Tudo ou nada". Provisioning atômico = se uma etapa falha, todas voltam atrás. Não fica meio pronto. |
| **Sincronização plano↔features** | Quando você muda o plano do cliente (upgrade/downgrade/add-on), o sistema **automaticamente** liga/desliga as funcionalidades certas — sem operador apertar botão. |
| **Bloqueio progressivo** | Cliente que não paga não corta o acesso de uma vez. Primeiro avisa (D+3), depois deixa só ler (D+7), depois bloqueia tudo (D+15). |
| **Inadimplência** | Cliente que está devendo. ≥3 dias vencido = entra na régua. |
| **Régua de cobrança** | Sequência automática: WhatsApp dia 1, e-mail dia 3, ligação dia 7, suspensão dia 15. |

---

## Contexto

A auditoria de 10 agentes apontou **4 gaps críticos** que comprometem a operação SaaS comercial:

1. **Auditor G (Plataforma):** `BillingSaas.AssinaturaCriada` publica, mas **provisioning não é atômico**. Cliente pode pagar e ficar sem acesso (RLS tenant_id criado? admin user criado? features ativadas? e-mail enviado? — sem checkpoint).
2. **Auditor H (BPM/Automações):** **Sincronização entre `Plano.componentes` (ADR-0013) e `tenant_features` (ADR-0006) não está documentada**. Add-on contratado mid-cycle → feature liga em quanto tempo? Plano cancelado → features cortam imediato ou no próximo ciclo?
3. **Auditor G:** `BillingSaas.TenantSuspenso` publica, mas **não desabilita features automaticamente**. Tenant em read-only ainda vê botão "emitir certificado".
4. **Auditores A, B, D:** Cliente inadimplente >90 dias **não bloqueia OS/orçamento/agenda**. Continua abrindo OS, técnico vai no campo, OS executada, fatura nunca paga → receita perdida + custo operacional.

**Impacto comercial agregado:**
- Tenant paga R$ X mas não usa por 24h pq provisioning falhou silenciosamente → reembolso + reputação
- Tenant cancela add-on Marketplace mas continua usando por 5min → uso não cobrado
- Cliente inadimplente acumula débito porque agenda continua aceitando OS dele
- Operador comercial Aferê desabilita feature, mas tenant continua usando por TTL de cache (5 min)

---

## Decisão

Cravar **3 fluxos de lifecycle de tenant** com eventos novos, checkpoints atômicos, sincronização declarativa e bloqueios progressivos. Cada fluxo vira **invariante (INV-INT-007..010)**.

### Fluxo 1 — Provisioning atômico (INV-INT-007)

**Cenário:** Tenant novo assina Plano Pro via billing-saas.

**Antes (status quo):** `BillingSaas.AssinaturaCriada` publica → cada consumer reage independentemente → nenhum checkpoint atômico → falha silenciosa possível.

**Depois (decisão):** Provisioning vira **state machine explícita** em `suporte-plataforma/onboarding` com **8 etapas** (era 7 — emenda Sprint 3 P5 saneamento ADR-0067 adicionou etapa 0 `COLETA_PERFIL_REGULATORIO`), cada uma idempotente, todas precisam completar antes do tenant ser considerado "pronto".

**Estados:**
```
NAO_INICIADO
  ↓ (recebe BillingSaas.AssinaturaCriada)
COLETA_PERFIL_REGULATORIO  (NOVA — Sprint 3 ADR-0067 / INV-TENANT-PERFIL-005:
                            wizard pede perfil A/B/C/D + motivo >=100 chars +
                            evidência CGCRE se perfil A. Sem perfil = bloqueia
                            avanço. Comando `provisionar_tenant` é o atalho CLI
                            para esta etapa em uso operacional.)
  ↓
TENANT_DB_CRIADO       (cria registro em `tenants` com `perfil_regulatorio`
                        cravado + RLS app.tenant_id + 1 linha em
                        TenantPerfilHistorico direção PROVISIONAMENTO_INICIAL)
  ↓
ADMIN_PROVISIONADO     (cria User admin do tenant + senha temporária + MFA obrigatório no 1º login)
  ↓
FEATURES_ATIVADAS      (sincroniza `tenant_features` com `Plano.componentes.bundle + addons`
                        + matriz feature×perfil de docs/conformidade/comum/matriz-feature-perfil.md
                        — features marcadas DESABILITADO no perfil são removidas)
  ↓
CONFIG_INICIAL_CRIADA  (cria registros default em `configuracoes-sistema` — empresa, série fiscal placeholder, papel admin)
  ↓
EMAIL_BOAS_VINDAS_ENVIADO (via comunicacao-omnichannel)
  ↓
SANDBOX_DISPONIBILIZADO (cria ambiente de sandbox isolado pro tenant testar antes de produção)
  ↓
PRONTO  → publica `BillingSaas.AssinaturaPronta` (cliente pode usar)
```

**Garantias:**
- Cada etapa é idempotente (re-rodar não duplica efeito) — outbox pattern + `event_id`
- Falha em qualquer etapa pausa state machine + alerta ANTI-11 dispara pro dono Aferê (P1)
- Tenant NÃO consegue logar até estado = `PRONTO` (`AuthorizationProvider.can("login", tenant_id=X)` checa `onboarding.estado`)
- Evento `BillingSaas.AssinaturaPronta` (não `AssinaturaCriada`) é o que ativa cobrança recorrente
- Audit trail síncrono registra timestamp de cada transição

**Novos eventos:**
- `Onboarding.ProvisioningEmpezado` (publicado em `TENANT_DB_CRIADO`)
- `Onboarding.ProvisioningCompletado` (publicado em `PRONTO`)
- `BillingSaas.AssinaturaPronta` (alias de `Onboarding.ProvisioningCompletado` no domínio billing)
- `Onboarding.ProvisioningFalhou` (publicado se qualquer etapa falhar — alerta P1)

**INV-INT-007** registrada.

---

### Fluxo 2 — Sincronização plano-features (INV-INT-008)

**Cenário:** Tenant contratou Plano Pro (bundle: OS+Calibração+Certificados+Fiscal) e add-on Marketplace mid-cycle. Depois faz upgrade pra Plano Enterprise (bundle: TODOS os 48 módulos).

**Antes (status quo):** ADR-0013 (`Plano.componentes`) e ADR-0006 (`tenant_features`) coexistem mas **nenhum evento sincroniza**. Operação manual → erro garantido.

**Depois (decisão):** **Um único evento `BillingSaas.PlanoMudouModulos`** é a fonte de verdade da sincronização.

**Quando publica:**
- Contratação inicial (`BillingSaas.AssinaturaCriada`) → publica com `modulos_novos = Plano.componentes.bundle + addons_ativos`, `modulos_removidos = []`
- Upgrade/downgrade de plano (`BillingSaas.PlanoMudou`) → publica com delta `modulos_novos`, `modulos_removidos`
- Add-on contratado (`BillingSaas.AddonContratado`) → publica com `modulos_novos=[modulo]`, `modulos_removidos=[]`
- Add-on cancelado (`BillingSaas.AddonCancelado`) → publica com `modulos_novos=[]`, `modulos_removidos=[modulo]`, `efetivo_em=proximo_ciclo` (não imediato)
- Plano cancelado (`Assinatura.cancelada`) → publica com `modulos_removidos=tudo`, `efetivo_em=fim_periodo_pago` (não imediato — cliente já pagou)

**Payload:**
```yaml
event_name: BillingSaas.PlanoMudouModulos
tenant_id: <uuid>
plano_versao: pro@v3
modulos_novos: [marketplace]
modulos_removidos: []
efetivo_em: 2026-05-17T12:00:00Z  # imediato; ou futuro pra mudanças "próximo ciclo"
motivo: "addon_contratado"  # ou "plano_upgrade", "plano_downgrade", "cancelamento", "trial_expirado"
```

**Consumer único e obrigatório:** `acesso-seguranca` (módulo dono do `tenant_features`)

```python
@on_event("BillingSaas.PlanoMudouModulos")
def sync_tenant_features(event):
    if event.efetivo_em > now():
        # agendar via Celery Beat
        scheduler.schedule(sync_tenant_features, run_at=event.efetivo_em, ...)
        return
    
    for modulo in event.modulos_novos:
        TenantFeature.objects.update_or_create(
            tenant_id=event.tenant_id,
            feature=modulo,
            defaults={"ativo": True, "ativado_em": now()}
        )
    
    for modulo in event.modulos_removidos:
        TenantFeature.objects.filter(
            tenant_id=event.tenant_id, feature=modulo
        ).update(ativo=False, desativado_em=now())
    
    # Invalida cache Redis IMEDIATAMENTE (não espera TTL)
    cache.delete_many([
        f"tenant_features:{event.tenant_id}",
        f"auth:tenant:{event.tenant_id}:*",  # padrão glob
    ])
    
    # Encerra sessões ativas se features críticas foram removidas
    if any(m in CRITICAL_FEATURES for m in event.modulos_removidos):
        SessaoAtiva.objects.filter(tenant_id=event.tenant_id).update(forcar_relogin=True)
    
    # Audit trail síncrono
    AuditTrail.create(
        evento="features_sync",
        tenant_id=event.tenant_id,
        antes=event.modulos_removidos,
        depois=event.modulos_novos,
    )
```

**SLA:** Sincronização ≤ 5 minutos do evento ao reflexo na UI do tenant. Medido em Grafana.

**Garantia ANTI-11:** Admin tenant não consegue ativar feature fora do plano (INV-030 já cravada). Esta ADR só garante que feature contratada **é ativada de verdade**.

**INV-INT-008** registrada.

---

### Fluxo 3 — Suspensão por inadimplência desliga features atomicamente (INV-INT-009)

**Cenário:** Tenant atrasou pagamento da fatura SaaS. Régua progressiva:
- **D+3:** banner de aviso + e-mail
- **D+7:** entra modo `read_only` (não cria/edita; só lê e exporta)
- **D+15:** suspensão total (`suspensa` — apenas área de regularização acessível)
- **Pagamento confirmado:** reativação automática em ≤5min

**Antes (status quo):** `BillingSaas.TenantSuspenso` publica mas não detalha o modo (read-only? bloqueio total?). Features continuam ativas até cache expirar.

**Depois (decisão):**

`BillingSaas.TenantSuspenso` payload ganha campo `modo: enum (read_only, bloqueado_total)` + consumers obrigatórios.

**Consumer 1 — `acesso-seguranca`:**
- Modo `read_only`: invalida cache Redis `auth:tenant:{id}:*` + força re-auth em próximo request; `AuthorizationProvider.can()` passa a negar actions de tipo `create/update/delete`
- Modo `bloqueado_total`: encerra TODAS as sessões ativas + bloqueia login até `BillingSaas.TenantReativado`

**Consumer 2 — `billing-saas` (ele mesmo, callback):**
- Publica `BillingSaas.PlanoMudouModulos` com `modulos_removidos=tudo, efetivo_em=imediato` quando `modo=bloqueado_total`
- Features são desligadas em cascata pelo Fluxo 2 acima

**Consumer 3 — `comunicacao-omnichannel`:**
- Envia notificação por WhatsApp + e-mail explicando suspensão e link de regularização

**Reativação:**
- `BillingSaas.TenantReativado` publica
- `acesso-seguranca` re-permite login + recria cache RBAC
- `billing-saas` publica `BillingSaas.PlanoMudouModulos` com `modulos_novos=Plano.componentes.bundle + addons`, restaurando features

**SLA:** Reativação ≤ 5 minutos do pagamento confirmado (AC-BIL-003-4).

**INV-INT-009** registrada.

---

### Fluxo 4 — Inadimplência bloqueia operação (INV-INT-010)

**Cenário:** Cliente do tenant (não o tenant) está inadimplente >90 dias em contas-receber.

**Antes (status quo):** `ContasReceber.TituloVencido` publica mas nenhum consumer em `operacao/os`, `comercial/orcamentos`, `operacao/agenda`. Cliente continua tendo OS abertas.

**Depois (decisão):**

Job Celery diário (`job_inadimplencia_alertas`) varre `ContasReceber.TituloVencido`:

```python
@celery.task
def job_inadimplencia_alertas():
    for tenant in Tenant.objects.filter(status="ativo"):
        clientes_inadimplentes = Cliente.objects.filter(
            tenant_id=tenant.id,
            contas_receber__status="vencido",
            contas_receber__dias_vencido__gte=3
        ).distinct()
        
        for cliente in clientes_inadimplentes:
            dias_max = cliente.contas_receber.aggregate(Max('dias_vencido'))
            
            if dias_max >= 90:
                # Bloqueia
                if not cliente.bloqueado:
                    Cliente.objects.filter(id=cliente.id).update(bloqueado=True, motivo="inadimplencia_90d")
                    publish(Cliente.Bloqueado(
                        tenant_id=tenant.id,
                        cliente_id=cliente.id,
                        motivo="inadimplencia_90d"
                    ))
                    publish(ContasReceber.ClienteInadimplenteAlertaP1(
                        tenant_id=tenant.id,
                        cliente_id=cliente.id,
                        dias_vencido=dias_max,
                        valor_total_devido=cliente.contas_receber.aggregate(Sum('valor'))
                    ))
            elif dias_max >= 30:
                # Régua de cobrança
                publish(ContasReceber.ReguaCobrancaDispachada(
                    tenant_id=tenant.id,
                    cliente_id=cliente.id,
                    dias_vencido=dias_max,
                    canal="whatsapp"
                ))
```

**Consumers de `Cliente.Bloqueado`:**
- `operacao/os` — `AuthorizationProvider.can("os.criar", {"cliente_id": X})` retorna `denied, reason="cliente_bloqueado_inadimplencia"` se cliente.bloqueado=true
- `comercial/orcamentos` — orçamentos pendentes do cliente ganham flag `bloqueado_por_inadimplencia=true` + notificam vendedor
- `operacao/agenda` — alocações futuras desse cliente são canceladas + reagendadas pra "quando regularizar"
- `comunicacao-omnichannel` — notifica gerente operacional + cliente final

**Reativação (`Cliente.Desbloqueado`):**
- Quando última fatura vencida é paga (`ContasReceber.Pago`)
- Publica `Cliente.Desbloqueado` → consumers re-permitem operação

**INV-INT-010** registrada.

---

## Os 4 eventos NOVOS (somam ao catálogo v9)

| Evento | Origem | Quem publica | Consumers |
|---|---|---|---|
| `Onboarding.ProvisioningEmpezado` | onboarding | Ao receber `BillingSaas.AssinaturaCriada` | observabilidade |
| `Onboarding.ProvisioningCompletado` | onboarding | Ao atingir estado `PRONTO` | billing-saas (libera 1ª fatura), comunicacao-omnichannel (e-mail) |
| `BillingSaas.AssinaturaPronta` | billing-saas (alias) | Ao receber `Onboarding.ProvisioningCompletado` | módulos (todos podem aceitar requests do tenant agora) |
| `ContasReceber.ClienteInadimplenteAlertaP1` | financeiro/contas-receber (job diário) | Cliente atinge 90d vencido | clientes (publica `Cliente.Bloqueado`), comunicacao-omnichannel (notifica) |

---

## Alterações em eventos existentes

| Evento | Mudança |
|---|---|
| `BillingSaas.TenantSuspenso` | Payload ganha `modo: enum (read_only, bloqueado_total)` |
| `BillingSaas.PlanoMudouModulos` | (novo evento — já listado em catálogo v9 ADR-0013) — formaliza payload com `modulos_novos, modulos_removidos, efetivo_em, motivo` |

---

## Mecanismo de defesa em profundidade

1. **Hook pre-commit `provisioning-checkpoint-check`** — bloqueia merge se módulo novo não consome `BillingSaas.AssinaturaPronta` ANTES de aceitar requests do tenant
2. **AuthorizationProvider.can("login", {tenant_id})** — checa `onboarding.estado == PRONTO`; falha senão
3. **AuthorizationProvider.can("os.criar", {cliente_id})** — checa `cliente.bloqueado != true`; falha senão
4. **Cache Redis invalidação síncrona** — não espera TTL pra refletir mudança de feature
5. **Audit trail síncrono** — todo `BillingSaas.PlanoMudouModulos` e `Cliente.Bloqueado` grava em `audit_trail.authz_decisions`

---

## Alternativas consideradas

### 1. Provisioning assíncrono fire-and-forget — REJEITADA
**Rejeitada porque:** sem checkpoint atômico, tenant paga e fica sem acesso silenciosamente. State machine resolve.

### 2. Sincronização plano-features via job periódico — REJEITADA
**Rejeitada porque:** lag de 5-15 min entre mudança de plano e features ativas; cliente fica frustrado. Evento síncrono é melhor.

### 3. Bloqueio de cliente via flag denormalizada em cada query — REJEITADA
**Rejeitada porque:** N+1 problem + risco de inconsistência. Porta `AuthorizationProvider` centraliza.

### 4. Cancelamento imediato de features ao cancelar plano — REJEITADA
**Rejeitada porque:** cliente já pagou pelo período; cortar imediato é cobrança em vão. `efetivo_em=fim_periodo_pago` é justo.

---

## Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Provisioning atômico vs paralelo | Atômico (state machine) | Garantia de consistência > velocidade |
| Sincronização real-time vs eventual | Real-time via evento dedicado | Cliente espera feature ativar agora, não em 5 min |
| Cancelamento imediato vs próximo ciclo | Próximo ciclo (já pagou) | Justiça contratual |
| Bloqueio cliente vs aviso | Bloqueio após 90d | Antes era só aviso → cliente acumulava |
| Re-auth forçada vs cache invalidate só | Re-auth forçada se feature crítica removida | UX confusa se vê botão mas API nega |

---

## Consequências

### Positivas
- Provisioning falha = visível imediato + alerta P1 (não silencioso)
- Sincronização plano-features ≤5min — cliente não fica esperando
- Suspensão por inadimplência desliga features atomicamente — sem "uso grátis" pós-bloqueio
- Cliente inadimplente bloqueia novas OS automaticamente — receita protegida
- Audit trail completo de cada transição — fiscalização e contestação cliente OK

### Negativas
- 4 eventos novos + alterações em 2 existentes — complexidade incremental
- State machine de provisioning com 7 estados — manutenção
- Job Celery diário pra inadimplência — mais um cron
- Re-auth forçada pode causar UX "perdeu sessão" — mitigar com mensagem clara

---

## Itens a fazer

### Bloqueantes antes de Foundation F-B (auth)
- [ ] Atualizar `docs/comum/integracoes-inter-modulos.md` v9 com os 4 eventos novos (Tarefa 2/12 cobriu ADR-0013 e ADR-0014; adicionar agora ADR-0015) — feito na Tarefa 2
- [ ] Atualizar `REGRAS-INEGOCIAVEIS.md` com INV-INT-007..010 (Tarefa 6/12 desta sessão)
- [ ] Atualizar PRD `billing-saas` com US-BIL-011 (provisioning atômico) + US-BIL-012 (suspensão com modo) (Tarefa 5/12 desta sessão)
- [ ] Atualizar PRD `clientes` com US-CLI-NNN (bloqueio inadimplente) (Tarefa 5/12)
- [ ] Atualizar PRD `os` com bloqueio em can() (Tarefa 5/12)
- [ ] Tabela `onboarding_state` (state machine) + migration + RLS
- [ ] Tabela `tenant_features` com `ativo, ativado_em, desativado_em` + RLS
- [ ] Job Celery `job_inadimplencia_alertas` diário 02:00 BRT
- [ ] Hook `provisioning-checkpoint-check`

### Bloqueantes antes de Wave A começar
- [ ] State machine `OnboardingState` em `suporte-plataforma/onboarding`
- [ ] Consumer `acesso-seguranca` de `BillingSaas.PlanoMudouModulos` com invalidação Redis
- [ ] UI de "regularização" pra tenant suspenso (read-only ou bloqueado)
- [ ] Drill mensal: simular falha em cada etapa de provisioning + verificar rollback

---

## Critérios de reversão

| Sinal | Resposta |
|---|---|
| Provisioning leva >5 min em 95% dos casos | Otimizar etapas (paralelizar e-mail + sandbox); se persistir, revisar arquitetura |
| Sincronização plano-features falha >2x/mês | Investigar cache invalidação; ANTES de reescrever ADR, adicionar fallback "validação síncrona no login" |
| Cliente bloqueado virar pesadelo operacional (>5 reclamações/sem) | Não relaxa o gate; investiga se régua de cobrança está sendo respeitada nos D+3/+7/+15 antes do bloqueio |
| State machine de onboarding ficar travada em estado X | Job de "rescue" tenta avançar; se 3x falhar, escalação P0 ao dono Aferê |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita lifecycle de tenant com provisioning atômico
- [ ] **Auditor de Segurança:** confirma que suspensão encerra sessões + invalida caches
- [ ] **Auditor de Qualidade:** confirma cobertura E2E dos 4 fluxos
- [ ] **Tech-lead substituto:** confirma viabilidade da state machine + job inadimplência

---

## Referências

- ADR-0001, ADR-0002, ADR-0006, ADR-0007, ADR-0012, ADR-0013, ADR-0014
- Auditoria de 10 agentes 17/05/2026 — Auditores A (Comercial), B (Financeiro), G (Plataforma), H (BPM/Automações)
- `docs/comum/integracoes-inter-modulos.md` v9
- `REGRAS-INEGOCIAVEIS.md` — INV-INT-007..010 (criadas nesta ADR)
