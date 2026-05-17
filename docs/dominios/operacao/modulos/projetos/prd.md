---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
modulo: projetos
dominio: operacao
---

# PRD — Módulo Gestão de Projetos

## 1. O que este módulo é

Container de trabalhos grandes que não cabem em uma única OS: instalação de balança rodoviária, reforma grande em sistema de pesagem, implantação de automação industrial. Reúne múltiplas OS, compras, técnicos, faturamentos e marcos sob um único guarda-chuva com escopo, cronograma (Gantt), etapas, marcos, budget previsto vs realizado, riscos, diário de execução, entregáveis, aceite por etapa e controle de aditivos.

## 2. Por que este módulo existe

A operação já tem OS, chamados e agenda — mas projetos grandes ficam órfãos. Sem container de projeto, custo se espalha por várias OS, etapa não tem aceite formal, aditivo é perdido e cliente não recebe relatório consolidado. Cobre Adicional 4 do `docs/novas funcionalidades.txt` (linhas 1201-1234).

## 3. Personas

Ver `personas.md` + transversais em `../../personas.md` e `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Cadastro de Projeto com cliente vinculado, escopo, datas previstas
- Etapas + marcos com responsável e prazo
- Tarefas dentro de etapas (atribuídas a pessoa)
- Cronograma com visualização Gantt
- Orçamento previsto (custo + receita) e custo realizado (vindo de OS, Compras, Estoque)
- Margem do projeto (receita − custo, atualizada conforme execução)
- Documentos do projeto (contratos, plantas, atas)
- Riscos do projeto (cadastro + plano de mitigação)
- Reuniões (ata, decisões, próximos passos)
- Diário de obra/execução (entradas datadas, anexos)
- Status do projeto (PLANEJADO | EM_EXECUCAO | PAUSADO | CONCLUIDO | CANCELADO)
- Entregáveis por etapa
- Aceite formal por etapa (assinatura cliente)
- Controle de aditivos (escopo, prazo, valor) versionando o contrato original
- Múltiplas OS dentro do projeto + agregação de custo
- Eventos `Projeto.Aberto`, `Etapa.Concluida`, `Marco.Atingido`, `Aditivo.Aprovado`, `Projeto.Concluido`

## 5. Non-goals

- Não substitui ferramenta de PMO completa (MS Project, Asana) — gestão leve focada no fluxo do tenant
- Não faz ERP financeiro completo do projeto (vai pro Financeiro)
- Não emite NF-e (Fiscal/Financeiro cuida; Projeto só dispara faturamento por etapa)
- Não faz BIM nem desenho técnico (Engenharia Técnica futura)
- Não substitui Engenharia Técnica (módulo separado, item 5 das funcionalidades)

## 6. User Stories

### US-PRJ-001: cadastrar projeto

**Como** gerente de projetos, **quero** cadastrar projeto com cliente, escopo, datas previstas e orçamento, **para** ter o container do trabalho consolidado.

**AC:**
- **AC-PRJ-001-1:** GIVEN tenant, WHEN cadastra projeto com nome+cliente+data_inicio+data_fim_prevista+orcamento_previsto, THEN sistema cria Projeto status PLANEJADO.
- **AC-PRJ-001-2:** GIVEN cliente do projeto, WHEN consulta, THEN sistema verifica vínculo (CRM) e bloqueia se cliente bloqueado financeiramente.

**Invariantes:** `INV-001`, `INV-TENANT-001`.

---

### US-PRJ-002: estruturar etapas e marcos

**Como** gerente de projetos, **quero** criar etapas sequenciais e marcos do projeto, **para** acompanhar progresso e disparar faturamento por etapa.

**AC:**
- **AC-PRJ-002-1:** GIVEN projeto PLANEJADO, WHEN adiciona etapa (nome, ordem, prazo, responsável), THEN etapa entra na linha do tempo.
- **AC-PRJ-002-2:** GIVEN etapa, WHEN marca como MARCO_DE_FATURAMENTO, THEN sistema dispara `Marco.Atingido` ao concluir.

---

### US-PRJ-003: vincular OS ao projeto

**Como** atendente/gerente, **quero** que OS abertas para este projeto fiquem vinculadas a ele, **para** que custo e progresso agreguem automaticamente.

**AC:**
- **AC-PRJ-003-1:** GIVEN projeto EM_EXECUCAO, WHEN abre OS com flag `projeto_id`, THEN OS aparece na timeline do projeto e custo agrega.
- **AC-PRJ-003-2:** GIVEN OS concluída vinculada, WHEN consulta projeto, THEN custo realizado é atualizado.

---

### US-PRJ-004: visualizar Gantt e progresso

**Como** gerente de projetos, **quero** ver Gantt + % de conclusão de cada etapa, **para** identificar atraso cedo.

**AC:**
- **AC-PRJ-004-1:** GIVEN projeto com etapas, WHEN abre Gantt, THEN sistema mostra barras por etapa (data_prev_inicio, data_prev_fim, data_real_inicio, data_real_fim, % concluído).
- **AC-PRJ-004-2:** GIVEN etapa atrasada, WHEN dispara cron, THEN sistema notifica responsável.

---

### US-PRJ-005: comparar budget previsto vs realizado

**Como** dono, **quero** ver, em tempo real, custo realizado vs previsto e margem do projeto, **para** decidir se entra em zona de prejuízo.

**AC:**
- **AC-PRJ-005-1:** GIVEN projeto com OS e compras vinculadas, WHEN consulta dashboard, THEN sistema mostra previsto, realizado, % consumido, margem atual.
- **AC-PRJ-005-2:** GIVEN realizado > 80% do previsto sem etapa equivalente concluída, THEN sistema dispara alerta P1.

---

### US-PRJ-006: registrar riscos e diário

**Como** responsável pelo projeto, **quero** cadastrar riscos (com probabilidade, impacto, mitigação) e fazer entradas diárias de execução, **para** documentar tudo e proteger juridicamente.

**AC:**
- **AC-PRJ-006-1:** GIVEN projeto, WHEN cadastra risco, THEN sistema calcula nivel_risco = probabilidade × impacto.
- **AC-PRJ-006-2:** GIVEN entrada de diário, THEN gravação é imutável (`INV-001`).

---

### US-PRJ-007: registrar aceite por etapa

**Como** gerente, **quero** aceite formal do cliente por etapa (assinatura digital opcional), **para** garantir faturamento sem disputa.

**AC:**
- **AC-PRJ-007-1:** GIVEN etapa concluída, WHEN cliente assina aceite (ou aceite registrado por gerente com evidência), THEN sistema marca ETAPA_ACEITA e libera faturamento.
- **AC-PRJ-007-2:** GIVEN aceite assinado digitalmente, THEN sistema grava assinatura + carimbo do tempo (`INV-017` quando aplicável).

---

### US-PRJ-008: controlar aditivos

**Como** gerente, **quero** registrar aditivos (escopo, prazo, valor) versionando o contrato original, **para** rastrear toda alteração.

**AC:**
- **AC-PRJ-008-1:** GIVEN projeto EM_EXECUCAO, WHEN cria aditivo com motivo + alterações, THEN sistema cria nova versão do contrato sem apagar a anterior (`INV-026` análogo).
- **AC-PRJ-008-2:** GIVEN aditivo aprovado, THEN dispara `Aditivo.Aprovado` e atualiza orçamento e data_fim_prevista.

---

## 7. Métricas

Ver `metricas.md`. Primárias: % projetos no prazo, margem média, % aceites no prazo.

## 8. NFR

- Audit log imutável (`INV-001`)
- Multi-tenant rigoroso (`INV-TENANT-001`)
- WCAG 2.1 AA (`INV-016`) — portal-cliente quando expõe Gantt/aceite
- Gantt funciona em desktop; mobile read-only no MVP

## 9. Glossário

Ver `glossario.md`.

## 10. Como evolui

US nova → próximo ID `US-PRJ-NNN`. Mudança em AC implementado → ADR.
