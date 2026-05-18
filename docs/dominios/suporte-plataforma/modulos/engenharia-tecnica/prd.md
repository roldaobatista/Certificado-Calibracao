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
  - docs/adr/0006-feature-flags.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
---

# PRD — Módulo Engenharia Técnica

> Documentação técnica rastreável (desenhos, diagramas, BOM, memorial, cálculos) ligada a Projetos, OS, Orçamentos e Equipamentos. Reduz erro de montagem/manutenção e transforma conhecimento técnico em ativo do tenant.

---

## 1. O que este módulo é

Repositório versionado de **artefatos técnicos de engenharia** — desenhos CAD, diagramas elétricos, esquemas de ligação, memoriais descritivos, especificações, cálculos, BOM (lista técnica de materiais) e biblioteca de componentes — com **versionamento, aprovação técnica e rastreabilidade** ao projeto/OS/orçamento/equipamento que utilizou o artefato.

Atende empresas de automação, pesagem, calibração e manutenção que precisam reter conhecimento técnico, padronizar montagem e manutenção, e provar (para cliente ou auditoria) qual versão do desenho foi usada em qual OS.

## 2. Por que este módulo existe

Sem o módulo, desenhos e diagramas vivem em pastas de rede sem controle de versão, sem aprovação formal e sem ligação ao trabalho de campo. Resultado: técnico monta com desenho desatualizado, equipe perde o memorial descritivo do projeto entregue ao cliente, recall não consegue identificar quais equipamentos foram montados com a revisão errada do esquema.

Resolve as dores de: **conhecimento volátil** (sai com o engenheiro que muda de emprego), **erro de montagem por desenho errado** e **falta de rastreabilidade entre projeto técnico → execução em campo**.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Cadastro de **desenhos técnicos** (CAD, PDF, imagens).
- Cadastro de **diagramas elétricos** e **esquemas de ligação**.
- **BOM** (Bill of Materials / Lista Técnica de Materiais) — itens, quantidade, posição, componente.
- **Memorial descritivo** estruturado (escopo, premissas, soluções, normas aplicáveis).
- **Especificações técnicas** parametrizadas (capacidade, classe, faixa, IP, tensão).
- **Cálculos técnicos** (planilhas anexadas + campos estruturados pra valores-chave).
- **Biblioteca de componentes** reutilizáveis (modelo, fabricante, datasheet, preço referencial).
- **Versionamento de projeto** (revisão A, B, C; quem aprovou; quando).
- **Aprovação técnica** (workflow simples; pode delegar ao módulo Automações & BPM).
- **Anexos** CAD/PDF/imagem (até X MB por arquivo; storage Backblaze B2).
- **Relação** projeto técnico ↔ OS ↔ Orçamento ↔ Equipamento (rastreabilidade bidirecional).
- **Histórico de alterações** (diff de revisões; quem editou, quando, motivo).
- Marcação de revisão "obsoleta" sem deletar (norma técnica exige).

## 5. Non-goals (o que NÃO está neste módulo)

- **Não** é editor CAD — é repositório + metadados. Edição acontece em ferramenta externa (AutoCAD, Eplan, KiCad).
- **Não** é PLM (Product Lifecycle Management) industrial completo — não cobre simulação, MRP, roteiro de fabricação.
- **Não** é módulo de Gestão de Projetos (Gantt, marcos, cronograma) — esse é módulo separado.
- **Não** substitui o módulo de Calibração (procedimentos, certificados, incerteza) — apenas referencia.
- **Não** cuida de estoque de componentes — só referencia o item da Biblioteca; saldo fica em Estoque.
- **Não** cuida de cotação/compra do componente — fica em Compras.

## 6. User Stories

### US-ENG-001: Cadastrar desenho técnico com versionamento

**Como** engenheiro projetista, **quero** subir desenho CAD com metadados (cliente, projeto, revisão, normas aplicáveis), **para** ter histórico imutável de revisões e rastreabilidade.

**Critérios de aceite:**
- **AC-ENG-001-1**: GIVEN cadastro novo, WHEN subir arquivo + preencher metadados, THEN sistema cria revisão "A" + registra hash do arquivo + envia pro Backblaze B2.
- **AC-ENG-001-2**: GIVEN desenho existente, WHEN subir nova versão, THEN sistema cria revisão "B" sem apagar "A" + permite ver diff (visual no PDF, lista no BOM).
- **AC-ENG-001-3**: GIVEN revisão antiga, WHEN marcada "obsoleta", THEN não some da listagem, mas é destacada visualmente e fica fora dos filtros default.

**Non-goals:** edição inline; conversão CAD→PDF (faz upload de ambos).

**Invariantes:** `INV-001` (revisão imutável após aprovação — trilha WORM), `INV-TENANT-001`.

**Dependências:** bloqueado por ADR-0001 (storage).

---

### US-ENG-002: Aprovação técnica de projeto

**Como** engenheiro responsável técnico, **quero** aprovar formalmente uma revisão de projeto antes que vire "ativa", **para** que campo só monte com base aprovada.

**Critérios de aceite:**
- **AC-ENG-002-1**: GIVEN revisão em status "rascunho", WHEN engenheiro responsável aprova, THEN status muda pra "aprovada" + assinatura digital registrada (nome, CREA/CFT, data, IP).
- **AC-ENG-002-2**: GIVEN revisão "aprovada", WHEN tentar editar, THEN sistema impede e sugere "criar nova revisão".
- **AC-ENG-002-3**: GIVEN aprovação configurada com workflow BPM, WHEN submeter, THEN módulo Automações & BPM cria pendência (integração com `BPM.PendenciaCriada`).
- **AC-ENG-002-4**: implementa **INV-INT-012** (REGRAS-INEGOCIAVEIS.md). Resumo: revisão aprovada que altera BOM bloqueia conversão de orçamentos abertos até vendedor revalidar; OS já criada preserva snapshot. Fonte de verdade do payload/consumers: ADR-0016 fluxo 2 + REGRAS INV-INT-012.
- **AC-ENG-002-5**: implementa **INV-INT-006** (REGRAS-INEGOCIAVEIS.md). Resumo: revisão aprovada que afeta procedimento de calibração bloqueia OS em execução afetadas até RT confirmar revalidação. Fonte de verdade do payload/consumers: ADR-0014 fluxo 6 + REGRAS INV-INT-006.

**Non-goals:** A3/ICP-Brasil cert (decisão geral em ADR de assinatura; aqui pode ser assinatura interna ou ICP, conforme política do tenant).

---

### US-ENG-003: Ligar projeto técnico a OS

**Como** técnico de campo, **quero** abrir uma OS e ver qual revisão do projeto técnico devo seguir, **para** não montar com desenho velho.

**Critérios de aceite:**
- **AC-ENG-003-1**: GIVEN OS com projeto vinculado, WHEN tela da OS aberta, THEN exibe link pra revisão "aprovada" mais recente + alerta se há revisão mais nova "rascunho".
- **AC-ENG-003-2**: GIVEN OS concluída, WHEN consulta histórica, THEN exibe qual revisão exata estava ativa no momento de conclusão (snapshot imutável).

---

### US-ENG-004: Biblioteca de componentes reutilizáveis

**Como** projetista, **quero** consultar e reutilizar componentes já cadastrados (sensor X, transmissor Y), **para** padronizar projetos e não cadastrar duplicado.

**Critérios de aceite:**
- **AC-ENG-004-1**: GIVEN biblioteca, WHEN buscar "célula carga 5t aço inox", THEN lista componentes com fabricante, modelo, datasheet anexo, projetos onde foi usado.
- **AC-ENG-004-2**: GIVEN componente novo, WHEN cadastrar, THEN validação de duplicidade (fabricante + modelo) com sugestão de fundir cadastros.
- **AC-ENG-004-3**: GIVEN componente vinculado a projetos ativos, WHEN tentar deletar, THEN bloqueia e mostra projetos que referenciam.

---

### US-ENG-005: BOM (lista técnica de materiais) gerada do desenho

**Como** projetista, **quero** declarar BOM estruturado no projeto técnico, **para** que Orçamento e Estoque possam consumir a mesma lista.

**Critérios de aceite:**
- **AC-ENG-005-1**: GIVEN projeto com BOM, WHEN gerar orçamento a partir do projeto, THEN módulo Orçamentos pré-popula itens com componentes da BOM + quantidades + preço referencial.
- **AC-ENG-005-2**: GIVEN OS executada, WHEN técnico baixar materiais, THEN Estoque consulta BOM ativa do projeto da OS pra validar quantidades.

**Non-goals:** roteiro de fabricação, MRP, simulação.

---

### US-ENG-006: Memorial descritivo estruturado

**Como** engenheiro, **quero** preencher memorial descritivo em formulário estruturado (escopo, premissas, soluções, normas) em vez de doc Word solto, **para** padronizar e permitir exportar PDF consistente ao cliente.

**Critérios de aceite:**
- **AC-ENG-006-1**: GIVEN memorial vazio, WHEN preencher campos, THEN salva como JSON estruturado + permite gerar PDF com template do tenant.
- **AC-ENG-006-2**: GIVEN memorial publicado, WHEN cliente abrir link de entrega, THEN PDF assinado disponível pra download.

---

### US-ENG-007: Diff visual entre revisões

**Como** engenheiro revisor, **quero** ver lado a lado o que mudou entre revisão A e B (BOM, especificações, anexos), **para** aprovar com confiança.

**Critérios de aceite:**
- **AC-ENG-007-1**: GIVEN duas revisões selecionadas, WHEN abrir diff, THEN exibe (a) diff textual de campos estruturados; (b) lista de anexos adicionados/removidos; (c) diff de BOM (item adicionado, removido, quantidade alterada).

---

### US-ENG-008: Histórico de alterações com motivo

**Como** auditor (interno ou cliente), **quero** consultar histórico completo de alterações de um projeto técnico (quem, quando, o que, por quê), **para** rastrear conformidade.

**Critérios de aceite:**
- **AC-ENG-008-1**: GIVEN projeto com 3 revisões, WHEN abrir histórico, THEN lista cronológica com autor, timestamp, motivo declarado, link pra revisão.

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- % de OS executadas com projeto técnico vinculado = ≥ 80% (das que aplicam).
- % de revisões aprovadas dentro do SLA = ≥ 90%.
- Redução de retrabalho atribuído a "desenho errado" = -50% em 6 meses (medido em OS reclassificadas).

## 8. NFR

- **Performance:** upload de arquivo até 100MB com progress bar; busca em biblioteca < 500ms p95.
- **Disponibilidade:** SLO 99.5% (módulo de suporte; não-crítico de execução em campo se cache local OK).
- **Segurança:** assinatura de aprovação imutável (`INV-001` WORM); tenant isolation (`INV-TENANT-001`); controle de download de anexos (`SEC-LEAST-PRIV-001`).
- **Acessibilidade:** WCAG AA.
- **Storage:** Backblaze B2 (ADR-0001); criptografia em repouso via KMS (ADR-0002).

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID `US-ENG-NNN`.
- Mudança em fluxo de aprovação técnica → ADR + comunicação.
- Quebra de contrato com Orçamentos/Estoque (BOM) → ADR + janela.
