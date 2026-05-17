# ADR-0011 — Banco analítico/BI separado do operacional (3 fases por escala)

> **Status:** **PROPOSTA** (17/05/2026, madrugada). Resolve achado da auditoria de 10 agentes (Auditor 5 — BI/dados e Auditor 2 — Multi-tenant) que apontaram que PostgreSQL único cobrindo OLTP + OLAP **trava o sistema quando o BI roda consulta pesada**. Decisão é "começar simples com PG único + views materializadas, separar OLAP em duas etapas conforme escala", não "subir data warehouse no dia 1".
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Auditoria 10 agentes 17/05/2026 — Auditor 5 (BI/dados) e Auditor 2 (multi-tenant) convergiram em "PG único até ~50 tenants, depois read-replica/OLAP separado".
> **Depende de:** ADR-0001 (stack — PostgreSQL escolhido), ADR-0002 (multi-tenant RLS).

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **OLTP** | "Online Transaction Processing" — banco de **operação do dia a dia**. Criar OS, emitir certificado, lançar contas a receber. Muitas operações pequenas e rápidas. É o banco que está rodando o sistema. |
| **OLAP** | "Online Analytical Processing" — banco de **análise/relatório**. Calcular DRE do mês, gráfico de OS por período, comparar receita de 12 meses. Poucas operações, mas pesadas (varrem milhares de linhas). |
| **Read-replica** | "Cópia somente-leitura" do banco principal. Atualiza com pequeno atraso (segundos). Serve pra rodar relatório pesado sem travar o banco principal. |
| **View materializada** | Tabela "pré-calculada" do PostgreSQL. Em vez de recalcular a DRE toda vez que alguém abre o painel, o sistema calcula 1x e guarda o resultado. Atualiza periodicamente (a cada 15 min, 1 hora, ou de madrugada). |
| **ETL / ELT** | "Extract Transform Load" — processo de mover dados do banco operacional pro banco analítico (ou pra views materializadas). |
| **DuckDB** | Banco analítico que roda "embarcado" (igual SQLite). Não precisa servidor separado. Excelente em consulta pesada, péssimo em escrita concorrente. Custo: zero (open source). |
| **ClickHouse** | Banco analítico de verdade, em servidor próprio. Escala pra bilhões de linhas. Custo: ~R$ 500/mês cloud (sa-east-1) ou ~R$ 200/mês self-hosted. |
| **CDC** | "Change Data Capture" — replicação em tempo real do banco operacional pro analítico. Cada INSERT/UPDATE/DELETE no OLTP vira evento que o OLAP consome. Ferramenta típica: Debezium. |
| **Cross-tenant** | "Olhando vários clientes ao mesmo tempo". Você (Roldão) abrindo o painel da Aferê vê dados de TODOS os tenants — diferente de cada tenant que vê só os dele. |
| **Append-only** | Tabela que só aceita "adicionar linha nova". Não dá pra editar nem apagar. Usado pra trilha de auditoria. |

---

## Contexto

O sistema é um ERP SaaS multi-tenant com 48 módulos. Hoje o banco PostgreSQL é único e atende tudo — OLTP (operação) e OLAP (relatórios). A auditoria de 10 agentes (17/05/2026 madrugada) identificou que com **48 módulos × N tenants**, esse esquema **trava** quando:

1. Roldão abre o painel do dono e o sistema roda agregação pesada por cima de 1M de linhas de OS, certificado, audit log
2. Cliente final abre relatório financeiro (DRE, fluxo de caixa, custeio real, comissões) na mesma instância que está emitindo NFS-e ao vivo
3. BI Wave B traz builder de relatórios customizáveis — usuário monta query agregando milhões de linhas
4. Painel-do-dono precisa ver **todos os tenants ao mesmo tempo** — RLS atual bloqueia isso (defesa em profundidade) e exige role separada

**Cenários que disparam o problema:**
- Wave A com 3-5 tenants reais: já começa a sentir (OS table com 5k linhas/dia/tenant × 5 = 25k/dia)
- Wave B com 20-50 tenants: garantido trava se BI roda em horário de operação
- Wave C com 500+ tenants: insustentável sem banco analítico separado

**Restrições:**
- Orçamento ano 1 não comporta data warehouse pago (Snowflake, BigQuery custariam R$ 800-1.500/mês fixo + compute)
- 21 CFR Part 11 (cliente farma TOP em V2/V3) exige audit trail imutável de **quem viu o quê** no BI
- LGPD: link público compartilhado de relatório com `n < 3 tenants/clientes` agregados expõe receita concorrente — proibido
- Roldão (cross-tenant) precisa ver painel da Aferê sem violar RLS dos tenants
- Manutenção operada por agentes IA — solução deve ter pool grande de exemplos e baixa complexidade operacional

---

## Decisão

Adotar **estratégia em 3 fases progressivas**, com gates de migração baseados em escala real (número de tenants + carga observada), não em data calendário.

### Fase 0 — MVP-1 e Wave A (1-15 tenants) → PostgreSQL ÚNICO + views materializadas + Superset

**Sem banco analítico separado.** Toda a inteligência de BI vive dentro do mesmo PG que roda o operacional, mas isolada em:

- **Schema dedicado `analytics_*`** dentro do PG principal — vistas materializadas (`mv_dre_tenant`, `mv_fluxo_caixa_tenant`, `mv_os_aberta_kpi`, `mv_certificados_emitidos_mes`)
- **Job Celery noturno (02:00-05:00 BRT)** atualiza as vistas (`REFRESH MATERIALIZED VIEW CONCURRENTLY`) — não trava queries de leitura durante o refresh
- **Real-time (≤ 1 min)** via outbox pattern: comandos que mutam OLTP publicam evento → handler Celery atualiza vista resumida específica (não a vista inteira)
- **Apache Superset embedded** (open source, free, self-hosted no mesmo VPS) lê as vistas materializadas e renderiza dashboards. Respeita RLS automaticamente.
- **Dashboards fixos pra MVP-1** (não customizáveis): DRE, fluxo de caixa, inadimplência, OS abertas/atrasadas, certificados emitidos no mês, comissões devidas

**Painel do dono (cross-tenant):**
- Role PostgreSQL separada `afere_bi_admin` que NÃO é `NOBYPASSRLS` (defesa em profundidade mantida)
- Em vez disso, painel-do-dono consulta **vistas materializadas dedicadas que JÁ AGREGAM cross-tenant** (`mv_dono_receita_consolidada`, `mv_dono_uso_por_tenant`)
- Essas vistas são populadas por job Celery que roda com role admin separada (autenticada com credencial fora do contexto multi-tenant)
- Toda query da role admin gera log em `audit_trail.bi_admin_queries` (tabela append-only)

**Custo Fase 0:** R$ 0 adicional (tudo dentro do PG existente, Superset gratuito self-hosted).

**Critério de saída:** ≥ 50 tenants OU `pg_stat_statements` mostrar que queries de BI consomem >20% do tempo de CPU do PG OU latência p95 do OLTP subir 30% em horário de BI ativo.

---

### Fase 1 — pós-MVP-1 com 15-50 tenants → Read-replica PostgreSQL dedicada

Quando a Fase 0 saturar, **adicionar uma réplica de leitura do PostgreSQL** numa segunda VM:

- **Streaming replication assíncrona** PG nativa (latência ~1-5 segundos) — incluído no PostgreSQL, sem ferramenta extra
- **Replica fica em VM separada** (Hostinger KVM 4 dedicada ou já AWS RDS sa-east-1 read-replica se MVP-1 migrou pra cloud antes)
- **Superset + jobs de refresh materialized view + painel-do-dono passam a ler DA RÉPLICA**, não do primário
- **OLTP fica intocado** — sem queries pesadas competindo com NFS-e/OS/certificado
- **Painel do dono cross-tenant** continua via role admin separada, mas roda na réplica (zero impacto operacional)

**Vantagens:**
- Migração transparente — código não muda (só configuração de connection string da camada BI)
- Sem nova tecnologia pra agentes IA aprenderem
- Custo: +1 VPS (Hostinger KVM 4 = R$ 400/mês) OU +read-replica gerenciada AWS (~R$ 300/mês)

**Critério de saída:** ≥ 200 tenants OU `mv_*` levarem >5 min pra atualizar OU tamanho do banco > 100 GB.

---

### Fase 2 — escala (200+ tenants) → DuckDB embedded ou ClickHouse

Quando a Fase 1 saturar, **migrar a camada analítica para tecnologia OLAP de verdade** (não mais PostgreSQL). Duas opções, decisão diferida pro momento da migração com base no perfil real de carga:

**Opção 2a — DuckDB embedded:**
- DuckDB roda **dentro do processo Python** (igual SQLite). Não precisa servidor separado.
- ETL noturno (job Celery) lê do read-replica PG, transforma, carrega num arquivo `*.duckdb` local
- Superset aponta pro DuckDB pra dashboards históricos; queries em tempo real continuam no PG read-replica
- **Custo: R$ 0** (open source, mesmo VPS)
- **Limite: ~1 TB comprimido** — suficiente pra ~500 tenants × 5 anos de dados

**Opção 2b — ClickHouse self-hosted:**
- ClickHouse em VM dedicada (Hostinger KVM 4 ou AWS sa-east-1)
- Replicador Debezium (ou trigger PG nativo) populando ClickHouse em tempo quase real
- **Custo: ~R$ 400-500/mês** (VM dedicada + storage)
- **Limite: bilhões de linhas** — escalável horizontalmente

**Critério de escolha 2a vs 2b** (decidido no momento da migração):
- Se BI Wave B/V2 ficou em "dashboards históricos com latência aceitável de 1 dia" → DuckDB
- Se omnichannel, manutenção preditiva ou farma exigirem analytics em tempo quase real → ClickHouse

**NÃO migrar pra Snowflake/BigQuery** mesmo em Fase 2. Motivo: ambos custam R$ 800-1.500/mês fixo + compute, e não há ganho funcional sobre ClickHouse self-hosted. Reabrir se TAM ultrapassar 2.000 tenants ou cliente farma exigir BigQuery por contrato.

---

## ETL/ELT — como os dados chegam à camada analítica

**Estratégia híbrida em todas as fases:**

| Tipo de dado | Atualização | Como |
|---|---|---|
| KPIs fixos do dono (receita, churn, MRR) | Diário 02:00 BRT | Job Celery agrega cross-tenant na role admin |
| DRE/Fluxo de caixa por tenant | A cada hora | `REFRESH MATERIALIZED VIEW CONCURRENTLY` |
| OS abertas/em atraso (operacional crítico) | Real-time (≤ 1 min) | Outbox pattern: comando publica evento → handler atualiza vista resumida |
| Certificados emitidos / por vencer | Real-time | Mesmo padrão outbox |
| Comissões devidas | Diário noite | Job Celery + vista materializada |
| Inadimplência | Diário noite | Job Celery + vista materializada |
| Auditoria de BI (quem viu o quê) | Real-time (síncrono) | Trigger PG na role admin grava em tabela append-only |
| Manutenção preditiva (ML) | Semanal | Job Celery treina modelo + serializa em Backblaze B2 |

**Outbox pattern (definição rápida):** cada comando do OLTP (criar OS, emitir certificado) escreve numa tabela `outbox` ao mesmo tempo que escreve nas tabelas operacionais (mesma transação). Job Celery a cada 10s lê `outbox`, dispara handlers (atualizar vista materializada, publicar evento, etc), marca como processado. Garante consistência sem perder eventos se o Celery cair.

**Por que não Debezium/CDC desde a Fase 0:** Debezium é poderoso mas exige Kafka/Redpanda + operação adicional. Outbox pattern em Python puro cobre 95% dos casos com 5% da complexidade. Debezium entra só se Fase 2 escolher ClickHouse com replicação em tempo real.

---

## Dashboards e relatórios — onde rodam

| Tipo | Tecnologia | Quando entra |
|---|---|---|
| **Dashboards fixos por tenant** (DRE, fluxo, OS, certificados) | Apache Superset embedded no Django via iframe + RLS | Fase 0 (MVP-1) |
| **Painel do dono cross-tenant** (Roldão) | Superset com role admin separada, vistas dedicadas | Fase 0 |
| **Gráficos dentro dos módulos** (mini-charts em listagens, página de OS, dashboard do técnico) | ECharts via HTMX (ADR-0010 Camada 2) — não usa Superset | Fase 0 |
| **Builder de relatórios customizáveis** (usuário monta cubo) | Superset (modo "explore" + dashboard saver) | Wave B (pós-MVP-1) |
| **Link público compartilhado** (cliente baixa relatório agregado) | Superset com permissão "explore" desabilitada + filtro forçado de agregação mínima | Wave B/V2 |
| **Manutenção preditiva ML** (V3) | Modelo treinado offline (scikit-learn) + endpoint Django que serve predição | V3 |

**Por que Superset e não Metabase/Grafana:**
- Superset é open source 100% (Apache Software Foundation) — Metabase community version tem limitações de embed
- Superset suporta RLS PostgreSQL nativamente
- Permissões granulares por usuário/dataset/coluna
- Editor de gráfico tem builder visual decente (não é tão bom quanto Tableau/PowerBI, mas é suficiente)
- Pool de exemplos pra agentes IA é grande (~5k empresas usam em produção)

**Por que não Grafana pra dashboards de negócio:** Grafana é excelente pra observabilidade (métricas de servidor, logs, traces), mas não é otimizado pra dashboards de negócio com filtros por tenant, drill-down em dimensões, export de relatório. Mantemos Grafana só pra observabilidade (ADR-0001 e operação).

---

## LGPD + link público de relatório

Quando Wave B liberar link público compartilhado de relatório (cliente final compartilha métrica com cliente dele), aplicar **3 travas**:

1. **Agregação mínima:** se o resultado tem menos de 3 clientes distintos OU menos de 10 linhas agregadas, bloquear render com erro "Resultado insuficientemente agregado pra link público — exporte CSV em vez disso".
2. **Sem campos PII no resultado:** CPF, nome cliente, email, telefone são automaticamente removidos do dataset acessível via link público (camada de view dedicada `analytics_public.*` que já filtra).
3. **Rate limit + audit:** 30 requests/min/IP por link, e cada acesso grava em `audit_trail.bi_public_links` (append-only).

A regra "n ≥ 3" segue o padrão usado por Datafolha e IBGE em divulgação de microdados — proteção contra de-anonimização por inferência.

---

## Audit trail de BI (21 CFR Part 11 quando cliente farma chegar)

Tabela `audit_trail.bi_events` registra **toda interação com BI**:

| Campo | Conteúdo |
|---|---|
| `timestamp` | Quando |
| `user_id` | Quem |
| `tenant_id` | Em qual tenant (ou `NULL` se cross-tenant admin) |
| `acao` | `view_dashboard`, `run_query`, `export_pdf`, `share_link`, `drill_down` |
| `recurso_id` | ID do dashboard/relatório/query |
| `parametros` | JSON dos filtros aplicados |
| `resultado` | `sucesso` / `bloqueado_lgpd` / `bloqueado_rbac` / `erro` |
| `tamanho_bytes` | Tamanho do resultado |
| `ip_hash` | SHA-256 do IP (LGPD — não armazena IP cru) |

**Imutabilidade:**
- Tabela `INSERT-only` (trigger bloqueia UPDATE/DELETE)
- Cópia para Backblaze B2 (WORM Object Lock) a cada hora via Celery
- Hash chain entre linhas (cada linha referencia hash da anterior) — detecta adulteração

**Retenção:** conforme `docs/conformidade/comum/retencao-matriz.md`:
- 5 anos no PG quente (consulta rápida)
- 25 anos no B2 WORM (auditoria ISO 17025 + 21 CFR Part 11)
- Crypto-shredding por tenant: chave KMS do tenant criptografa o `parametros` e `resultado`; deletar a chave = dado fica ilegível mesmo no B2 (LGPD direito ao esquecimento honrado sem violar retenção)

---

## Custo estimado

| Fase | Tenants | Custo BI adicional/mês | Custo BI cumulativo/ano |
|---|---|---|---|
| Fase 0 | 1-15 | R$ 0 (dentro do VPS existente) | R$ 0 |
| Fase 1 | 15-50 | R$ 300-400 (read-replica VPS ou RDS) | R$ 3.600-4.800 |
| Fase 2a (DuckDB) | 50-500 | R$ 50 (storage adicional B2 pra modelos ML) | R$ 600 |
| Fase 2b (ClickHouse) | 50-500+ | R$ 400-500 (VM ClickHouse + Debezium) | R$ 4.800-6.000 |

**Comparativo (que NÃO vamos pagar):**
- Snowflake: R$ 800/mês mínimo + compute → ~R$ 1.500-3.000/mês real
- BigQuery: R$ 0 mínimo mas storage + query custam ~R$ 1.000-2.000/mês em escala
- Metabase Cloud: R$ 400/mês por instância sem multi-tenant decente

---

## Alternativas consideradas

### 1. Manter PG único pra sempre — REJEITADA
**Atrativo:** sem nova infra, sem migração.
**Rejeitada porque:** com 48 módulos × 100+ tenants, BI roda agregação por cima de dezenas de milhões de linhas concorrendo com NFS-e/OS/certificado. Auditor 5 mostrou que sem materialização + read-replica, OLTP entra em lock e SLA 99.9% quebra.

### 2. Snowflake/BigQuery desde o dia 1 — REJEITADA
**Atrativo:** padrão moderno, escala infinita.
**Rejeitada porque:** custo fixo R$ 800-1.500/mês com 1-5 tenants é desperdício. Auditor 5 e Auditor 9 marcaram explicitamente como erro #1 ("subir Snowflake pra 10 tenants"). Reabrir se TAM > 2.000 tenants ou farma top exigir.

### 3. Metabase em vez de Superset — REJEITADA
**Atrativo:** UI mais polida que Superset.
**Rejeitada porque:** Metabase Community não tem embed multi-tenant decente (precisa Enterprise = R$ 400+/mês). Superset (Apache) é 100% gratuito com features equivalentes. Diferença de UI é marginal.

### 4. Grafana pra dashboards de negócio — REJEITADA
**Atrativo:** já vamos ter Grafana pra observabilidade.
**Rejeitada porque:** Grafana é otimizado pra time-series e métricas operacionais, não pra agregações de negócio com filtros tenant + drill-down + export. Forçar Grafana onde Superset cabe = ferramenta errada.

### 5. Construir builder de relatórios próprio dentro do Django — REJEITADA
**Atrativo:** controle total, integração nativa.
**Rejeitada porque:** Superset já tem 10+ anos de evolução, builder visual maduro, permissões granulares. Reconstruir = 6+ meses de trabalho de agentes IA + manutenção eterna. Auditor 5 marcou explicitamente como erro #3.

### 6. CDC via Debezium desde Fase 0 — REJEITADA (diferida)
**Atrativo:** real-time perfeito, sem outbox.
**Rejeitada porque:** Debezium exige Kafka/Redpanda + operação. Outbox pattern em Python puro cobre 95% dos casos com 5% da complexidade. Considerar em Fase 2b se escolher ClickHouse.

---

## Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Real-time perfeito vs simplicidade operacional | Outbox pattern + vistas materializadas | 1 min de atraso é aceitável pra 95% dos dashboards; Debezium é overkill em Fase 0 |
| Data warehouse pago (Snowflake) vs PG self-hosted | PG self-hosted | Custo zero adicional Fase 0; migra pra DuckDB/ClickHouse em Fase 2 sem reescrita do código de aplicação (só ETL) |
| Builder próprio vs Superset embedded | Superset | Maduro, gratuito, multi-tenant via RLS, pool agentes IA grande |
| Cross-tenant via BYPASSRLS vs role admin separada com vistas dedicadas | Role admin + vistas | Defesa em profundidade — admin não bypassa RLS, ele consulta vista que já agrega |
| Audit trail BI síncrono vs assíncrono | Síncrono (trigger PG) | 21 CFR Part 11 exige garantia forte; perda de evento de auditoria é inaceitável |

---

## Consequências

### Positivas
- **Fase 0 custa zero** — entrega BI funcional em MVP-1 sem aumentar fatura
- **Migração entre fases é gradual** — Fase 1 troca só connection string; Fase 2 só troca destino do ETL
- **Anti-corrosion respeitado** — código de aplicação consulta a "porta `AnalyticsBackend`" (vide ADR-0010 e revisão futura do anti-corrosion-layer.md); implementação troca sem afetar domínio
- **LGPD e 21 CFR Part 11 cobertos desde MVP-1** — audit trail imutável + crypto-shredding + agregação mínima
- **Painel do dono cross-tenant funciona** sem violar RLS dos tenants

### Negativas
- **Latência de 1 min nos dashboards** (não real-time absoluto) — aceitável pra 95% dos casos; críticos usam outbox (≤ 10s)
- **Superset adiciona 1 container Docker** ao VPS — ~500 MB RAM, 0.5 vCPU
- **Vistas materializadas precisam refresh agendado** — se job Celery falhar, dashboard fica desatualizado; mitigação: alerta Grafana se `pg_stat_user_tables.last_refresh` > 2h
- **Migração Fase 0 → Fase 1 exige planejamento de cutover** — 2-4 horas de janela de manutenção pra promover read-replica e ajustar connection strings

---

## Itens a fazer (consequência operacional desta ADR)

### Bloqueantes antes de MVP-1 (Fase 0)
- [ ] **`docs/arquitetura/bi-convencoes.md`** — convenções pra criação de vistas materializadas, naming, refresh strategy, permissões Superset
- [ ] **Atualizar `docs/arquitetura/anti-corrosion-layer.md`** — adicionar porta `AnalyticsBackend` (já recomendada pelo Auditor 10 da auditoria anterior)
- [ ] **Schema `analytics_*` no PG** — DDL inicial com placeholders pras vistas Wave A
- [ ] **Setup do Superset embedded** — container Docker, integração com Django (auth compartilhada via JWT), config multi-tenant
- [ ] **Role `afere_bi_admin` no PG** — credencial segregada, sem `BYPASSRLS`, com acesso só ao schema `analytics_admin_*`
- [ ] **Tabela `audit_trail.bi_events`** — INSERT-only com trigger, hash chain

### Bloqueantes antes de Fase 1
- [ ] **Spike de carga** — gerar 5 tenants sintéticos com 6 meses de dados realistas, medir `pg_stat_statements` em horário de BI ativo
- [ ] **Critério objetivo de "saturado"** — definir antes (qual métrica, qual limiar, qual janela)
- [ ] **Ansible playbook** pra provisionar read-replica em < 30 min
- [ ] **Runbook de cutover** Fase 0 → Fase 1

### Bloqueantes antes de Fase 2
- [ ] **Spike DuckDB vs ClickHouse** — montar ambos em staging com dataset real de Fase 1, medir latência + custo operacional
- [ ] **ADR-0011-rev1** documentando a escolha 2a vs 2b com fato

---

## Critérios de reversão (quando esta ADR é revisitada)

| Sinal | Resposta |
|---|---|
| Fase 0 saturar mais cedo que esperado (< 15 tenants) | Antecipar Fase 1; revisar se a causa é design ruim de vista materializada ou volume real |
| Cliente farma TOP exigir BigQuery por contrato | Reabrir; avaliar BigQuery isoladamente pra esse tenant (DB-per-tenant pattern) |
| 21 CFR Part 11 evoluir e exigir audit trail em ferramenta certificada (Splunk, etc) | Reabrir item "audit_trail.bi_events"; pode precisar migrar pra ferramenta certificada |
| Superset descontinuar embed ou ficar pago | Migrar pra Apache Cubejs ou construir builder próprio (último recurso) |
| Outbox pattern não escalar (> 100k eventos/min) | Migrar pra Debezium + Kafka/Redpanda — Fase 2b já considera isso |
| TAM real ultrapassar 2.000 tenants em < 3 anos | Reabrir Fase 2: avaliar BigQuery ou ClickHouse Cloud |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita estratégia em 3 fases progressivas
- [ ] **Auditor de Qualidade:** confirma cobertura de testes para vistas materializadas + outbox
- [ ] **Auditor de Segurança:** confirma role admin separada não cria brecha cross-tenant; audit trail imutável defensável em fiscalização
- [ ] **Tech-lead substituto:** confirma viabilidade operacional de Superset embedded + cutover Fase 0 → Fase 1

---

## Referências

- ADR-0001 — Stack técnica (PostgreSQL escolhido)
- ADR-0002 — Multi-tenancy (RLS + role NOBYPASSRLS)
- ADR-0010 — Estratégia de tela (BI Camada 2: HTMX + ECharts pros mini-charts intra-módulo)
- Auditoria 10 agentes 17/05/2026 — Auditor 5 (BI/dados/analytics), Auditor 2 (Multi-tenant escala)
- Auditoria às cegas 17/05/2026 — Auditores F (BI), E (multi-tenant), G (DevOps) convergiram em "PG único até saturar, depois read-replica, depois OLAP"
- `docs/dominios/dados/modulos/bi/prd.md`
- `docs/painel-do-dono.md`
- `docs/conformidade/comum/retencao-matriz.md` (a criar — referenciada por ADR-0001)
