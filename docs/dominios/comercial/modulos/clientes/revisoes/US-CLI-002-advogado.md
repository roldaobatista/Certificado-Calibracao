---
owner: advogado-saas-regulado
revisado-em: 2026-05-18
proximo-review: 2026-08-18
status: stable
tipo: revisao-juridica-consultiva
us: US-CLI-002
plano: docs/dominios/comercial/modulos/clientes/planos/US-CLI-002.md
revisor: subagente advogado-saas-regulado (IA — NÃO substitui OAB)
audiencia: agente
---

# Parecer Jurídico Consultivo — US-CLI-002 (LGPD)

> **Aviso legal obrigatório:** sou subagente IA, não tenho OAB ativa, este texto é minuta consultiva. Antes de qualquer go-live público envolvendo log de visualização de dados de titulares finais, advogado humano licenciado deve revisar — especialmente o enum de finalidades de acesso (§3) e a política de acesso aos próprios logs pelo titular (R5, Wave B).

---

## Sumário (≤150 palavras)

**APROVADO COM RESSALVAS BLOQUEANTES (R1–R5).** O plano US-CLI-002 acerta na coluna estrutural — audit síncrono ANTES de renderizar, RLS pattern v2, trigger anti-mutation, INV-013 cravado. **Cinco buracos LGPD precisam ser tampados antes do code-complete:** (R1) faltam `categoria_dado_acessado` (PII identificadora vs sensível) e `recurso` JSON sem PII cru — sem categoria, fiscalização ANPD não consegue priorizar incidente; (R2) `finalidade` precisa enum cravado **distinto** das 4 finalidades-base de `finalidades-lgpd.md` — visualização é ato secundário, não base legal nova; (R3) Roldão/operador Aferê **NUNCA** lê esses logs sem sessão Suporte SaaS RAT-15 (consentimento admin tenant + janela ≤2h); (R4) retenção alinhada com `audit trail` da matriz (5–10 anos B2 WORM, NÃO Marco Civil 6m, NÃO retenção de Cliente); (R5) art. 18 II direito de saber quem acessou é do **titular final** — Aferê expõe via tenant (controlador) na Wave B `portal-cliente`, NÃO direto.

---

## Veredito

**APROVADO COM RESSALVAS BLOQUEANTES.** A arquitetura está correta (audit síncrono pré-render, RLS, trigger imutável). Falta saneamento de payload (R1), cravar enum de finalidades de acesso (R2), bloquear acesso operador Aferê (R3), alinhar retenção (R4) e registrar contrato futuro art. 18 II (R5).

### Ressalvas (R1–R5)

#### R1 — Payload do audit precisa `categoria_dado_acessado` + `recurso` SEM PII cru (BLOQUEANTE)

O AC-CLI-002-3 lista `{user_id, tenant_id, cliente_id, finalidade, timestamp, ip_hash}`. Faltam **dois campos críticos**:

1. **`categoria_dado_acessado`** (enum) — distinguir o que efetivamente foi exposto na tela:
   - `pii_identificadora` (nome, CPF, endereço, contato) — padrão da visão 360°
   - `pii_sensivel` (saúde, biometria) — quando módulo ASO/biometria entrar (RAT-13/14), visão 360° pode mostrar
   - `dado_fiscal` (NF-e, valor, histórico financeiro) — quando módulo financeiro publicar eventos
   - `dado_regulatorio` (certificado ISO 17025, laudo) — confidencialidade cl. 4.2 reforçada
   - `metadado` (timeline vazia — só evento `cliente.criado` sem expor dados do cliente)

   **Por quê:** sem categoria, fiscalização ANPD pergunta "esse acesso pegou CPF ou só viu que existia cliente?" e a resposta é "não sei" — viola Art. 6º VI (transparência) + INV-013. Categoria também alimenta dashboard de drift (acessos a `pii_sensivel` que cresce inexplicavelmente vira alerta).

2. **`recurso`** (JSONB) — referência à tabela + chave **sem PII bruta** (igual `isolamento-multi-tenant.md` §8.1). Exemplo: `{"tabela": "clientes_cliente", "id": "<uuid>"}`. **NUNCA** gravar nome/CPF/email do cliente no audit. Motivos idênticos ao veto US-CLI-005 R1:
   - Crypto-shredding impossível em 2031 quando titular exercer art. 18 VI (audit em WORM não permite UPDATE).
   - Cross-tenant blast radius — admin Aferê (suporte forense) lê dado do tenant sem cláusula DPA cobrindo.
   - NC LGPD art. 6º III (necessidade) — audit prova **que** houve acesso, não **qual conteúdo** foi exposto.

   `cliente_id` (UUID) é suficiente — quem precisa do nome consulta a tabela `Cliente` cruzando o UUID + autorização adicional.

**Payload sanitizado final:**
```json
{
  "user_id": "<uuid>",
  "tenant_id": "<uuid>",
  "cliente_id": "<uuid>",
  "categoria_dado_acessado": "pii_identificadora",
  "finalidade": "atendimento_pos_venda",
  "recurso": {"tabela": "clientes_cliente", "id": "<uuid>"},
  "ip_hash": "sha256:...",
  "timestamp": "2026-05-18T14:32:11Z"
}
```

---

#### R2 — `finalidade` precisa enum próprio de **finalidades de acesso**, distinto das 4 bases legais (BLOQUEANTE)

O plano não especifica o enum e o catálogo `finalidades-lgpd.md` lista **bases legais** (`execucao_contrato`, `obrigacao_legal`, `interesse_legitimo`, `consentimento`). **Misturar os dois é erro categorial:**

- **Base legal LGPD** responde "por que é lícito tratar este dado?" — 4 valores fechados (art. 7º I/II/V/IX).
- **Finalidade de acesso** responde "por que ESTE usuário consultou ESTE cliente AGORA?" — operacional, granular.

Toda visualização de dado de cliente cai em **`execucao_contrato`** (base legal — já gravado em `authz_decisions.purpose` quando ABAC entrar Wave A). Mas pra fiscalização ANPD precisar saber **qual ato operacional** justificou — senão "execução de contrato" vira carta branca pra olhar 1000 clientes/dia.

**Enum sugerido `finalidade_acesso_dados_cliente` (cravar no MVP-1; estensível Wave A):**

| Código | Quando o atendente/técnico escolhe |
|---|---|
| `atendimento_pos_venda` | Cliente liga/aparece presencial, atendente abre a 360° pra contextualizar |
| `preparar_orcamento` | Pré-venda — vendedor consulta histórico pra dimensionar proposta |
| `executar_os` | Técnico em campo abre cliente pra confirmar contato/endereço/equipamentos |
| `emitir_documento_fiscal` | Faturamento abre 360° pra validar dado antes de NF-e/certificado |
| `cobranca_inadimplencia` | Financeiro consulta antes de acionar cobrança |
| `auditoria_interna` | RT, gestor ou auditor revisa por amostragem (sempre logado, INV-001) |
| `atendimento_lgpd_titular` | Titular exerceu art. 18 (acesso/correção/portabilidade) — consulta é a resposta |
| `investigacao_incidente` | Suporte SaaS Aferê em sessão RAT-15 (consentimento admin tenant) — única finalidade que admite user_id de operador Aferê |

**Regras de validação:**
- Campo obrigatório (NOT NULL).
- UI obriga seleção antes de carregar a 360° — não há "default invisível".
- Valor `atendimento_lgpd_titular` cruza com tabela `lgpd_solicitacoes` (futura — Wave B); audit registra solicitação_id.
- Valor `investigacao_incidente` exige `support_session_id` válida (RAT-15) — sem sessão, o hook bloqueia.
- Hook futuro `purpose-acesso-validator.sh` (Wave A) impede valor fora do enum em código novo.

**Onde mora:** seed em `docs/conformidade/comum/finalidades-acesso-dados.md` (criar — irmão de `finalidades-lgpd.md`); modelo Python `class FinalidadeAcessoCliente(TextChoices)`.

---

#### R3 — Roldão/operador Aferê **NÃO PODE** ler `acessos_dados_cliente` direto (BLOQUEANTE)

A pergunta original sugeria "Roldão Aferê (operador) deve ter acesso? Em que cenário?". Resposta jurídica: **NÃO, exceto via RAT-15 (Suporte SaaS) com consentimento explícito do admin do tenant**.

**Por quê:**
- Aferê é **operador** (LGPD art. 5º VII); tenant é **controlador** (art. 5º VI). RAT-03 cravado.
- Log de quem-viu-o-quê do tenant É DO TENANT, não do Aferê. Operador lê = vazamento contratual + risco art. 18 II.
- Mesmo Roldão sendo dono do Aferê **e** dono do primeiro tenant (Balanças Solution — dogfooding), são **personas distintas**: como dono-do-tenant ele acessa via login do tenant (admin); como operador Aferê **não acessa** — caso contrário, fura o desenho pra todos os outros tenants futuros e o produto vira indefensável regulatoriamente.

**Matriz de quem vê `audit_trail.acessos_dados_cliente`:**

| Perfil | Acesso | Como | Base legal |
|---|---|---|---|
| `admin_tenant` (admin do tenant proprietário) | SIM | UI nativa "Quem acessou meus clientes" (módulo `lgpd-portal` Wave B) | Direito do controlador (art. 5º VI) |
| `rt_signatario` / `tecnico` / `atendente` do tenant | NÃO | — | Sem necessidade operacional (art. 6º III) |
| `cliente_externo_leitura` (cliente final do tenant) | SIM, apenas linhas onde `cliente_id = seu_próprio_id` | Portal cliente — Wave B | Art. 18 II — saber quem tratou seus dados |
| Roldão como operador Aferê | NÃO em produção; SIM via sessão RAT-15 com consentimento admin tenant + audit reforçado | Suporte SaaS — incidente/bug crítico | Art. 7º V (contrato Aferê↔tenant) + art. 7º I (consentimento admin) |
| Roldão como admin do Balanças Solution (dogfooding) | SIM | Login normal no tenant | Direito do controlador no SEU tenant |
| Auditor Família 5 (auditor IA) | Apenas amostras anonimizadas + métricas agregadas | Pipeline auditor | Legítimo interesse Aferê (qualidade) + LGPD art. 6º V — sem PII bruta |
| ANPD / autoridade | Mediante requisição formal | Plano-de-controle, registrado em audit WORM | Obrigação legal (art. 7º II) |

**Implementação MVP-1 (US-CLI-002):**
- Endpoint `GET /api/v1/clientes/{id}/visao-360/` retorna 200 só pros 4 perfis listados em T-CLI-033 (todos do tenant).
- Endpoint de **leitura do próprio audit** (`GET /api/v1/audit/acessos-cliente/{cliente_id}/`) **NÃO** é escopo desta US — entra em US futura do módulo `lgpd-portal` (Wave B). Registrar como contrato futuro no plano (R5 abaixo).
- Hook `authz-check` (já ativo) bloqueia chamada do operador Aferê a esses endpoints sem sessão RAT-15 ativa.

---

#### R4 — Retenção do `acessos_dados_cliente` segue matriz "audit trail", NÃO Marco Civil nem retenção do Cliente

A pergunta original lista 3 opções (Marco Civil 6m mín, retenção Cliente 5+a, `obrigacao_legal`). Resposta jurídica: **nenhuma das 3 isoladamente — segue `retencao-matriz.md` §2 linha "Audit trail (toda ação de usuário)"** com agravante.

**Análise das opções rejeitadas:**
- **Marco Civil art. 15 (6 meses mín)** — aplica a provedores de aplicação para **log de acesso a aplicação** (login). Visualização de PII de cliente final NÃO é log de acesso à aplicação; é registro LGPD específico (INV-013 + cl. 4.2 ISO 17025). Marco Civil é piso, não teto.
- **Retenção do Cliente (vigência contrato + 5 anos)** — errada. Cliente pode ser excluído (soft-delete US-CLI-005) e o audit do acesso a ele continua sendo prova jurídica de quem viu antes da exclusão.
- **`obrigacao_legal` puro** — base certa, prazo errado se não quantificado.

**Prazo correto:**

| Camada | Prazo | Local | Base |
|---|---|---|---|
| Quente (consulta operacional admin tenant) | 90 dias | PG | Performance |
| Frio (audit trail geral) | 2 anos | B2 frio | `retencao-matriz.md` §2 "Audit trail" |
| WORM (audit reforçado — paths sensíveis OU `categoria_dado_acessado = pii_sensivel`) | 5–10 anos | B2 WORM | `retencao-matriz.md` §2 "Audit trail ações sensíveis" + ISO 17025 cl. 4.2 |
| ISO 17025 (acesso a dado vinculado a certificado emitido) | **~25 anos** | B2 WORM (cifrado chave KMS tenant) | ISO 17025 cl. 8.4 — rastreabilidade da custódia |

**Ação fim de prazo:** crypto-shredding via destruição da chave KMS do tenant. NUNCA UPDATE/DELETE em WORM (INV-001 + trigger anti-mutation).

**Decisão MVP-1 simplificada (cravar no plano):** 5 anos B2 WORM uniformes (segue `retencao-matriz.md` linha "Audit trail ações sensíveis em paths sensíveis"). Refinamento das 4 camadas vira Wave B quando volume justificar tier de storage.

---

#### R5 — Art. 18 II (titular direito saber quem tratou) é contrato futuro Wave B — registrar como dependência

LGPD art. 18 II: titular tem direito de saber **quais agentes de tratamento** acessaram seus dados. Operacionalização típica: portal exposto pro titular consultar próprio log.

**Por quê NÃO entra no US-CLI-002 mas PRECISA ser registrado:**

- Titular final NÃO tem login no Aferê em MVP-1 — Portal Cliente (Wave B `portal-cliente`) é onde isso vai morar.
- Mas a **modelagem da tabela** `acessos_dados_cliente` precisa **suportar a consulta futura sem migration disruptiva**. Já está: `cliente_id` indexado, `categoria_dado_acessado` permite filtrar exposição, `recurso` JSONB permite expandir. Schema atual cobre.
- O que **falta no plano**: registrar como **contrato futuro** que `portal-cliente.minha-trilha-de-acesso` consumirá esta tabela. Senão, daqui 18 meses alguém esquece e cria tabela paralela.

**Adicionar ao plano US-CLI-002 (seção "Contratos futuros"):**

> **Contrato futuro Wave B `portal-cliente`** — endpoint `GET /portal/api/v1/minha-trilha-de-acesso/` retorna linhas de `audit_trail.acessos_dados_cliente` filtradas por `cliente_id = sessão.cliente_id`, sem expor `user_id` cru (anonimizar para "Atendente A / Técnico B / Sistema" — operador Aferê NUNCA aparece nessa tela, sempre rotulado "Suporte Aferê - sessão #N" com link pro contrato DPA). Resposta inclui `categoria_dado_acessado` + `finalidade` + `timestamp` — cumpre art. 18 II.

**Diferimento autorizado** porque (a) MVP-1 dogfooding-only (memória `project_sem_cliente_externo_agora`), (b) ANPD não fiscaliza Aferê diretamente (operador), (c) tenant pode responder titular manualmente em prazo razoável (15 dias úteis) consultando admin UI.

---

### Não-ressalvas (validadas como corretas)

- ✅ **Audit síncrono ANTES de renderizar** (AC-CLI-002-3) — correto. Fire-and-forget perde evento + prova jurídica (`isolamento-multi-tenant.md` §9.7).
- ✅ **`ip_hash` em vez de IP cru** — correto. LGPD art. 6º III (necessidade) + art. 5º II — IP é PII identificadora; hash basta pra investigação.
- ✅ **Trigger PG anti-mutation** (T-CLI-031) — correto. INV-013 estendida + INV-001. Cobertura pelo hook `audit-immutability-check`.
- ✅ **RLS pattern v2** (T-CLI-031) — correto. Isolamento cross-tenant (INV-TENANT-001).
- ✅ **Reusar tabela `auditoria` como timeline source** (T-CLI-034) — correto. Não há leitura nova de dado sensível; só agregação cronológica do que já está auditado.

---

## Enum sugerido cravado — `FinalidadeAcessoCliente`

```python
# src/infrastructure/audit/enums.py
from django.db import models

class FinalidadeAcessoCliente(models.TextChoices):
    ATENDIMENTO_POS_VENDA = "atendimento_pos_venda", "Atendimento pós-venda"
    PREPARAR_ORCAMENTO = "preparar_orcamento", "Preparar orçamento"
    EXECUTAR_OS = "executar_os", "Executar OS"
    EMITIR_DOCUMENTO_FISCAL = "emitir_documento_fiscal", "Emitir documento fiscal"
    COBRANCA_INADIMPLENCIA = "cobranca_inadimplencia", "Cobrança/inadimplência"
    AUDITORIA_INTERNA = "auditoria_interna", "Auditoria interna"
    ATENDIMENTO_LGPD_TITULAR = "atendimento_lgpd_titular", "Atendimento LGPD (art. 18)"
    INVESTIGACAO_INCIDENTE = "investigacao_incidente", "Suporte Aferê (RAT-15)"
```

Seed canônico em `docs/conformidade/comum/finalidades-acesso-dados.md` (criar como T-CLI-037 do plano).

---

## Matriz de retenção resumida (R4)

| Camada | Prazo | Local | Acionamento |
|---|---|---|---|
| MVP-1 simplificado | **5 anos** | B2 WORM (chave KMS tenant) | Default cravado agora |
| Wave B refinado | 90d quente + 2a frio + 5–10a WORM + 25a se vinculado a certificado | PG + B2 frio + B2 WORM | Quando volume justificar tier; ação fim de prazo = crypto-shredding |

**Fim de prazo:** sempre crypto-shredding (destruição chave KMS tenant) — nunca UPDATE/DELETE em WORM. Drill a adicionar: DRILL-RET-11 (acesso 360° de 2026 lido em 2031 deve estar legível; acessível em 2046 só se cliente teve certificado ISO emitido).

---

## Análise por área

### LGPD / Privacidade

- **Base legal do log de visualização:** art. 7º II (obrigação legal — INV-013/cl. 4.2 ISO 17025) + art. 7º V (execução de contrato — boa prática auditável). Não é "consentimento" — titular não escolhe, é obrigação do controlador.
- **Categoria do dado tratado no audit:** o audit em si é PII (`user_id` é PII do operador) — entra como **RAT-08 (audit trail)** já catalogado. Esta US **não cria RAT novo**; usa o existente.
- **Art. 18 II (saber quem tratou):** contrato futuro Wave B (R5).
- **Art. 19 (informações ao titular):** o tenant (controlador) responde solicitações em 15 dias úteis — Aferê provê a UI de consulta + relatório exportável (admin tenant Wave A; titular Wave B).
- **Crypto-shredding:** chave KMS do tenant destrói o audit junto com os demais dados. Drill DRILL-RET-06 já cobre.

### Contratual

- DPA tenant↔Aferê deve ter cláusula expressa: "Aferê mantém audit trail de acessos a dados de clientes finais, acessível ao admin do tenant; Aferê não lê esse audit fora de sessão Suporte SaaS RAT-15 com consentimento explícito do admin do tenant" (incorporar a `dpa-modelo.md` antes do primeiro tenant pago — pendência conhecida).

### Regulatório (ANPD)

- **Res. CD/ANPD 15/2024 (incidente):** se invasão extrair PII de cliente final, o `acessos_dados_cliente` é a evidência primária pra reportar quantos titulares afetados — `categoria_dado_acessado` permite estimar gravidade (PII identificadora vs sensível muda prazo de notificação).
- **Res. CD/ANPD 18/2024 (DPO):** quando V2 ativar DPO Aferê voluntário, este audit é evidência operacional do programa de privacidade.

### ISO 17025 cl. 4.2 (confidencialidade)

- Cobertura INV-013 reforçada — log de visualização "incluindo admins" cobre cláusula 4.2.
- Vinculação com módulo `certificados` (Wave A): acessos a cliente que tem certificado emitido vão pra retenção 25 anos.

---

## Riscos identificados

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Audit sem `categoria_dado_acessado` — ANPD pergunta gravidade do incidente e não dá pra estimar | Alta sem R1 | Falha na notificação 72h Res. 15/2024 | R1 — campo obrigatório no schema |
| `recurso` com PII cru — crypto-shredding impossível em WORM | Alta sem R1 | NC LGPD art. 18 VI em 2031+ | R1 — JSONB sem PII bruta, só UUID |
| `finalidade` virar carta branca "execução de contrato" | Alta sem R2 | Acesso indiscriminado + NC art. 6º III | R2 — enum operacional cravado, UI obriga seleção |
| Operador Aferê lê audit do tenant sem cláusula DPA | Média sem R3 | Quebra contratual + risco art. 18 II | R3 — `authz-check` bloqueia + DPA explícito + RAT-15 |
| Confusão de retenção (Marco Civil 6m vs Cliente 5a vs ISO 25a) | Média sem R4 | Eliminação prematura de evidência OU retenção excessiva (NC art. 16) | R4 — segue `retencao-matriz.md` audit trail, 5a default MVP-1 |
| Esquecer art. 18 II Wave B — tabela vira incompatível | Baixa | Migration disruptiva Wave B | R5 — contrato futuro registrado no plano |
| Atendente seleciona `auditoria_interna` por padrão pra todo acesso | Alta sem hook | Audit polui, métricas distorcidas | Hook `purpose-acesso-validator` Wave A + dashboard de drift |

---

## Próximos passos

- ✅ Aplicar R1–R5 no plano `US-CLI-002.md` (autoria: agente que implementar — tech-lead ou implementador).
- ✅ Adicionar **T-CLI-037**: criar `docs/conformidade/comum/finalidades-acesso-dados.md` com enum cravado + seed Python `FinalidadeAcessoCliente`.
- ✅ Adicionar **T-CLI-038**: registrar contrato futuro Wave B no plano (seção "Contratos futuros" — endpoint titular art. 18 II).
- ✅ Adicionar **AC-CLI-002-4** (sugestão): "audit grava `categoria_dado_acessado` + `recurso` JSONB sem PII; nunca grava nome/CPF/email do cliente em texto cru".
- ✅ Adicionar **teste** ao T-CLI-036: `test_audit_acesso_jamais_grava_pii_cru_no_recurso` (regex check no payload — falhar se aparecer CPF/email/nome).
- ⚠️ **Antes do go-live público:** advogado humano com OAB ativa revisa o enum `FinalidadeAcessoCliente` + texto exibido ao titular no portal Wave B (art. 18 II) — estimar 1–2h de revisão.
- ⏳ Diferido pra Wave A: hook `purpose-acesso-validator.sh` (impede valor fora do enum em código novo).
- ⏳ Diferido pra Wave B: módulo `lgpd-portal` — endpoint `minha-trilha-de-acesso` pro titular (art. 18 II).
- ⏳ Diferido pra Wave B: refinamento das 4 camadas de retenção (PG quente / B2 frio / B2 WORM / WORM 25a-vinculado-a-certificado).

---

## Referências normativas usadas

- Lei 13.709/2018 (LGPD) — art. 5º I/II/VI/VII, 6º III/V/VI, 7º I/II/V/IX, 16 I/II, 18 II/VI, 19
- Marco Civil da Internet (Lei 12.965/2014) — art. 15 (analisado e descartado como piso, não teto — R4)
- Res. CD/ANPD 15/2024 — incidentes (`categoria_dado_acessado` alimenta notificação 72h)
- Res. CD/ANPD 18/2024 — DPO
- ISO/IEC 17025:2017 cl. 4.2 (confidencialidade) + cl. 8.4 (retenção)
- INV-001, INV-013, INV-AUTHZ-002, INV-TENANT-001/002 (`REGRAS-INEGOCIAVEIS.md`)
- RAT-03, RAT-08, RAT-15 (`docs/conformidade/comum/lgpd-rat.md`)
- `docs/conformidade/comum/finalidades-lgpd.md` (catálogo de bases legais — distinto deste enum)
- `docs/conformidade/comum/retencao-matriz.md` §2 (linha "Audit trail")
- `docs/conformidade/comum/isolamento-multi-tenant.md` §8.1 (schema canônico tabela `acessos_dados_cliente`)
