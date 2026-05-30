---
owner: roldao
revisado-em: 2026-05-29
status: stable
ordem-descoberta: 14/17
proximo: docs/descoberta/integracoes-externas.md
idioma: pt-BR
limite-linhas: 180
proposito: inventário de dados legados a migrar.
---

<!--
template: dados-existentes.md
destino: docs/descoberta/dados-existentes.md
uso: condicional — só se migra dados de sistema legado. Marque N/A em nao-aplica.md se greenfield.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §3 (condicional, 🔵)
limite: ≤180 linhas.
-->

# Dados existentes (migração legado) — Aferê Prumo

> Se o produto é greenfield (sem migração), marcar N/A em `docs/nao-aplica.md`.

> **Contexto (atualizado 2026-05-28 com dados reais):** a fonte principal hoje é o **Auvo** (gestão
> de field service), de onde saem exports estruturados (planilhas). Migração do Auvo → Aferê é
> **importação estruturada** (não papel solto). Volumes reais confirmados pelos arquivos em `dados-reais/`.

## 1. Inventário de fontes (volumes REAIS — fonte: exports do Auvo, 2026-05-28)

> **Números exatos (export Auvo de 28/05/2026, importados em `dados-reais/_banco/`):** 341 clientes ·
> 389 produtos com preço · 80 serviços · 429 orçamentos · 424 itens orçados. (Onde antes constava
> "342/390/~430", harmonizado para os valores exatos do banco.)

| Fonte | Sistema | Volume real | Formato | Qualidade |
|---|---|---|---|---|
| F-001 | Auvo — **clientes** (com geolocalização, contato "falar com", segmento, dados de cobrança) | **341 clientes** (~211 PJ; 169 em MT) | XLSX export | boa (estruturado) |
| F-002 | Auvo — **produtos/peças** (custo + venda + dados fiscais NCM/CFOP/CST) | **389 produtos** com preço | XLSX export | boa |
| F-003 | Auvo — **serviços** (tabela de preços, descrição NFS-e, CNAE) | **80 serviços** (muitos sem preço fixo) | XLSX export | boa |
| F-004 | Auvo — **orçamentos** + itens orçados (status, valores, observação, validade) | **429 orçamentos** / **424 itens orçados** (pipeline R$ 4,35 mi; só 10 aprovados) | XLSX export | boa |
| F-005 | Equipamentos + histórico de calibração + **prazos de vencimento** | parcial (a confirmar) | Auvo/papel | baixa — incompleto (dor H-002) |
| F-006 | Histórico de conversas/atendimento (**maioria ÁUDIO** — D-PROD-013) | 5 conversas = **1.120 áudios** transcritos; total `(A VALIDAR)` | WhatsApp | baixa — não estruturado |
| F-007 | **Conhecimento dos parceiros** (grupo nacional de balanceiros) — vocabulário do ramo, marcas/peças, problemas→soluções, preços de mercado, objeções | 946 áudios transcritos + 20.240 mensagens → consolidado agregado | WhatsApp (grupo) | não-estruturado → **agregado/anonimizado** |

> **F-007 não migra para o Aferê** (não é dado de cliente): é conhecimento **agregado e anonimizado** que alimenta o **cérebro** (`integracoes-externas.md` INT-010), classificado **restrito-interno** (D-PROD-016, R-020). Consolidado em `dados-reais/grupos/_transcricao/conhecimento-parceiros.md`; o `vocabulario-tecnico.txt` melhora o STT (INT-009).

## 2. Mapeamento campo-a-campo (high-level)

> Mapear PROPRIEDADES, não tabelas — abstração do domínio. Detalhamento técnico fica em `docs/dados/dicionario.md` em C3.

| Entidade-alvo (V1) | Fonte | Campo origem | Campo destino | Transformação |
|---|---|---|---|---|
| Cliente | F-001 | `customer_name` | `customer.name` | trim |
| Cliente | F-001 | `cpf_cnpj` | `customer.tax_id` | normalizar (sem máscara) |
| Transação | F-003 | `amount_cents` / `amount` | `transaction.amount` | converter para cents inteiros |

## 3. Qualidade dos dados

### Problemas esperados (a confirmar)
- Cadastro de clientes duplicado/incompleto entre planilhas.
- Histórico de equipamento incompleto ou só na cabeça das pessoas.
- Prazos de calibração não registrados de forma sistemática (a dor H-002).

### Plano de organização inicial
- Definir o cadastro mínimo (cliente, equipamento, serviço, prazo) — vira o modelo de dados (C3).
- Importar o que existe e completar o resto no uso (não esperar dado perfeito para começar).
- Priorizar prazos de calibração ativos (maior valor — receita recorrente).

## 4. Volume e performance

- **Total estimado**: ~1.660 registros estruturados (341 clientes + 389 produtos + 80 serviços + 429 orçamentos + 424 itens) + acervo documental (cérebro, ver `integracoes-externas.md` INT-010).
- **Estoque ≠ fluxo (reconciliação — gap da auditoria):** os **429 orçamentos** são o **acumulado histórico** no Auvo (maioria rascunho antigo nunca fechado — só 10 aprovados), **não** um volume anual; o **ritmo atual é ~30 orçamentos/semana** (H-001). Os dois números não se contradizem — um é estoque parado, o outro é a vazão semanal. A linha de base real de vazão se mede no piloto (2 semanas, H-001).
- **Tempo estimado de migração**: baixo (volume pequeno, dados já estruturados em XLSX) — `(detalhar no ADR de migração)`.
- **Janela de migração aceitável**: a migração Auvo→Aferê é **Onda −1**, antes do go-live — não há produção da IA no ar para parar.
- **Estratégia**: **one-shot** (importação estruturada XLSX→Aferê) com validação por amostra; reimportável se necessário.

## 5. Conformidade na migração

- **PII envolvida?**: <sim/não>
- **Consentimento original cobre uso novo?**: <verificar com DPO>
- **Crypto-shredding necessário?**: <se LGPD exigir>
- **Logs de auditoria da migração**: <retenção 5 anos para dados fiscais>

## 6. Plano B se migração falhar

- **Rollback**: como é one-shot com volume pequeno, manter o **Auvo intacto** (não desligar) até validar 100% no Aferê; cópia de segurança dos XLSX originais antes de importar (estão em `dados-reais/`).
- **Custo de rollback**: baixo (reimportar; o legado segue disponível durante a transição).
- **Critério de "go/no-go"**: **≥99% dos registros migrados** + amostra validada manualmente (clientes-chave, preços dos produtos mais cotados) antes de considerar o Aferê a fonte única.

## 7. Cronograma

> ⚠️ Datas-modelo antigas (todas 2026-05-28) removidas — eram placeholders. A migração é **Onda −1** e
> só ganha data quando a descoberta fechar e o ADR de migração for aberto (não antecipar).

- **Análise + amostra**: ✅ feita (dados exportados e estruturados em `dados-reais/_banco/`).
- **Script de migração pronto**: a definir (ADR de migração).
- **Dry-run em ambiente de teste**: a definir.
- **Migração em produção (Onda −1)**: a definir (antes da Onda 0/1).
- **Validação pós-migração**: migração + 7 dias.

## Critério para promover de `draft` para `stable`

- [ ] ≥1 fonte inventariada com volume e qualidade.
- [ ] Mapeamento de pelo menos as entidades-âncora.
- [ ] Plano de limpeza para os ≥3 problemas conhecidos.
- [ ] Plano B definido.
