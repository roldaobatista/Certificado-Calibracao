---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/adr/0005-engine-automacoes.md
  - docs/adr/0014-transicoes-regulatorias.md
  - docs/adr/0015-lifecycle-tenant.md
  - docs/adr/0016-operacao-consistente.md
  - docs/comum/integracoes-inter-modulos.md
---

# Catálogo de Automações Cross-Módulo

> **Pra quê:** lista versionada das **automações sem programador** (Camada 3 da ADR-0005) que o produto entrega. Cada automação é uma regra **gatilho → condição → ação** sobre o catálogo de eventos (v9). Tenant ativa/desativa via UI; Aferê governa o catálogo (catálogo fechado — ANTI-11 preservado).
>
> Auditor H (auditoria 17/05/2026) identificou que ADR-0005 listou 5 ações no catálogo inicial mas o sistema precisa de ~13. Este documento expande o catálogo + lista 15 automações de alto valor identificadas pelos 10 auditores.

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Automação** | "Robô que faz coisa sozinho" — gatilho dispara, condição confere, ação acontece. Sem programador. |
| **Gatilho** | Evento que dispara o robô. Ex: "certificado emitido", "cliente atrasou 7 dias", "estoque baixou do mínimo". |
| **Condição** | Filtro "robô só age se ...". Ex: "se o valor da OS > R$ 5.000", "se cliente tem contrato premium". |
| **Ação** | O que o robô faz. Ex: "envia WhatsApp", "cria tarefa CRM", "bloqueia agenda". |
| **Catálogo fechado** | Gatilhos/condições/ações são pré-aprovados por Aferê. Tenant **combina** (não inventa código). Princípio ANTI-11. |
| **Idempotência** | Mesmo evento disparando 2x → automação roda só 1x (não duplica). |

---

## Estrutura de uma automação

```yaml
# Schema padrão
automacao:
  id: aut-NNN                          # ID único na release atual do catálogo
  nome: "Nome amigável pro tenant"
  descricao: "1 frase explicando"
  versao: v1                           # semver dentro do catálogo
  dominio: comercial|operacao|...      # qual domínio é o "dono"
  publica_em: wave_a | wave_b | v2

  gatilho:
    evento: Dominio.VerboParticipio    # nome canônico
    filtro_evento:                     # opcional, filtra antes
      campo: valor
  
  condicoes:                           # AND entre condições
    - tipo: comparar
      campo: payload.valor
      operador: gte
      valor: 5000
    - tipo: intervalo_tempo
      campo: payload.vencimento
      intervalo: "30d"
      direcao: antes
  
  acoes:                               # executadas em ordem
    - tipo: enviar_whatsapp
      template: <id_template_aprovado>
      destinatario: payload.cliente.telefone
    - tipo: criar_tarefa_crm
      tipo_tarefa: lembrete_recalibracao
      atribuir_a: <papel_id>
  
  idempotencia_key:
    expressao: "{evento.event_id}::aut-NNN"
    janela: 24h                        # mesma chave em 24h ignora
  
  observabilidade:
    metrica: count_disparos_por_tenant
    alerta_se_falha_x_vezes: 5
```

---

## Catálogo de ações ampliado (13 ações)

> Auditor H (ADR-0005 Camada 3) identificou 5 ações iniciais + 8 faltantes. Versão consolidada:

### Ações de comunicação
1. **`enviar_whatsapp(template_id, destinatario, variaveis)`** — via porta `OmniChannelProvider` (#10 ACL)
2. **`enviar_email(template_id, destinatario, variaveis)`** — via porta `EmailTemplateProvider` (#18 ACL)
3. **`enviar_sms(template_id, destinatario, variaveis)`** — via porta `OmniChannelProvider`
4. **`notificar_painel(severidade, mensagem, destinatario_papel)`** — interno (banner UI)

### Ações de criação/transição
5. **`criar_tarefa_crm(tipo_tarefa, atribuir_a, prazo_horas, payload_dados)`** — em `comercial/crm`
6. **`criar_os_rascunho(template_os, cliente_id, equipamento_id, dados)`** — em `operacao/os`
7. **`criar_cotacao_fornecedores(itens, n_fornecedores=3, criterio="homologados")`** — em `suporte-plataforma/fornecedores`
8. **`criar_nc(severidade, descricao, entidade_origem, responsavel_id)`** — em `rh-frota-qualidade/qualidade`

### Ações de bloqueio
9. **`bloquear_emissao_certificado(motivo, padrao_id_opcional, justificativa)`** — em `metrologia/certificados`
10. **`bloquear_alocacao_tecnico(tecnico_id, motivo, vigencia_ate)`** — em `operacao/agenda`
11. **`bloquear_cliente(cliente_id, motivo, justificativa)`** — em `comercial/clientes`

### Ações de escalação/aprovação
12. **`escalar_para(papel_id | usuario_id, urgencia, contexto)`** — via BPM
13. **`solicitar_aprovacao(tipo_aprovacao, alcada, dados)`** — em `suporte-plataforma/automacoes-bpm`

**Hook validador:** `AuthorizationProvider.can()` chamado ANTES de cada ação executar — automação não pode burlar autorização (mesmo princípio de admin tenant: ANTI-11).

---

## As 15 automações (Wave A + Wave B)

### Wave A (entrega no MVP-1)

#### AUT-001 — Recalibração proativa 30 dias antes
- **Gatilho:** `Calibracao.VencendoEm30d`
- **Condição:** cliente ativo (não bloqueado, com contrato ou histórico)
- **Ações:** (1) `enviar_whatsapp(lembrete_recal_30d, cliente.telefone)`; (2) `criar_tarefa_crm(tipo=recalibracao, atribuir_a=vendedor_responsavel, prazo=7d)`
- **Idempotência:** evento + 30d (não dispara duas vezes em janela)
- **Origem:** OP1 + BIG-10; Auditor A

#### AUT-002 — Estoque mínimo → cotação automática 3 fornecedores
- **Gatilho:** `Estoque.MinimoAtingido`
- **Condição:** tenant tem ≥ 3 fornecedores homologados pra esse item
- **Ações:** (1) `criar_cotacao_fornecedores(item, n=3, criterio=homologados)`; (2) `notificar_painel(severidade=media, mensagem="Estoque mínimo de X — cotação automática em andamento")`
- **Idempotência:** item + 7d
- **Origem:** Auditor F (supply chain)

#### AUT-003 — Padrão metrológico vencido bloqueia emissão + NC preventiva
- **Gatilho:** `Padroes.CertificadoVencido` (job diário publica)
- **Condição:** sempre (não há exceção)
- **Ações:** (1) `bloquear_emissao_certificado(motivo=padrao_vencido, padrao_id)`; (2) `criar_nc(severidade=alta, descricao=padrao_vencido, entidade_origem=padrao_id, responsavel=RT)`
- **Idempotência:** padrão + por validade (não duplica até nova calibração)
- **Origem:** INV-INT-004 (ADR-0014)

#### AUT-004 — Treinamento/ASO vencido bloqueia agenda
- **Gatilho:** `Treinamentos.CertificadoVencido` OU `SST.ASOVencido`
- **Condição:** técnico tem alocações futuras em OS que exigem essa habilitação
- **Ações:** (1) `bloquear_alocacao_tecnico(tecnico_id, motivo=habilitacao_vencida)`; (2) `criar_tarefa_crm(tipo=reciclagem_treinamento, atribuir_a=RH)`; (3) `notificar_painel(severidade=alta, mensagem="Técnico X com habilitação Y vencida — reagende OSs")`
- **Origem:** INV-INT-005 (ADR-0014)

#### AUT-005 — Cliente inadimplente 90d bloqueia operação
- **Gatilho:** `ContasReceber.ClienteInadimplenteAlertaP1` (job diário publica)
- **Condição:** sempre
- **Ações:** (1) `bloquear_cliente(cliente_id, motivo=inadimplencia_90d)`; (2) `enviar_whatsapp(notif_bloqueio_cliente, cliente.telefone)`; (3) `notificar_painel(severidade=alta, papel=financeiro)`
- **Origem:** INV-INT-010 (ADR-0015)

#### AUT-006 — OS atrasada > 2h notifica gerente
- **Gatilho:** job Celery diário detecta `OS.status="em_execucao" AND now() - sla_target > 2h`
- **Condição:** OS não tem evento `OS.AtrasoNotificado` nas últimas 12h
- **Ações:** (1) `notificar_painel(severidade=media, papel=gerente_operacional)`; (2) `enviar_whatsapp(notif_atraso_os, cliente.telefone)` (se cliente opt-in)
- **Origem:** Auditor D (operação)

#### AUT-007 — Régua de cobrança progressiva (D+30/60/89)
- **Gatilho:** job Celery diário detecta `ContasReceber.TituloVencido` em janelas
- **Condição:** cliente não recebeu mesma notificação nessa janela
- **Ações:**
  - D+30: `enviar_whatsapp(cobranca_30d, cliente.telefone)`
  - D+60: `enviar_email(cobranca_60d_formal, cliente.email)` + `criar_tarefa_crm(ligar_cliente_inadimplente)`
  - D+89: `escalar_para(papel=gerente_financeiro, urgencia=alta)` + último aviso WhatsApp
- **Origem:** ADR-0015 (fluxo 4)

#### AUT-008 — NPS < 7 cria ticket de retenção
- **Gatilho:** `Qualidade.NPSRespondido`
- **Condição:** nota < 7
- **Ações:** (1) `criar_tarefa_crm(tipo=retencao, atribuir_a=vendedor_responsavel, prazo=24h)`; (2) `notificar_painel(severidade=media, papel=gerente_cs)`
- **Origem:** Auditor A + Auditor I (BI)

---

### Wave B (entrega pós-MVP-1)

#### AUT-009 — Contrato vence em 60d → renovação proativa
- **Gatilho:** `Contrato.VigenciaAVencer` (60d, 30d, 7d antes)
- **Condição:** contrato não foi marcado "não renovar"
- **Ações:** (1) `criar_tarefa_crm(tipo=renovacao_contrato, atribuir_a=vendedor)`; (2) D-60: `enviar_email(prep_renovacao)`; (3) D-30: `enviar_whatsapp(proposta_renovacao)`; (4) D-7: `escalar_para(gerente_comercial)`
- **Origem:** Auditor A

#### AUT-010 — Acidente registrado notifica cliente automaticamente
- **Gatilho:** `SST.AcidenteRegistrado`
- **Condição:** OS estava em cliente externo
- **Ações:** (1) `enviar_whatsapp(comunicado_acidente, cliente.telefone)` (template aprovado); (2) `enviar_email(comunicado_acidente_formal, cliente.email)`; (3) `criar_tarefa_crm(acompanhamento_pos_acidente, vendedor + gerente)`
- **Origem:** Auditor E (SST)

#### AUT-011 — OS de garantia procedente marca despesas pra reconciliar
- **Gatilho:** `Garantia.Procedente`
- **Condição:** OS-mãe tem despesas/adiantamentos lançados em caixa-tecnico
- **Ações:** (1) marca despesas com flag `a_reconciliar=true` (interno); (2) `notificar_painel(severidade=media, papel=financeiro, mensagem="Garantia X procedente — reconciliar despesas")`
- **Origem:** Auditor D (operação)

#### AUT-012 — NC crítica sem fechamento > 90d escala automaticamente
- **Gatilho:** job Celery diário verifica `Qualidade.NC.status="aberta" AND dias_aberta > 90`
- **Condição:** sempre
- **Ações:** (1) `escalar_para(papel=dono_aferere, urgencia=critica)`; (2) `criar_nc(severidade=sistemica, descricao="NC X aberta há > 90 dias", responsavel=RT)`
- **Origem:** Auditor C (metrologia/qualidade)

#### AUT-013 — Capacity sobrecarregado solicita contratação
- **Gatilho:** `CapacityPlanning.SobrecargaDetectada` por 3 semanas consecutivas
- **Condição:** sempre
- **Ações:** (1) `criar_tarefa_crm(tipo=processo_seletivo, atribuir_a=RH, prazo=30d)`; (2) `notificar_painel(severidade=media, papel=diretor)`
- **Origem:** Auditor E (RH) + Auditor D

#### AUT-014 — MRR cair > 10% mês alerta dono
- **Gatilho:** job Celery mensal (3º dia útil) compara MRR mês anterior vs atual
- **Condição:** delta < -10%
- **Ações:** (1) `notificar_painel(severidade=alta, papel=dono_aferere, mensagem="MRR caiu X%")`; (2) `enviar_email(relatorio_mrr_decline, dono.email)` com breakdown por tenant
- **Origem:** Auditor I (BI) + ADR-0011

#### AUT-015 — Reincidência peça (3+ garantias em 6m) abre análise engenharia
- **Gatilho:** job Celery mensal detecta reincidência
- **Condição:** mesma peça com `Garantia.Procedente >= 3` em 6 meses
- **Ações:** (1) `criar_nc(severidade=alta, descricao=reincidencia_peca_X, entidade_origem=peca_id, responsavel=engenharia)`; (2) `criar_tarefa_crm(tipo=revisao_engenharia, atribuir_a=engenharia)`
- **Origem:** Auditor D (operação)

---

## Governança do catálogo

- **Versionamento:** catálogo segue semver. Adição de gatilho/condição/ação = versão MINOR. Mudança breaking = MAJOR.
- **Aprovação de catálogo:** Auditor de Segurança + Auditor de Produto revisam cada PR.
- **Hot reload:** mudança no catálogo é aplicada via release-management (`Release.Publicada`); tenants em beta podem testar antes do GA.
- **Limite por tenant:** plano define quantas automações tenant pode ativar (componente `LimiteDuro` no Plano — ADR-0013).
- **Auditoria:** toda automação executada grava em `audit_trail.automacoes_executadas` com `evento_disparador, condicoes_avaliadas, acoes_executadas, resultado`.

---

## Critérios de mortalidade (quando reabrir o catálogo)

| Sinal | Resposta |
|---|---|
| Tenants pedem ≥5x/sem ação fora do catálogo | Avaliar ADR-0005 evolução pra Camada 3 (DSL aberta com sandbox) |
| Catálogo > 50 ações | Considerar splitting por domínio + governança específica |
| Loop infinito detectado (regra A dispara B dispara A) | Engine adiciona detecção de ciclo + timeout 30s (ADR-0005 já cobre) |
| Spam de WhatsApp gerado por regra mal configurada | Hard cap por tenant/mês + opt-out forte |

---

## Itens a fazer

- [ ] Implementar engine de regras conforme ADR-0005 Camada 3 (Wave B)
- [ ] UI de "automações" pro tenant (Wave B)
- [ ] Catálogo de templates WhatsApp/Email aprovados pra cada ação `enviar_*`
- [ ] Testes E2E pra cada uma das 15 automações antes de Wave B GA
- [ ] Dashboard Grafana com métricas: execuções/dia por automação, taxa de falha, tempo médio

---

## Referências

- ADR-0005 (engine automações), ADR-0006 (feature flags), ADR-0013 (pricing — `LimiteDuro` em plano), ADR-0014, ADR-0015, ADR-0016
- `docs/comum/integracoes-inter-modulos.md` v9 (catálogo de eventos)
- `REGRAS-INEGOCIAVEIS.md` — INV-AGENT-001 (UntrustedInput), INV-INT-001..013
