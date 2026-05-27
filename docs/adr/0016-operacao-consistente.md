# ADR-0016 — Operação consistente: desligamento síncrono + BOM/orçamento + NC notifica cliente + 10 gaps médios

> **Status:** **ACEITO** (2026-05-27 noite — auditoria 10 lentes pré-Wave A, Onda PRE-A.2). Estava em proposta desde 17/05/2026. INV-INT-011..013 destravadas pra Wave A. Resolve 3 gaps críticos restantes da Onda 3 + 10 gaps médios identificados pela auditoria de 10 agentes.
> **Aceito-em:** 2026-05-27.
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Auditoria de integrações inter-modulares 17/05/2026 madrugada — Auditores C, D, E, F, G, H, I.
> **Depende de:** ADR-0001, ADR-0005 (engine automações), ADR-0007 (outbox), ADR-0011 (BI), ADR-0012 (autorização), ADR-0014 (transições regulatórias), ADR-0015 (lifecycle tenant).
> **Bloqueia:** Wave A da Operação (sem desligamento síncrono e BOM consistente, retrabalho garantido).

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Desligamento síncrono** | Quando técnico sai, sistema **na hora** corta acesso ao app, bloqueia comissões pendentes, reatribui OS. Não fica esperando alguém apertar botão. |
| **BOM** | "Bill of Materials" — lista de peças que um projeto/serviço usa. Engenharia atualiza, orçamentos antigos podem ficar desatualizados. |
| **NC** | "Não Conformidade" — quando algo deu errado (calibração rejeitada, padrão fora de tolerância, processo violado). |
| **PT** | "Proficiency Test" — comparação interlaboratorial. Lab manda mesmo padrão pra outros labs, comparam resultados. Se sair fora do limite, lab tem problema. |
| **Reemissão de certificado** | Quando descobre erro no cert emitido, gera versão nova (v2) substituindo. Fiscal precisa saber pra estornar/ajustar NF-e. |

---

## Contexto

A auditoria de 10 agentes apontou **3 gaps críticos** restantes (não cobertos pelas ADRs 0014/0015) + **10 gaps médios** que comprometem consistência operacional:

**Críticos:**
1. **Auditor E, G:** Desligamento de técnico → revogar acesso síncrono + flag comissões pendentes
2. **Auditor F:** Engenharia.BOMAtualizada → invalidar orçamentos abertos
3. **Auditor C:** Qualidade.NCAberta → notificar cliente externo automaticamente

**Médios (consolidados):**
4. Workflow de auditoria externa Cgcre sem state machine formal (Auditor C, H)
5. Garantia com fornecedor externo sem timeout/escalação (Auditor D)
6. Bypass de treinamento invisível na agenda (Auditor E)
7. Resultado PT (proficiência) ruim sem revalidação retroativa dos certs do período (Auditor C)
8. Reemissão de certificado sem ajuste de NF-e + notificação cliente (Auditor C)
9. NPS publicado em 2 lugares (CRM vs Qualidade) — drift semântico (Auditor I)
10. CAC não tem sinal de canal de aquisição (Auditor I)
11. Comissão de técnico desligado sem flag explícita de revisão (Auditor E, B)
12. Cache de feature flags pode ficar 5min desatualizado (Auditor G, H)
13. Sessão remota de suporte-SaaS não invalida RBAC ao encerrar (Auditor G)

---

## Decisão

Cravar **3 fluxos críticos** + **10 ajustes médios** com eventos novos, consumers explícitos e bloqueios automatizados. Cada fluxo crítico vira invariante (INV-INT-011..013). Médios são alterações em PRDs específicos.

### Fluxo 1 — Desligamento síncrono de técnico (INV-INT-011)

**Cenário:** Técnico João Silva é desligado em 2026-05-17 às 14:00.

**Antes:** `Colaborador.Desligado` publicado, agenda libera slots futuros. Nada mais.

**Depois:** Consumers obrigatórios reagem em ≤2s:

| Consumer | Ação imediata |
|---|---|
| **acesso-seguranca** | Encerra sessões ativas (web + mobile JWT) + bloqueia login (publica `AcessoSeguranca.UsuarioDesativado` + `AcessoSeguranca.SessoesEncerradasForcado`) |
| **operacao/os** | OSs alocadas a João + status IN (AGENDADA, EM_EXECUCAO) → flag `tecnico_desligado_pendente_reatribuicao=true`; publica `OS.PendenteReatribuicao(motivo=tecnico_desligado)` |
| **operacao/capacity-planning** | Recalcula disponibilidade da equipe; se sobrecarga → publica `CapacityPlanning.SobrecargaDetectada` |
| **financeiro/comissoes** | Marca todas `ComissaoPrevista` e `ComissaoDevida` pendentes de João com flag `bloqueado_por_desligamento=true`; publica `Comissoes.ComissaoBloqueadaPorDesligamento` |
| **financeiro/caixa-tecnico** | Marca despesas/adiantamentos pendentes do João como "a reconciliar em fechamento" |
| **metrologia/certificados** | (se João era RT signatário — INV-INT-002 já cobre — esta ADR só reforça que ambos consumers rodam paralelos) |
| **suporte-saas** | Encerra sessão remota se João estava num tenant nesse momento |

**Eventos novos publicados:**
- `AcessoSeguranca.SessoesEncerradasForcado` (audit trail crítico)
- `OS.PendenteReatribuicao(motivo, tecnico_desligado_id, os_id)`
- `Comissoes.ComissaoBloqueadaPorDesligamento`

**INV-INT-011** registrada.

---

### Fluxo 2 — BOM atualizada invalida orçamentos abertos (INV-INT-012)

**Cenário:** Engenharia descobre erro técnico na revisão A de um projeto; aprova revisão B (BOM atualizada com peça diferente). Orçamentos abertos usam revisão A.

**Antes:** `Engenharia.BOMAtualizada` publica → consumer `orcamentos` listado mas sem efeito explícito.

**Depois:**

Consumer `orcamentos`:
- Identifica orçamentos `status=aberto` que referenciam revisão antiga da BOM
- Marca cada um com `status="pendente_revalidacao_bom", motivo, revisao_nova_id, revisao_antiga_id`
- Publica `Engenharia.BomDesatualizadaNotificada(orcamentos_afetados=[ids])` com payload por orçamento
- Notifica vendedor responsável via `comunicacao-omnichannel` ("Orçamento #123 com BOM desatualizada — revise antes de aceitar conversão em OS")
- **Bloqueia hard** conversão em OS até vendedor revalidar (`AuthorizationProvider.can("orcamento.converter_em_os")` consulta status)

Consumer `os`:
- Se OS já foi criada a partir de orçamento com BOM antiga **antes da revisão B**, OS continua válida com snapshot da BOM antiga (INV-026 — preço/snapshot não retroage). Mas se OS ainda em RASCUNHO sem técnico alocado, recebe flag `bom_desatualizada=true` + revalidação obrigatória.

Consumer `engenharia-tecnica`:
- Publica `Engenharia.RevisaoAprovada` (já existe) também atualiza `procedimentos_calibracao_afetados` (INV-INT-006).

**INV-INT-012** registrada.

---

### Fluxo 3 — NC notifica cliente externo automaticamente (INV-INT-013)

**Cenário:** RT abre NC em padrão de calibração reprovado em verificação intermediária. NC bloqueia emissão de futuros certificados para cliente C (porque equipamento dele usou esse padrão na última calibração).

**Antes:** `Qualidade.NCAberta` publica → consumers `responsavel, dono` reagem. Cliente externo **não é notificado** — descobre 3 meses depois quando tenta recalibrar.

**Depois:**

Consumer novo `Qualidade.NCNotificacaoCliente`:
- Quando `Qualidade.NCAberta` com `entidade_origem_tipo IN ("padrao", "procedimento")` e `bloqueia_emissao=true`:
  - Identifica clientes afetados (clientes cujos equipamentos foram calibrados com esse padrão/procedimento nos últimos 12 meses)
  - Publica `Qualidade.NCNotificacaoCliente(cliente_id, nc_id, equipamentos_afetados=[ids], impacto_descricao)` por cliente
  - Consumer `comunicacao-omnichannel` envia notificação (WhatsApp + e-mail) com template aprovado:
    ```
    "Olá [cliente], identificamos uma não-conformidade em [padrão/procedimento] usado na calibração do seu equipamento [modelo, série]. Estamos investigando e entraremos em contato em até 5 dias úteis com plano de ação. Detalhes: [link portal]"
    ```
  - Consumer `portal-cliente` cria entry na timeline 360° do cliente com NC + impacto + prazo
- Quando NC fechada com plano de ação concluído (`Qualidade.NCFechada`):
  - Publica `Qualidade.NCResolucaoNotificada(cliente_id, nc_id, resolucao_descricao, certificados_revalidados=[ids opcional])`
  - Cliente recebe notificação de resolução

**Defesa LGPD:** notificação tenant→cliente carrega apenas dados mínimos (modelo, série do equipamento, não dados pessoais cruzados); audit trail registra cada envio.

**INV-INT-013** registrada.

---

## Ajustes médios (10)

### M1 — Workflow de auditoria externa com state machine

Criar state machine `AuditoriaExternaState` em `rh-frota-qualidade/auditoria-externa`:
- `PLANEJADA → DOCUMENTOS_PREPARADOS → EM_EXECUCAO → NCS_REGISTRADAS → PLANO_ACAO_APROVADO → EFICACIA_REVISADA → FECHADA`
- Cada transição: evento + audit trail
- SLA por etapa: documentos preparados ≤7d antes da visita; plano ação ≤30d pós-NC; eficácia revisada ≤90d
- Job Celery monitora SLA + escala automaticamente se vence

### M2 — Garantia com fornecedor: timeout + escalação

PRD `operacao/garantia`:
- Estado `aguardando_fornecedor` ganha `prazo_max_dias` (default 30)
- Job diário verifica garantias estagnadas
- Se > prazo: publica `Garantia.FornecedorAtrasado` + escalação automática pro comprador

### M3 — Bypass de treinamento visível na agenda

PRD `operacao/agenda` + `rh-frota-qualidade/treinamentos`:
- `Treinamentos.BypassExecutado` ganha consumer `agenda`
- Agenda marca técnico com flag visível ao despachante: "Bypass NR-X ativo até [data]"
- Acúmulo (≥3 bypasses em 30d) → escalação automática gerente

### M4 — PT (proficiency test) ruim → revalidação retroativa

PRD `metrologia/calibracao`:
- `Proficiencia.EscoreInsatisfatorio` ganha consumer `calibracao`
- Busca certificados emitidos no período do PT que usam mesma grandeza + mesmos padrões
- Publica `Calibracao.NecessidadeRevisaoRetroativa(certificados=[ids])`
- RT recebe lista pra revisar; NC automática vincula

### M5 — Reemissão de certificado ajusta NF-e

PRD `metrologia/certificados` + `financeiro/fiscal`:
- `Certificados.Reemitido` ganha consumer `fiscal`
- Fiscal emite CC-e (Carta de Correção Eletrônica) automática se NFS-e original ainda válida
- Consumer `comunicacao-omnichannel` notifica cliente da reemissão

### M6 — NPS unificado em um único publisher

Decisão: `Qualidade.NPSRespondido` é o canônico (resultado de OS = qualidade). `CRM.NPSRespondido` é deprecado (alias aceito Wave A, removido V2). CRM consome `Qualidade.NPSRespondido` pra timeline.

### M7 — CAC por canal de aquisição

`BillingSaas.AssinaturaCriada` payload ganha `canal_aquisicao` opcional (preenchido se Lead foi convertido — derivado de `Lead.canal`).

### M8 — Comissão de técnico desligado com flag

Já coberto em INV-INT-011 (Fluxo 1 desta ADR).

### M9 — Cache de feature flags com invalidação síncrona

Já coberto em INV-INT-008 (ADR-0015 Fluxo 2 — invalidação imediata, não TTL).

### M10 — Sessão remota suporte-SaaS invalida RBAC ao encerrar

PRD `suporte-plataforma/suporte-saas`:
- `SessaoRemota.Encerrada` ganha consumer obrigatório `acesso-seguranca`
- Invalida cache RBAC do suporte naquele tenant imediatamente (não espera TTL)

---

## Os 6 eventos NOVOS (somam ao catálogo v9)

| Evento | Origem | Quem publica | Consumers |
|---|---|---|---|
| `AcessoSeguranca.SessoesEncerradasForcado` | acesso-seguranca | Ao receber `Colaborador.Desligado` | audit trail crítico |
| `OS.PendenteReatribuicao` | operacao/os | Ao receber `Colaborador.Desligado` (se OS atribuída) | capacity-planning (sugere reatribuição), notificações |
| `Comissoes.ComissaoBloqueadaPorDesligamento` | financeiro/comissoes | Ao receber `Colaborador.Desligado` | audit (RH/financeiro libera manual) |
| `Engenharia.BomDesatualizadaNotificada` | engenharia-tecnica | Ao receber `Engenharia.BOMAtualizada` | orcamentos (bloqueia conversão), vendedor (notif) |
| `Qualidade.NCNotificacaoCliente` | qualidade | Ao receber `Qualidade.NCAberta` com `bloqueia_emissao=true` | comunicacao-omnichannel (notifica cliente), portal-cliente (timeline) |
| `Qualidade.NCResolucaoNotificada` | qualidade | Ao receber `Qualidade.NCFechada` com plano de ação concluído | comunicacao-omnichannel (notif resolução), portal-cliente |
| `Calibracao.NecessidadeRevisaoRetroativa` | calibracao | Ao receber `Proficiencia.EscoreInsatisfatorio` | RT (lista pra revisar), qualidade (NC automática) |
| `Garantia.FornecedorAtrasado` | operacao/garantia | Job diário | comprador (escalação) |

---

## Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Desligamento síncrono (1s) vs assíncrono (5min) | Síncrono | LGPD risco (acesso pós-desligamento) é P0 |
| Bloqueio hard de orçamento por BOM vs warning | Hard block | Vendedor cria OS errada = retrabalho caro |
| Notificar cliente de NC vs esperar plano de ação | Notificar imediato + resolução depois | Transparência > preocupação de "assustar cliente" |
| State machine de auditoria externa vs ad-hoc | State machine | Fiscalização Cgcre exige rastreabilidade |
| Reemitir CC-e automática vs manual | Automática se possível | Reduz fricção fiscal |
| NPS unificado (Qualidade) vs duplicado (CRM+Qualidade) | Unificado em Qualidade | Drift semântico = bug futuro |

---

## Itens a fazer

### Bloqueantes antes de Wave A começar
- [ ] Atualizar `docs/comum/integracoes-inter-modulos.md` v9 com os 6 eventos novos desta ADR (Onda 1 cobriu — adicionar agora)
- [ ] INV-INT-011..013 em `REGRAS-INEGOCIAVEIS.md` (Tarefa 8/12 cobre via PRDs)
- [ ] State machine `AuditoriaExternaState` em PRD `auditoria-externa`
- [ ] Consumer `acesso-seguranca` de `Colaborador.Desligado` (encerra sessões síncrono)
- [ ] Consumer `os` de `Colaborador.Desligado` (reatribuição pendente)
- [ ] Consumer `comissoes` de `Colaborador.Desligado` (flag bloqueio)
- [ ] Consumer `orcamentos` de `Engenharia.BOMAtualizada` (bloqueia conversão)
- [ ] Consumer `qualidade` publicador de `NCNotificacaoCliente` quando aplicável
- [ ] Job Celery diário monitorar garantias com fornecedor atrasadas
- [ ] PRD `qualidade` adicionar US de notificação cliente
- [ ] Deprecar `CRM.NPSRespondido` em favor de `Qualidade.NPSRespondido`

---

## Critérios de reversão

| Sinal | Resposta |
|---|---|
| Desligamento síncrono ultrapassar 5s p95 | Investigar (cache, fila Celery); pode degradar pra "eventual" se latência impactar UX |
| Bloqueio de orçamento por BOM causar >5 reclamações/sem | Não relaxa; investigar se engenharia está versionando demais |
| Notificação NC cliente gerar reclamação ("não quero saber") | Adicionar opt-out granular no portal-cliente |
| State machine auditoria virar pesadelo de manutenção | Migrar pra Temporal (gate ADR-0005) |

---

## Referências

- ADR-0001, ADR-0005, ADR-0007, ADR-0011, ADR-0012, ADR-0014, ADR-0015
- Auditoria 10 agentes 17/05/2026 — Auditores C, D, E, F, G, H, I
- `docs/comum/integracoes-inter-modulos.md` v9
- `REGRAS-INEGOCIAVEIS.md` — INV-INT-011..013 (criadas via PRDs nesta sessão)
