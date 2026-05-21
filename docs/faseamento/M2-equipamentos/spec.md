---
owner: roldao
revisado_em: 2026-05-21
proximo_review: 2026-08-21
status: stable
diataxis: reference
audiencia: agente
marco: Wave A Marco 2 — equipamentos
tipo: especificacao-forward
relacionados:
  - .specify/memory/constitution.md
  - docs/dominios/suporte-plataforma/modulos/equipamentos/prd.md
  - docs/dominios/suporte-plataforma/modulos/equipamentos/modelo-de-dominio.md
  - docs/dominios/suporte-plataforma/modulos/equipamentos/transferencia-aceite-presencial-marco2.md
  - docs/faseamento/M1-clientes/spec.md
  - docs/adr/0002-multi-tenancy.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0014-transicoes-regulatorias.md
  - docs/adr/0018-scanner-qr-pwa.md
  - docs/adr/0019-segurabilidade-codigo-ia.md
  - REGRAS-INEGOCIAVEIS.md
---

# Wave A — Marco 2 (equipamentos) — Especificação (forward, autoritativa)

> **O que este documento é (Constituição §1, §2):** a fonte da verdade
> do que o Marco 2 `equipamentos` **deve fazer**. Spec-as-source: o
> código é derivado/validado contra esta spec. Onde código divergir
> (após revisão dos 4 subagentes em P2), **o código é corrigido**, não
> a spec.
>
> **Por que existe (decisão Roldão 2026-05-21):** Marco 1 `clientes`
> fechou via ritual Spec Kit em 2026-05-21 (P5 10 auditores Família 5,
> rodada 2 reauditada, zero CRÍTICO/ALTO/MÉDIO). Marco 2 destrava agora.
> PRD v2 stable (2026-05-18) e 6 planos US revisados pelos 4
> subagentes; esta spec recria o passo 1 do ritual.
>
> **Pra Roldão (uma frase):** este é o "contrato" do módulo que
> cadastra o equipamento físico do cliente (balança, paquímetro,
> termômetro), gera QR Code, registra recebimento físico no laboratório
> e versiona mudanças pós-emissão de certificado.

---

## 1. Escopo

Cadastro completo do equipamento físico do cliente + QR Code com hash
HMAC-SHA256 + ficha 360° auditada + versionamento pós-emissão de
certificado + transferência entre clientes do mesmo tenant + sucatamento
com notificação + **recebimento físico no laboratório (ISO 17025 cl. 7.4)**.
Construído sobre F-A (multi-tenant + RLS + audit + PII HMAC), F-B (auth
+ authz + MFA) e Marco 1 (clientes, bloqueio, identidade canônica).

### Non-goals explícitos (Constituição §5 — proibição positiva)

Marco 2 `equipamentos` **NÃO** entrega, e nenhum agente deve inferir
que entrega:

- **NG-EQP-1**: emissão de certificado — fica em `operacao/certificados`
  (módulo futuro Wave A).
- **NG-EQP-2**: cálculo de incerteza de medição — `metrologia/calculos`
  (V2).
- **NG-EQP-3**: controle de estoque do tenant — equipamento é do cliente
  final, não do laboratório.
- **NG-EQP-4**: cobrança/fatura — `financeiro/contas-receber` (módulo
  futuro). Aqui só **consume** evento de inadimplência do cliente para
  bloquear transferência.
- **NG-EQP-5**: transferência cross-tenant — proibido por `INV-050`
  (vazamento de PII + violação de jurisdição contratual).
- **NG-EQP-6**: padrão metrológico do laboratório (rastreabilidade
  metrológica) — `metrologia/padroes` (V2).
- **NG-EQP-7**: blur facial automático em foto de recebimento — V2 quando
  pipeline ML existir. Marco 2 entrega aviso textual + EXIF strip.
- **NG-EQP-8**: app Flutter nativo — Tela 5 vira PWA (ADR-0018);
  Flutter fica para Wave B.
- **NG-EQP-9**: sincronização offline-first do PWA — ADR-0004, Wave B.
- **NG-EQP-10**: portal-cliente OTP para aceite presencial forte —
  portal-cliente é Wave B; Marco 2 entrega aceite presencial fraco via
  atendente com aviso CLT art. 482 "a" + CP art. 299 (dívida regulatória
  documentada em `transferencia-aceite-presencial-marco2.md`).
- **NG-EQP-11**: emissão de etiqueta térmica direta (impressora Zebra/
  Brother) — Marco 2 entrega PDF para impressão; integração com
  impressoras é Wave A+.
- **NG-EQP-12**: OCR anti-CPF/CNPJ em foto de recebimento — V2; Marco 2
  entrega aviso textual.

### Invariantes governados (Constituição Regra mestre 2 — citar IDs)

Texto canônico em `REGRAS-INEGOCIAVEIS.md`. Marco 2 `equipamentos`
materializa:

- `INV-049` (TAG única por tenant — UNIQUE `(tenant_id, tag) WHERE deletado_em IS NULL`),
- `INV-050` (transferência intra-tenant — cross-tenant bloqueado hard, 422 sem oracle),
- `INV-051` (QR Code HMAC-SHA256 com `KMS_qr_secret` — payload opaco; allowlist anônima documentada),
- `INV-025` (imutabilidade pós-emissão de certificado — versionamento captura mudanças sem mutar histórico),
- `INV-EQP-LOC-001` (`localizacao_fisica` rejeita PII direta),
- `INV-EQP-VERSAO-001` (`motivo_detalhe`/`parecer_gestor_texto` rejeitam PII),
- `INV-EQP-VERSAO-002` (5 categorias proibidas no payload de evento `equipamento.editado`/`equipamento.versao_criada`),
- `INV-EQP-ANOM-001/002` (anomalias + justificativa anti-PII no recebimento físico),
- `INV-EQP-PROV-001` (`RecebimentoProvisorio` não emite certificado — tabela separada, FK bloqueada),
- `INV-013` (log de visualização de PII — INV herdado de F-A; ficha 360° grava `AcessoDadosCliente`),
- `INV-TENANT-001..004` (multi-tenant — herdado de F-A),
- `INV-AUTHZ-001..003` (autorização — herdado de F-B).

Marco 2 **introduz** os IDs novos (a registrar em `REGRAS-INEGOCIAVEIS.md`
durante P2/P4):

- `INV-EQP-001` (perfil_tenant snapshot imutável — RBC B4 anti-downgrade),
- `INV-EQP-002` (segregação ISO 17025 cl. 6.2 — solicitante ≠ aprovador
  em `AprovacaoPendenteEquipamentoVersao`),
- `SEC-QR-001` (QR HMAC com `KMS_qr_secret` em ambiente isolado;
  formalização de `INV-051` como SEC).

Todos exigem cobertura `tests/regressao/inv_eqp_*.py` happy + unhappy
ANTES do fechamento — pré-condição de segurabilidade (ADR-0019 + AUDIT-07
R-EQP-01).

---

## 2. Como ler as User Stories

`US-EQP-NNN` → `AC-EQP-NNN-N` (aceite **binário**: passou / não passou).
Cada AC ganha em P3 (`tasks.md`) coluna **Estado**: `OK` (código satisfaz,
validado), `GAP` (diverge — vira `T-EQP-NNN`), `TRACK` (gate Wave A
rastreado — não bloqueia fechamento do marco). Marco 2 é **greenfield**
(zero código pré-existente neste módulo), então em P3 a matriz será
quase-toda GAP → T-EQP-NNN.

Severidade no fechamento: `INV-RITUAL-001` — MÉDIO bloqueia igual a
CRÍTICO/ALTO; só BAIXO é rastreável.

---

## US-EQP-001 — Cadastrar equipamento com QR Code

**Como** almoxarife ou atendente, **quero** cadastrar um equipamento e
imprimir QR Code, **para** identificar fisicamente o ativo do cliente.

- **AC-EQP-001-1**: POST `/equipamentos/` cria `Equipamento` com `id`
  (UUID), `tenant_id` (do middleware, nunca do payload), `tag` (string
  ≤50 chars), `numero_serie` (string ≤100), `fabricante` (≤100),
  `modelo` (≤100), `faixa` (≤100), `classe` (≤100), `cliente_atual_id`
  (FK para `Cliente`), `localizacao_fisica` (≤200, anti-PII —
  `INV-EQP-LOC-001`), `perfil_tenant_snapshot` (JSONB imutável capturado
  na criação — RBC B4).
- **AC-EQP-001-2**: POST `/equipamentos/{id}/etiqueta.pdf` gera PDF
  com QR Code (WeasyPrint + libpango — TL1) contendo TAG + NS + logo
  do tenant. Cache 60s. Idempotente.
- **AC-EQP-001-3** (`INV-049`): TAG duplicada no mesmo tenant retorna
  409 com link para equipamento existente. UNIQUE parcial `(tenant_id,
  tag) WHERE deletado_em IS NULL`. Equipamento soft-deletado libera TAG.
- **AC-EQP-001-4** (`INV-EQP-LOC-001`): `localizacao_fisica` que contém
  PII direta (regex CPF/CNPJ/e-mail/telefone/≥2 nomes próprios capitalizados
  consecutivos) retorna 400 com mensagem PT-BR citando "LGPD art. 5º I +
  INV-EQP-LOC-001 — descreva sem nomes/documentos". Limite 200 chars.
- **AC-EQP-001-5** (`INV-051` / `SEC-QR-001`): QR Code gerado contém
  `hash = base64url(HMAC-SHA256("<equipamento_id>|<tenant_id>|<emitido_em_iso>",
  KMS_qr_secret))` com ≥22 chars (≥128 bits entropia). `KMS_qr_secret`
  vem de variável de ambiente; hook `qr-hmac-check.sh` (a criar) bloqueia
  hardcode + valida que dev/prod usam segredos diferentes (corretora).
  Re-emissão revoga hash anterior.
- **AC-EQP-001-6**: cadastro publica `Equipamento.Criado` no bus via
  `publicar_evento(outbox=True)` com `tenant_id`, `equipamento_id`,
  `tag_hash` (HMAC), `cliente_atual_id_no_momento_hash` (HMAC),
  `numero_serie_hash` (HMAC), `causation_id` da request. Payload
  sanitizado em ESCRITA (`SEC-SANITIZE-001`).
- **AC-EQP-001-7** (`INV-EQP-001`): `perfil_tenant_snapshot` no
  equipamento é IMUTÁVEL (trigger PG BEFORE UPDATE bloqueia) — RBC B4
  anti-downgrade: se tenant for downgradeado (ex: cancelar pacote
  metrologia), equipamentos antigos preservam o perfil em que foram
  criados; novas criações usam perfil corrente.

## US-EQP-002 — Editar equipamento com versionamento pós-emissão

**Como** metrologista, **quero** editar atributo descritivo de
equipamento que já tem certificado emitido, **para** corrigir
informação sem violar imutabilidade do certificado.

- **AC-EQP-002-1**: PATCH `/equipamentos/{id}/` em campo versionável
  (`modelo`, `faixa`, `classe`, `descricao`, `localizacao_fisica`) com
  certificado já emitido cria `EquipamentoVersao(id, equipamento_id,
  campo, valor_anterior_hash, valor_novo_hash, motivo_mudanca,
  motivo_detalhe, snapshot_jsonb, cliente_atual_id_no_momento,
  criado_por, criado_em)`. Enum `motivo_mudanca` 6 valores (RBC B7):
  `correcao_cadastral`, `mudanca_local`, `troca_acessorio`,
  `recalibracao_diferente_faixa`, `mudanca_classe_metrologica`, `outros`.
- **AC-EQP-002-2** (`INV-025`): alteração em campos imutáveis pós-cert
  (`tag`, `numero_serie`, `fabricante`) retorna 422 com texto PT-BR de 5
  variantes pré-aprovadas (advogado) citando "ISO 17025 cl. 8.4 —
  registros técnicos imutáveis pós-emissão". Lista canônica em
  `docs/conformidade/equipamentos/textos-rejeicao-422.md` (a criar).
- **AC-EQP-002-3** (RBC + perfil A): perfil A editando `classe` ou
  `faixa` exige assinatura A3 do Responsável Técnico (RT) antes de
  gravar — ADR-0009 fluxo. Marco 2 entrega contrato + endpoint
  `POST /equipamentos/{id}/versao/assinar/`; integração A3 cliente-side
  via Lacuna é GATE-EQP-1 Wave A.
- **AC-EQP-002-4**: `motivo_mudanca=outros` exige `motivo_detalhe`
  ≥100 chars + dispara fluxo aprovação `gestor_qualidade` (US-EQP-002b).
  POST retorna 202 com `aprovacao_id`; PATCH só se efetiva após aprovação.
- **AC-EQP-002-5** (`INV-EQP-VERSAO-001`): `motivo_detalhe` rejeita PII
  direta (mesma regex de `INV-EQP-LOC-001`). 400 com texto PT-BR.
- **AC-EQP-002-6** (`INV-EQP-VERSAO-002`): evento `equipamento.versao_criada`
  no bus traz APENAS hashes + UUIDs opacos + nome do campo + enum
  motivo. Proibido no payload: `motivo_detalhe` cru, `valor_anterior`/
  `valor_novo` crus, `cliente_atual_id` cru, `assinatura_a3_hash`
  completo (apenas 16 bytes truncados), `numero_serie` em claro.

## US-EQP-002b — Aprovação `gestor_qualidade` de versionamento "outros"

**Como** gestor de qualidade, **quero** revisar e aprovar mudanças com
`motivo_mudanca=outros` antes de o sistema versionar, **para** atender
ISO/IEC 17025 cl. 6.2 (segregação de funções).

- **AC-EQP-002b-1**: tabela `AprovacaoPendenteEquipamentoVersao` com 16
  campos: `id`, `tenant_id`, `equipamento_id`, `solicitante_id`,
  `campo`, `valor_anterior_hash`, `valor_novo_hash`, `motivo_mudanca`,
  `motivo_detalhe`, `solicitado_em`, `sla_vencimento`, `status` enum
  (`pendente`/`aprovada`/`rejeitada`/`expirada`), `decisor_id`,
  `parecer_gestor_texto`, `decidida_em`, `evidencia_documental_id`
  (opcional). Trigger PG bloqueia UPDATE de `status` saindo de
  estado terminal (`aprovada`/`rejeitada`/`expirada`).
- **AC-EQP-002b-2** (RBC + SLA): SLA diferenciado por presença de
  certificado vigente: D+3 dias úteis (sem cert) | D+7 (com cert).
  Job `job_aprovacao_versionamento_escalacao` (Procrastinate diário
  03:00 BRT) marca `status=expirada` + alerta P2 + evento
  `equipamento.aprovacao_expirada` no bus.
- **AC-EQP-002b-3** (`INV-EQP-002` — ISO 17025 cl. 6.2 segregação):
  CHECK constraint `ck_aprovacao_solicitante_neq_decisor` no banco
  proíbe `solicitante_id = decisor_id`. Defesa em profundidade —
  validação também no use case + serializer.
- **AC-EQP-002b-4**: Django admin com botão `aprovar`/`rejeitar` +
  campo `parecer_gestor_texto` (≥30 chars, anti-PII — regex idêntica
  a `INV-EQP-VERSAO-001`).
- **AC-EQP-002b-5**: aprovação dispara `equipamento.versao_aprovada`;
  rejeição dispara `equipamento.versao_rejeitada`; expiração dispara
  `equipamento.versao_expirada`. Todos via `publicar_evento(outbox=True)`.

## US-EQP-003 — Ficha 360° + scan QR dual-mode + PWA

**Como** técnico de campo, metrologista ou cliente final, **quero**
escanear o QR Code do equipamento, **para** ver dados da ficha em ≤1.5s
p95 com nível de detalhe baseado em quem sou.

- **AC-EQP-003-1**: GET `/equipamentos/{id}/` (autenticado mesmo tenant)
  retorna ficha 360°: dados + versões + lista de certificados (via porta
  stub `CertificadoQueryService`) + lista de OS (porta stub
  `OSQueryService`) + eventos. p95 < 1.5s para equipamento com ≤500
  eventos. `INV-013`: grava `AcessoDadosCliente` ANTES de renderizar.
- **AC-EQP-003-2** (`INV-051` + RBC B6 confidencialidade): GET
  `/v1/qr/{hash}` resolve em 3 modos:
  - **Escopo A** (autenticado mesmo tenant, perfil ≥ atendente): ficha
    completa.
  - **Escopo B** (autenticado outro tenant): payload mínimo allowlist —
    apenas `tipo_equipamento`, `tem_certificado_vigente_bool` (sem
    dados; sem PII; sem localização; sem histórico; sem foto).
  - **Escopo C** (anônimo): payload mínimo allowlist (idem B).
  Allowlist canônica em `docs/conformidade/equipamentos/qr-publico-allowlist.md`
  (a criar).
- **AC-EQP-003-3** (TL2 — anti-enumeração): QR inválido, revogado,
  cross-tenant resolve em SELECT bloqueado por RLS — todos retornam 404
  indistinguível. Latência constante ±5ms via `time.perf_counter`
  buffer (test de fuzzing valida).
- **AC-EQP-003-4** (corretora — defesa em profundidade): rate-limit
  60 req/min por IP (Redis); 100+ 4xx em 1h por IP dispara lockout
  24h + alerta P2 + evento `sistema.qr_lockout_disparado`.
- **AC-EQP-003-5** (ADR-0018): PWA scanner em `/scan/` usa
  `BarcodeDetector` API nativo (Chrome/Edge mobile) com fallback `jsQR`
  (Safari/Firefox). Service-worker `network-only` para `/qr/*`
  (impedir cache de payload sensível). Funciona em iOS Safari 17+
  e Chrome Android 90+.
- **AC-EQP-003-6**: cessionário pós-transferência (US-EQP-004) sem
  consentimento explícito do cedente NÃO vê histórico de certificados
  anteriores — banner "Histórico preservado e confidencial conforme
  RBC ISO/IEC 17025 cl. 4.2". Toggle de consentimento expresso no
  termo de transferência libera visualização (auditável).

## US-EQP-004 — Transferir equipamento entre clientes (mesmo tenant)

**Como** atendente ou metrologista, **quero** transferir o vínculo de
um equipamento para outro cliente do mesmo tenant, **para** registrar
mudança de titularidade.

- **AC-EQP-004-1**: POST `/equipamentos/{id}/transferir/` exige
  `cessionario_id` + `motivo_categoria` enum (`venda`, `comodato`,
  `doacao`, `correcao_cadastral`, `outro`) + `aceite_cedente` (`{tipo:
  presencial_atendente|contrato_fisico_digitalizado|portal_cliente_otp,
  usuario_id_atendente, observacao}`) + `aceite_cessionario` (mesmo
  schema). Cria `TransferenciaEquipamentoAceite` em estado `pendente`;
  efetivação só após ambos aceites válidos.
- **AC-EQP-004-2** (`INV-050`): cessionário em tenant diferente
  retorna 422 com texto genérico "cliente não encontrado neste tenant"
  (sem oracle cross-tenant). RLS no banco bloqueia + use case valida
  defesa em profundidade.
- **AC-EQP-004-3** (`INV-INT-010`): cessionário com bloqueio comercial
  ativo (Marco 1 US-CLI-004) retorna 412 "cliente bloqueado, regularize
  antes". Cedente bloqueado retorna 412 "operação não permitida —
  cedente bloqueado".
- **AC-EQP-004-4** (`Idempotency-Key` — TL3): POST exige header
  `Idempotency-Key` UUID; retry com mesma chave retorna mesmo
  `transferencia_id` sem reaplicar.
- **AC-EQP-004-5** (advogado v1.0 texto): termo de transferência tem
  3 cláusulas obrigatórias mínimas: (a) LGPD art. 18 — titular pode
  exercer direitos sobre histórico; (b) Lei 14.063 art. 4º — natureza
  da assinatura (presencial fraca exige aviso CLT art. 482 "a" + CP
  art. 299 fraude); (c) cessão NÃO transfere garantia ou contrato de
  serviço.
- **AC-EQP-004-6** (RBC cl. 4.2 — confidencialidade): cessionário sem
  consentimento expresso no termo NÃO vê certificados anteriores
  (AC-EQP-003-6). Toggle no payload de aceite.
- **AC-EQP-004-7**: transferência efetivada publica
  `Equipamento.Transferido(equipamento_id, cedente_id_hash,
  cessionario_id_hash, motivo_categoria, transferencia_id,
  causation_id)`. Outbox transacional (`SANEA-08`).

> Dívida regulatória: aceite presencial fraco (atendente afirma "li o
> termo pra ele" sem assinatura física do cliente final) é fonte de
> risco de fraude — documentado em
> `transferencia-aceite-presencial-marco2.md`. Portal-cliente OTP
> (aceite forte) é Wave B+ → **GATE-EQP-3**.

## US-EQP-005 — Sucatar equipamento com notificação

**Como** metrologista, **quero** marcar equipamento como sucata,
**para** registrar fim da vida útil e notificar o cliente se há
certificado vigente.

- **AC-EQP-005-1**: POST `/equipamentos/{id}/sucatear/` com
  `justificativa` ≥30 chars + `confirmacao_simples` quando NÃO há
  certificado vigente nem OS aberta (porta stub Marco 2 retorna
  `tem_cert_vigente=False` e `tem_os_aberta=False`). Cria evento
  `Equipamento.Sucateado` no bus + RLS aplica.
- **AC-EQP-005-2** (RBC + advogado): COM certificado vigente exige
  `confirmacao_dupla=True` no payload + modal UI com checkbox "ciente
  de que o certificado emitido permanece tecnicamente válido conforme
  ISO/IEC 17025 §7.1.1; sucatamento é decisão comercial/operacional
  separada da emissão". Dispara
  `Equipamento.SucateadoComCertificadoVigente` adicional +
  `NotificacaoClienteService` (stub Marco 2 — consumer real quando
  `comunicacao-omnichannel` nascer).
- **AC-EQP-005-3** (`INV-INT-002` — transição regulatória): sucata é
  estado terminal. Trigger PG BEFORE UPDATE em `equipamento.status`
  bloqueia transição de `sucata` para qualquer outro estado, EXCETO
  `extraviado` (corretora — se equipamento sumiu fisicamente, registro
  precisa refletir). Admin Django reservado a perfil A (RT).
- **AC-EQP-005-4** (advogado — template v1.0): template de notificação
  ao cliente passa por allowlist semântica anti-CTA: proibido oferecer
  recompra, desconto em recalibração ou outra ação comercial junto com
  o aviso de sucatamento (manipulação emocional vedada por LGPD art. 5º
  IX — boa-fé).

## US-EQP-006 — Receber equipamento no laboratório (ISO 17025 cl. 7.4)

**Como** almoxarife, **quero** registrar a entrada física do
equipamento no laboratório com condição visual + foto + checklist de
anomalias, **para** atender ISO/IEC 17025 cl. 7.4 e proteger o
laboratório de responsabilização por dano pré-existente.

- **AC-EQP-006-1**: POST `/equipamentos/{id}/recebimentos/` cria
  `EquipamentoRecebimento` com `condicao_visual_chegada` enum
  (`integro`, `amassado`, `lacre_violado`, `contaminado`,
  `sem_acessorios`, `outros`) + `anomalias_observadas` (texto ≤500,
  anti-PII — `INV-EQP-ANOM-001`) + ≥1 foto (obrigatória em **perfil
  A**, opcional em **B/C/D** — perfis do tenant) + `recebido_por`
  (usuário) + `data_recebimento`. Estado inicial `recebido_pendente_inspecao`.
- **AC-EQP-006-2**: `condicao_visual_chegada != integro` exige
  `decisao_apos_anomalia` enum (`prosseguir`, `contatar_cliente_aguardando`,
  `recusar_recebimento`, `aceitar_com_ressalva`) + `justificativa_decisao`
  ≥30 chars (`INV-EQP-ANOM-002` anti-PII). Se
  `contatar_cliente_aguardando`, publica evento que aciona
  `NotificacaoClienteService`.
- **AC-EQP-006-3** (ADR-0014 — máquina de estados): 8 fases válidas:
  `aguardando_recebimento` → `recebido_pendente_inspecao` →
  `em_inspecao_visual` → `aguardando_calibracao` → `em_calibracao` →
  `aguardando_aprovacao_tecnica` → `aguardando_devolucao` → `devolvido`.
  Alternativos terminais: `nao_conformidade_recebimento`,
  `nao_conformidade_calibracao`. Trigger PG valida transições contra
  matriz declarada.
- **AC-EQP-006-4** (cl. 7.4.5 — devolução): POST
  `/equipamentos/{id}/devolucoes/` exige `condicao_visual_devolucao`
  enum (mesmo escopo) + fotos (perfil A obrigatória) +
  `termo_devolucao_assinado` (presencial documento particular CPC art.
  411 III; V2 Lei 14.063 art. 4º — assinatura eletrônica forte).
  Evento `Equipamento.Devolvido` publicado.
- **AC-EQP-006-5** (corretora — RAT-EQP-FOTO + EXIF strip): upload de
  foto passa por `FotoStorageService.salvar` que (a) remove EXIF via
  `Image.new() + Image.putdata() + ImageOps.exif_transpose` (TL2), (b)
  valida tamanho ≤5MB, (c) valida MIME `image/jpeg`/`image/png`, (d)
  apresenta aviso UX "Sem face do cliente / sem dados pessoais legíveis
  — CLT art. 482 'a' + CP art. 299 (fraude)". Retorna `storage_key`
  (NÃO URL — TL3) — view monta URL assinada na hora. OCR anti-CPF =
  V2; Marco 2 apenas aviso textual.
- **AC-EQP-006-6** (`INV-EQP-PROV-001` — Caminho A Roldão):
  `RecebimentoProvisorio` é tabela SEPARADA (não FK em `equipamento`)
  para casos onde o equipamento chegou sem cadastro completo. Trigger
  PG bloqueia INSERT em `certificado` referenciando `RecebimentoProvisorio.id`.
  Promoção a `Equipamento` definitivo é evento único auditável
  `equipamento.promovido_de_provisorio`.

---

## 3. Critérios de fechamento do Marco 2

Marco 2 `equipamentos` FECHADO via ritual quando **todos** abaixo verdes,
e o **loop dos 10 auditores Família 5 = zero CRÍTICO/ALTO/MÉDIO** nas
10 lentes:

1. Todos os AC-EQP-NNN-N acima OK ou rebaixados para TRACK com gate.
2. Suite verde no fluxo padrão (`pytest -p no:randomly`), cobertura ≥
   80% global e ≥ 90% nos arquivos `equipamentos/` (path crítico).
3. `_test-runner.sh` ≥168+ casos verdes (sem reabrir hooks; +casos novos
   por hooks Marco 2).
4. `makemigrations --check` limpo; `migrate --database=migrator`
   from-scratch verde.
5. Drill `validar_f_a` 5/5 verde (não regredir F-A); drill
   `validar_m1_clientes` verde (não regredir Marco 1); novo drill
   `validar_m2_equipamentos` (a criar em P4) com cenário concorrente
   cadastro + scan QR + transferência + recebimento multi-tenant.
6. `INV-EQP-001`, `INV-EQP-002`, `SEC-QR-001` (novos) + `INV-049`,
   `INV-050`, `INV-051`, `INV-025`, `INV-EQP-LOC-001`,
   `INV-EQP-VERSAO-001/002`, `INV-EQP-ANOM-001/002`, `INV-EQP-PROV-001`
   (existentes) registrados em `REGRAS-INEGOCIAVEIS.md` com hooks
   correspondentes (lista em P2 `plan.md`).
7. ADR-0018 (PWA scanner QR) aceita pelo Roldão antes da implementação
   de US-EQP-003.
8. Texto canônico das 5 variantes de mensagem 422 (campos imutáveis
   pós-cert) em `docs/conformidade/equipamentos/textos-rejeicao-422.md`
   stable.
9. Allowlist anônima do QR público em
   `docs/conformidade/equipamentos/qr-publico-allowlist.md` stable.
10. **Suite anti-regressão** `tests/regressao/inv_eqp_*.py` cobre cada
    um dos 3 INVs novos + 8 INVs existentes materializados aqui com
    **happy + unhappy** (corretora §D + ADR-0019 Pilar 2).
11. Hooks novos cravados e em `_test-runner.sh`:
    `qr-hmac-check.sh` (SEC-QR-001), `equipamento-imutabilidade-check.sh`
    (INV-025 — pós-cert), `port-binding-validator.sh` (ADR-0007 —
    portas usadas via DI, não import direto).

---

## 4. Eventos do bus (publicados pelo módulo)

| Evento | Quando | Consumers | Retenção |
|--------|--------|-----------|----------|
| `Equipamento.Criado` | POST `/equipamentos/` | crm, operação, certificados (stub) | 5 anos (Receita) |
| `Equipamento.Atualizado` | PATCH `/equipamentos/{id}/` (campo NÃO versionável) | crm | 5 anos |
| `Equipamento.VersaoCriada` | PATCH em versionável pós-cert | certificados, governança | **25 anos / WORM** (ISO 17025 §8.4) |
| `Equipamento.VersaoAprovada` | gestor_qualidade aprova `motivo=outros` | governança | 25 anos / WORM |
| `Equipamento.VersaoRejeitada` | gestor_qualidade rejeita | governança | 25 anos / WORM |
| `Equipamento.VersaoExpirada` | job escalação D+3/D+7 | governança, operação | 5 anos |
| `Equipamento.Transferido` | POST `/equipamentos/{id}/transferir/` (efetivado) | crm, certificados, financeiro | 25 anos / WORM (RBC cl. 4.2) |
| `Equipamento.Sucateado` | POST `/equipamentos/{id}/sucatear/` | crm, comunicacao-omnichannel | 25 anos / WORM |
| `Equipamento.SucateadoComCertificadoVigente` | sucata com cert ativo | comunicacao-omnichannel, governança | 25 anos / WORM |
| `Equipamento.Recebido` | POST `/equipamentos/{id}/recebimentos/` | operação, faturamento | 25 anos / WORM |
| `Equipamento.Devolvido` | POST `/equipamentos/{id}/devolucoes/` | operação, faturamento, omnichannel | 25 anos / WORM |
| `Equipamento.PromovidoDeProvisorio` | promoção de `RecebimentoProvisorio` | operação | 25 anos / WORM |

Helper único de gravação `audit/event_helpers.py` (`SANEA-08`) — não
copiar o envelope 12×.

---

## 5. Premissas e dependências (portas/stubs)

- **F-A FECHADA via ritual** (multi-tenant + RLS fail-loud +
  audit-imutavel + PII HMAC versionado + hooks 168/168). `equipamentos`
  herda integralmente.
- **F-B FECHADA via ritual** (auth + authz + MFA). US-EQP-003 depende
  de `INV-013` registrar acesso ANTES de renderizar ficha; US-EQP-002b
  depende de `AuthorizationProvider.can`.
- **Marco 1 `clientes` FECHADO via ritual** (2026-05-21). Marco 2 usa
  repositório real de clientes; AC-EQP-004-3 (cessionário bloqueado)
  depende de `cliente_nao_bloqueado` predicate.

### Portas/stubs (ADR-0007)

| Porta | Status Marco 2 | Adapter futuro |
|-------|----------------|----------------|
| `CertificadoQueryService` | Stub `EmptyCertificadoQueryService` retorna `tem_cert_vigente=False` | VIEW `certificado` quando `operacao/certificados` nascer (Wave A) |
| `OSQueryService` | Stub `EmptyOSQueryService` retorna `tem_os_aberta=False` | `operacao/os` (Wave A) |
| `BloqueioClienteQueryService` | **Real** — adapter Django consulta `cliente_nao_bloqueado` (Marco 1) | já entregue |
| `FinanceiroQueryService` | Stub `EmptyFinanceiroQueryService` retorna `tem_fatura_aberta=False` | `financeiro/contas-receber` (Wave A) |
| `NotificacaoClienteService` | Stub grava evento no bus; sem efeito externo | `comunicacao-omnichannel` (Wave A) |
| `FotoStorageService` | `LocalFotoStorageService` (dev) + `S3MockFotoStorageService` (test); produção real é GATE-EQP-2 Wave A com B2 | B2 Backblaze (Wave A) |

### ADRs novas/relevantes

- **ADR-0018** — Scanner QR PWA (`BarcodeDetector` + fallback `jsQR`).
  Status: proposta → exige ACEITE Roldão antes de implementar US-EQP-003.
- **ADR-0019** — Segurabilidade código IA. Marco 2 mantém os 2 pilares
  (cobertura suite anti-regressão + revisão humana antes commit em
  paths críticos: KMS, financeiro, certificados).
- **ADR-0017** — CNPJ alfanumérico. `cliente_atual_id` do equipamento
  resolve via repositório Marco 1 (que já trata CNPJ alfanumérico).

---

## 6. O que NÃO redefiniu (herdado, não duplicar)

- Toda multi-tenant infra (middleware, RLS templates, contexts) é F-A.
- Todo authz/MFA/sessão é F-B.
- PII HMAC + sanitização + cadeia de auditoria + trigger anti-mutation
  + `bus_outbox` + worker outbox são F-A + Marco 1.
- Helper único `audit/event_helpers.publicar_evento` (`SANEA-08`).
- Política LGPD única `audit/politicas_lgpd.base_legal_aplicavel_pos_revogacao`
  (Marco 1 INV-CLI-002) — Marco 2 chama, não duplica.
- Hooks já cobrem `INV-TENANT-001..004`, `audit-immutability`,
  `migration-rls-check`, `tenant-id-validator`, `event-helper-unico`,
  `cliente-canonico-imutavel`, `lgpd-policy-unica`, `csv-safety-import`
  — não recriar.

Onde Marco 2 ADICIONA invariante novo (`INV-EQP-001`, `INV-EQP-002`,
`SEC-QR-001`), P2 decide o hook correspondente; P4 implementa.

---

## 7. Decisões dos 4 revisores PRD v1→v2 (registro auditável)

Cada bullet abaixo veio do parecer dos 4 subagentes humano-substitutos
sobre o PRD v1 e foi absorvido no PRD v2 stable (2026-05-18). Esta
spec forward materializa os ajustes como AC binários.

### `tech-lead-saas-regulado`

- **TL1**: `KMS_qr_secret` em env var; hook `qr-hmac-check.sh` valida
  hardcode + dev/prod distintos. Cravado em AC-EQP-001-5.
- **TL2**: timing constant em 404 do QR público (anti-enumeração).
  Cravado em AC-EQP-003-3.
- **TL3**: `Idempotency-Key` em tabela PG (não Redis); retry retorna
  mesmo `transferencia_id`. Cravado em AC-EQP-004-4.
- **TL4**: `FotoStorageService.salvar` retorna `storage_key`, não URL
  (anti-vazamento em log/audit). Cravado em AC-EQP-006-5.
- **TL5**: trigger PG com sufixo `_v0_stub` quando stub Marco 2; remove
  o `_v0_stub` quando consumer real entrar em Wave A. Convenção
  cravada em modelo-de-dominio.md.

### `advogado-saas-regulado`

- **A1**: 5 textos PT-BR de rejeição 422 pré-aprovados (campos imutáveis
  pós-cert). Cravado em AC-EQP-002-2 + lista canônica em arquivo
  separado (§3 item 8).
- **A2**: payload de evento de versionamento sanitizado — hashes + sem
  motivo_detalhe bruto + sem NS em claro. Cravado em
  `INV-EQP-VERSAO-002` + AC-EQP-002-6.
- **A3**: termo de transferência v1.0 com 3 cláusulas legais mínimas
  (LGPD art. 18 + Lei 14.063 art. 4º + não-cessão de garantia).
  Cravado em AC-EQP-004-5.
- **A4**: aceite presencial fraco documentado como dívida regulatória
  + aviso UX (CLT 482 "a" + CP 299). Cravado em AC-EQP-004-1 + NG-EQP-10
  + `transferencia-aceite-presencial-marco2.md`.
- **A5**: template de notificação de sucatamento com allowlist
  semântica anti-CTA (proibido oferecer recompra junto). Cravado em
  AC-EQP-005-4.

### `corretora-seguros-saas`

- **S1**: `KMS_qr_secret` dev/prod distintos reduz prêmio cyber.
  Cravado em AC-EQP-001-5 + TL1.
- **S2**: defesa em profundidade rate-limit + timing oracle reduz
  exposição a varredura. Cravado em AC-EQP-003-3 + AC-EQP-003-4.
- **S3**: foto de recebimento como evidência (RAT-EQP-FOTO + EXIF
  strip). Cravado em AC-EQP-006-5.
- **S4**: perfil A obrigatória foto no recebimento — RBC B2.
  Cravado em AC-EQP-006-1.

### `consultor-rbc-iso17025`

- **R1**: `perfil_tenant_snapshot` imutável no equipamento (RBC B4
  anti-downgrade). Cravado em AC-EQP-001-7 + `INV-EQP-001`.
- **R2**: enum `motivo_mudanca` 6 valores fechados (RBC B7). Cravado
  em AC-EQP-002-1.
- **R3**: máquina de estados ≥6 fases no recebimento físico (ISO 17025
  cl. 7.4.4). Cravado em AC-EQP-006-3 (8 fases + 2 alternativos).
- **R4**: segregação ISO 17025 cl. 6.2 (solicitante ≠ aprovador) em
  `AprovacaoPendenteEquipamentoVersao`. Cravado em AC-EQP-002b-3 +
  `INV-EQP-002`.
- **R5**: SLA D+3 (sem cert) / D+7 (com cert) razoáveis. Cravado em
  AC-EQP-002b-2.
- **R6**: recebimento + devolução cobre cl. 7.4.4 + cl. 7.4.5 + cl.
  7.10 (não-conformidade). Cravado em AC-EQP-006-4 + estados
  alternativos `nao_conformidade_*`.
- **R7**: histórico oculto para cessionário sem consentimento
  (RBC cl. 4.2 confidencialidade — RBC B6). Cravado em AC-EQP-003-6 +
  AC-EQP-004-6.
- **R8**: log de visualização da ficha (cl. 4.2). Cravado em
  AC-EQP-003-1 + INV-013.

---

## 8. Recomendações de segurabilidade (ADR-0019 Pilar 2)

Antes do 1º tenant externo pago que opere equipamentos:

- Apólice cyber + RC profissional cobrindo KMS leak + QR enumeração +
  vazamento de PII em foto/EXIF.
- Auditoria humana licenciada sobre código que toca `KMS_qr_secret`,
  `bus_outbox` e triggers PG do Marco 2 — `tech-lead-saas-regulado`
  cobre revisão pré-1º tenant; humano sênior contratado revisa
  pré-pago.
- Contratação de consultor RBC humano credenciado antes da 1ª
  supervisão CGCRE — este Marco 2 cobre ~80% do dossiê técnico.
