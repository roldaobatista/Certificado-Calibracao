---
owner: roldao
revisado_em: 2026-05-22
proximo_review: 2026-08-22
status: draft
modulo: clientes
dominio: comercial
diataxis: explanation
audiencia: agente
---

# PRD — Módulo Clientes

## 1. O que este módulo é

Cadastro único de clientes PF/PJ do tenant + visão 360° consolidada (timeline de OS, certificados, financeiro, contatos, NPS) + limite de crédito + segmentação + rating. **É a base de todos os outros módulos comerciais e operacionais** — sem cliente master, OS/orçamento/contrato/cobrança não existem.

## 2. Por que existe

Dor #01 (cadastro duplicado entre sistemas) + dor universal "cadê o cadastro do Sr. Silva?" + BIG-07 (Cliente 360°). Discovery: founder e validações externas confirmam que cadastro duplicado é Top 3 das dores de atendente. Foundation F-C destrava OP1, OP2, OP4, OP7, OP15.

## 3. Personas

Ver `../../personas.md` (P-COM-01 Atendente, P-COM-02 Vendedor, P-COM-05 Dono). Cliente final do tenant (P-COM-03) **não** edita seu próprio cadastro neste módulo — vai pelo portal (módulo separado).

## 4. Escopo MVP-1 (o que ESTÁ neste módulo)

- Cadastro PF (CPF + RG + telefone + e-mail + endereço + LGPD aceite)
- Cadastro PJ (CNPJ + razão + fantasia + IE + IM + endereço + contatos múltiplos + unidades/filiais)
- Validação automática CPF/CNPJ (algoritmo + opcional consulta ReceitaWS — V2)
- Dedup automático na criação (mesmo CPF/CNPJ) + wizard de dedup manual
- Visão 360° (timeline cronológica + abas: OS, Certificados, Financeiro, Contatos, NPS, Anexos)
- Limite de crédito (valor + uso atual + bloqueio quando excedido)
- Segmentação (tags configuráveis pelo tenant)
- Importação 1-clique (Cali/Bling/CSV) — Foundation F-C
- Bloqueio comercial (manual ou automático por inadimplência via régua OP11)

## 5. Non-goals (NÃO entra)

- **Equipamentos do cliente** (vai pra módulo `suporte-plataforma/equipamentos`, OP17)
- **Histórico técnico de calibração** (vai pra `operacao/certificados`)
- **Lead não-convertido** (vai pra módulo `crm/leads` — lead vira cliente só ao converter)
- **Cobrança ativa / boleto** (vai pra `financeiro/contas-receber`)
- **Rating de crédito por bureau externo** (Serasa/SPC) — fora do MVP-1
- **Cadastro próprio pelo cliente final no portal** — V2
- **CRM custom fields** com lógica condicional — Wave B no módulo crm
- **Mailing/campanha de e-mail marketing** — fora do produto

## 6. User Stories principais

### US-CLI-001: Cadastrar cliente PF em menos de 1 minuto
**Como** atendente, **quero** abrir um formulário curto e digitar CPF/nome/telefone/e-mail, **para** começar atendimento sem perder o cliente na linha.
- AC-1: GIVEN tela `/clientes/novo` WHEN preencho CPF válido THEN sistema valida algoritmo + busca duplicata + se duplicar mostra link "este cliente já existe".
- AC-2: GIVEN form preenchido WHEN salvo THEN cliente master criado com `tenant_id`, aceite LGPD registrado (RAT-03), evento `Cliente.Criado` publicado.
- **AC-CLI-001-3 (formalizado Onda 4 M1-CLI):** GIVEN cliente existente WHEN PATCH em campos do agregado (nome_ou_razao, documento, endereço principal, rating, segmento_ids, limite_credito, bloqueio_comercial) THEN evento `Cliente.Atualizado` publica payload `{cliente_id, campos_alterados: list[str]}` listando atributos alterados (declarativo — não inclui valores antes/depois; auditoria preserva valores em `audit_trail` INV-001).
- **AC-CLI-001-4 (ADR-0039 — tipos expandidos):** GIVEN seletor de tipo `{PF, PJ, MEI, CLIENTE_EXTERIOR}` WHEN usuário escolhe `CLIENTE_EXTERIOR` THEN form pede `pais_origem` (ISO 3166-1 alpha-2, ≠ `BR`) + `tax_id_estrangeiro` (texto livre uppercase 40 chars); aceite contratual base legal "execução de contrato" (LGPD art. 7º V) substitui aceite LGPD. WHEN usuário escolhe `MEI` THEN form força `regime_tributario=SIMEI` (não editável).
- **AC-CLI-001-5 (formalizado Onda 4 — Lead→Cliente, ver T-CLI-SAN-07):** GIVEN conversão de lead (Wave B módulo `crm/leads`) WHEN endpoint `POST /clientes` recebe `lead_id_origem: UUID` THEN cliente criado carrega esse campo no payload `Cliente.Criado` para o BI medir conversão por canal/campanha.
- **AC-CLI-001-6 (reativação pós-anonimização, ver `reativacao-anonimizacao.md`):** GIVEN documento D tem hash registrado em `DocumentoAnonimizadoHistorico(tenant_id, hash(D, salt))` WHEN cadastro novo é tentado por usuário comum THEN 409 com texto canônico "Já existe cadastro anterior com este documento que foi anonimizado por solicitação do titular...". Usuário com papel `cadastro_avancado` (T-CLI-SAN-03) prossegue com justificativa ≥30 chars + aceite LGPD reforçado + flag `documento_zona_b_anonimizado=True` + evento `Cliente.CadastroPosAnonimizacaoCriado`.
- **INV:** INV-024 (dedup), INV-TENANT-001, INV-TENANT-002, INV-CLI-001, INV-CLI-CONTATO-001, INV-CLI-ENDERECO-001, INV-CLI-REATIV-001.

### US-CLI-002: Ver visão 360° do cliente
**Como** atendente/vendedor, **quero** abrir `/clientes/{id}` e ver tudo do cliente em uma tela, **para** atender sem trocar de aba 6 vezes.
- AC-1: Timeline cronológica reversa com eventos de todos os módulos (OS criada/concluída, certificado emitido, NF-e, NPS, contato registrado).
- AC-2: Carregamento p95 < 1.5s pra clientes com até 500 eventos.
- AC-3 (INV-013): cada abertura de visão 360° grava linha em `audit_trail.acessos_dados_cliente` com `{user_id, tenant_id, cliente_id, finalidade, timestamp, ip_hash}` antes de renderizar — LGPD exige saber quem viu CPF/dados pessoais do cliente.
- **AC-CLI-002-4 (formalizado Onda 4 M4-CLI — bloqueio comercial × finalidade LGPD):** GIVEN cliente em `bloqueio_comercial.ativo=True` (manual ou por inadimplência) WHEN consulta vem com `finalidade ∈ {COMERCIAL, MARKETING}` THEN `AuthorizationProvider.can()` retorna 403 com texto canônico "Cliente bloqueado comercialmente — consulta para finalidade comercial/marketing não autorizada". Finalidades `COBRANCA`, `JURIDICO`, `SUPORTE_TECNICO`, `AUDITORIA_INTERNA` continuam permitidas (vínculo ativo para cobrar/resolver litígio existe; LGPD art. 7º VI exercício de direitos). Aderente a INV-CLI-002 (política LGPD num único lar).
- **AC-CLI-002-5 (Visão 360° materializada — T-CLI-SAN-01):** GIVEN tenant com até 10.000 clientes × 500 eventos/cliente WHEN abrir `/clientes/{id}` THEN p95 < 1.5s (medido via OTel). Tenants 10k-50k clientes: degradação aceita até p95 3.0s. Acima de 50k: gate de mitigação dedicada (fora MVP).
- **INV:** INV-013 (confidencialidade — log de visualização), INV-TENANT-001, INV-CLI-002 (política LGPD num único lar).

### US-CLI-003: Importar planilha de clientes (1-clique)
**Como** dono migrando de Cali/Bling, **quero** subir CSV/XLSX e ver mapeamento automático, **para** não digitar 800 cadastros.
- AC-1: GIVEN arquivo válido WHEN upload THEN preview com 10 primeiras linhas + mapeamento sugerido.
- AC-2: GIVEN confirmação WHEN executa THEN cria clientes em lote, dedup automático, relatório final (criados/atualizados/rejeitados).

### US-CLI-004: Bloquear cliente inadimplente (manual + automático)
**Como** financeiro/dono, **quero** marcar cliente como bloqueado (manual) OU que sistema marque automaticamente após inadimplência > 90 dias, **para** impedir nova OS/orçamento/agenda sem quitar débito.

**Critérios de aceite — Bloqueio manual:**
- **AC-CLI-004-1**: GIVEN financeiro/dono autenticado, WHEN abre cadastro de cliente e clica "Bloquear", THEN sistema exige justificativa ≥30 chars, publica `Cliente.Bloqueado(motivo="manual", justificativa=...)` + audit trail.
- **AC-CLI-004-2**: GIVEN cliente bloqueado, WHEN tenta criar OS/orçamento/agendar visita, THEN `AuthorizationProvider.can()` retorna `denied, reason="cliente_bloqueado_manual"` + sugere "Quitar débito ou desbloqueio manual com justificativa".

**Critérios de aceite — Bloqueio automático por inadimplência (ADR-0015 fluxo 4):**
- **AC-CLI-004-3**: GIVEN cliente tem `ContasReceber.TituloVencido` com `dias_vencido >= 90`, WHEN job Celery diário `job_inadimplencia_alertas` roda 02:00 BRT, THEN sistema marca `Cliente.bloqueado=true, motivo="inadimplencia_90d"`, publica `Cliente.Bloqueado` + `ContasReceber.ClienteInadimplenteAlertaP1(valor_total_devido, dias_vencido)`.
- **AC-CLI-004-4**: GIVEN cliente bloqueado por inadimplência, WHEN módulos consumidores reagem:
  - `operacao/os` — `AuthorizationProvider.can("os.criar", {"cliente_id": X})` retorna `denied, reason="cliente_bloqueado_inadimplencia"`
  - `comercial/orcamentos` — orçamentos pendentes ganham flag `bloqueado_por_inadimplencia=true` + notificam vendedor
  - `operacao/agenda` — alocações futuras canceladas + reagendadas para "quando regularizar"
  - `comunicacao-omnichannel` — notifica gerente operacional + cliente final
- **AC-CLI-004-5 (régua progressiva D+30..89)**: Antes de bloquear, dispara `ContasReceber.ReguaCobrancaDispachada` em D+30, D+60, D+89 (escalada WhatsApp → e-mail → ligação) — bloqueio só em D+90.
- **AC-CLI-004-6 (reativação automática)**: GIVEN última fatura vencida é paga, WHEN `ContasReceber.Pago` chega, THEN publica `Cliente.Desbloqueado(motivo="quitou_inadimplencia")` em ≤5min; consumers re-permitem operação.
- **AC-CLI-004-7 (auditoria)**: Toda transição grava em `audit_trail.authz_decisions` com `causation_id` ligando ao título vencido que disparou.

**Invariantes:** `INV-INT-010` (cliente bloqueado bloqueia operação), `INV-001` (audit), `INV-013` (confidencialidade — log de visualização).

**Dependências:** ADR-0015 fluxo 4, ADR-0012 (autorização), `financeiro/contas-receber`, `comunicacao-omnichannel`.

### US-CLI-005: Dedup manual de cadastros duplicados
**Como** atendente, **quero** wizard que mostre 2 cadastros lado a lado e me deixe escolher campo a campo qual valor manter, **para** consolidar sem perder histórico.
- AC-1: Histórico (OS, certificados, financeiro) do cadastro perdedor migra integralmente pro vencedor.
- AC-2: Cadastro perdedor é soft-deleted (auditável), nunca hard-deleted (LGPD).

### US-CLI-009: Gerir contatos múltiplos do PJ (formalizado Onda 4 C1-CLI)
**Como** atendente/vendedor, **quero** cadastrar múltiplos contatos por cliente PJ (RT do cliente, financeiro, comercial, técnico) com canais e consentimentos próprios, **para** garantir comunicação correta + emissão ISO 17025 com RT identificado.
- **AC-CLI-009-1:** GIVEN cliente PJ/MEI WHEN cadastro contatos THEN sistema permite N contatos com `cargo ∈ {RT_cliente, financeiro, comercial, tecnico_responsavel, outro}`, `telefones[]` (E.164), `emails[]` (RFC 5322), `canal_preferido`, `consentimento_whatsapp_em`, `consentimento_whatsapp_canal`, `principal: bool`.
- **AC-CLI-009-2:** GIVEN cliente PJ/MEI WHEN salvar THEN exatamente 1 contato deve ter `principal=True` (INV-CLI-CONTATO-001). Tentativa sem principal bloqueia.
- **AC-CLI-009-3:** GIVEN emissão envolve laudo ISO 17025 WHEN cliente não tem `Contato.cargo=RT_cliente` ativo THEN emissão bloqueia com texto canônico "Cliente exige RT cadastrado antes de emitir laudo ISO 17025" (ISO 17025 cl. 7.8).
- **AC-CLI-009-4:** GIVEN canal preferido = WhatsApp WHEN régua D+30/60/89 (T-CLI-SAN-02) tenta enviar THEN `consentimento_whatsapp_em` deve ser ≤24 meses; senão fallback automático para e-mail.
- **INV:** INV-CLI-CONTATO-001.

### US-CLI-010: Gerir endereços e filiais do PJ (formalizado Onda 4 C2-CLI)
**Como** atendente, **quero** cadastrar múltiplos endereços por cliente PJ (matriz + filiais operacionais + cobrança + entrega), **para** OS/agenda/NF-e usar o endereço correto por operação.
- **AC-CLI-010-1:** GIVEN cliente PJ WHEN cadastra endereço THEN permite N endereços com `tipo ∈ {principal, cobranca, entrega, unidade_filial}`.
- **AC-CLI-010-2:** GIVEN cliente qualquer WHEN salvar THEN ≥1 endereço com `tipo=principal` existe (INV-CLI-ENDERECO-001); default na criação cria o principal a partir dos dados do form.
- **AC-CLI-010-3:** GIVEN cliente PJ tem N `unidade_filial` WHEN abrir OS THEN seletor de "local de execução" lista filiais (mais matriz) e default = filial mais usada nas últimas 10 OS.
- **AC-CLI-010-4 (CLIENTE_EXTERIOR):** GIVEN `tipo=CLIENTE_EXTERIOR` WHEN cadastrar endereço THEN aceita `pais ≠ BR` (ISO 3166-1 alpha-2); UF e CEP viram opcionais quando `pais ≠ BR`.
- **INV:** INV-CLI-ENDERECO-001.

### US-CLI-011: Registrar sucessão societária (formalizado Onda 4 C3-CLI)
**Como** administrador do tenant, **quero** wizard que registre fusão / cisão / incorporação entre clientes PJ, **para** preservar rastreabilidade fiscal + ISO 17025 dos predecessores enquanto sucessor absorve equipamentos/histórico.
- **AC-CLI-011-1:** GIVEN papel `cadastro_avancado` ou `dono_tenant` (T-CLI-SAN-03) WHEN abre wizard "registrar sucessão" THEN escolhe tipo `{FUSAO, CISAO, INCORPORACAO, INCORPORACAO_CNPJ_NOVO}` → seleciona predecessor(es) → seleciona sucessor(es) → carrega ato societário (PDF anexo) → digita fundamento legal (≥10 chars).
- **AC-CLI-011-2:** GIVEN wizard confirmado WHEN salvar THEN cria N linhas `SucessaoSocietaria(predecessor_id, sucessor_id, ...)`, marca predecessor.estado = `ARQUIVADO_POR_SUCESSAO` (predecessor NÃO é deletado nem anonimizado — INV-CLI-SUCESSAO-002), migra equipamentos do predecessor para sucessor via evento `Equipamento.SucessaoSocietaria`, publica `Cliente.SucessaoSocietariaRegistrada`.
- **AC-CLI-011-3 (intra-tenant):** GIVEN tentativa de sucessão para cliente fora do tenant atual WHEN salvar THEN 422 genérico "cliente sucessor não encontrado neste tenant" (sem oracle cross-tenant — INV-CLI-SUCESSAO-001).
- **AC-CLI-011-4 (certificados imutáveis):** GIVEN equipamento migra de predecessor para sucessor WHEN certificados emitidos antes do `data_evento` da sucessão consultados THEN PDF preserva snapshot do **predecessor** original (INV-025 + ADR-0021 Zona B); novos certificados emitidos pós-sucessão usam dados do sucessor.
- **AC-CLI-011-5 (anexo obrigatório):** GIVEN wizard WHEN salvar sem `ato_societario_anexo_id` ou `fundamento_legal < 10 chars` THEN bloqueia com 422 (INV-CLI-SUCESSAO-003).
- **INV:** INV-CLI-SUCESSAO-001..003.

## 7. Métricas

Ver `metricas.md`. Resumo: taxa de duplicidade < 1%, tempo médio cadastro PF < 60s, % clientes com 360° usado/semana > 40%.

## 8. NFR

- Performance: cadastro p95 < 800ms; visão 360° p95 < 1.5s.
- Disponibilidade: 99.9% (módulo crítico).
- LGPD: RAT-03 obrigatório no cadastro; RAT-06 quando comunicação WhatsApp ativada.
- Multi-tenancy: INV-TENANT-001/002/003/004 absolutos.

## 9. Glossário

Ver `glossario.md`.

## 10. Vocabulário (referência rápida — fonte canônica é `glossario.md`)

> Lista declarativa para agentes IA evitarem termo errado em código/UI. Definição em 1 linha; ver `glossario.md` para detalhe + sinônimos proibidos. Catálogo de eventos consolidado em ADR-0037 (Onda 1 — fonte única).

| Termo | Em 1 linha |
|---|---|
| Cliente PF | Pessoa física com CPF — atendido pelo tenant. |
| Cliente PJ | Pessoa jurídica com CNPJ (raiz alfanumérica a partir de jul/2026 — ADR-0017). |
| Cliente MEI | PJ regime SIMEI (LC 123/2006) — ADR-0039. |
| Cliente do exterior | Pessoa/empresa fora do BR com `tax_id_estrangeiro` + `pais_origem` — ADR-0039. |
| Cliente master | Cadastro vencedor da cadeia `cliente_canonico_id` (INV-CLI-001) — pra onde tudo aponta após dedup. |
| Visão 360° | Tela única (timeline materializada `EventoTimeline` — T-CLI-SAN-01) com tudo do cliente. |
| RT do cliente | `Contato.cargo=RT_cliente` — responsável técnico do cliente que assina laudo ISO 17025. **Não confundir** com RT do tenant Aferê (ADR-0022). |
| Unidade/filial | `Endereco.tipo=unidade_filial` — endereço operacional adicional do PJ (não cria novo cliente). |
| Sucessão societária | Fusão/cisão/incorporação registrada via `SucessaoSocietaria` — ver `sucessao-societaria.md`. |
| Reativação pós-anonimização | Cadastro novo com documento previamente anonimizado Zona B/C — ver `reativacao-anonimizacao.md`. |
| Régua D+30/60/89 | Notificação progressiva de inadimplência antes do bloqueio D+90 — T-CLI-SAN-02 + INV-CLI-BLOQ-001. |
| Bloqueio comercial | `bloqueio_comercial.ativo=True` — impede OS/orçamento; consulta com finalidade COMERCIAL/MARKETING também nega (AC-CLI-002-4). |

## 11. Eventos publicados (referência — fonte canônica é catálogo ADR-0037)

| Evento | Quando | Notas Onda 4 |
|---|---|---|
| `Cliente.Criado` | cadastro novo | payload inclui `lead_id_origem: UUID NULL` (T-CLI-SAN-07) |
| `Cliente.Atualizado` | PATCH em campos do agregado | payload inclui `campos_alterados: list[str]` (AC-CLI-001-3) |
| `Cliente.Bloqueado` / `Cliente.Desbloqueado` | bloqueio manual ou automático | inalterado vs Marco 1 |
| `Cliente.Dedup.Mesclado` | wizard dedup concluído (INV-CLI-001) | inalterado |
| `Cliente.SucessaoSocietariaRegistrada` | wizard sucessão concluído | novo Onda 4 — `sucessao-societaria.md` |
| `Cliente.CadastroPosAnonimizacaoCriado` | cadastro com doc anonimizado | novo Onda 4 — `reativacao-anonimizacao.md` |
| `Cliente.Anonimizado` | Zona A/B/C aplicada | propaga para módulos via ADR-0032 (`ReferenciaPIIAnonimizavel`) |
