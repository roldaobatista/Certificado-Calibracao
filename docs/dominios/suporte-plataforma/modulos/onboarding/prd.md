---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/suporte-plataforma/README.md
  - docs/novas funcionalidades.txt
---

# PRD — Módulo Onboarding (Implantação de Clientes)

> Product Requirements Document do módulo de Implantação e Onboarding. Baseado em `docs/novas funcionalidades.txt` linhas 1119-1140 (Adicional 1).

---

## 1. O que este módulo é

Módulo responsável pelo processo formal de implantação de novos tenants (empresas-cliente) no Aferê. Cobre cadastro guiado da empresa, assistente de configuração inicial, importação de dados (clientes, produtos, serviços, equipamentos, estoque), checklist de etapas, registro de treinamento, validação do ambiente, termo de aceite e migração do sistema antigo. Inclui ambiente sandbox/teste antes da produção.

## 2. Por que este módulo existe (problema a resolver)

> "Um sistema grande precisa de processo formal de implantação. Sem isso, cada novo cliente vira um projeto manual e desorganizado." — `novas funcionalidades.txt:1138-1139`.

Sem onboarding estruturado, cada empresa nova consome dias de configuração ad-hoc, perde dados na migração e demora a perceber valor (alto tempo até primeiro uso real).

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Cadastro guiado inicial da empresa (wizard multi-etapa).
- Assistente de configuração inicial (dados básicos, filiais, primeiros usuários, parâmetros mínimos).
- Importação inicial de clientes, produtos, serviços, equipamentos e estoque (CSV/XLSX).
- Checklist de implantação por cliente (etapas pré-definidas).
- Etapas de implantação configuráveis por cliente.
- Responsável interno (do Aferê) pela implantação atribuído.
- Status: não iniciada, em andamento, pendente do cliente, concluída.
- Treinamento inicial registrado (datas, participantes, módulos cobertos).
- Validação final do ambiente (checklist de "pronto pra produção").
- Termo de aceite da implantação (assinado pelo cliente).
- Migração de dados do sistema antigo (mapeamento de campos + execução).
- Registro de inconsistências encontradas na migração.
- Ambiente sandbox/teste isolado por tenant antes de virar produção.

## 5. Non-goals (o que NÃO está neste módulo)

- Não substitui o módulo `configuracoes-sistema` (este faz o setup INICIAL; mudanças contínuas são lá).
- Não faz cobrança/billing da implantação (módulo financeiro).
- Não gerencia tickets de suporte pós-implantação (módulo chamados).
- Não substitui treinamento contínuo (apenas registra o inicial).
- Não constrói o conector com cada sistema antigo possível — oferece template CSV/XLSX e mapeamento; conectores específicos viram US separadas se contratados.

## 6. User Stories

### US-ONB-001: Cadastro guiado da empresa

**Como** responsável interno pela implantação, **quero** preencher os dados da nova empresa-cliente em um wizard sequencial, **para** garantir que nenhuma informação crítica falte antes de habilitar o tenant.

**Critérios de aceite:**
- **AC-ONB-001-1**: GIVEN tenant recém-criado, WHEN responsável abre o wizard, THEN sistema mostra etapas: dados cadastrais, filiais, CNAE, regime tributário, primeiros usuários administradores.
- **AC-ONB-001-2**: GIVEN etapa incompleta, WHEN tenta avançar, THEN bloqueia com mensagem clara em PT-BR apontando campo faltante.
- **AC-ONB-001-3**: GIVEN wizard interrompido, WHEN responsável retorna, THEN retoma exatamente na etapa em que parou.

**Invariantes relacionadas:** `INV-TENANT-001` (toda query tem tenant_id), ADR-0002 (multi-tenancy).

---

### US-ONB-002: Importação inicial de dados

**Como** responsável pela implantação, **quero** importar clientes, produtos, serviços, equipamentos e estoque do sistema antigo via planilha, **para** evitar redigitação manual.

**Critérios de aceite:**
- **AC-ONB-002-1**: GIVEN planilha CSV/XLSX no template, WHEN responsável faz upload, THEN sistema valida estrutura e mostra prévia das primeiras 20 linhas.
- **AC-ONB-002-2**: GIVEN linhas com erro, WHEN valida, THEN gera arquivo de inconsistências (linha, campo, motivo) sem importar nada parcial.
- **AC-ONB-002-3**: GIVEN validação OK, WHEN confirma, THEN importa em lote dentro do tenant correto, gera log de inconsistências (US-ONB-007) e retorna resumo (X criados / Y duplicados / Z ignorados).

**Invariantes:** `INV-TENANT-001`, `INV-006` (idempotência em imports).

---

### US-ONB-003: Checklist de implantação por etapa

**Como** responsável, **quero** acompanhar etapas pré-definidas com status individual, **para** saber exatamente o que falta antes do go-live.

**Critérios de aceite:**
- **AC-ONB-003-1**: GIVEN nova implantação, WHEN criada, THEN sistema instancia checklist padrão (configurável globalmente) com todas as etapas em "não iniciada".
- **AC-ONB-003-2**: GIVEN etapa concluída, WHEN marcada, THEN registra data, responsável e observações; eventos `Onboarding.EtapaConcluida` disparados.

---

### US-ONB-004: Atribuir responsável interno

**Como** gestor do time de implantação, **quero** atribuir um responsável interno (do Aferê) a cada implantação, **para** ter accountability claro.

**Critérios de aceite:**
- **AC-ONB-004-1**: GIVEN implantação criada, WHEN atribuída a usuário interno, THEN ele recebe notificação e vê a implantação no seu painel.
- **AC-ONB-004-2**: GIVEN responsável trocado, WHEN reatribuído, THEN registra histórico (quem, quando, por quê).

---

### US-ONB-005: Status da implantação

**Como** gestor, **quero** ver o status agregado de cada implantação (não iniciada, em andamento, pendente cliente, concluída), **para** priorizar atenção onde está parado.

**Critérios de aceite:**
- **AC-ONB-005-1**: GIVEN checklist parcial, WHEN >0 etapas em andamento, THEN status = "em andamento".
- **AC-ONB-005-2**: GIVEN etapa aguardando ação do cliente, WHEN marcada como "aguarda cliente", THEN status agregado = "pendente cliente".
- **AC-ONB-005-3**: GIVEN todas etapas concluídas + termo assinado, WHEN última fechada, THEN status = "concluída".

---

### US-ONB-006: Registro de treinamento inicial

**Como** responsável, **quero** registrar treinamentos realizados (data, participantes, módulos cobertos), **para** comprovar que o cliente recebeu capacitação antes do go-live.

**Critérios de aceite:**
- **AC-ONB-006-1**: GIVEN treinamento ocorrido, WHEN registrado, THEN salva data, participantes (pessoas do tenant), módulos do Aferê cobertos, anexos opcionais (slides, gravações).
- **AC-ONB-006-2**: GIVEN treinamento marcado, WHEN consultado, THEN aparece na timeline da implantação.

---

### US-ONB-007: Registro de inconsistências na migração

**Como** responsável, **quero** ver TODAS as inconsistências detectadas na migração de dados, **para** decidir o que corrigir antes do go-live.

**Critérios de aceite:**
- **AC-ONB-007-1**: GIVEN importação executada, WHEN há linhas com erro ou alerta, THEN cada uma vira registro de inconsistência (severidade, descrição, dado original, sugestão).
- **AC-ONB-007-2**: GIVEN inconsistência resolvida, WHEN marcada, THEN exige justificativa e fica auditável.

---

### US-ONB-008: Validação final do ambiente

**Como** responsável, **quero** rodar checklist técnico de "pronto pra produção" (RLS ativo, KMS configurado, backup agendado, usuários criados, integrações testadas), **para** evitar virar produção com gap crítico.

**Critérios de aceite:**
- **AC-ONB-008-1**: GIVEN implantação na etapa final, WHEN responsável aciona "validar ambiente", THEN sistema roda checks automáticos (RLS, KMS, backup, integrações configuradas) e mostra resultado.
- **AC-ONB-008-2**: GIVEN qualquer check falha, WHEN tenta virar produção, THEN bloqueia com mensagem clara apontando o que falta.

**Invariantes:** `SEC-001` (RLS sempre ativo), `SEC-KMS-*` (KMS configurado por tenant).

---

### US-ONB-009: Termo de aceite da implantação

**Como** gestor, **quero** que o cliente assine termo de aceite formal, **para** marcar o fim da implantação e início da operação contratual.

**Critérios de aceite:**
- **AC-ONB-009-1**: GIVEN implantação validada, WHEN gera termo, THEN PDF contém escopo, checklist concluído, treinamentos registrados, inconsistências aceitas.
- **AC-ONB-009-2**: GIVEN termo assinado, WHEN registrado, THEN status final = "concluída" e bloqueia reabertura sem nova OS de implantação.

---

### US-ONB-010: Ambiente sandbox/teste

**Como** responsável e cliente, **quero** que cada implantação tenha ambiente sandbox isolado por tenant, **para** testar imports e configurações sem afetar produção.

**Critérios de aceite:**
- **AC-ONB-010-1**: GIVEN nova implantação, WHEN criada, THEN sandbox correspondente é provisionado com mesmo isolamento de tenant (RLS).
- **AC-ONB-010-2**: GIVEN dados validados no sandbox, WHEN responsável promove pra produção, THEN sistema copia configurações aprovadas e registra a promoção.

**Invariantes:** `INV-TENANT-001`, ADR-0002.

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Tempo médio de implantação (do cadastro ao termo) ≤ 30 dias.
- Taxa de inconsistências resolvidas antes do go-live ≥ 95%.

## 8. NFR

- **Performance:** import de até 50k linhas em ≤ 5min.
- **Segurança:** SEC-001 (RLS), SEC-KMS-* (chaves por tenant), `INV-TENANT-001`.
- **Acessibilidade:** WCAG AA no wizard.
- **Disponibilidade:** sandbox segue mesmo SLO do tenant produtivo.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-ONB-NNN`.
- Mudança em AC implementado → ADR + novo teste.
