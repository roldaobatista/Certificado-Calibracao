---
owner: agente-ia
revisado-em: 2026-06-11
proximo-review: 2026-09-11
status: stable
diataxis: reference
audiencia: [agente, auditor, tech-lead, advogado]
frente: produtos-pecas-servicos
tipo: spec-faseamento
relacionados:
  - docs/faseamento/produtos-pecas-servicos/T-PPS-000-investigacao.md
  - docs/faseamento/plano-dependencia-sistema.md
  - docs/dominios/suporte-plataforma/modulos/produtos-pecas-servicos/prd.md
  - docs/dominios/suporte-plataforma/modulos/produtos-pecas-servicos/modelo-de-dominio.md
  - docs/faseamento/configuracoes-sistema/spec.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-3-padroes.md
---

# Spec de faseamento — frente `produtos-pecas-servicos` + TabelaPreco (núcleo: catálogo + preço vigente)

> **v2 (2026-06-11)** — incorpora P2 (`tech-lead` TL-PPS-01..16 + `advogado` ADV-PPS-01..09,
> ambos **APROVA COM CORREÇÕES**, zero CRÍTICO). Log de incorporação em §10.
>
> **Escopo:** catálogo central do tenant (4 tipos: produto/peça/serviço/kit) com
> **preço versionado imutável** (INV-026, molde `Imposto` da frente #1) + **`TabelaPreco`
> única** (promovida de "V2" — US-OS-015 da OS avulsa exige consulta vigente fail-closed
> 422 `PrecoTabelaAusente`). Importação **CSV-only** em staging (molde M6).
> **DIFERIDOS:** saldo de estoque, custo médio, cotação fornecedor, NF, multi-canal/
> segmento, XLSX (GATE-PPS-XLSX), wire-in na OS (GATE-PPS-WIREIN-OS — **bloqueante
> pré-1º tenant externo**), consumo por orcamentos (frente #5).

## 1. Por que agora (dependency-first)

Frente #2 da ordem cravada: `orcamentos` (#5, GATE A-ORC-001 do próprio PRD) e
`precificacao` (#3) não existem sem catálogo + preço vigente; `estoque` precisa de SKU
canônico (BIG-12). **Conflito de wave RESOLVIDO:** `faseamento-modulos.md:95` dizia Wave B;
PRD de orçamentos exige Wave A → **sobe pra Wave A** (emenda P3/P8).

## 2. Seam pronto / o que NÃO reconstruir (T-PPS-000 §2)

| Tema | Dono existente | Decisão |
|------|----------------|---------|
| Snapshot de preço na OS (`valor_unitario_snapshot`) | `ordens_servico` ✅ | NÃO tocar — esta frente cria a FONTE. **Estado atual DECLARADO (TL-PPS-06): o valor vem do request body do caller (`ordens_servico/views.py:507`); o 422 de US-OS-015 hoje é simulado por `valor ≤ 0`. Tolerável em dogfooding; mass-assignment de preço com tenant externo → GATE-PPS-WIREIN-OS bloqueante pré-1º tenant externo** |
| `amount` da NFS-e | `fiscal` (input do caller) ✅ | NÃO tocar — orçamentos pluga depois |
| Imposto vigente | `configuracoes_sistema` ✅ | seam pronto; consumo real é da `precificacao`/fiscal — NÃO entra no núcleo |
| VO `JanelaVigencia` (ADR-0030) | `domain/shared` ✅ | REUSAR |
| Idempotência/RLS v2/authz/observabilidade/eventos WORM | infra F-A..F-C2 ✅ | molde — zero padrão novo |
| Molde linha imutável + exclusion + one-shot (`Imposto` 0003/0004) | frente #1 ✅ | REUSAR completo (trigger Padrão B + revogação + block DELETE) |
| Registro app + conftest seed | molde fiscal/configuracoes ✅ | copiar (achatado → sem `_APP_MODULE_SUBPATH`) |
| Hook `csv-safety-import` + staging não-auto-persiste (M6 INV-ECMC-007) | ✅ | REUSAR na importação |

## 3. Escopo — US do PRD cobertas (núcleo)

| US do PRD | O que entra AGORA | O que difere |
|-----------|-------------------|--------------|
| **US-CAT-001** cadastrar peça | `ItemCatalogo` (4 tipos) + versão 1 com preço; AC-001-1; AC-001-2 (código duplicado → 409 PT) | categoria hierárquica (string simples no núcleo) |
| **US-CAT-002** atualizar preço sem afetar histórico | nova `ItemCatalogoVersao` imutável (INV-026); consulta com `data_referencia`; AC-002-1/2 + **proteção anti-retroativa TL-PPS-08** | recálculo de orçamentos abertos (consumidor futuro de `Catalogo.PrecoAlterado`) |
| **US-CAT-003** criar kit | `KitComposicao` (anti-ciclo estrutural: filho ≠ kit); preço manual OU soma como **default sugerido na criação** (AC-003-1) | kit dinâmico/condicional |
| **US-CAT-004** importar planilha | **CSV-only** (dialeto Excel BR: `;` + vírgula decimal + BOM) em staging RASCUNHO, aceite POR LINHA reusando o use case canônico; colunas fora do layout fixo são DESCARTADAS no parse (ADV-PPS-06) | **XLSX = GATE-PPS-XLSX** (dep openpyxl — DEP-001; "salvar como CSV" resolve onboarding); mapeamento configurável |
| **US-CAT-005** inativar item | `status=inativo` (ADR-0031; AC-005-1) | — |
| **TabelaPreco (promovida de V2)** | `TabelaPreco` (única por tenant no MVP — `eh_padrao` UNIQUE parcial) + `LinhaTabelaPreco` imutável; porta `preco_para_os` fail-closed | multi-tabela por cliente/segmento (frente #3/V2) |

## 4. Non-goals (núcleo)

Os 5 do PRD (saldo estoque, NF, cotação fornecedor, custo médio, multi-canal) + de
faseamento: SEM retrofit dos snapshots da OS; SEM cálculo de imposto; SEM UI; SEM vínculo
metrológico; SEM outbox (eventos só na cadeia hash — GATE-PPS-OUTBOX-ESTOQUE promove
`ItemCadastrado`/`PrecoAlterado` a outbox `_schema_version: v1` quando estoque/orçamentos
chegarem — TL-PPS-05). **No núcleo só `kit` e `servico` têm regra própria
(`controla_estoque=false` default); `produto`×`peca` são rótulos sem comportamento
distinto — NÃO inventar regra (TL-PPS-14).**

## 5. Entidades + invariantes do núcleo (pós-P2)

- **`ItemCatalogo`** — id, tenant_id, `codigo_interno` (imutável; **INV-PPS-CODIGO-UNICO**
  UNIQUE `(tenant, codigo_interno)` → 409), `tipo` (imutável), codigo_fabricante?
  (identifica produto, não pessoa — não-PII, ADV-PPS-09), **`controla_estoque` (flag
  ESTRUTURAL do item, mutável com auditoria — TL-PPS-12: não é atributo temporal de
  versão)**, status (ativo|inativo — ADR-0031), criado_em. RLS v2.
- **`ItemCatalogoVersao`** — id, tenant_id, item_id, `versao_n`, nome, descricao,
  categoria, `unidade_medida` (**texto curto validado contra seed de UMs comuns —
  TL-PPS-11; enum engessaria**), `preco_padrao` (**VO `Preco`: Decimal escala 2,
  `ROUND_HALF_EVEN`, > 0 — TL-PPS-15/16**), vigência (JanelaVigencia), criado_por, motivo.
  **INV-PPS-VERSAO-IMUTAVEL** (trigger Padrão B completo, molde Imposto: campos probatórios
  imutáveis + `revogado_em`+motivo one-shot + block DELETE) + UNIQUE `(tenant,item,versao_n)`
  + **não-sobreposição por item** (exclusion `btree_gist` `WHERE revogado_em IS NULL`).
  **Densidade de `versao_n` = `max+1` sob advisory lock por item (TL-PPS-04 — UNIQUE não
  garante densidade; sem trigger de consecutividade: não é gap-less fiscal).**
  **INV-PPS-PRECO-NAO-RETROATIVO (TL-PPS-08):** criar versão exige `vigencia_inicio_nova ≥
  max(agora, inicio_da_vigente)` — encerrar a anterior NÃO pode truncar vigência já
  decorrida (consulta histórica `preco_vigente_em(D)` NUNCA muda de resposta; teste de
  regressão dedicado). Exceção única: importação inicial em item SEM versão prévia pode
  carregar vigência passada.
- **`KitComposicao`** — kit_item_id, item_filho_id (filho ≠ kit — **INV-PPS-KIT-SEM-CICLO**
  estrutural, 1 nível), quantidade. **UM derivada da versão vigente do filho (TL-PPS-11 —
  campo próprio removido: duplicaria e divergiria).**
- **`TabelaPreco`** — id, tenant_id, nome, descricao, `eh_padrao` (**única por tenant no
  MVP**: UNIQUE parcial `WHERE eh_padrao`, molde INV-037; schema já N-tabelas — D-PPS-3).
  **`LinhaTabelaPreco`** (nome cravado — TL-PPS-13) — tabela_id, item_id, `preco` (VO
  `Preco` > 0 — CHECK no banco; cortesia/desconto 100% é da frente `precificacao`,
  TL-PPS-16), vigência. **INV-PPS-LINHA-IMUTAVEL** (molde Imposto completo — decisão
  conjunta TL-(c) + ADV-PPS-04: imutabilidade é prova mais forte que auditoria de UPDATE)
  + **INV-PPS-LINHA-SEM-SOBREPOSICAO** por `(tenant,tabela,item)` (exclusion
  `WHERE revogado_em IS NULL`). **Use case composto `corrigir_linha` (revoga+recria
  ATÔMICO — TL-PPS-03: preço digitado errado é o erro nº1 de catálogo; sem caminho
  composto o operador contorna).** Kit na tabela exige **linha própria** (fail-closed
  simples; soma das partes é default sugerido na criação, nunca resolução runtime —
  TL-PPS-09 evita 422 em cascata e N+1). **Decisão consciente (emenda P9 SEG-B5):
  `criar_linha`/`encerrar_linha` de VENDA aceitam janela passada (backfill legítimo de
  política comercial já praticada) — a anti-retroatividade INV-PPS-PRECO-NAO-RETROATIVO
  cobre a LISTA; na venda, a proteção é o caller persistir as refs probatórias do
  `PrecoResolvido` (INV-026 ponto 3) + evento WORM auditando cada linha criada.**
- **Porta `preco_para_os(tenant, item_id, data_referencia) -> PrecoResolvido |
  PrecoTabelaAusente`** — resolve na TABELA PADRÃO, fail-closed, sem fallback ao
  `preco_padrao` (D-PPS-2; fallback silencioso cobraria preço não aprovado — ADV-PPS-09c).
  **`PrecoResolvido` nasce COMPLETO (TL-PPS-06/10 + ADV-PPS-05): `(item_id, item_versao_n,
  linha_tabela_id, tabela_id, preco, data_referencia, origem_preco: manual|soma_partes,
  composicao_resolvida?: [(filho, qtd, versao_n, preco)])`** — caller persiste refs junto
  do valor (INV-026 ponto 3 do modelo-de-dominio); semântica de `data_referencia` = data
  do FATO GERADOR COMERCIAL (contratação/lançamento, não faturamento — CDC art. 39 X;
  docstring + teste de contrato fixam).
- **`ImportacaoCatalogo`** — staging RASCUNHO (linhas validada|rejeitada|aceita; aceitar =
  use case canônico; one-shot; molde INV-ECMC-007). **Minimização (ADV-PPS-06): célula fora
  do layout fixo NUNCA persiste; TTL do staging 90 dias (linhas rejeitadas/abandonadas
  eliminadas); **o arquivo original NÃO é retido** (lido, hasheado e descartado na
  request — emenda P9 LGPD-B3: minimização SUPERIOR à planejada; o SHA-256 no evento
  WORM é a prova permanente de integridade).** CSV via hook `csv-safety-import`.

**Transversais:** INV-TENANT-001 (RLS v2 em todas); Idempotency-Key nos POST; sem
perfil-gating (D-PPS-7; snapshot `perfil_no_evento` automático); eventos `Catalogo.*`
PascalCase SÓ na cadeia hash (`outbox=False` — TL-PPS-05). **LGPD nos eventos WORM
(ADV-PPS-01/02): `criado_por` vira `criado_por_id_hash` (HMAC tenant, molde M5) — UUID de
usuário é pseudônimo (art. 12), não "não-PII"; `descricao`/`motivo` entram como hash
canonicalizado ADR-0029 (texto livre = PII acidental ineliminável em WORM); `nome` do item
em claro passando pelo sanitizador. Coluna operacional `criado_por` fica (art. 7º V);
parágrafo no RAT (tarefa P3).** `# lgpd-base` N/A nas entidades core (ADV-PPS-09a).

## 6. Decisões cravadas (D-PPS-*, pós-P2)

- **D-PPS-1 (FECHADA TL-(a)):** raiz achatada `src/{domain,application,infrastructure}/
  produtos_pecas_servicos/` — ADR-0072 só normatiza metrologia; PRD diz suporte-plataforma
  (aninhar em `comercial/` contradiria o PRD); precedente de mesma natureza =
  `configuracoes_sistema`. `comercial/clientes` fica assimetria conhecida.
- **D-PPS-2 (mantida; vira ADR no P3 — TL-PPS-02):** duas fontes com papéis distintos —
  `preco_padrao` = LISTA histórica imutável; `LinhaTabelaPreco` = VENDA vigente que a OS
  consulta fail-closed 422; `preco_padrao` é default sugerido na criação da linha, NUNCA
  fallback runtime. Contrato `PrecoResolvido` completo (refs + origem + composição).
- **D-PPS-3:** schema N-tabelas; MVP trava 1 via `eh_padrao` UNIQUE parcial.
- **D-PPS-4:** versão densa `max+1` sob advisory lock por item; encerrar anterior na MESMA
  transação; anti-retroatividade INV-PPS-PRECO-NAO-RETROATIVO; exclusion = verdade no banco
  (camada independente do lock — não redundante).
- **D-PPS-5:** kit 1 nível (filho ≠ kit); preço de kit na tabela = linha própria.
- **D-PPS-6:** importação CSV-only staging 90d TTL; XLSX GATE-PPS-XLSX; dialeto Excel BR
  obrigatório no parser.
- **D-PPS-7:** sem perfil-gating.
- **D-PPS-8 (nova — TL-(c)+ADV-PPS-04):** linha/versão IMUTÁVEIS molde Imposto completo +
  use case composto `corrigir_linha`/`corrigir_versao` (revoga+recria atômico).
- **D-PPS-9 (nova — TL-(e)):** eventos cadeia-hash-só; GATE-PPS-OUTBOX-ESTOQUE nomeado;
  payload já no shape do modelo-de-dominio.
- **D-PPS-10 (nova — TL-(f)):** porta nasce aqui com contrato+teste; GATE-PPS-WIREIN-OS
  **bloqueante pré-1º tenant externo** (estado atual: preço client-supplied na OS avulsa).

## 7. ADR nova exigida pela P2

**ADR-0081 — Duas fontes de preço com papéis distintos** (lista histórica imutável ×
tabela de venda vigente fail-closed; contrato `PrecoResolvido` com referências
probatórias; sem fallback runtime). Criar proposta no P3; promover no P8 (consumida
pelas frentes #3 e #5 — TL-PPS-02).

## 8. Dependências

- **Pré-requisitos (✅):** frente #1 fechada (molde Imposto/JanelaVigencia/btree_gist),
  infra F-A..F-C2, hook csv-safety-import, staging M6.
- **Consumidores a jusante (seam):** `precificacao` (#3), `orcamentos` (#5), `estoque`,
  `ordens_servico` (GATE-PPS-WIREIN-OS).

## 9. Critérios de pronto (núcleo)

Domínio puro (entidades + VO `Preco` + transições + erros + Protocols) + schema PG
(migrations RLS v2 + triggers imutabilidade versão/linha molde Imposto + exclusions +
CHECK preco>0 + grants + seed authz `catalogo.*`) + use cases (cadastrar / nova-versão
[anti-retroativa] / corrigir [revoga+recria] / montar-kit / inativar / criar-tabela /
criar-linha / corrigir-linha / encerrar-linha [one-shot — emenda P9 PROD-B3] / importar-staging / aceitar-linha / rejeitar-linha / TTL-staging) + REST
ACTION_MAP + Idempotency + porta `preco_para_os` (contrato completo + testes: vigente
resolve; ausente/revogada/kit-sem-linha-própria → PrecoTabelaAusente; histórico imutável)
+ drill `validar_produtos_pecas_servicos` + família INV-PPS-* em REGRAS + hooks P7 +
emendas cross-doc (faseamento-modulos Wave A; modelo-de-dominio [TabelaPreco promovida +
controla_estoque no item + UM derivada]; retencao-matriz [2 linhas ADV-PPS-03/06 +
DRILL-RET-PPS-01]; lgpd-rat [criado_por pseudônimo]; T-PPS-000 [LinhaTabelaPreco];
AC-CAT-004-1 [CSV-only]) + ADR-0081 aceita + matriz-reconciliação + P9 roteado.
Testes obrigatórios da P2: regressão INV-026 dura (consulta histórica não muda);
concorrência 2 criar-versão PG-real; unhappy trigger UPDATE direto; CSV dialeto BR.

## 10. P2 — revisões incorporadas (tech-lead + advogado, ambos APROVA COM CORREÇÕES)

| Achado | Sev | Incorporação |
|--------|-----|--------------|
| TL-PPS-01 | MÉD | D-PPS-1 fechada: raiz achatada (§6) |
| TL-PPS-02 | MÉD | D-PPS-2 → **ADR-0081** no P3 (§7) |
| TL-PPS-03 | ALTO | Molde Imposto COMPLETO + use case composto corrigir (D-PPS-8) |
| TL-PPS-04 | MÉD | Densidade = max+1 sob lock; declarado em §5 |
| TL-PPS-05 | BAIXO | Eventos cadeia-só + GATE-PPS-OUTBOX-ESTOQUE (D-PPS-9) |
| TL-PPS-06 | ALTO | Estado client-supplied DECLARADO (§2) + GATE-PPS-WIREIN-OS bloqueante + PrecoResolvido com refs (D-PPS-10) |
| TL-PPS-07 | BAIXO | CSV-only + dialeto Excel BR + GATE-PPS-XLSX (D-PPS-6) |
| TL-PPS-08 | ALTO | INV-PPS-PRECO-NAO-RETROATIVO + teste regressão duro (§5) |
| TL-PPS-09 | MÉD | Kit = linha própria na tabela (§5/D-PPS-5) |
| TL-PPS-10 | MÉD | PrecoResolvido de kit com composição resolvida (§5) |
| TL-PPS-11 | MÉD | UM texto+seed; composição deriva UM do filho (§5) |
| TL-PPS-12 | MÉD | `controla_estoque` move pro ItemCatalogo (§5; emenda modelo P8) |
| TL-PPS-13 | BAIXO | `LinhaTabelaPreco` cravado; emendar T-PPS-000 |
| TL-PPS-14 | BAIXO | produto×peça = rótulos; sem regra inventada (§4) |
| TL-PPS-15 | MÉD | VO `Preco` escala 2 ROUND_HALF_EVEN + teste reconciliação centavos |
| TL-PPS-16 | ALTO | `preco > 0` CHECK+VO (sentinela 0 da OS preservada) |
| ADV-PPS-01 | MÉD | `criado_por_id_hash` nos eventos WORM; RAT (tarefa P3) |
| ADV-PPS-02 | MÉD | `descricao`/`motivo` como hash ADR-0029 nos eventos; nome sanitizado |
| ADV-PPS-03 | ALTO | Linha retenção preço (CTN+CC art.205, 10a teto; NÃO 25a) + DRILL-RET-PPS-01 — minuta pronta, emenda P3 |
| ADV-PPS-04 | MÉD | Linha IMUTÁVEL confirmada (D-PPS-8) |
| ADV-PPS-05 | MÉD | PrecoResolvido com refs probatórias + data_referencia = contratação |
| ADV-PPS-06 | MÉD | Importação: descarta colunas fora do layout; TTL 90d; arquivo ≤90d cifrado + SHA-256 no evento |
| ADV-PPS-07 | BAIXO `[OAB-PRE-PROD]` | Cláusula ToS titularidade dos dados importados — lote pré-produção |
| ADV-PPS-08 | BAIXO | `origem_preco` + decomposição no contrato; claim de "economia do kit" = nota pra frente #5 |
| ADV-PPS-09 | BAIXO | Confirmações registradas (lgpd-base N/A; sem perfil-gating; fail-closed correto) |

## 11. Pendências para humano licenciado (pré-produção, não bloqueiam núcleo)

`[OAB-PRE-PROD]`: cláusula ToS de titularidade/indenidade sobre dados importados
(ADV-PPS-07 — entra no lote único ToS/DPA já existente).
