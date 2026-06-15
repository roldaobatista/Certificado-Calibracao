---
owner: agente-ia
revisado-em: 2026-06-15
proximo-review: 2026-09-15
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: contas-receber
tipo: reviews-consolidado
relacionados:
  - docs/faseamento/contas-receber/spec.md
  - docs/faseamento/contas-receber/T-CR-000-investigacao.md
---

# P2 — Revisão consolidada da spec `contas-receber`

> Revisão P2 do ritual (2026-06-15) por 3 subagentes especialistas sobre a `spec.md` v1.
> `tech-lead-saas-regulado` (Opus — decisão arquitetural), `advogado-saas-regulado` (Sonnet),
> `consultor-rbc-iso17025` (Sonnet). **Veredito agregado: APROVA COM CORREÇÕES.** Os 3 CRIT do
> tech-lead bloqueavam a v2 (contratos de módulos JÁ FECHADOS ignorados pela spec) e foram
> incorporados. Detalhe por achado abaixo; o destino (spec v2 / plan / GATE) está marcado.

## Veredito por revisor

| Revisor | Veredito | Achados |
|---|---|---|
| `tech-lead-saas-regulado` | APROVA COM CORREÇÕES | TL-CR-01..13 + R-CR-NOVO-1..4 |
| `advogado-saas-regulado` | APROVA COM CORREÇÕES | ADV-CR-01..07 |
| `consultor-rbc-iso17025` | APROVA COM CORREÇÕES | RBC-CR-01..06 |

---

## 1. Achados CRÍTICOS do tech-lead (bloqueavam v2 — RESOLVIDOS na spec v2)

### TL-CR-01 (CRIT) — Bloqueio de inadimplência: `clientes` JÁ tem modelo PULL D+90; não criar PUSH paralelo
- **Achado.** `src/domain/comercial/clientes/inadimplencia_source.py:17-33` define Protocol
  `InadimplenciaSource.iter_inadimplentes_90d()` (hard-coded 90d); `src/infrastructure/clientes/
  inadimplencia.py:38-39` documenta que o adapter real virá de `contas-receber`; o job
  `clientes/management/commands/job_inadimplencia_alertas.py:53-120` é quem itera, checa flag
  `Tenant.bloqueio_automatico_inadimplencia_habilitado` e cria `ClienteBloqueio` + publica
  `cliente.bloqueado` (modelo **PULL**). A spec D-CR-9 propunha PUSH (CR roda job → publica evento →
  clientes consome). Dois caminhos = bloqueio não-determinístico + duas flags divergentes.
- **DECISÃO (acatada — PULL canônico, menor blast radius em módulo fechado):** CR implementa o **adapter
  real do Protocol `InadimplenciaSource` existente** em `src/infrastructure/contas_receber/`,
  substituindo o interino. O adapter aplica `grace_period_inadimplencia_por_perfil` ao montar a lista (só
  entra o título com `vencimento + grace_do_perfil <= today`); `InadimplenciaItem` ganha `perfil`/`grace_perfil`.
  O job/`ClienteBloqueio` continua dono do bloqueio (módulo `clientes`). Reconciliar a flag: a
  `bloqueio_inadimplencia_habilitado` (ADR-0043 §2) **é a mesma** `bloqueio_automatico_inadimplencia_habilitado`
  já existente em `clientes` — não criar flag nova. → **spec v2 D-CR-9 reescrita; GATE-CR-INADIMPLENCIA-RECONCILIA no plan.**

### TL-CR-02 (CRIT) — OS já consome `os.faturada`/`os.paga` (dangling); CR deve publicá-los
- **Achado.** `ordens_servico/apps.py:131-132` registra `handle_os_faturada`/`handle_os_paga`;
  `ordens_servico/consumers/financeiro.py:1-12` diz "módulo financeiro (Wave A futuro) publicará". Os
  eventos `os.faturada`/`os.paga` **não estão em `ACOES_CANONICAS` e ninguém os publica** — caminho morto.
  A saga de anonimização (`anonimizacao.py:35`) lista `faturada`/`paga` como terminais alcançáveis.
- **DECISÃO (acatada):** CR publica, **além de** `contas_receber.titulo_emitido`, o evento `os.faturada`
  (payload `{os_id}`) quando o título nasce de OS; e `os.paga` ao dar baixa de título de OS. Namespace:
  ficam em `ACOES_OS` (são fatos de estado da OS, mesmo publicados por CR — o namespace reflete o agregado
  dono do estado). CR é autorizado a publicá-los. → **spec v2 §6 (eventos) + plan (fatia emissão/baixa).**

### TL-CR-03 (CRIT) — Enriquecer `os.concluida` no OUTBOX, nunca no WORM imutável da OS
- **Achado (corrige erro factual da spec v1).** O `os.concluida` cross-módulo NÃO passa por
  `sanitizar_payload_evento_os` — passa pelo genérico `sanitizar_payload_audit` (`audit/services.py:120-142`),
  que NÃO bloqueia `cliente_id` e preserva UUIDs (por isso `orcamento.aprovado` publica `cliente_id` raw). PORÉM
  o `os.concluida` é gravado **primeiro na cadeia WORM `evento_de_os` (append-only, 25a)** via
  `**snapshot.payload_data` e só depois cruza pro outbox (`repositories.py:660-665`). Injetar `cliente_id`/`valor`
  no `EventoDeOS.payload_data` os grava no WORM imutável por 25 anos — onde o `sanitizar_payload_evento_os`
  (INV-OS-AUD-001) corretamente os proíbe.
- **DECISÃO (acatada):** o enriquecimento de `os.concluida` adiciona `cliente_referencia_hash`/`cliente_key_id`
  /`valor_total` **ao payload do OUTBOX** (montado em `repositories.py:660` no momento de cruzar, lendo da
  `OS`/`OSSnapshot`), mantendo o `payload_data` da cadeia WORM minimalista (só `tipo_predominante`/
  `nao_conformidade_global`). Cliente vai como **ReferenciaPIIAnonimizavel** (hash+key_id), NÃO `cliente_id` raw
  no WORM. → **spec v2 D-CR-12 + T-CR-000 §7 corrigidas; fatia GATE-CR-OS-EVENTO no plan (toca OS, skip hooks legado).**

---

## 2. Achados ALTOS do tech-lead

### TL-CR-04 (ALTO) — Path FLAT (igual `fiscal`), não aninhado em `financeiro/`
- `src/domain/financeiro/` não existe; o irmão financeiro `fiscal` está flat (`src/domain/fiscal/`).
- **DECISÃO:** `src/domain/contas_receber/` + `src/application/contas_receber/` + `src/infrastructure/contas_receber/`
  (flat, molde fiscal). → **spec v2 D-CR-1; fecha a hesitação.**

### TL-CR-05 (ALTO) — CR não desbloqueia cliente; `clientes` é dono do `ClienteBloqueio`
- D-CR-11 dizia CR publica `Cliente.Desbloqueado`. Mas o estado vive em `ClienteBloqueio` (`clientes/views.py:611-628`);
  evento canônico é `cliente.desbloqueado` (lowercase, `acoes_canonicas.py:27`).
- **DECISÃO (acatada):** CR publica `contas_receber.pago` + expõe query `tem_outra_vencida_em_aberto(cliente_id) -> bool`.
  O módulo `clientes` ganha **consumer novo** de `contas_receber.pago` que encerra o `ClienteBloqueio` e publica
  `cliente.desbloqueado` ≤5min. → **spec v2 D-CR-11; fatia cross-módulo em `clientes` no plan.**

### TL-CR-06 (ALTO) — Faturar na conclusão da OS é correto; tratar título órfão de OS cancelada/reaberta
- Momento correto = conclusão da OS (serviço entregue, valor carimbado), NÃO aprovação do orçamento (cobrar antes
  de entregar quebra B2B; ADR-0043 rejeitou pré-pago). Mas falta tratar `os.reaberta` (`value_objects.py:144`).
- **DECISÃO:** idempotência de negócio por `os_id` — `UNIQUE(tenant_id, os_id_origem) WHERE estado != cancelado`
  (1 OS → 1 título ativo). Comportamento em `os.reaberta`: cancelar título só se sem pagamento parcial (D-CR-3 cobre);
  consumer `os.reaberta` ou non-goal explícito com GATE. → **spec v2 D-CR-12 + INV nova; plan.**

### TL-CR-07 (ALTO) + RBC-CR-03 (MÉDIO) — `perfil_no_evento` no consumer vem do ENVELOPE, não de current_setting
- O consumer assíncrono NÃO pode reler `obter_perfil_tenant_corrente()` (pegaria o perfil ATUAL do tenant, não o
  do fato gerador — fura a defesa CGCRE cl. 8.4 se o perfil mudou entre publicação e consumo). O perfil vem de
  `envelope["perfil_no_evento"]` (INT-03, já existe no envelope v10), gravado na publicação. Trigger fallback
  `BEFORE INSERT` só ativa via `COALESCE(NEW.perfil_no_evento, current_setting(...))` quando chega NULL — nunca
  sobrescreve. → **spec v2 D-CR-6 reescrita (separar caminho síncrono REST × assíncrono consumer).**

---

## 3. Achados MÉDIOS/BAIXOS do tech-lead (anotados no plan)

- **TL-CR-08 (MÉDIO):** dupla cobrança cert×OS — análise correta (confirmado por RBC-CR-05). Confirmar no P8 que
  não há certificado avulso sem OS (RBC confirmou: todo cert vem de atividade de OS — ADR-0023). Certificado de
  padrão interno = não-faturável (declarar na ADR de reconciliação).
- **TL-CR-09 (MÉDIO):** recorrência PIX Wave A emite só o **1º título** + registra convênio no gateway (Mock);
  geração dos títulos subsequentes = **GATE Wave B** (precisa do agrupador `Fatura`/`Contrato`).
- **TL-CR-10 (MÉDIO):** assinatura `calcular_valor_atualizado(titulo, pagamentos, data, regra) -> Dinheiro`;
  juros incidem sobre `valor_original - sum(pagamentos)` (saldo), não sobre `valor_original`.
- **TL-CR-11 (MÉDIO):** D-CR-14 confirmado. Criar bloco `ACOES_CONTAS_RECEBER` + adicionar à união
  `ACOES_CANONICAS` (senão `assert_acao_canonica` em `:469` faz todo publish falhar). Não precisa migration de
  CHECK (CHECK é sintático). Incluir `os.faturada`/`os.paga` em `ACOES_OS` (TL-CR-02).
- **TL-CR-12 (MÉDIO):** webhook — baixa + INSERT `gateway_events` + `publicar_evento` na MESMA
  `transaction.atomic`. Idempotência DUPLA: por `gateway_event_id` (replay exato) E por estado (título já
  `pago` → 200 sem re-gravar `Pagamento`).
- **TL-CR-13 (MÉDIO):** GATE-CR-SERIE-REGIME **fechado** por ADR-0080 — título = documento fiscal-adjacente =
  **GAP_LESS** (derivado do tipo via `regime_numeracao_do_tipo`, nunca do caller). Confirmar se
  `numero_sequencial_tenant` é exigência contábil real ou over-engineering (se o número vier do gateway/boleto,
  id interno basta — remover dependência `SerieDocumento`).
- **R-CR-NOVO-1 (ALTO):** webhook público + RLS — resolver tenant via `SECURITY DEFINER`/índice antes de
  `run_in_tenant_context`; anti-oráculo (gateway_id inexistente ≡ HMAC inválido = 401 indistinguível, sem
  diferença de timing). Validação real = **pentest externo** no GATE-CR-ASAAS.
- **R-CR-NOVO-2 (MÉDIO):** `valor_total` da OS/orçamento é **string decimal** (`"1234.56"`), fiscal usa
  `valor_centavos` int. CR padroniza internamente em centavos (VO `Dinheiro`); conversão num único ponto na
  borda + teste de borda (`"0.10"`, `"100.005"`, zero).
- **R-CR-NOVO-3 (MÉDIO):** tenant suspenso (ADR-0035) — **o PRD §10 já decide**: "tenant suspenso → mantém
  leitura, bloqueia emissão de novo título". O consumer NÃO cria título quando tenant suspenso (manda pra
  dead-letter / reprocessa ao reativar). Sem necessidade de decisão do Roldão.
- **R-CR-NOVO-4 (BAIXO):** override limite 5%/mês — contador por query mensal no use case; estouro → alerta P1 +
  bloqueia novos overrides (ADR-0043 §3).

---

## 4. Achados do advogado (ADV-CR-*)

- **ADV-CR-01 (CRIT):** notificação D+30/D+45 precisa de **conteúdo mínimo CDC** (art. 6º III/IV + Lei 14.181/2021
  + art. 42). Payload de `contas_receber.inadimplencia_dura_atingida` (e do aviso D+30) deve carregar
  `titulos_vencidos[{titulo_id, valor_original, data_vencimento, dias_vencido}]` + `data_bloqueio_prevista` +
  `canal_regularizacao_url` (config do tenant). → **spec v2 D-CR-9 + AC; converge com RBC-CR-01.**
- **ADV-CR-02 (ALTO):** declarar explícito que o bloqueio **NÃO alcança documentos já emitidos/pagos** (CDC art.
  39 V — recusa de serviço já contratado). → **spec v2 §1 fronteira + nota INV-CLI-BLOQ-001.**
- **ADV-CR-03 (ALTO):** retenção do hash pós-anonimização — base legal por perfil (ISO 8.4 art. 7º II p/ A/B/C
  25a; CTN art. 195 p/ D 5a; hash não é PII sem chave KMS — re-identificabilidade ANPD Res. CD 2/2022). →
  **GATE-LGPD-RAT-CR (congelado).**
- **ADV-CR-04 (MÉDIO):** override `justificativa` ≥100 chars **anti-PII** — rastrear `INV-CAL-TXT-001` ou criar
  `INV-CR-OVERRIDE-ANTI-PII`. → **spec v2 D-CR-10 + INV; verificar existência de INV-CAL-TXT-001.**
- **ADV-CR-05 (MÉDIO):** webhook payload mínimo — adapter Asaas real não loga payload bruto com PII do pagador
  (`customer.*`); extrai só o que `Pagamento` precisa. → **INV-CR-WEBHOOK-PAYLOAD-MINIMO no GATE-CR-ASAAS.**
- **ADV-CR-06 (BAIXO):** `CALIBRACAO_RBC` só A = defesa anti-fraude adequada (CP art. 299). APROVADO.
- **ADV-CR-07 (BAIXO):** perfis B/C/D — evento `contas_receber.titulo_vencido` carrega payload suficiente p/
  notificação; termos de uso atribuem ao tenant a comunicação prévia (tenant = controlador; Aferê = operador).
  → **spec v2 nota + GATE-LGPD-RAT-CR (termos de uso).**

---

## 5. Achados do consultor-RBC (RBC-CR-*)

- **RBC-CR-01 (MÉDIO):** grace D+45 perfil A correto, MAS a notificação D+30/D+45 não pode ficar só em Wave B
  enquanto o bloqueio é Wave A — violação CDC se o tenant A ativar a flag sem canal. **DECISÃO:** entregar
  notificação D+30/D+45 em Wave A via **`send_mail` Django simples** (cumpre CDC); os lembretes ricos D-7/D-3/D-0
  ficam Wave B (`OmniChannelProvider`). Criar **GATE-CR-NOTIF-D30-PERFIL-A** (bloqueante: tenant A só ativa flag
  se canal de notificação operacional). → **spec v2 D-CR-9 + recorte §2 US-CR-010; converge com ADV-CR-01.**
- **RBC-CR-02 (BAIXO):** dependência cruzada — `fiscal` deve mapear `CALIBRACAO_BASICA` para descrição sem "ISO
  17025"/"RBC" (hook ADR-0067 §8). Payload `titulo_emitido` carrega o enum correto. → **spec v2 nota cross-módulo.**
- **RBC-CR-03 (MÉDIO):** = TL-CR-07 (perfil do envelope, trigger só se NULL).
- **RBC-CR-04 (BAIXO):** anonimização perfil D do `Pagamento` preserva `valor`/`data`/`origem`/`titulo_id`
  (obrigação fiscal RF 5a); zerável `comprovante_url`. → **GATE-LGPD-RAT-CR + nota D-CR-17.**
- **RBC-CR-05 (NENHUM):** dupla cobrança cert×OS — confirmado correto (todo cert vem de OS; ADR-0023/0082; reter
  cert seria NC cl. 7.8). Sem ação.
- **RBC-CR-06 (MÉDIO):** clarear escopo do bloqueio: atinge **abertura de nova OS + aprovação de novo orçamento**;
  NÃO impede emissão de certificado de **OS já em andamento** (reter seria NC cl. 7.8) nem download histórico. AC
  de teste para a janela "cliente fica inadimplente durante execução da OS". → **spec v2 §1 + AC; nota INV-CLI-BLOQ-001.**

---

## 6. Síntese — destino dos achados

- **Incorporados na spec v2 (texto, sem mudar modelo nem tocar módulo fechado):** TL-CR-04/05/06/07, ADV-CR-01/02,
  RBC-CR-01/03/06, D-CR-9 reescrita (PULL + grace no adapter + notificação Wave A), D-CR-11 (inverter desbloqueio),
  D-CR-12 (enriquecer outbox não-WORM), D-CR-6 (perfil do envelope), eventos `os.faturada`/`os.paga`.
- **Cravados como riscos/decisões no plan:** TL-CR-08..13, R-CR-NOVO-1..4, ADV-CR-04, RBC-CR-02/04.
- **GATEs novos:** GATE-CR-INADIMPLENCIA-RECONCILIA (PULL adapter), GATE-CR-NOTIF-D30-PERFIL-A (notificação CDC
  antes de ativar flag), GATE-CR-OS-EVENTO (enriquecer outbox da OS). GATE-CR-SERIE-REGIME **fechado** (ADR-0080).
- **Congelado (GATE-LGPD-RAT-CR):** ADV-CR-03/05/07, RBC-CR-04, base legal de retenção/bloqueio, termos de uso
  controlador×operador. Respeitado o congelamento RAT/DPIA (decisão Roldão 2026-06-12).
- **Limite de honestidade (tech-lead + advogado):** webhook público anti-oráculo/timing + HMAC real do gateway =
  **pentest externo** antes do 1º tenant pago (GATE-CR-ASAAS). Contrato vendor↔tenant (controlador/operador) =
  **revisão OAB** pré-produção.
