---
owner: agentes-afere
revisado-em: 2026-06-11
status: stable
---

# T-PPS-000 — Investigação regra #0 — frente `produtos-pecas-servicos` + TabelaPreco

> P0 do ritual (2026-06-11, 2 leitores paralelos sobre código + docs). Frente #2 da
> ordem cravada em `docs/faseamento/plano-dependencia-sistema.md`. Consome os seams da
> frente #1 `configuracoes-sistema` (FECHADA 2026-06-11).

## §1. Estado real do código (greenfield confirmado)

**Zero código de catálogo/produto/peça/serviço/TabelaPreco hoje.** Só existem
*consumidores de preço pronto* (snapshot no momento do evento, Padrão B):

- `src/domain/operacao/os/entities.py:68` — `AtividadeSnapshot.valor_unitario_snapshot`
  (Decimal; US-OS-015 + INV-CLI-PRICE-001).
- `src/infrastructure/ordens_servico/models.py:99-110` — `OS.valor_total`/
  `valor_total_atualizado` (vêm do orçamento; `orcamento_origem_id` FK
  `db_constraint=False` "até módulo Orcamentos chegar", linha 57-61).
- `src/application/fiscal/emitir_nfse.py:50` — `amount_centavos` = input do caller
  (seam declarado no fechamento da frente fiscal: "orçamentos diferido").

**Padrão consagrado:** preço NASCE a montante e é snapshotado imutável a jusante —
a frente #2 cria a FONTE (catálogo + tabela vigente), não mexe nos snapshots.

## §2. Seams prontos (consumir, não recriar)

| Seam | Onde | Uso pela frente #2 |
|---|---|---|
| `imposto_vigente_em(impostos, tipo, filial_id, momento)` | `src/domain/configuracoes_sistema/transicoes.py:102` | preço com imposto por item/NF futura; **1º caller de produção** (fecha nota B16/N2 da auditoria P9 config) |
| `DjangoImpostoRepository.listar(tenant_id, tipo?, filial_id?)` | `src/infrastructure/configuracoes_sistema/repositories.py:97` | idem |
| `reservar_numero` (2 regimes ADR-0080) | `src/infrastructure/configuracoes_sistema/repositories.py:173` | não-essencial no núcleo (catálogo não numera documento) |
| VO `JanelaVigencia` (ADR-0030) | `src/domain/shared/value_objects.py:185` | vigência de `TabelaPreco` e de versão de preço |
| VO `Aliquota` | `src/domain/configuracoes_sistema/value_objects.py:13` | referência de molde p/ VO `Preco`/`Percentual` |
| Molde app novo | fiscal: `config/settings/base.py:270` + `config/urls.py:33` + `apps.py` | registro idêntico |
| Conftest seed | `tests/conftest.py:103-181` (`_SEED_MIGRATIONS` + `_APP_MODULE_SUBPATH`) | 1 linha de seed authz; subpath SÓ se path aninhado |

**Questão de path pro tech-lead (P2):** fiscal e configuracoes_sistema são raiz achatada
(`src/domain/fiscal/`); ADR-0072 só normatiza metrologia; mas `clientes` (M1) já usa
`src/application/comercial/clientes/`. Decidir: `src/domain/comercial/produtos_pecas_servicos/`
(espelha clientes) vs raiz achatada. PRD coloca o módulo no domínio `suporte-plataforma`
(cadastro base compartilhado) — path deve seguir o domínio do PRD ou o precedente comercial.

## §3. PRD e escopo (docs)

- PRD: `docs/dominios/suporte-plataforma/modulos/produtos-pecas-servicos/prd.md` —
  5 US (US-CAT-001 cadastrar peça · 002 atualizar preço SEM afetar histórico/INV-026
  versionamento · 003 kit · 004 importar planilha · 005 inativar) + 7 ACs + 5 non-goals
  (sem saldo de estoque, sem NF, sem cotação fornecedor, sem custo médio, sem
  multi-canal V1 — tabela ÚNICA no MVP).
- **TabelaPreco:** o plano de dependência (linhas 86-101) crava: catálogo carrega
  `ItemCatalogoVersao.preco_padrao`; `TabelaPreco` = preço VIGENTE por cliente/segmento.
  **US-OS-015 (OS avulsa, Wave A) exige TabelaPreco vigente na data — 422
  `PrecoTabelaAusente` sem fallback ao padrão.** Logo TabelaPreco entra NESTA frente
  (gap documentado: modelo dizia "V2" mas Wave A exige — promover).
- **Conflito de faseamento (resolver em P1):** `faseamento-modulos.md:95` põe o módulo
  em Wave B; PRD de `orcamentos` o declara GATE Wave A (A-ORC-001). Plano de dependência
  recomenda alinhar pelo PRD (subir pra Wave A) — emendar `faseamento-modulos.md` no P8.
- **Cadeia (T-CR-000):** preço nasce em orcamentos ← consome catálogo+TabelaPreco desta
  frente; contas-receber é a última peça. Não inverter.
- **Perfil A/B/C/D:** NENHUMA feature de catálogo/preço é perfil-aware
  (matriz-feature-perfil — preço é global por tenant; ADR-0013 é billing SaaS, outro plano).

## §4. ADRs que tocam a frente

- **ADR-0013** (pricing composicional) = billing-saas (planos do Aferê), NÃO preço
  operacional do tenant — não confundir; nenhuma ADR específica de TabelaPreco existe.
- ADR-0030 (JanelaVigencia) + ADR-0031 (soft-delete: inativar item = padrão
  estado-máquina/`deletado_em`?) + ADR-0017 (sem CNPJ aqui) + ADR-0080 (não numera).
- Provável ADR nova OU decisão em plan: versionamento de preço do item
  (`ItemCatalogoVersao` imutável estilo Imposto/INV-026) × TabelaPreco vigente
  por cliente — espelhar o molde "linha de vigência imutável" da frente #1.

## §5. Recorte núcleo proposto (validar em P1/P2)

**Núcleo startável sem dependência inexistente:**
1. `ItemCatalogo` (peça/serviço/kit; código único por tenant INV a criar; UM;
   controla_estoque flag — saldo é non-goal) + `ItemCatalogoVersao` (preço padrão
   versionado imutável — molde Imposto da frente #1).
2. `TabelaPreco` + `ItemTabelaPreco` (vigência JanelaVigencia; tabela única MVP —
   multi-canal/segmento = non-goal V1; consulta `preco_vigente_em(item, momento)`
   fail-closed 422 — contrato que US-OS-015 espera).
3. Kit (preço = soma OU manual — AC-CAT-003-1).
4. Importação XLSX/CSV (US-CAT-004) — avaliar diferir sub-fatia (csv-safety-import
   hook existe; molde extração M6 = staging não-auto-persiste).
5. Inativar item (US-CAT-005 — não afeta OS abertas; soft-delete ADR-0031).

**Diferido (GATE):** integração com estoque/custo médio (módulo estoque),
multi-canal, cotação fornecedor, consumo por orcamentos (frente #5 pluga).

## §6. Próximos passos do ritual

P1 spec (recorte núcleo vs diferido sobre o PRD; resolver conflito de wave) →
P2 revisões `tech-lead` (path + versionamento + molde WORM/RLS) + `advogado`
(LGPD: catálogo não tem PII a princípio — confirmar; preço não é PII) →
P3 plan/tasks fatiado (molde 1a domínio puro → 1b schema → 2 use cases/REST →
3 P7 INVs+hooks → P8 docs → P9 auditores roteados).
