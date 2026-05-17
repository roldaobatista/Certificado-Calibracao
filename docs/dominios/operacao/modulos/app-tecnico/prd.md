---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/operacao/README.md
  - docs/adr/0003-mobile-tecnico-campo.md
  - docs/adr/0004-sync-offline-first.md
  - docs/adr/0009-a3-cliente-side.md
  - docs/dominios/operacao/modulos/os/prd.md
  - docs/dominios/operacao/modulos/agenda/prd.md
  - docs/dominios/financeiro/modulos/caixa-tecnico/prd.md
  - docs/conformidade/comum/lgpd-rat.md#RAT-13
  - docs/conformidade/comum/dpia-modulos-novos.md#DPIA-02
  - docs/conformidade/comum/retencao-matriz.md
---

# PRD — Módulo App do Técnico

> Aplicativo mobile (Flutter — ADR-0003) que consolida toda a operação de campo do técnico em um único ponto: agenda, OS, chamados, deslocamento, execução, peças, despesas e comunicação com a base.

---

## 1. O que este módulo é

Aplicativo mobile que é a "mesa de trabalho" do técnico de campo. Substitui papel, WhatsApp pessoal e ligações à base. Funciona **offline-first** (ADR-0004): técnico em obra sem sinal continua trabalhando; sincroniza quando sinal volta. Consolida funcionalidades hoje espalhadas em OS, Agenda, Chamados, Estoque, Caixa do Técnico — o técnico não precisa abrir 5 telas, só este app.

## 2. Por que este módulo existe (problema a resolver)

Dor mapeada: técnicos perdem 20-40% do tempo útil em retrabalho de comunicação (anotação em papel + redigitação na base), perdem peças/despesas por falta de registro imediato, e clientes ficam sem retorno em tempo real do andamento. Sem app dedicado, a operação é refém de WhatsApp pessoal (compliance LGPD zero) e planilhas paralelas.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Agenda do dia do técnico (visão lista + mapa)
- Lista de OS atribuídas + lista de chamados atribuídos
- Detalhes do cliente e do equipamento (cache offline)
- Navegação até o cliente (integração com Google Maps / Waze / Apple Maps)
- Check-in com GPS (timestamp + coordenadas + foto opcional)
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
- Coleta de assinatura do cliente na tela (não-A3 — ver non-goal 1)
- Lançamento de despesas (combustível, pedágio, alimentação, hospedagem)
- Pedido de adiantamento de viagem
- Prestação de contas pós-viagem
- Chat interno com equipe (base, outros técnicos, coordenador)
- Notificações push (nova OS, alteração de agenda, mensagem de chat)
- Funcionamento 100% offline para todas operações de execução
- Sincronização automática quando sinal retorna
- Resolução de conflitos de sincronização (merge guiado por regras + escalonamento ao coordenador)

## 5. Non-goals (o que NÃO está neste módulo)

- **Assinatura A3 do CERTIFICADO de calibração** não acontece no app — ela é cliente-side via Web PKI Lacuna no PC do metrologista (ADR-0009). Assinatura coletada no app é só de aceite de serviço/OS (não tem valor regulatório ISO 17025).
- App **não emite NF-e nem certificado de calibração** — só captura dados; emissão fiscal e certificado ficam em módulos próprios.
- App **não faz cálculo metrológico** (incerteza, ajustes) — captura medições; cálculo fica em módulo Calibração no servidor.
- App **não substitui ERP web** — não tem dashboards, relatórios gerenciais, cadastros completos.
- App **não roda em desktop/web** — escopo é mobile Android + iOS (Flutter).

## 6. User Stories

### US-APP-001: Ver agenda do dia ao abrir o app

**Como** técnico de campo, **quero** ver minha agenda do dia ao abrir o app, **para** saber meus compromissos sem ligar pra base.

**Critérios de aceite (Given-When-Then):**
- **AC-APP-001-1**: GIVEN técnico autenticado, WHEN abre o app, THEN tela inicial mostra agenda do dia ordenada por horário com endereço e tipo (OS/chamado/visita técnica).
- **AC-APP-001-2**: GIVEN técnico sem sinal, WHEN abre o app, THEN agenda do último sync é exibida com badge "offline desde HH:MM".

**Non-goals desta story:** não inclui agenda de outros técnicos.

**Invariantes relacionadas:** `INV-TENANT-001` (tenant na query), `INV-AGENT-001` (input não-confiável tipado — anti prompt injection ao processar texto livre de campo).

**Dependências:**
- Bloqueado por: ADR-0001 stack, ADR-0003 mobile, ADR-0004 sync, US-AGE-001 (módulo Agenda)

---

### US-APP-002: Iniciar deslocamento até o cliente

**Como** técnico, **quero** registrar início de deslocamento com 1 toque, **para** que a base saiba que estou indo e o tempo conte pra apropriação de custos.

**Critérios de aceite:**
- **AC-APP-002-1**: GIVEN OS aberta no app, WHEN toca "Iniciar deslocamento", THEN registra timestamp + GPS origem + abre navegação no app de mapa preferido.
- **AC-APP-002-2**: GIVEN deslocamento em andamento, WHEN técnico pausa (ex: parada pra abastecer), THEN registra pausa e tempo pausado não conta no custo.

**Invariantes:** `INV-TENANT-001`.

**Dependências:** US-APP-001.

---

### US-APP-003: Check-in com GPS na chegada ao cliente

**Como** técnico, **quero** registrar chegada com GPS, **para** comprovar presença ao cliente e iniciar contagem de hora trabalhada.

**Critérios de aceite:**
- **AC-APP-003-1**: GIVEN deslocamento em andamento, WHEN técnico toca "Cheguei", THEN registra timestamp + GPS + diferença vs endereço do cliente (alerta se >500m).
- **AC-APP-003-2**: GIVEN GPS indisponível, WHEN check-in tentado, THEN permite check-in manual com justificativa obrigatória.
- **AC-APP-003-3 (LGPD):** Coleta de GPS atende base **Execução de contrato (art. 7º V) + Legítimo interesse (art. 7º IX)** com opt-in documentado em política de admissão (RAT-13 + DPIA-02). GPS só ativo durante "OS em execução" — desligado quando app fechado.
- **AC-APP-003-4 (Retenção):** GPS/trilha conforme `retencao-matriz.md` linha "Trilha GPS contínua do técnico" (5 anos); após prazo: crypto-shredding. Técnico vê e exporta próprio histórico via "Meus dados (LGPD)" (US-ACS-012).

**Dependências:** US-APP-002.

---

### US-APP-004: Registrar serviços executados e peças consumidas

**Como** técnico, **quero** marcar serviços feitos e peças usadas durante o atendimento, **para** que a OS seja faturada correta e o estoque do meu veículo seja baixado automaticamente.

**Critérios de aceite:**
- **AC-APP-004-1**: GIVEN OS em execução, WHEN técnico marca serviço executado, THEN registra hora início/fim e quem executou.
- **AC-APP-004-2**: GIVEN técnico adiciona peça consumida, WHEN confirma, THEN baixa do estoque do veículo (saldo local atualizado) e marca pra ressuprimento.
- **AC-APP-004-3**: GIVEN saldo do veículo zerado pra peça X, WHEN técnico tenta consumir, THEN bloqueia e oferece "Solicitar peça à base" (US-APP-005).

**Dependências:** US-EST-NNN (módulo Estoque).

---

### US-APP-005: Solicitar peça à base

**Como** técnico, **quero** solicitar peça que não tenho no veículo, **para** receber sem voltar à base.

**Critérios de aceite:**
- **AC-APP-005-1**: GIVEN técnico precisa de peça, WHEN solicita, THEN registra peça + prazo desejado + OS vinculada + base recebe notificação push.
- **AC-APP-005-2**: GIVEN base aceita transferência de outro técnico, WHEN técnico destino aceita no app, THEN estoque é transferido entre veículos.

**Dependências:** US-APP-004.

---

### US-APP-006: Capturar fotos e checklist do serviço

**Como** técnico, **quero** anexar fotos e marcar checklist, **para** documentar serviço e gerar evidência pro cliente e pra qualidade.

**Critérios de aceite:**
- **AC-APP-006-1**: GIVEN OS em execução, WHEN técnico tira foto, THEN categoriza (antes/durante/depois/avaria) e foto é vinculada à OS com timestamp + GPS embarcados.
- **AC-APP-006-2**: GIVEN checklist definido pro tipo de serviço, WHEN técnico marca itens, THEN se item obrigatório não marcado, bloqueia conclusão da OS.
- **AC-APP-006-3 (LGPD biometria implícita):** Captura de face em foto NÃO ativa matching biométrico — apenas evidência fotográfica (RAT-13 + DPIA-02). Introdução futura de face match exige novo RIPD aprovado + ADR (hook `block-biometric-feature.sh` a criar). UI obriga categorização + texto "não fotografe terceiros sem autorização".
- **AC-APP-006-4 (Retenção + EXIF):** Foto conforme `retencao-matriz.md` linha "Foto com GPS/EXIF do App Técnico" (5 anos); após prazo: anonimização (face borrada + EXIF removido); foto-anônima preservada 25 anos se compõe evidência ISO 17025. EXIF removido antes de exposição via Portal do Cliente / e-mail / WhatsApp (DPIA-02 R3).

**Invariantes:** `INV-001` (foto imutável após upload — trilha WORM com hash + EXIF preservado).

---

### US-APP-007: Coletar assinatura de aceite do cliente

**Como** técnico, **quero** que o cliente assine na tela do celular aceitando o serviço, **para** ter prova de conclusão sem papel.

**Critérios de aceite:**
- **AC-APP-007-1**: GIVEN serviço concluído, WHEN técnico solicita assinatura, THEN cliente assina em campo touch + nome + CPF + foto opcional.
- **AC-APP-007-2**: GIVEN assinatura coletada, WHEN OS é fechada, THEN PDF de aceite é gerado offline (assinatura embutida) e fica na fila de sync.
- **AC-APP-007-3 (LGPD)**: Tela de aceite atende base **Execução de contrato (art. 7º V)** — prova de aceite contratual (RAT-13). UI mostra resumo serviço + valor + termos em fonte legível + checkbox "li e concordo" antes do touch (DPIA-02 R4); cliente recebe cópia PDF.
- **AC-APP-007-4 (Retenção)**: Assinatura touch + CPF conforme `retencao-matriz.md` linha "Assinatura touch de aceite + CPF" (5 anos); após prazo: anonimização CPF (hash) + traçado preservado 25 anos se compõe evidência ISO 17025.

**Non-goals:** essa assinatura NÃO é A3 ICP-Brasil — só aceite contratual. Certificado de calibração assina via ADR-0009 (Web PKI Lacuna no PC).

---

### US-APP-008: Lançar despesa de viagem

**Como** técnico, **quero** lançar despesa (combustível, alimentação) no momento que acontece, **para** não esquecer e não acumular comprovante físico.

**Critérios de aceite:**
- **AC-APP-008-1**: GIVEN técnico em viagem, WHEN lança despesa, THEN captura categoria + valor + foto do comprovante + vincula a viagem/OS.
- **AC-APP-008-2**: GIVEN despesa lançada, WHEN sync ocorre, THEN aparece no módulo Caixa do Técnico pra prestação de contas.

**Dependências:** módulo Caixa do Técnico (financeiro).

---

### US-APP-009: Pedir adiantamento e prestar contas

**Como** técnico em viagem longa, **quero** pedir adiantamento e depois prestar contas no app, **para** não usar dinheiro pessoal.

**Critérios de aceite:**
- **AC-APP-009-1**: GIVEN técnico precisa de adiantamento, WHEN solicita, THEN registra valor + justificativa + OS/viagem; coordenador aprova/recusa via web.
- **AC-APP-009-2**: GIVEN viagem encerrada, WHEN técnico inicia prestação de contas, THEN app lista todas despesas + adiantamentos vinculados + calcula saldo a receber/devolver.

**Dependências:** US-APP-008.

---

### US-APP-010: Conversar com a equipe interna

**Como** técnico, **quero** chat interno com coordenador e outros técnicos, **para** tirar dúvida sem usar WhatsApp pessoal.

**Critérios de aceite:**
- **AC-APP-010-1**: GIVEN técnico em campo, WHEN abre chat, THEN vê threads ativos (1:1, grupo de equipe, dúvida técnica por OS).
- **AC-APP-010-2**: GIVEN mensagem recebida com app fechado, WHEN chega ao dispositivo, THEN notificação push é exibida.

**Non-goals:** chat não substitui ticket de suporte; mensagens não viram OS automaticamente.

---

### US-APP-011: Trabalhar 100% offline

**Como** técnico em local sem sinal, **quero** todas operações funcionarem offline, **para** não parar por causa de cobertura ruim.

**Critérios de aceite:**
- **AC-APP-011-1**: GIVEN técnico sem sinal, WHEN executa qualquer operação de campo (US-APP-002 a US-APP-009), THEN operação é registrada localmente e marcada como pendente de sync.
- **AC-APP-011-2**: GIVEN técnico sem sinal há ≥7 dias, WHEN abre app, THEN exibe alerta "dados locais antigos — sincronize quando possível".

**Dependências:** ADR-0004 (sync offline-first).

---

### US-APP-012: Sincronizar dados quando sinal retorna

**Como** sistema, **quero** sincronizar automaticamente quando detectar conectividade, **para** garantir consistência sem ação do técnico.

**Critérios de aceite:**
- **AC-APP-012-1**: GIVEN dispositivo offline com fila de sync, WHEN conectividade retorna (Wi-Fi ou 4G), THEN sync inicia em background com progresso visível.
- **AC-APP-012-2**: GIVEN sync em andamento, WHEN técnico fecha o app, THEN sync continua em background até concluir.

**Dependências:** ADR-0004.

---

### US-APP-013: Resolver conflitos de sincronização

**Como** sistema, **quero** detectar conflito (ex: OS alterada na base e no app offline simultaneamente) e resolver via regra ou escalonamento, **para** não perder dado e não duplicar.

**Critérios de aceite:**
- **AC-APP-013-1**: GIVEN conflito detectado (mesmo campo alterado em base e app), WHEN regra de merge se aplica (ex: "campo data sempre vence o mais recente"), THEN resolve automático e loga decisão.
- **AC-APP-013-2**: GIVEN conflito sem regra clara, WHEN sync tenta resolver, THEN escalona ao coordenador com diff visual + bloqueio temporário da OS.

**Dependências:** ADR-0004, US-APP-012.

---

## 7. Métricas de sucesso deste módulo

Ver `metricas.md`. Resumo:
- % de OS executadas sem retorno à base = ≥85%
- Tempo médio entre chegada ao cliente e início do serviço = ≤10min
- Taxa de sync sem conflito = ≥98%

## 8. NFR (Requisitos Não-Funcionais)

- **Performance:** abertura do app ≤3s, captura de foto ≤2s, sync incremental ≤30s por dia de operação.
- **Disponibilidade:** app funciona offline indefinidamente; sync depende de servidor (SLO ver `../../../operacao/observabilidade.md`).
- **Segurança:** SEC-NNN (a definir — pin de PIN/biometria no app, sessão expirada após X dias offline, wipe remoto em caso de furto).
- **Acessibilidade:** WCAG 2.1 AA aplicado ao mobile (alvo). Suporte a screen reader (TalkBack/VoiceOver).
- **Bateria:** background sync usa <5%/h.

## 9. Glossário

Ver `glossario.md` deste módulo.

## 10. Como este PRD evolui

- US nova → adicionar com próximo ID livre (`US-APP-NNN`).
- US deprecada → marcar `@deprecated` + ADR.
- Mudança em AC já implementado → ADR + novo teste.
