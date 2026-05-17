---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
modulo: precificacao
dominio: comercial
diataxis: explanation
---

# PRD — Módulo Precificação Inteligente

## 1. O que este módulo é

Motor central de formação de preço que combina custo real (consumido do módulo `custeio-real`), margem desejada, simulações de comissão/imposto/deslocamento/parcelamento e regras de tabela (por região, segmento, contrato) para gerar preço mínimo, preço sugerido, desconto máximo permitido e alertas de margem. Atua como **biblioteca de regras** consumida por `orcamentos`, `marketplace`, `contratos` e `os` — não emite documento próprio.

## 2. Por que este módulo existe

Sem precificação centralizada, vendedor dá desconto no olho, fecha orçamento com margem negativa e a empresa só descobre o prejuízo meses depois (quando o financeiro fecha o mês). Precificação Inteligente força transparência: ninguém pode vender abaixo do mínimo sem aprovação, e todo desconto exibe impacto na margem no momento da decisão.

## 3. Personas

Ver `personas.md` (P-PRC-01 Gestor de pricing, P-PRC-02 Vendedor que aplica preço, P-PRC-03 Aprovador de desconto) + transversais em `../../personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Formação de preço por custo (cost-plus).
- Formação de preço por margem desejada (markup ou margem líquida).
- Cálculo de preço mínimo (chão absoluto).
- Cálculo de preço sugerido (default exibido).
- Desconto máximo permitido (por item, por vendedor, por cliente).
- Margem por item + margem por orçamento consolidada.
- Simulação de comissão (% por vendedor / por tipo de serviço).
- Simulação de impostos (alíquota efetiva por regime).
- Simulação de deslocamento (custo por km × distância).
- Simulação de parcelamento (juros vs à vista).
- Alerta de orçamento abaixo da margem mínima.
- Aprovação obrigatória por faixa de desconto.
- Tabela de preço por região, por segmento, por contrato.
- Histórico de preço praticado (audit trail).
- Versionamento de tabela (toda mudança gera nova versão).

## 5. Non-goals (o que NÃO está neste módulo)

- **Cálculo de custo real** — pertence ao módulo `custeio-real` (dependência); precificação CONSOME custo, não calcula.
- **Emissão de orçamento/contrato/nota** — pertence aos respectivos módulos; precificação só fornece números.
- **Pricing dinâmico de mercado (web scraping, ML de elasticidade)** — V2.
- **Leilão/lances/preço dinâmico em tempo real** — fora.
- **Cálculo fiscal exato** — pertence à porta `fiscal` (ADR-0008); precificação faz SIMULAÇÃO estimada.
- **Re-precificação retroativa de orçamento já emitido** — proibido por INV-026.
- **Cálculo de comissão devida** — pertence ao módulo `comissoes` (RH/Financeiro); precificação só SIMULA.

## 6. User Stories

### US-PRC-001: Gestor define regra de formação de preço por item
**Como** gestor de pricing, **quero** configurar para cada item do catálogo a fórmula de preço (custo + markup OU margem líquida desejada), **para** padronizar precificação na empresa.

- **AC-PRC-001-1**: GIVEN item do catálogo, WHEN abro tela de regra de preço, THEN posso escolher modo (cost-plus / margem-alvo / preço fixo).
- **AC-PRC-001-2**: GIVEN modo "cost-plus" definido, WHEN salvo, THEN sistema lê custo do módulo `custeio-real` e calcula preço sugerido.
- **AC-PRC-001-3**: GIVEN regra publicada, WHEN salvo, THEN cria nova versão da regra (a anterior fica arquivada — INV-026).

**Non-goals desta story:** preço dinâmico hora-a-hora.

**Invariantes relacionadas:** INV-026 (mudança de regra NÃO retroage a orçamentos/OS emitidos), INV-TENANT-001.

**Dependências:** Bloqueado por: módulo `custeio-real` (custo real por serviço/produto).

### US-PRC-002: Sistema calcula preço mínimo e sugerido
**Como** sistema, **quero** dados de custo + regra de markup + alíquotas + comissão prevista, **para** calcular preço mínimo (margem zero ou definida) e preço sugerido (margem-alvo).

- **AC-PRC-002-1**: GIVEN custo R$100 + comissão 5% + imposto 10% + margem mínima 5%, WHEN calculo preço mínimo, THEN resultado = custo absorvendo todos os percentuais (fórmula documentada em `glossario.md`).
- **AC-PRC-002-2**: GIVEN mesmos parâmetros com margem-alvo 25%, WHEN calculo preço sugerido, THEN resultado > preço mínimo.
- **AC-PRC-002-3**: Recálculo é determinístico; mesmas entradas → mesmo resultado.

**Invariantes:** INV-TENANT-001.

**Dependências:** Bloqueado por: `custeio-real`, porta `fiscal`.

### US-PRC-003: Vendedor vê impacto do desconto na margem em tempo real
**Como** vendedor, **quero** que ao digitar desconto no orçamento apareça novo preço + nova margem + alerta se cair abaixo do mínimo, **para** decidir conscientemente.

- **AC-PRC-003-1**: GIVEN orçamento aberto, WHEN altero desconto, THEN vejo em < 200ms: preço novo, margem nova, % desconto, alerta visual se < margem mínima.
- **AC-PRC-003-2**: GIVEN desconto que viola limite do vendedor (ex: 20% e o limite é 10%), WHEN tento salvar, THEN sistema exige aprovação do superior antes de fechar.
- **AC-PRC-003-3**: GIVEN desconto que viola preço mínimo, WHEN tento salvar, THEN sistema BLOQUEIA (não é só aprovação — é proibição).

**Invariantes:** INV-TENANT-001.

**Dependências:** Bloqueia: US-ORC-004 (impacto na comissão).

### US-PRC-004: Aprovação obrigatória por faixa de desconto
**Como** dono / aprovador, **quero** receber notificação de desconto que excede limite, **para** decidir aprovar ou negar antes do orçamento ir ao cliente.

- **AC-PRC-004-1**: GIVEN faixas configuradas (ex: 0-10% livre, 10-20% gerente, 20%+ dono), WHEN vendedor solicita 15%, THEN gerente recebe notificação com contexto (cliente, valor, margem resultante).
- **AC-PRC-004-2**: GIVEN aprovação dada, WHEN cliente clica, THEN orçamento libera para envio.
- **AC-PRC-004-3**: GIVEN aprovação negada, WHEN é negada, THEN vendedor é notificado com justificativa.
- **AC-PRC-004-4**: Toda aprovação fica em audit trail imutável.

**Invariantes:** INV-TENANT-001.

### US-PRC-005: Tabela de preço por região / segmento / contrato
**Como** gestor de pricing, **quero** criar tabelas diferentes (ex: "Sudeste +10%", "cliente VIP -15%", "contrato anual fechado"), **para** atender realidades comerciais distintas.

- **AC-PRC-005-1**: GIVEN tabela publicada, WHEN vendedor abre orçamento, THEN sistema escolhe tabela aplicável conforme cliente/região/contrato vinculado.
- **AC-PRC-005-2**: GIVEN cliente sem tabela específica, WHEN abro orçamento, THEN aplica tabela padrão do tenant.
- **AC-PRC-005-3**: Toda alteração de tabela gera nova versão; orçamentos/OS já emitidos preservam versão da emissão (INV-026).
- **AC-PRC-005-4**: Conflito entre 2 tabelas aplicáveis: precedência documentada (contrato > segmento > região > padrão).

**Invariantes:** INV-026, INV-TENANT-001.

### US-PRC-006: Simulações no orçamento (comissão, imposto, deslocamento, parcelamento)
**Como** vendedor, **quero** ver no orçamento simulação de comissão, imposto, deslocamento e parcelamento, **para** apresentar números completos ao cliente.

- **AC-PRC-006-1**: GIVEN serviço com deslocamento, WHEN informo km, THEN sistema soma custo por km × distância (parâmetro do tenant).
- **AC-PRC-006-2**: GIVEN parcelamento solicitado, WHEN escolho 3x, 6x, 12x, THEN vejo valor da parcela e juros (taxa do tenant).
- **AC-PRC-006-3**: GIVEN simulação fiscal, WHEN orçamento é montado, THEN sistema usa porta `fiscal` para alíquota estimada por regime do cliente.
- **AC-PRC-006-4**: Simulações são CARIMBADAS no orçamento (snapshot); não recalculam depois.

**Invariantes:** INV-026.

### US-PRC-007: Alerta de orçamento abaixo da margem mínima
**Como** gestor, **quero** ser alertado em tempo real e ver dashboard de orçamentos abaixo da margem mínima, **para** intervir antes do fechamento.

- **AC-PRC-007-1**: GIVEN orçamento com margem < mínima após desconto, WHEN é salvo, THEN alerta dispara para gestor.
- **AC-PRC-007-2**: GIVEN dashboard de margem, WHEN abro, THEN vejo ranking de orçamentos pendentes por margem (do pior pro melhor).

### US-PRC-008: Histórico de preço praticado
**Como** gestor, **quero** ver para cada item/cliente o histórico de preços efetivamente fechados, **para** entender tendência e renegociar conscientemente.

- **AC-PRC-008-1**: GIVEN item, WHEN abro histórico, THEN vejo timeline de preço médio praticado nos últimos 12 meses.
- **AC-PRC-008-2**: GIVEN cliente, WHEN abro perfil de pricing, THEN vejo média de desconto concedido + comparativo com média do tenant.
- **AC-PRC-008-3**: Histórico é imutável (WORM); só leitura.

**Invariantes:** INV-026.

## 7. Métricas

Ver `metricas.md`. Resumo:
- % de orçamentos fechados com margem ≥ alvo > 70%.
- % de descontos que exigiram aprovação aprovados > 60% (sinaliza limites bem calibrados).
- Margem média realizada vs margem alvo: gap ≤ 5pp.

## 8. NFR

- **Performance:** cálculo de preço < 200ms (p95) — usado em tempo real na UI do orçamento.
- **Disponibilidade:** 99.7% (módulo bloqueador — sem precificação não tem orçamento).
- **Segurança:** regras de pricing e descontos são RBAC-controladas; SEC-PRICING (a definir — quem pode alterar tabela).
- **Auditabilidade:** toda alteração de regra/tabela/aprovação fica em audit trail imutável (WORM).
- **Determinismo:** mesmas entradas → mesmo resultado (sem aleatoriedade).

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-PRC-NNN`.
- US deprecada → marcar `@deprecated` + ADR.
- Mudança em AC já implementado → ADR + novo teste.
