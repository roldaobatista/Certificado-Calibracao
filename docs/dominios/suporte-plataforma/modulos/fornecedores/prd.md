---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fornecedores
dominio: suporte-plataforma
---

# PRD — Módulo Fornecedores

> **Wave C** explicitamente. Não entra em MVP-1 nem Wave A/B. Documentado agora para garantir coerência futura.

## 1. O que este módulo é

Cadastro de fornecedores do tenant + processo de cotação paralela + pedido de compra + avaliação. Permite ao comprador (P-SUP-03) cotar peça com 3+ fornecedores ao mesmo tempo, comparar respostas, escolher e formalizar compra. Mantém histórico de preço por fornecedor/item e avaliação após entrega. **OP14 — NOVA**.

## 2. Por que existe

- OP14 (cotação multi-fornecedor + histórico) — *NOVA*
- Dor mapeada (P-SUP-03): "fornecedor me dá preço A; entrega com preço B"; "esqueci de renovar contrato — fornecedor parou de entregar"
- Sem o módulo: comprador usa Excel paralelo → perde histórico, sem comparativo objetivo.

## 3. Personas

Ver `personas.md` + `../../personas.md` (P-SUP-03 comprador, P-SUP-06 fornecedor externo V2).

## 4. Escopo (o que ESTÁ — em Wave C)

- CRUD de fornecedor (CNPJ, razão, contatos, categorias, status, dados bancários, condições padrão)
- Homologação: checklist de documentos antes de ativar
- Cotação: criar pedido de cotação para N itens; enviar para M fornecedores (e-mail/WhatsApp/portal V2)
- Resposta de cotação: registrar preço + prazo + condições
- Comparativo de cotação: tabela lado-a-lado + escolha justificada
- Pedido de compra: formaliza após escolha; vira contas a pagar (integra com Financeiro)
- Avaliação pós-entrega: nota em prazo, qualidade, preço; média rolling 12m
- Histórico de preço por (fornecedor, item)
- Alerta: contrato/credenciamento vencendo

## 5. Non-goals

- NÃO recebe NF eletrônica direto do SEFAZ (Financeiro/integração fiscal)
- NÃO faz contas a pagar (Financeiro)
- NÃO controla saldo de estoque (Estoque — recebe da nota)
- NÃO emite NF de saída (Financeiro)
- NÃO faz marketplace público de fornecedores (V3 talvez)

## 6. User Stories

### US-FOR-001: Cadastrar e homologar fornecedor

**Como** comprador, **quero** cadastrar e homologar fornecedor, **para** ativá-lo como apto.

- **AC-FOR-001-1**: GIVEN CNPJ válido + razão + contato, WHEN salvo, THEN fornecedor é criado com status=em_homologacao.
- **AC-FOR-001-2**: GIVEN checklist de documentos completo (contrato social, comprovante bancário, certidões), WHEN homologo, THEN status=ativo.

### US-FOR-002: Cotação em paralelo

**Como** comprador, **quero** cotar 5 peças com 3 fornecedores ao mesmo tempo, **para** comparar preços.

- **AC-FOR-002-1**: GIVEN seleciono 5 itens + 3 fornecedores, WHEN crio cotação, THEN sistema envia (e-mail/WhatsApp) e gera link único de resposta por fornecedor.
- **AC-FOR-002-2**: GIVEN fornecedor responde via link, WHEN preencho preço/prazo/condição por item, THEN resposta entra no comparativo.

### US-FOR-003: Comparativo + escolha justificada

**Como** comprador, **quero** ver comparativo + escolher fornecedor com motivo, **para** ter trilha de auditoria.

- **AC-FOR-003-1**: GIVEN 3 respostas, WHEN abro comparativo, THEN vejo tabela com preço/prazo/condição por item por fornecedor; melhor preço destacado.
- **AC-FOR-003-2**: GIVEN escolho fornecedor que NÃO tem menor preço, WHEN confirmo, THEN sistema exige justificativa (categoria + texto livre).

### US-FOR-004: Pedido de compra

**Como** comprador, **quero** gerar pedido de compra após escolha, **para** formalizar e enviar.

- **AC-FOR-004-1**: GIVEN cotação escolhida, WHEN crio pedido, THEN sistema gera PDF + envia ao fornecedor + dispara evento pra Financeiro (contas a pagar futuro).

### US-FOR-005: Avaliação pós-entrega

**Como** comprador, **quero** avaliar fornecedor após entrega, **para** medir desempenho.

- **AC-FOR-005-1**: GIVEN entrega registrada no Estoque, WHEN abro avaliação, THEN preencho notas (prazo, qualidade, preço) + comentário; média rolling 12m atualiza.

### US-FOR-006: Histórico de preço

**Como** comprador, **quero** ver gráfico de preço de uma peça por fornecedor ao longo do tempo, **para** negociar.

- **AC-FOR-006-1**: GIVEN item X, WHEN abro histórico, THEN vejo linhas por fornecedor com pontos de cotação aceita.

## 7. Métricas

Ver `metricas.md`.

## 8. NFR

- Performance: comparativo p95 ≤ 1.5s
- Segurança: link de resposta de cotação é token de uso único, expira em 7 dias
- LGPD: contato pessoal de fornecedor tem base legal "execução de contrato"

## 9. Glossário

Ver `glossario.md`.
