---
owner: roldao
revisado-em: 2026-05-23
status: proposta
---

# ADR-0014 — Transições regulatórias críticas (6 invariantes de integração + 3 fluxos proativos Onda 8)

> **Status:** **PROPOSTA** (17/05/2026, madrugada). Resolve 6 gaps críticos identificados pela auditoria de 10 agentes (Auditores C, E, F, J) + **3 fluxos proativos adicionados pela auditoria Onda 8 (2026-05-23 — auditor regulatório 7)**: ampliação de escopo CGCRE, NC CGCRE com SLA 30d, revisão CGCRE quinquenal. Também atualiza Fluxo 4 (bypass exige A3 do dono Aferê — local ou cross-tenant via SaaS suporte).
> **Autor:** Claude Code (orquestrador) + Roldão (decisor)
> **Origem:** Auditoria de integrações inter-modulares 17/05/2026 madrugada.
> **Depende de:** ADR-0001 (stack), ADR-0007 (camada domínio + outbox), ADR-0011 (BI 3 fases), ADR-0012 (autorização), ADR-0008 (fiscal pluggable).
> **Bloqueia:** Wave A da Metrologia/Qualidade (sem essas integrações, certificado emitido pode virar inválido retroativamente).

---

## Glossário rápido (pra Roldão)

| Termo técnico | O que é, na prática |
|---|---|
| **Transição regulatória** | Mudança que altera o que pode ou não ser feito por norma. Ex: técnico foi desligado → não pode mais assinar. |
| **Snapshot** | "Foto" de uma informação no momento que algo aconteceu. Cert emitido hoje guarda "foto" da acreditação atual; se acreditação for suspensa amanhã, foto continua mostrando que estava válida ontem. |
| **Bloqueio em cascata** | Quando um problema em um lugar bloqueia automaticamente várias outras coisas. Ex: padrão vencido bloqueia emissão de certificado que usa esse padrão. |
| **Retroatividade** | Mexer em coisa passada. ISO 17025 proíbe: certificado emitido ontem com tudo válido ontem **continua válido** mesmo se algo ficar inválido amanhã. |
| **Causation_id** | Marca que liga eventos em cadeia. "OS 123 → certificado X → NF-e Y" — tudo carrega o mesmo ID pra auditoria rastrear. |

---

## Contexto

A auditoria de 10 agentes (17/05/2026 madrugada) identificou **6 gaps críticos** onde **eventos publicados pelos módulos NÃO são consumidos por quem precisa bloquear/notificar**:

1. **Auditor J (cross-domínio):** `Fiscal.NFSeEmitida` permite `certificado_id = NULL` — NF-e órfã quebra rastreabilidade ISO 17025 cláusula 8.4
2. **Auditor C (metrologia):** RT signatário desligado bloqueia futuras emissões (correto) mas **NÃO** há checklist de transição (cliente não é avisado, OS futuras não são reatribuídas)
3. **Auditor C (metrologia):** Acreditação RBC suspensa retroativamente — certificados emitidos durante período válido não carregam **snapshot da acreditação vigente na emissão**
4. **Auditor C, E, F:** Padrão metrológico vencido só notifica RT — **NÃO bloqueia automaticamente** emissão de certificado que usa esse padrão
5. **Auditor E:** Treinamento NR (NR-10, NR-12, NR-35) ou ASO vencido só notifica RH — **NÃO bloqueia agendamento** do técnico em OS que exige a habilitação
6. **Auditor C, F:** Engenharia muda procedimento de calibração (`Engenharia.RevisaoAprovada`) — **NÃO pausa** OS em execução nem dispara revalidação RT

**Impacto regulatório agregado:**
- ISO 17025 cláusula 7.11 (validação de método) violada — método mudou, OS continuou
- ISO 17025 cláusula 6.5 (rastreabilidade de medições/padrões) violada — padrão vencido emitiu
- ISO 17025 cláusula 6.2 (competência de pessoal) violada — RT desligado sem substituto
- ISO 17025 cláusula 8.4 (registros) violada — NF-e órfã sem cert
- NR-10/NR-12/NR-35 violadas — técnico sem treinamento em OS de risco
- Lei 13.103/2015 (motorista) já coberta por INV-020

**Em fiscalização Cgcre:** auditor descobre regressivamente que cadeia foi quebrada em período X → não-conformidade maior → suspensão de acreditação → recall de certificados emitidos no período (R-039 ativo).

---

## Decisão

Cravar **6 fluxos de integração de transição regulatória** com eventos novos, consumers obrigatórios, snapshots imutáveis e bloqueios automáticos. Cada fluxo vira **invariante (INV-INT-001..006)** com hook validador.

### Fluxo 1 — NFS-e rastreável ao certificado (INV-INT-001)

**Problema:** `Fiscal.NFSeEmitida` permite `certificado_id` opcional. NF-e avulsa (não vinculada a certificado de calibração) é caso legítimo, mas hoje está **misturada** com NF-e de calibração.

**Decisão:**
- Reclassificar `Fiscal.NFSeEmitida` payload — adicionar campo obrigatório `tipo_servico: enum (calibracao | manutencao | consultoria | avulso)`.
- Se `tipo_servico == "calibracao"`, `certificado_id` torna-se **obrigatório** (constraint no schema + validação no save).
- Se `tipo_servico != "calibracao"`, `certificado_id` pode ser `null` (uso legítimo de NF-e avulsa).
- **Hook validador:** publish de `Fiscal.NFSeEmitida` com `tipo_servico=calibracao AND certificado_id IS NULL` é rejeitado pelo bus (não cria o evento).
- **INV-INT-001** registrada em `REGRAS-INEGOCIAVEIS.md`.

**Consequência operacional:** auditoria fiscal/Cgcre pode rastrear toda NF-e de calibração até o certificado de origem em < 1 query SQL. NF-e avulsa fica explicitamente sinalizada (não confundir).

---

### Fluxo 2 — RT desligado dispara checklist de transição (INV-INT-002)

**Problema:** `Colaborador.Desligado` publica, mas apenas `agenda` consome (libera slots). **Nenhum consumer em `metrologia/certificados`, `metrologia/calibracao`, `comercial/contratos`, `comunicacao-omnichannel`**.

**Decisão:**
- Adicionar consumers ao evento `Colaborador.Desligado`:
  - **`metrologia/certificados`:** se desligado é RT signatário, marca todos certificados antigos do RT como "últimos assinados por RT agora desligado" (sem invalidar — INV-026 preço/cert não retroage); registra ação em audit trail
  - **`metrologia/calibracao`:** bloqueia novas calibrações que exigem assinatura desse RT (até que outro RT seja designado pro tipo de serviço)
  - **`comercial/contratos`:** contratos vigentes que dependem desse RT entram em estado `pendente_designacao_rt` — não fatura recorrente até resolver
  - **`comunicacao-omnichannel`:** notifica clientes que têm contrato dependente — template "houve mudança no nosso time técnico, aguarde designação"
- **Novo evento publicado:** `Certificados.SignatarioTransicaoIniciada` (carrega `colaborador_id, tipos_servico_afetados, certificados_pendentes_count, contratos_afetados_count`)
- **Workflow obrigatório:** RH/Diretor designa RT substituto via UI; até resolver, futuras emissões dos tipos afetados ficam bloqueadas.
- **INV-INT-002** registrada.

**Consequência:** cenário do auditor C resolvido — desligamento dispara checklist explícito, não vácuo.

---

### Fluxo 3 — Snapshot de acreditação na emissão (INV-INT-003)

**Problema:** se acreditação RBC é suspensa retroativamente pela Cgcre (após auditoria), certificados emitidos durante período "válido" não conseguem provar **"estavam dentro de acreditação vigente NA DATA da emissão"**.

**Decisão:**
- Toda emissão de certificado RBC grava **snapshot completo** em `Certificado.snapshot_acreditacao`:
  - `acreditacao_id`, `versao_documento_id`, `data_validade_naquele_momento`, `escopo_acreditado_naquele_momento` (lista de tipos), `cgcre_status_naquele_momento` (`ativo/suspenso/cancelado`)
  - Hash do PDF do documento de acreditação vigente naquele momento (do módulo `gestao-documental` — armazenado em B2 WORM)
- Snapshot é **imutável** (campo JSONB selado por trigger PG `BEFORE UPDATE`)
- Se Cgcre depois suspender retroativamente, fiscalização vê snapshot mostrando "no momento da emissão, acreditação estava ATIVA e válida até `dd/mm/yyyy`"
- **Novo evento:** `Certificados.SnapshotAcreditacaoGravado` (audit trail)
- **INV-INT-003** registrada.

**Consequência:** ataque retroativo Cgcre defendido — certificados emitidos antes da suspensão **permanecem válidos com evidência**.

---

### Fluxo 4 — Padrão vencido bloqueia emissão automaticamente (INV-INT-004)

**Problema:** `Padroes.CertificadoVencendo` notifica RT (correto), mas se RT ignora e padrão vence, **emissão segue acontecendo** com padrão vencido. INV-011 e INV-021 cobrem "deve bloquear" mas não há hook automático.

**Decisão:**
- Job diário (Celery Beat) varre padrões com `data_validade_externa <= now()`:
  - Publica `Padroes.CertificadoVencido` (evento novo, diferente de `CertificadoVencendo`)
  - Atualiza tabela `padroes_disponibilidade`: padrão marcado como `bloqueado_uso: true`
- Consumer em `metrologia/certificados` **bloqueia hard** emissão que usaria padrão bloqueado:
  - `AuthorizationProvider.can(action="certificado.emitir", resource={"padroes_usados": [...]})` consulta `padroes_disponibilidade` e retorna `denied, reason="padrao_X_vencido_em_Y"`
- **Modo emergencial (INV-033 — atualizado Onda 8 A-REG-07):** bypass exige **A3 do dono Aferê presente no ambiente do cliente**. Se não houver A3 do dono local (caso típico de tenant pequeno sem dono Aferê presencial), bypass é executado **cross-tenant via Aferê SaaS suporte** (operador do dono assina remotamente via canal Aferê), com `audit WORM + retenção 25a + escalação síncrona ao dono Aferê`. Publica `Padroes.ModoEmergencialAcionado{modo: local_a3 | saas_suporte_remoto}`. Justificativa mínima 50 chars obrigatória.
- **Verificação intermediária:** se passou data de verificação intermediária + 7 dias sem registro, padrão também marca como bloqueado (INV-022 automatizada)
- **INV-INT-004** registrada.

**Consequência:** padrão vencido = bloqueio automático em 24h (próxima rodada do job). Cgcre não encontra certificado emitido com padrão vencido.

---

### Fluxo 5 — Treinamento/ASO vencido bloqueia agendamento (INV-INT-005)

**Problema:** `Treinamentos.CertificadoVencido` e `SST.ASOVencendo` apenas notificam RH. Agenda continua alocando o técnico em OS que exigem aquela habilitação.

**Decisão:**
- Tabela `tecnico_habilitacoes` atualizada em tempo real conforme eventos:
  - `Treinamentos.CertificadoEmitido` → marca habilitação como `vigente até <data>`
  - `Treinamentos.CertificadoVencido` → marca como `vencido` (não apaga — mantém histórico)
  - `SST.ASOEmitido` → marca ASO como `vigente até <data>`
  - `SST.ASOVencido` (evento novo) → marca como `vencido`
- Agenda (e App-Técnico) consultam `tecnico_habilitacoes` ANTES de alocar técnico em OS:
  - OS exige `nr_35` (trabalho em altura) E técnico tem habilitação NR-35 vencida → agenda **rejeita alocação** (hard block)
  - Mensagem clara pro despachante: "Técnico João Silva está com NR-35 vencida em 15/05/2026 — reciclagem necessária"
- **Modo emergencial:** Diretor pode autorizar bypass com justificativa + A3, mas dispara `Treinamentos.BypassAlocacaoCritica` (escalação automática pra dono Aferê — ANTI-11)
- **Job Celery diário** detecta alocações futuras que ficarão inválidas com vencimentos próximos (30 dias) — propõe reatribuição
- **INV-INT-005** registrada.

**Consequência:** zero acidentes por técnico sem treinamento. MTE em fiscalização vê "técnico bloqueado automaticamente" — sistema demonstra controle.

---

### Fluxo 6 — Mudança de procedimento pausa OS em execução (INV-INT-006)

**Problema:** `Engenharia.RevisaoAprovada` é consumida por `os` (no catálogo), mas **não interrompe OS em execução** que usa procedimento agora alterado.

**Decisão:**
- `Engenharia.RevisaoAprovada` payload expandido com `procedimentos_calibracao_afetados: list[procedimento_id]` (calculado pela engenharia ao aprovar)
- Consumer em `metrologia/calibracao` busca OS com `status IN ("agendada", "em_execucao", "em_revisao")` e que usam procedimentos afetados:
  - Marca OS com flag `procedimento_revisado_pendente_revalidacao = true`
  - Publica novo evento `Calibracao.OSPendenteRevalidacao`
  - Notifica RT responsável: "Procedimento P foi atualizado pra versão V; revalide os parâmetros usados nesta OS antes de continuar"
- App-técnico (offline) recebe push na próxima sync — exibe banner "procedimento atualizado, contate o RT antes de continuar"
- OS **não pode ser finalizada** sem ack do RT que confirma "ciente da mudança, parâmetros revalidados ou método antigo aplicável a esta OS"
- **INV-INT-006** registrada (espírito de INV-004b — mudança em rotina exige revalidação registrada)

**Consequência:** ISO 17025 cláusula 7.11 (validação de métodos) cumprida automaticamente. Auditoria Cgcre vê trilha: "procedimento atualizado em data X, OSs em andamento foram pausadas, RT revalidou cada uma, registro em audit trail".

---

---

### Fluxo 7 (Onda 8) — Ampliação de escopo de acreditação CGCRE (INV-INT-007 — proativo)

**Problema:** RT identifica nova grandeza/faixa que quer acreditar. Sem fluxo guiado, dossiê é montado por planilha + e-mail; CGCRE devolve por documentação incompleta; cronograma se arrasta.

**Decisão:**
- US-LIC-010 (em `licencas-acreditacoes/prd.md`) cria entidade `PedidoAmpliacaoEscopo` com pré-requisitos validados antes da submissão (dossiê 7.11 + ART RT + padrões rastreáveis pra novas grandezas + procedimentos validados).
- Eventos publicados: `Licencas.AmpliacaoEscopoSubmetida`, `Licencas.AcreditacaoAmpliada` (consumido por `metrologia/certificados` pra liberar emissão nas novas grandezas).
- Snapshot acreditação (INV-INT-003) congelado com novo escopo na data efetiva CGCRE.

---

### Fluxo 8 (Onda 8) — Resposta a NC CGCRE com SLA 30 dias (INV-INT-008 — proativo)

**Problema:** CGCRE abre NC em supervisão (NIT-DICLA-021 prevê severidade `menor` / `maior` / `crítica`). Sem fluxo, prazo vence e supervisão escalona pra suspensão.

**Decisão:**
- US-LIC-011 cria entidade `NCCgcre` com `{numero, severidade, prazo_resposta, evidencias_solicitadas}`.
- Sistema agenda alertas D-15/7/3/1 antes do prazo (≤30 dias padrão; menor pode ter prazo distinto).
- Severidade `maior` AND escopo afetado bloqueia emissão **hard** durante o período (INV-032).
- Evento `Licencas.NCCgcreAberta` consumido por `certificados` (bloqueia emissão se escopo afetado), `dashboard-dono-afere` (escalação), `comunicacao-omnichannel` (notifica RT + admin).
- Prazo vencido publica `Licencas.NCCgcrePrazoVencido` + escalation P1.

---

### Fluxo 9 (Onda 8) — Revisão CGCRE quinquenal (INV-INT-009 — proativo)

**Problema:** Acreditação CGCRE tem revisão obrigatória a cada 5 anos (NIT-DICLA-021). Sem aviso, admin descobre 30 dias antes do prazo e dossiê fica incompleto.

**Decisão:**
- US-LIC-012 calcula `proxima_revisao_5anos` a partir da última revisão; dispara alertas progressivos D-365/180/90/60/30.
- Checklist preparatório: atualização de padrões, ART RT vigente, validações 7.11 atualizadas, dossiê histórico, NCs fechadas.
- Evento `Licencas.DossieRevisao5AnosPronto` consumido por `dashboard-dono-afere`.

---

## Os 9 eventos NOVOS publicados (somam ao catálogo v8 → v10 com Onda 8)

**Eventos do Fluxo 7-9 (Onda 8):**
- `Licencas.AmpliacaoEscopoSubmetida{licenca_id, grandezas_novas, faixas_novas}`
- `Licencas.AcreditacaoAmpliada{licenca_id, escopo_novo}` → `certificados` libera emissão
- `Licencas.NCCgcreAberta{nc_id, severidade, prazo, escopo_afetado}` → `certificados` bloqueia se maior + escopo
- `Licencas.NCCgcreRespondida{nc_id}` → dashboard
- `Licencas.NCCgcrePrazoVencido{nc_id}` → P1 escalation
- `Licencas.DossieRevisao5AnosPronto{licenca_id}` → dashboard

## Os 6 eventos NOVOS originais (catálogo v8 → v9)

| Evento | Origem | Quem publica | Consumers |
|---|---|---|---|
| `Certificados.SignatarioTransicaoIniciada` | colaboradores → certificados | Job ao receber `Colaborador.Desligado` se for RT | calibracao (bloqueia novos), contratos (pendente designação), comunicacao-omnichannel (notifica cliente), audit |
| `Certificados.SnapshotAcreditacaoGravado` | certificados (ao emitir) | Sempre que emite cert RBC | audit, BI (rastreabilidade) |
| `Padroes.CertificadoVencido` | calibracao (subdomínio padrões) | Job Celery diário | certificados (bloqueia emissão), qualidade (NC automática), audit |
| `SST.ASOVencido` | seguranca-trabalho | Job Celery diário | agenda (bloqueia alocação), colaboradores (status update), audit |
| `Calibracao.OSPendenteRevalidacao` | calibracao | Ao receber `Engenharia.RevisaoAprovada` | app-tecnico (push), RT (notif), audit |
| `Padroes.ModoEmergencialAcionado` | calibracao (padrões) | RT força bypass | dono Aferê (escalação ANTI-11), audit WORM |

---

## Alterações em eventos existentes

| Evento | Mudança |
|---|---|
| `Fiscal.NFSeEmitida` | Payload ganha `tipo_servico: enum`. `certificado_id` torna-se condicionalmente obrigatório (se `tipo_servico=calibracao`). |
| `Colaborador.Desligado` | Payload ganha `is_rt_signatario: bool, tipos_servico_assinava: list[str]` (preenchido pelo módulo colaboradores ao identificar se desligado tem perfil RT). |
| `Engenharia.RevisaoAprovada` | Payload ganha `procedimentos_calibracao_afetados: list[procedimento_id]`. |
| `Treinamentos.CertificadoVencido` | Adicionar consumer `agenda` (atualiza `tecnico_habilitacoes`). |
| `Padroes.CertificadoVencendo` | Mantém alerta; novo evento `Padroes.CertificadoVencido` é o que bloqueia. |

---

## Alterações em policies RLS e autorização

Em `AuthorizationProvider.can()` (ADR-0012), adicionar regras ABAC dinâmicas:

```python
@authz_attribute("padroes_vigentes")
def _check_padroes_vigentes(user_id, resource, tenant_id, at_time):
    """Para ação certificado.emitir: padrões usados devem estar todos com data_validade > at_time"""
    if resource.get("padroes_usados"):
        for padrao_id in resource["padroes_usados"]:
            disponibilidade = PadraoDisponibilidade.get(padrao_id)
            if disponibilidade.bloqueado_uso:
                return False, f"padrao_{padrao_id}_bloqueado_em_{disponibilidade.bloqueado_em}"
    return True, "ok"

@authz_attribute("habilitacao_tecnico")
def _check_habilitacao_tecnico(user_id, resource, tenant_id, at_time):
    """Para ação agenda.alocar: técnico deve ter habilitações que OS exige + vigentes"""
    if resource.get("habilitacoes_exigidas"):
        habs = TecnicoHabilitacao.filter(tecnico_id=resource["tecnico_id"])
        for hab_exigida in resource["habilitacoes_exigidas"]:
            hab = habs.get(hab_exigida)
            if not hab or hab.status != "vigente" or hab.vence_em <= at_time:
                return False, f"habilitacao_{hab_exigida}_invalida"
    return True, "ok"
```

Hook lint custom (`semgrep`) bloqueia merge se função `emitir_certificado` ou `agenda_alocar` for chamada sem antes invocar `AuthorizationProvider.can()` com os atributos ABAC.

---

## Workflows novos a implementar (Wave A Foundation F-A + F-B)

| Workflow | Implementação | Onde |
|---|---|---|
| Designação de RT substituto após desligamento | Workflow BPM (`automacoes-bpm`) — etapa "Diretor designa RT para tipos X, Y, Z"; até resolver, bloqueio cascata permanece | `suporte-plataforma/automacoes-bpm` |
| Verificação intermediária programada | Job Celery diário + tabela `verificacao_intermediaria_padrao` | `metrologia/calibracao` (subdomínio padrões) |
| Bypass modo emergencial | UI dedicada exige justificativa + A3 + escalação automática | `metrologia/certificados` + `metrologia/calibracao` |
| Pausar OS por revisão de procedimento | Estado `pendente_revalidacao` na máquina de estados de OS + ack obrigatório do RT | `operacao/os` + `metrologia/calibracao` |

---

## Alternativas consideradas

### 1. Manter status quo (eventos publicados mas sem consumers de bloqueio) — REJEITADA
**Atrativo:** zero trabalho novo.
**Rejeitada porque:** 6 cenários reais de fiscalização Cgcre comprometidos — risco R-039 (Roldão solidário) ativo.

### 2. Bloqueio "soft" (apenas aviso, deixa passar) — REJEITADA
**Atrativo:** menos fricção operacional.
**Rejeitada porque:** ANTI-11 manda hard block; auditor Cgcre vê "aviso ignorado" como não-conformidade maior.

### 3. Centralizar tudo em workflow BPM externo (Temporal) — REJEITADA agora, considerada V2
**Atrativo:** workflow visual, escalável.
**Rejeitada porque:** ADR-0005 já decidiu Camada 2 (Django state machine + Celery) pro MVP-1; porta `BpmEngineProvider` permite migração futura sem reescrever domínio.

### 4. Snapshot apenas de campos críticos (não JSONB completo) — REJEITADA
**Atrativo:** menos storage.
**Rejeitada porque:** Cgcre pode questionar qualquer campo retroativamente; snapshot deve ser completo + hash do PDF da acreditação pra prova forense.

---

## Trade-offs explícitos

| Trade-off | Escolha | Razão |
|---|---|---|
| Bloqueio automático vs aprovação manual | Bloqueio automático com bypass via A3 | Auditoria Cgcre exige controle demonstrável |
| Snapshot completo (JSONB) vs campos selecionados | JSONB completo selado por trigger | Prova forense exige reproduzir o estado completo |
| Job diário vs real-time | Job diário pra padrões/ASO; real-time pra desligamento/revisão | Padrões vencem por data (latência 24h aceitável); desligamento é evento (deve ser imediato) |
| Hard block agenda vs warning | Hard block | NR-X é norma federal — não pode ser warning |
| BPM caseiro vs Temporal | Caseiro (Camada 2 ADR-0005) | Custos e simplicidade pro MVP-1; migração via porta protegida |

---

## Consequências

### Positivas
- **6 cenários regulatórios cobertos** com bloqueios automáticos demonstráveis em auditoria
- **R-039** (Roldão solidário) baixa de score 20 → ≤8
- **R-050** (acidente trabalhista) baixa de 30 → ≤10
- **Cadeia de rastreabilidade ISO 17025 8.4 reforçada** — qualquer NF-e de calibração rastreia até certificado
- **Snapshot retroativo** defende certificados antigos contra fiscalização Cgcre retroativa
- **ANTI-11 preservado** — bypass exige A3 + escalação ao dono Aferê

### Negativas
- **6 eventos novos no catálogo** — manutenção e versionamento; mitigado por ADR-0007 (outbox + versioning)
- **Consumers obrigatórios em 5 módulos** — risco de "esquecer 1" no MVP-1; mitigado por hook semgrep
- **Latência adicional de até 24h** no fluxo "padrão vence → bloqueio" (job diário); aceitável vs risco real
- **UI de bypass exige A3** — Roldão precisa de Web PKI Lacuna no desktop pra usar (já cravado na ADR-0009)
- **Snapshot JSONB cresce ~5-10KB por certificado** — em 1M certificados = ~10GB; barato

---

## Itens a fazer

### Bloqueantes antes de Foundation F-A começar
- [ ] Atualizar `docs/comum/integracoes-inter-modulos.md` → v9 com os 6 eventos novos + alterações em 5 existentes (Tarefa 2/12 desta sessão)
- [ ] Atualizar `REGRAS-INEGOCIAVEIS.md` com INV-INT-001..006 (Tarefa 3/12 desta sessão)
- [ ] Hook `bus-envelope-validator` (`.claude/hooks/`) — rejeita publish de evento com payload incompleto (ex: `Fiscal.NFSeEmitida` com `tipo_servico=calibracao AND certificado_id IS NULL`)
- [ ] Lint semgrep — `emitir_certificado()` deve invocar `AuthorizationProvider.can()` com `padroes_usados`; `agenda_alocar()` com `habilitacoes_exigidas`
- [ ] Tabelas: `padroes_disponibilidade`, `tecnico_habilitacoes`, `verificacao_intermediaria_padrao` (migrations + RLS)

### Bloqueantes antes de Wave A começar
- [ ] Workflow BPM "designação de RT substituto" em `automacoes-bpm`
- [ ] UI bypass modo emergencial (com A3 + escalação)
- [ ] Job Celery diário "varre padrões vencidos"
- [ ] Job Celery diário "varre ASOs vencidos" + dispara `SST.ASOVencido`
- [ ] Estado `pendente_revalidacao` na máquina de estados de OS (`operacao/os`)
- [ ] Snapshot JSONB selado por trigger PG em `certificados`

---

## Critérios de reversão

| Sinal | Resposta |
|---|---|
| Cgcre fiscalizar e ainda achar gap regulatório | Reabrir ADR + adicionar fluxo novo |
| Bypass modo emergencial > 3x/mês no mesmo tenant | Auditor de qualidade abre NC sistêmica; ADR-0005 catálogo recebe regra "se bypass repetir, bloqueia tipo de serviço inteiro" |
| Snapshot JSONB ultrapassar 50KB/certificado | Investigar; pode estar duplicando dados externos; otimizar |
| Latência do job diário virar problema (>48h) | Reduzir frequência pra horária ou trigger por evento (`Padroes.CertificadoVencendo` antecipa) |
| Hard block agenda causar mais de 5 reclamações/semana | Não relaxa — investiga se RH está renovando treinamentos no prazo; ANTI-11 manda |

---

## Aprovação

- [ ] **Roldão (decisor):** aceita 6 fluxos de transição regulatória
- [ ] **Auditor RBC/ISO 17025:** confirma que fluxos cobrem cláusulas 6.2, 6.5, 7.11, 8.4
- [ ] **Auditor de Segurança:** confirma que bypass exige A3 + escalação (ANTI-11 preservado)
- [ ] **Tech-lead substituto:** confirma viabilidade dos 4 jobs Celery + 3 tabelas novas + 5 consumers

---

## Referências

- ADR-0001 — Stack, ADR-0007 — domínio + outbox, ADR-0011 — BI, ADR-0012 — autorização, ADR-0008 — fiscal
- Auditoria de 10 agentes 17/05/2026 madrugada — Auditores C (metrologia/qualidade), E (RH/SST), F (supply chain), J (cross-domínio)
- `docs/comum/integracoes-inter-modulos.md` (v9 — atualizado nesta sessão)
- `REGRAS-INEGOCIAVEIS.md` — INV-001 (audit), INV-002 (cadeia), INV-003 (escopo signatário), INV-004b (revalidação método), INV-011 (padrão), INV-021 (classe), INV-022 (verificação intermediária), INV-032 (doc bloqueante), INV-033 (modo emergencial), **INV-INT-001..006 (criadas nesta ADR)**
- Normas: ISO 17025 cláusulas 6.2, 6.5, 7.11, 8.4; NIT-DICLA-030; NR-10/12/35; MP 2.200-2/2001
