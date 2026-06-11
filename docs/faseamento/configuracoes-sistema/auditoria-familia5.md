---
owner: agentes-afere
revisado-em: 2026-06-11
status: stable
---

# Auditoria Família 5 — frente `configuracoes-sistema` (P9 / T-CFG-044)

> **1ª passada executada em 2026-06-10.** Roteamento INV-RITUAL-003: 6 essenciais
> + Performance + Observabilidade (diff toca `views.py`/`use_cases`/`domain`).
> Supply-chain NÃO roteado (zero mudança em `pyproject/lock/Dockerfile`).
> Drift-docs numérico coberto por `scripts/status-projeto.sh --check`.
> Escopo do diff: commits `44bcbb2^..491e82a` (Fatias 1a/1b/2/3 + P7/P8).

## §1. Vereditos da 1ª passada (2026-06-10)

| Auditor | Veredito | C/A/M/B |
|---|---|---|
| seguranca | CONCERNS | 0/0/0/2 |
| qualidade | CONCERNS | 0/0/0/2 |
| llm-correctness | **FAIL** | 0/0/**2**/1 |
| idempotencia | CONCERNS | 0/0/**1**/2 |
| conformidade-lgpd | **FAIL** | 0/0/**2**/2 |
| produto | CONCERNS | 0/0/**1**/3 |
| performance | CONCERNS | 0/0/**1**/2 |
| observabilidade | CONCERNS | 0/0/0/2 |

**Total: 0 CRÍTICO / 0 ALTO / 7 MÉDIO / ~14 BAIXO.** MÉDIO bloqueia fechamento
(INV-RITUAL-001). Decisão padrão Roldão: resolver TUDO (crítico→baixo) na causa-raiz.

## §2. Achados MÉDIO (bloqueantes) + estado do conserto

| # | Auditor | Achado | Conserto | Estado |
|---|---|---|---|---|
| M1 | llm | `object` residual em `encerrar_vigencia(fim)` e `SerieDocumento.obter(tipo)` (repositories.py) | tipos reais `datetime`/`TipoDocumento`, sem isinstance/getattr | ✅ RESOLVIDO `b817e2b` |
| M2 | llm | `imposto_vigente_em` NÃO descarta linha revogada — docstring promete unicidade que a exclusion (WHERE revogado_em IS NULL) não garante pro conjunto com revogadas; consumidor futuro pegaria a linha ERRADA | filtro `revogado_em is None` no loop (espelha o WHERE) | ✅ RESOLVIDO `b817e2b` — **falta teste de regressão** (revogada + substituta mesma janela → resolve a substituta) |
| M3 | idempotencia | CFG-IDEMP-01: replay 24h devolve `sequencial` de reserva gap-less que vive 5min; `confirmar_numero` endereça por `(serie, ano, sequencial)` em vez de `reserva_id` (Protocol M8 confirma por `reserva_id`) — caller de replay velho pode confirmar reserva VIVA de fluxo alheio | devolver `reserva_id` no body do reservar-numero + `confirmar_numero(reserva_id=...)` alinhado ao molde M8; Protocol domínio `reservar_numero` passa a retornar resultado estruturado (seq + reserva_id \| None) | ✅ RESOLVIDO `4cc64f3` (validado 2026-06-11: 68/68) |
| M4 | lgpd | LGPD-MEC-001: campos PII de `Empresa`/`Filial` (cnpj/endereco/telefone/nome) sem anotação de base legal in-code (RAT-CFG-EMPRESA existe e cobre — gap é só a anotação rastreável) | comentário `# lgpd-base: art. 7º II + V — RAT-CFG-EMPRESA` nos blocos PII de models.py | ✅ RESOLVIDO `62d51ee` |
| M5 | lgpd | LGPD-MEC-003: PII de empresa/filial sem rota de eliminação (CharField em claro, sem função de anonimização; crypto-shredding declarado na matriz mas não implementado pra essas tabelas) | migration 0007 com função `apagar_pii_empresa_filial()` (anonimiza endereco/telefone/contato; preserva razao_social/cnpj enquanto doc fiscal no prazo — contrato retencao-matriz linha 91) + teste PG-real | ✅ RESOLVIDO `62d51ee` (sem SECURITY DEFINER; teste cobre UNHAPPY cross-tenant + idempotência) |
| M6 | produto | "editar filial" prometido na spec §3 ("adicionar/EDITAR filial") NÃO entregue — filial errada fica imortal; não há como trocar a matriz | use case `editar_filial` (INV-037 no conjunto resultante; marcar eh_matriz=True desmarca a anterior na MESMA transação = troca atômica; desmarcar a única matriz → 422) + action REST detail=True + evento `Config.FilialEditada` em ACOES_CONFIG + testes puros e E2E | ✅ RESOLVIDO `86b87c3` (5 puros + 4 E2E; ordem desmarcar→marcar pelo UNIQUE parcial) |
| M7 | performance | `_reservar_gap_less` carrega TODOS os sequenciais da série pra memória Python segurando o advisory lock — série gap-less SEM `{ano}` (ano_dim=0 perpétuo) degrada O(n²) agregado, mês a mês | calcular menor-livre em SQL puro (anti-join `candidatos {1} ∪ {s+1}` + NOT EXISTS + ORDER BY LIMIT 1 — index-only, sem materializar em Python). ATENÇÃO: a sugestão do auditor (MAX(confirmado)+vivos) é INCORRETA — confirmados podem ter buraco temporário (reserva 2 confirma, 1 e 3 expiram → livre=1, não 3). Anti-join é correto sempre. Teste de equivalência SQL × `proximo_sequencial` puro com buracos | ✅ RESOLVIDO `b54d26d` (anti-join sobre a UNIQUE `uq_num_doc_reservado`; teste de equivalência com buraco interno) |

## §3. Achados BAIXO (resolver no mesmo batch — regra resolver-TUDO)

> **Estado final (2026-06-11):** B1/B3/B4/B5/B6/B8/B9/B10/B11/B12/B13/B14/B15 ✅
> RESOLVIDOS (commits em §4). B2/B7/B16 = notas/GATEs rastreados em §6.

| # | Auditor | Achado | Conserto planejado |
|---|---|---|---|
| B1 | seguranca | teste cross-tenant UNHAPPY só pra `empresa` (1 de 5 tabelas) | estender `test_configuracoes_schema_fatia1b.py` pras outras 4 |
| B2 | seguranca | janela DISABLE RLS no seed authz 0006 (`atomic=False`) | carryover do molde fiscal/M8/M9 já aceito — registrar nota, não mexer no molde |
| B3 | qualidade | `liberar_expirados` público sem caller nem teste direto | teste direto PG-real (faz parte do contrato do motor; job futuro usa) |
| B4 | qualidade | `assert status in (400, 422, 428)` tolerante (api_fatia2:309) | fixar o código real observado |
| B5 | llm | `_serializar_*(x: Any)` nas views — entidades de tipo conhecido | tipar com as entidades de domínio |
| B6 | idempotencia | fingerprints parciais (`encerrar-vigencia` só imposto_id; `cadastrar` sem vigencia_fim/cfop/ncm/flags; `criar` sem formato/padding) | fingerprint = payload completo (como atualizar/adicionar-filial) |
| B7 | idempotencia | chave órfã `em_processo` → 425 pra sempre (serviço F-C pré-existente, fora do diff) | GATE-IDEMP-EM-PROCESSO-TTL (rastreado, transversal) |
| B8 | lgpd | `razao_social` fora da `_CHAVES_PII_DENYLIST` (MEI = nome civil) | adicionar à denylist em audit/services.py + rodar suite audit (verificar impacto em testes que esperam em claro) |
| B9 | lgpd | `response_body_resumo` da idempotência persiste CNPJ/endereco/telefone em claro | reduzir resumo persistido dos 2 endpoints PII pra campos não-PII (ids/criada/eh_matriz); resposta ORIGINAL continua completa |
| B10 | produto | `proximo_numero` inicial não configurável (sempre 1) — AC-CFG-002-1 ambíguo | registrar interpretação na matriz (inicial ≠1 só faz sentido em BURACOS_ACEITOS → entra com GATE-CFG-RETROFIT-SERIE) |
| B11 | produto | PRD §1/§4 + glossario.md:23 ainda listam NF como série local (contradiz ADR-0080/ADV-04) | corrigir texto (prd.md:24/41/84 + glossario) |
| B12 | produto | ADR-0080 corpo linha 13 diz "proposta" mas frontmatter `aceito` | atualizar linha do corpo |
| B13 | observabilidade | `_falha` não loga erro de domínio 409/422 (morre silencioso no servidor) | `logger.warning` único dentro de `_falha` (processor injeta contexto) |
| B14 | observabilidade | DELETE de reservas expiradas sem rastro de contagem | `logger.info` com contagem em `_reservar_gap_less`/`liberar_expirados` |
| B15 | performance | `encerrar_vigencia` na view lista catálogo inteiro pra achar 1 por PK | usar `obter_por_id` (✅ método criado em `b817e2b`; **falta o wire-in na view**) |
| B16 | performance | `imposto_vigente_em(Iterable)` sem caller de produção — risco de consumidor futuro passar lista cheia | nota no consolidado; repo já suporta filtro (tipo, filial) + índice |

**Avaliação retrofit M8 (nota do auditor performance):** o mesmo shape O(n) existe no
motor `numero_certificado_reservado`, mas lá a dimensão é `(tenant, ano)` e reseta
anualmente — custo limitado ao volume anual de certificados. NÃO é defeito; sem ação.

## §4. Sequência de conserto (EXECUTADA — 2026-06-10/11)

1. ~~Commit LLM (M1+M2+B15-método)~~ ✅ `b817e2b`.
2. ~~Commit IDEMP: M3 + B6~~ ✅ `4cc64f3` (validado 2026-06-11: 68/68 + hooks 560/560 + higiene `3fde6da`).
3. ~~Commit PERF: M7 + B15 wire-in + teste equivalência~~ ✅ `b54d26d`.
4. ~~Commit LGPD: M4 + M5 + B8 + B9 + teste M2~~ ✅ `62d51ee` (auditores seguranca+lgpd PASS pré-commit).
5. ~~Commit PRODUTO: M6 + B10/B11/B12~~ ✅ `86b87c3`.
6. ~~Commit OBS/QUAL/SEG: B1/B3/B4/B5/B13/B14~~ ✅ `e1d3dc1`.
7. ~~Teste de regressão M2~~ ✅ no commit 4 (`test_imposto_vigente_ignora_revogada_e_resolve_substituta_mesma_janela`).
8. ~~Reverde~~ ✅ 2026-06-11: frente 82/82 + sanitize/audit 62 + INV-FIS 10 + drill 39/39 + hooks 560/560 + anti-drift OK + makemigrations limpo + django check 0.
9. ~~Re-passada (INV-RITUAL-003)~~ ✅ — ver §5.
10. ~~Zero C/A/M → fechar~~ ✅ — ver §5/§6.

## §5. 2ª passada (2026-06-11) — vereditos

| Auditor | 1ª passada | 2ª passada | Notas |
|---|---|---|---|
| llm-correctness | FAIL (2 M) | **PASS** 0/0/0/0 | M1/M2/B5 consertados na raiz; nota consultiva exceções órfãs → docstrings clarificadas no fechamento |
| idempotencia | CONCERNS (1 M) | **PASS** 0/0/0/2B | M3/B6 fechados por construção; B9-replay=resumo ACEITÁVEL (nota de contrato em §6); B7 segue GATE transversal F-C |
| conformidade-lgpd | FAIL (2 M) | **PASS** 0/0/0/0 | M4/M5/B8/B9 na raiz; B9 propagado ao endpoint novo editar_filial |
| produto | CONCERNS (1 M) | **PASS** 0/0/0/2B | M6/B10/B11/B12 ok; semântica troca-atômica (editar) vs 422 (adicionar) avaliada COERENTE; B-1 PRD emendado no fechamento; B-2 CHANGELOG → nota transversal §6 |
| performance | CONCERNS (1 M) | **PASS** 0/0/0/0 | M7 anti-join correto e indexado (rejeição do MAX(confirmado) confirmada); editar_filial sem N+1 |
| seguranca | CONCERNS (2 B) | **PASS** 0/0/0/0 | B1 fechado (5/5 tabelas UNHAPPY); B2 carryover do molde (nota); SQL parametrizado; 0007 sem SECURITY DEFINER |
| observabilidade | CONCERNS (2 B) | **PASS** 0/0/0/0 | B13/B14 na raiz (processor F-C2 injeta contexto); OBS-003 carryover GATE deploy-time M5..M9 |

**7/7 PASS — ZERO CRÍTICO/ALTO/MÉDIO. INV-RITUAL-001 satisfeito.**

## §6. Notas residuais rastreadas (não bloqueiam)

- **CFG-IDEMP-B9 (contrato):** replay de `atualizar`/`adicionar-filial`/`editar-filial`
  devolve resumo REDUZIDO sem PII (ids+flags), não a 1ª resposta completa — trade-off
  LGPD consciente, documentado in-code; registrar no OpenAPI quando a spec da API nascer.
- **B2 (carryover do molde):** janela DISABLE RLS no seed authz 0006 `atomic=False` —
  idêntico ao molde fiscal/M8/M9 já aceito.
- **B7 → GATE-IDEMP-EM-PROCESSO-TTL** (transversal F-C, já rastreado).
- **B16/N2:** `imposto_vigente_em(Iterable)` sem caller de produção — consumidores chegam
  com `produtos-pecas-servicos`/`precificacao` (frentes #2/#3 do plano de dependência).
- **N1 (perf):** menor-livre é O(n) por chamada DENTRO do índice PG (sem lock Python) —
  mesmo perfil do motor M8; recalibrar com P95 real pós-deploy.
- **B-2 (produto, transversal):** `CHANGELOG.md` sem entrada desde 2026-05-16 — drift de
  processo global (nenhum marco M1..M9/fiscal registrou); tratar em frente de higiene docs.
- **OBS-003:** métrica por endpoint = GATE-OBS-METRIC-SCRAPE-1 deploy-time (padrão M5..M9).

## §7. Veredito final

**Frente `configuracoes-sistema` (núcleo Empresa/Filial + Imposto/RegimeTributario +
SerieDocumento) FECHADA em 2026-06-11.** Ritual P0→P9 completo: 1ª passada 8 auditores
(0C/0A/7M/~16B) → conserto causa-raiz em 6 commits (`b817e2b` `4cc64f3` `b54d26d`
`62d51ee` `86b87c3` `e1d3dc1`) → 2ª passada 7 auditores roteados = 7/7 PASS zero C/A/M.
