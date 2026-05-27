---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
modulo: app-tecnico
dominio: operacao
diataxis: explanation
audiencia: agente
historico:
  - 2026-05-23 — versão inicial draft (operação dogfooding Wave A)
  - 2026-05-27 — Onda 3 saneamento BATCH B2 — frontmatter canônico (owner lowercase + hífen), perfil regulatório ADR-0067 declarado, AC-APP-003-3 endurecido (consentimento GPS server-side via `Colaborador.consente_gps_em` — nunca payload), persona inline, vocabulário Wave A/Wave B, status STABLE.
relacionados:
  - docs/prd.md
  - docs/dominios/operacao/README.md
  - docs/adr/0003-mobile-tecnico-campo.md
  - docs/adr/0004-sync-mobile-offline-first.md
  - docs/adr/0009-onde-a3-assina.md
  - docs/adr/0027-sync-mobile-merge-atividade.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/conformidade/comum/dpia-modulos-novos.md
  - docs/conformidade/comum/retencao-matriz.md
  - docs/dominios/operacao/modulos/os/prd.md
  - docs/dominios/operacao/modulos/agenda/prd.md
  - docs/dominios/financeiro/modulos/caixa-tecnico/prd.md
---

# PRD — Módulo App do Técnico

> Aplicativo mobile (Flutter — ADR-0003 + ADR-0004 offline-first + ADR-0027 sync por atividade) que consolida toda a operação de campo do técnico de campo (persona dominante: **P-OP-01 técnico de campo**) em um único ponto: agenda, OS, chamados, deslocamento, execução, peças, despesas e comunicação com a base.

---

## 1. O que este módulo é

Aplicativo mobile que é a "mesa de trabalho" do técnico de campo. Substitui papel, WhatsApp pessoal e ligações à base. Funciona **offline-first** (ADR-0004): técnico em obra sem sinal continua trabalhando; sincroniza quando sinal volta com merge por atividade LWW (ADR-0027). Consolida funcionalidades hoje espalhadas em OS, Agenda, Chamados, Estoque, Caixa do Técnico — o técnico não precisa abrir 5 telas, só este app.

## 2. Por que este módulo existe (problema a resolver)

Dor mapeada: técnicos perdem 20-40% do tempo útil em retrabalho de comunicação (anotação em papel + redigitação na base), perdem peças/despesas por falta de registro imediato, e clientes ficam sem retorno em tempo real do andamento. Sem app dedicado, a operação é refém de WhatsApp pessoal (compliance LGPD zero) e planilhas paralelas.

## 3. Personas

**Persona dominante:** P-OP-01 (técnico de campo). Detalhes em `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Perfil regulatório (ADR-0067)

Este módulo é **transversal a todos os perfis A/B/C/D** — todo tenant que tenha técnico de campo usa app. Mas algumas features têm gating por perfil (predicate canônico `tenant_perfil_e([...])` lê `Tenant.perfil_regulatorio` no banco, NUNCA do payload da request):

| Feature | A — Acreditado RBC | B — Rastreável | C — Em preparação D→A | D — Comercial puro |
|---|---|---|---|---|
| **App técnico básico** (US-APP-001..013) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |
| **GPS check-in** (US-APP-003) — server-side opt-in `Colaborador.consente_gps_em` | ⚪ OPCIONAL (opt-in por colaborador) | ⚪ OPCIONAL | ⚪ OPCIONAL | ⚪ OPCIONAL |
| **Aceite touch (US-APP-007)** | 🟡 OBRIGATÓRIO_PARCIAL (touch é aceite contratual; certificado de calibração assina A3 em PC — ADR-0009) | ⚪ OPCIONAL | ⚪ OPCIONAL | ⚪ OPCIONAL |
| **Sync mobile LWW por atividade** (ADR-0027) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |
| **Captura foto com GPS/EXIF preservado para evidência ISO 17025** (US-APP-006) | ✅ OBRIGATÓRIO (foto-anônima preservada 25a) | 🟢 OPCIONAL_RECOMENDADO | 🟢 OPCIONAL_RECOMENDADO | ⚪ OPCIONAL (foto 5a + anonimização agressiva) |

Atualização da matriz canônica deste módulo deve ser feita em `docs/conformidade/comum/matriz-feature-perfil.md` antes do merge — hook `feature-perfil-matriz-validator.sh` valida.

## 5. Escopo (o que ESTÁ neste módulo)

- Agenda do dia do técnico (visão lista + mapa)
- Lista de OS atribuídas + lista de chamados atribuídos
- Detalhes do cliente e do equipamento (cache offline)
- Navegação até o cliente (integração com Google Maps / Waze / Apple Maps)
- Check-in com GPS (timestamp + coordenadas + foto opcional) — gated por consentimento server-side
- Ciclo de deslocamento: início → pausa → retomada → chegada
- Ciclo de serviço: início → execução → conclusão
- Registro de serviços executados (cardápio do contrato + livre)
- Consumo de peças (baixa de estoque do veículo/maleta)
- Solicitação de peças à base (com prazo solicitado)
- Transferência de estoque entre técnicos (origem solicita, destino aceita)
- Aceite de transferência recebida
- Captura de fotos (antes/durante/depois — categorizadas)
- Upload de anexos (PDF, áudio, vídeo curto)
- Execução de checklist (definido por tipo de serviço)
- Coleta de assinatura touch de aceite do cliente
- Lançamento de despesas (combustível, pedágio, alimentação, hospedagem)
- Pedido de adiantamento de viagem
- Prestação de contas pós-viagem
- Chat interno com equipe (base, outros técnicos, coordenador) via `OmniChannelProvider`
- Notificações push (nova OS, alteração de agenda, mensagem de chat)
- Funcionamento 100% offline para todas operações de execução
- Sincronização automática quando sinal retorna — LWW por atividade (ADR-0027)
- Resolução de conflitos de sincronização (merge guiado por regras + escalonamento ao coordenador)

## 6. Não-objetivos (o que NÃO está neste módulo)

- **Assinatura A3 do CERTIFICADO de calibração** não acontece no app — ela é cliente-side via Web PKI Lacuna no PC do metrologista (ADR-0009). Assinatura coletada no app é só de aceite de serviço/OS (não tem valor regulatório ISO 17025).
- App **não emite NF-e nem certificado de calibração** — só captura dados; emissão fiscal e certificado ficam em módulos próprios.
- App **não faz cálculo metrológico** (incerteza, ajustes) — captura medições; cálculo fica em módulo Calibração no servidor.
- App **não substitui ERP web** — não tem dashboards, relatórios gerenciais, cadastros completos.
- App **não roda em desktop/web** — escopo é mobile Android + iOS (Flutter).
- App **não ativa face match biométrico** — fotos são evidência fotográfica apenas (ADR futura exigida pra ativar matching biométrico).

## 7. User Stories

### US-APP-001: Ver agenda do dia ao abrir o app

**Como** técnico de campo (P-OP-01), **quero** ver minha agenda do dia ao abrir o app, **para** saber meus compromissos sem ligar pra base.

- **AC-APP-001-1**: GIVEN técnico autenticado, WHEN abre o app, THEN tela inicial mostra agenda do dia ordenada por horário com endereço e tipo (OS/chamado/visita técnica).
- **AC-APP-001-2**: GIVEN técnico sem sinal, WHEN abre o app, THEN agenda do último sync é exibida com badge "offline desde HH:MM".

**Não-objetivos desta story:** não inclui agenda de outros técnicos.

**Invariantes:** `INV-TENANT-001` (tenant na query), `INV-AGENT-001` (input não-confiável tipado — anti prompt injection ao processar texto livre de campo).

**Dependências:** ADR-0001 stack, ADR-0003 mobile, ADR-0004 sync, US-AG-001 (módulo Agenda).

---

### US-APP-002: Iniciar deslocamento até o cliente

**Como** técnico (P-OP-01), **quero** registrar início de deslocamento com 1 toque, **para** que a base saiba que estou indo e o tempo conte pra apropriação de custos.

- **AC-APP-002-1**: GIVEN OS aberta no app, WHEN toca "Iniciar deslocamento", THEN registra timestamp + GPS origem (se consentimento ativo) + abre navegação no app de mapa preferido.
- **AC-APP-002-2**: GIVEN deslocamento em andamento, WHEN técnico pausa (ex: parada pra abastecer), THEN registra pausa e tempo pausado não conta no custo.

**Invariantes:** `INV-TENANT-001`.

**Dependências:** US-APP-001.

---

### US-APP-003: Check-in com GPS na chegada ao cliente

**Como** técnico (P-OP-01), **quero** registrar chegada com GPS, **para** comprovar presença ao cliente e iniciar contagem de hora trabalhada.

- **AC-APP-003-1**: GIVEN deslocamento em andamento + `Colaborador.consente_gps_em IS NOT NULL` (consentimento server-side ativo), WHEN técnico toca "Cheguei", THEN registra timestamp + GPS + diferença vs endereço do cliente (alerta se >500m).
- **AC-APP-003-2**: GIVEN GPS indisponível ou consentimento ausente, WHEN check-in tentado com modo GPS, THEN permite check-in manual com justificativa obrigatória.
- **AC-APP-003-3 (consentimento GPS — bloqueio server-side; fecha L6 da auditoria 10 lentes):** GIVEN `Colaborador.consente_gps_em IS NULL` (consentimento nunca registrado ou revogado), WHEN técnico habilita coleta GPS contínua, THEN servidor bloqueia com `403 GPS_CONSENTIMENTO_AUSENTE` + payload `{colaborador_id_hash, base_legal_obrigatoria: "art.7º V + IX LGPD"}` + cliente Flutter cai em modo sem-GPS (não envia coordenadas até consentimento renovado). Consentimento NUNCA é lido do payload da request — somente da coluna `Colaborador.consente_gps_em` (NOT NULL com `revogado_em`).
- **AC-APP-003-4 (LGPD base legal)**: Coleta de GPS atende base **Execução de contrato (art. 7º V) + Legítimo interesse (art. 7º IX)** com opt-in documentado em política de admissão (RAT-13 + DPIA-02). GPS só ativo durante "OS em execução" — desligado quando app fechado.
- **AC-APP-003-5 (Retenção)**: GPS/trilha conforme `retencao-matriz.md` linha "Trilha GPS contínua do técnico" (5 anos); após prazo: crypto-shredding. Técnico vê e exporta próprio histórico via "Meus dados (LGPD)" (US-ACS-012).
- **AC-APP-003-6 (Revogação)**: GIVEN técnico revoga consentimento (perfil → "revogar GPS"), WHEN servidor recebe pedido, THEN seta `Colaborador.consente_gps_em.revogado_em=now()` + cliente Flutter recebe pelo próximo sync e para coleta GPS no próximo evento; histórico passado permanece (purgado por job 5a).

**Invariantes:** `INV-LGPD-CONSENT-001` (consentimento server-side imutável append-only), `INV-TENANT-001`.

**Dependências:** US-APP-002, módulo `colaboradores` (Wave A) para tabela `Colaborador.consente_gps_em`.

---

### US-APP-004: Registrar serviços executados e peças consumidas

**Como** técnico (P-OP-01), **quero** marcar serviços feitos e peças usadas durante o atendimento, **para** que a OS seja faturada correta e o estoque do meu veículo seja baixado automaticamente.

- **AC-APP-004-1**: GIVEN OS em execução, WHEN técnico marca serviço executado, THEN registra hora início/fim e quem executou.
- **AC-APP-004-2**: GIVEN técnico adiciona peça consumida, WHEN confirma, THEN baixa do estoque do veículo (saldo local atualizado) e marca pra ressuprimento.
- **AC-APP-004-3**: GIVEN saldo do veículo zerado pra peça X, WHEN técnico tenta consumir, THEN bloqueia e oferece "Solicitar peça à base" (US-APP-005).

**Dependências:** US-EST-NNN (módulo Estoque).

---

### US-APP-005: Solicitar peça à base

**Como** técnico (P-OP-01), **quero** solicitar peça que não tenho no veículo, **para** receber sem voltar à base.

- **AC-APP-005-1**: GIVEN técnico precisa de peça, WHEN solicita, THEN registra peça + prazo desejado + OS vinculada + base recebe notificação push.
- **AC-APP-005-2**: GIVEN base aceita transferência de outro técnico, WHEN técnico destino aceita no app, THEN estoque é transferido entre veículos.

**Dependências:** US-APP-004.

---

### US-APP-006: Capturar fotos e checklist do serviço

**Como** técnico (P-OP-01), **quero** anexar fotos e marcar checklist, **para** documentar serviço e gerar evidência pro cliente e pra qualidade.

- **AC-APP-006-1**: GIVEN OS em execução, WHEN técnico tira foto, THEN categoriza (antes/durante/depois/avaria) e foto é vinculada à OS com timestamp + GPS embarcados (GPS só se `Colaborador.consente_gps_em` ativo — herda AC-APP-003-3).
- **AC-APP-006-2**: GIVEN checklist definido pro tipo de serviço, WHEN técnico marca itens, THEN se item obrigatório não marcado, bloqueia conclusão da OS.
- **AC-APP-006-3 (LGPD biometria implícita):** GIVEN captura de face em foto, WHEN upload ocorre, THEN NÃO ativa matching biométrico — apenas evidência fotográfica (RAT-13 + DPIA-02); introdução futura de face match exige novo RIPD + ADR (hook `block-biometric-feature.sh` a criar).
- **AC-APP-006-4 (Retenção + EXIF + perfil — fecha L6 evidência ISO 17025):** GIVEN tenant em perfil A/B/C, WHEN foto vinculada a atividade `tipo=calibracao`, THEN foto anônima (EXIF removido pra exibição pública) preservada **25 anos** (ISO 17025 cl. 8.4); GIVEN tenant em perfil D OU foto não vinculada a calibração, THEN retenção **5 anos** (`retencao-matriz.md`) + anonimização (face borrada + EXIF removido). Predicate de retenção: `tenant_perfil_e(['A','B','C'])` ler `Tenant.perfil_regulatorio`.
- **AC-APP-006-5 (UI)**: GIVEN técnico abre captura, WHEN tela renderiza, THEN exibe texto "não fotografe terceiros sem autorização" + categorização obrigatória antes do disparo.

**Invariantes:** `INV-001` (foto imutável após upload — trilha WORM com hash + EXIF preservado), `INV-AGENT-001` (categoria de foto = enum tipado).

---

### US-APP-007: Coletar assinatura de aceite do cliente

**Como** técnico (P-OP-01), **quero** que o cliente assine na tela do celular aceitando o serviço, **para** ter prova de conclusão sem papel.

- **AC-APP-007-1**: GIVEN serviço concluído, WHEN técnico solicita assinatura, THEN cliente assina em campo touch + nome + CPF + foto opcional.
- **AC-APP-007-2**: GIVEN assinatura coletada, WHEN OS é fechada, THEN PDF de aceite é gerado offline (assinatura embutida) e fica na fila de sync.
- **AC-APP-007-3 (LGPD)**: Tela de aceite atende base **Execução de contrato (art. 7º V)** — prova de aceite contratual (RAT-13). UI mostra resumo serviço + valor + termos em fonte legível + checkbox "li e concordo" antes do touch (DPIA-02 R4); cliente recebe cópia PDF.
- **AC-APP-007-4 (Retenção)**: Assinatura touch + CPF conforme `retencao-matriz.md` linha "Assinatura touch de aceite + CPF" (5 anos); após prazo: anonimização CPF (hash) + traçado preservado 25 anos se compõe evidência ISO 17025.
- **AC-APP-007-5 (perfil A — emenda ADR-0009)**: GIVEN tenant em perfil A + atividade `tipo=calibracao`, WHEN assinatura touch coletada, THEN touch vale **apenas como aceite do serviço** — NÃO substitui A3 ICP-Brasil obrigatória do certificado de calibração (executada em PC via Web PKI Lacuna — ADR-0009). Servidor bloqueia emissão de certificado perfil A com `412 PERFIL_A_EXIGE_A3_PC` se houver tentativa de assinar certificado só com touch.

**Não-objetivos:** essa assinatura NÃO é A3 ICP-Brasil — só aceite contratual.

---

### US-APP-008: Lançar despesa de viagem

**Como** técnico (P-OP-01), **quero** lançar despesa (combustível, alimentação) no momento que acontece, **para** não esquecer e não acumular comprovante físico.

- **AC-APP-008-1**: GIVEN técnico em viagem, WHEN lança despesa, THEN captura categoria + valor + foto do comprovante + vincula a viagem/OS.
- **AC-APP-008-2**: GIVEN despesa lançada, WHEN sync ocorre, THEN aparece no módulo Caixa do Técnico pra prestação de contas (IDEMP-001 via `client_offline_id` UUID4 — ADR-0033).

**Dependências:** módulo Caixa do Técnico (financeiro).

---

### US-APP-009: Pedir adiantamento e prestar contas

**Como** técnico em viagem longa (P-OP-01), **quero** pedir adiantamento e depois prestar contas no app, **para** não usar dinheiro pessoal.

- **AC-APP-009-1**: GIVEN técnico precisa de adiantamento, WHEN solicita, THEN registra valor + justificativa + OS/viagem; coordenador aprova/recusa via web.
- **AC-APP-009-2**: GIVEN viagem encerrada, WHEN técnico inicia prestação de contas, THEN app lista todas despesas + adiantamentos vinculados + calcula saldo a receber/devolver.

**Dependências:** US-APP-008.

---

### US-APP-010: Conversar com a equipe interna

**Como** técnico (P-OP-01), **quero** chat interno com coordenador e outros técnicos, **para** tirar dúvida sem usar WhatsApp pessoal.

- **AC-APP-010-1**: GIVEN técnico em campo, WHEN abre chat, THEN vê threads ativos (1:1, grupo de equipe, dúvida técnica por OS).
- **AC-APP-010-2**: GIVEN mensagem recebida com app fechado, WHEN chega ao dispositivo, THEN notificação push é exibida.
- **AC-APP-010-3 (anti prompt injection)**: GIVEN mensagem com payload contendo conteúdo livre, WHEN servidor processa pra triagem/automação, THEN texto é tipado como `TextoLivreNaoConfiavel` antes de qualquer consumo por LLM (INV-AGENT-001).

**Não-objetivos:** chat não substitui ticket de suporte; mensagens não viram OS automaticamente.

---

### US-APP-011: Trabalhar 100% offline

**Como** técnico em local sem sinal (P-OP-01), **quero** todas operações funcionarem offline, **para** não parar por causa de cobertura ruim.

- **AC-APP-011-1**: GIVEN técnico sem sinal, WHEN executa qualquer operação de campo (US-APP-002 a US-APP-009), THEN operação é registrada localmente e marcada como pendente de sync.
- **AC-APP-011-2**: GIVEN técnico sem sinal há ≥7 dias, WHEN abre app, THEN exibe alerta "dados locais antigos — sincronize quando possível".

**Dependências:** ADR-0004 (sync offline-first).

---

### US-APP-012: Sincronizar dados quando sinal retorna

**Como** sistema, **quero** sincronizar automaticamente quando detectar conectividade, **para** garantir consistência sem ação do técnico.

- **AC-APP-012-1**: GIVEN dispositivo offline com fila de sync, WHEN conectividade retorna (Wi-Fi ou 4G), THEN sync inicia em background com progresso visível.
- **AC-APP-012-2**: GIVEN sync em andamento, WHEN técnico fecha o app, THEN sync continua em background até concluir.
- **AC-APP-012-3 (LWW por atividade — ADR-0027)**: GIVEN duas edições offline da MESMA atividade da OS, WHEN sync resolve conflito, THEN aplica LWW (Last-Write-Wins) por `atividade_id` baseado em `client_event_ts` + tie-break por `device_id` ordenado; cliente vencido é notificado.

**Dependências:** ADR-0004, ADR-0027.

---

### US-APP-014: Login com biometria + PIN fallback + sessão offline 7 dias (A-APP-001)

**Como** sistema, **quero** exigir biometria (face/digital) com PIN de 6 dígitos como fallback e expirar a sessão local após 7 dias sem sync, **para** mitigar furto e abandono.

- **AC-APP-014-1**: GIVEN dispositivo com biometria disponível, WHEN técnico abre o app, THEN biometria é exigida; falha cai em PIN.
- **AC-APP-014-2**: GIVEN 7 dias sem sync com servidor, WHEN técnico abre o app, THEN é forçada re-autenticação completa contra o servidor (online).
- **AC-APP-014-3**: GIVEN servidor recebe comando `RemoteWipe`, WHEN próximo poll do app ocorre, THEN dados locais são limpos + sessão encerrada.

**Invariantes:** `INV-APP-SESS-001`.

---

### US-APP-015: Sync parcial — só OS atribuídas + 6 meses (A-APP-002)

**Como** sistema, **quero** baixar apenas OS atribuídas ao técnico + últimos 6 meses de histórico do cliente alvo, com quota local de 2GB + LRU eviction, **para** respeitar minimização LGPD + storage do dispositivo.

- **AC-APP-015-1**: GIVEN técnico autenticado, WHEN sync inicial roda, THEN servidor envia apenas OS onde `tecnico_id=current_user` + dados do cliente correspondente nos últimos 6 meses.
- **AC-APP-015-2**: GIVEN armazenamento local alcança 2GB, WHEN nova OS chega, THEN LRU eviction remove itens mais antigos não-pendentes (pendentes nunca são removidos).

**Invariantes:** `INV-APP-SYNC-001`.

---

### US-APP-016: Mídia local + retenção 30d pós-sync (A-APP-003)

**Como** sistema, **quero** armazenar mídia (fotos/vídeos) em filesystem local com metadata em `OperacaoSyncPendente.payload_json` e expirar local 30d após sync OK, **para** evitar JSONB inchado e respeitar storage local.

- **AC-APP-016-1**: GIVEN técnico tira foto, WHEN salva, THEN arquivo vai em filesystem local + entry em `OperacaoSyncPendente` referencia o arquivo.
- **AC-APP-016-2**: GIVEN sync OK confirmado pelo servidor, WHEN 30d passam, THEN arquivo local é removido (mídia preservada no servidor).

---

### US-APP-017: Back-off exponencial + dead-letter (M-APP-001)

**Como** sistema, **quero** retentar sync com back-off exponencial base 2, máximo 10 tentativas, e mover pra dead-letter na 11ª, **para** evitar tempestade de retry + permitir investigação manual de falhas.

- **AC-APP-017-1**: GIVEN sync falha, WHEN próxima tentativa, THEN intervalo é `2^n * base_segundos` (n=tentativa atual).
- **AC-APP-017-2**: GIVEN 10 tentativas falharam, WHEN próxima tentativa ocorre, THEN operação vai pra `OperacaoSyncPendente.status='dead_letter'` e alerta o coordenador.

---

### US-APP-018: Chat interno via OmniChannelProvider (M-APP-002)

**Como** técnico (P-OP-01), **quero** chat interno com a equipe usando o transporte da plataforma (`OmniChannelProvider`), **para** unificar configuração; cliente externo NÃO entra neste canal.

- **AC-APP-018-1**: GIVEN técnico abre chat, WHEN envia mensagem interna, THEN consome `OmniChannelProvider` (mesma porta WhatsApp/Email/SMS).
- **AC-APP-018-2**: GIVEN cliente externo, WHEN aparece em busca, THEN nunca aparece como contato; thread de cliente vai por `comunicacao-omnichannel` separado.

---

### US-APP-013: Resolver conflitos de sincronização

**Como** sistema, **quero** detectar conflito (ex: OS alterada na base e no app offline simultaneamente) e resolver via regra ou escalonamento, **para** não perder dado e não duplicar.

- **AC-APP-013-1**: GIVEN conflito detectado (mesmo campo alterado em base e app), WHEN regra de merge se aplica (ex: "campo data sempre vence o mais recente"), THEN resolve automático e loga decisão.
- **AC-APP-013-2**: GIVEN conflito sem regra clara, WHEN sync tenta resolver, THEN escalona ao coordenador com diff visual + bloqueio temporário da OS.
- **AC-APP-013-3 (ADR-0027 LWW)**: GIVEN conflito por atividade da OS, WHEN merge resolve, THEN aplica LWW por `atividade_id` (não por OS inteira — preserva paralelismo).

**Dependências:** ADR-0004, ADR-0027, US-APP-012.

---

## 8. Métricas de sucesso deste módulo

Ver `metricas.md`. Primárias (mínimo 2-3):
- % de OS executadas sem retorno à base = ≥85%
- Tempo médio entre chegada ao cliente e início do serviço = ≤10min
- Taxa de sync sem conflito = ≥98%

## 9. NFR (Requisitos Não-Funcionais)

- **Performance:** abertura do app ≤3s, captura de foto ≤2s, sync incremental ≤30s por dia de operação.
- **Disponibilidade:** app funciona offline indefinidamente; sync depende de servidor (SLO ver `../../../operacao/observabilidade.md`).
- **Segurança:** SEC-NNN (pin de PIN/biometria no app, sessão expirada após 7 dias offline, wipe remoto em caso de furto).
- **Acessibilidade:** WCAG 2.1 AA aplicado ao mobile. Suporte a screen reader (TalkBack/VoiceOver).
- **Bateria:** background sync usa <5%/h.

## 10. Dependências (ADRs)

- ADR-0001 (stack), ADR-0003 (Flutter mobile), ADR-0004 (sync offline-first), ADR-0009 (A3 cliente-side em PC), ADR-0027 (sync mobile LWW por atividade), ADR-0033 (bus idempotência consumer), ADR-0034 (saga compensação cross-módulo), ADR-0037 (glossário PT-EN), ADR-0067 (perfil regulatório do tenant), ADR-0023 (OS com atividades — App consome atividade).

## 11. Glossário

Ver `glossario.md` deste módulo + `docs/comum/glossario.md` (compartilhado) + ADR-0037 (canônico PT-EN).

## 12. Como este PRD evolui

- US nova → adicionar com próximo ID livre (`US-APP-NNN`).
- US deprecada → marcar `@deprecated` + ADR.
- Mudança em AC já implementado → ADR + novo teste.
- Toda feature nova com gating por perfil → atualizar `docs/conformidade/comum/matriz-feature-perfil.md` antes do merge.
