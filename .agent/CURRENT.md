# .agent/CURRENT.md

> ≤40 linhas curtas. Histórico detalhado em `docs/faseamento/diario/`. Contagens vivas: `docs/governanca/STATUS-GERADO.md`.

**Modo:** AUTÔNOMO. **Fase:** Wave A em curso.

## FILA DE FRENTES — ordem de dependência CRAVADA (Roldão 2026-06-16: "todos em sequência de dependência, não perguntar")

Receita fechada (config→pps→precificacao→colaboradores→orcamentos→contas-receber). Faltantes Wave A (topo-sort do `plano-dependencia-sistema.md`; deps já construídas; **seguir em ordem, sem perguntar**):

1. **`caixa-tecnico`** (N5) ← EM CURSO. **P0..P3 DONE** (`spec.md`+`reviews-consolidado.md`+`plan.md`+`tasks.md`; greenfield). **Decisões Roldão P0:** reembolso fail-open lazy; devolução só registra saldo (Wave B); foto local. **P2:** tech-lead (15 TL-CT: foto=`services_foto_storage` não AnexoStoragePort; HMAC-tenant pós-EXIF-strip; PDF=WeasyPrint; path flat; saldo derivado+advisory lock; sem AReembolsarPort=evento+backfill) + advogado (9 ADV-CT: base GPS **art.7º IX+V** não consentimento; retenção GPS curta ≠5a fiscais; GATE-CT-GPS-LGPD-OAB). **P3:** PRD corrigido (AC-005-3/002-5/002-7 + skip UX-states) + 8 gates CT-* registrados + plan/tasks (T-CT-010..062 + P8/P9 T-CT-070/071; 8 fatias). **P4 Fatia 1a DONE** (commit `060b77a` — domínio puro 11 arq + 79 testes). **Fatia 1b DONE** (6 models + 7 migrations RLS v2/WORM/constraints + repos + drill + `ACOES_CAIXA_TECNICO` na união; **16 testes**; hooks invariante limpos; tabelas `*_caixa`; débito P9: `0007_alter` só help_text). **AMBIENTE:** pré-commit ~14min — Defender excluído (18s→3s/hook); ver [[project-precommit-lento-defender]]; NUNCA 2 commits concorrentes. **Fatia 2 DONE** (T-CT-030..037 — 10 use cases + 3 ViewSets + serializers GPS read_only + `/sync/despesas-lote` per-item 207 + advisory lock no fechamento + idempotência REST; portas via `ports_stub.py` Wave A; seed `0008`; **24 testes E2E**). Revisão do maestro: trocou `disable_error_code` amplo (pyproject) por `type:ignore[assignment]` cirúrgico no campo `data` do serializer (TST-003); corrigiu authz `str(row[0])` incidental. **Fatia 3a DONE** (T-CT-040..043 — 4 adapters reais: FotoComprovanteStorageLocal EXIF-strip+HMAC-tenant pós-strip; ConsentimentoGpsAdapter; ColaboradorCaixaAdapter `e_tecnico`+`esta_referenciado`; OSReferenciaAdapter; `ports_stub.py` removido; `LancarDespesa` valida OS via `OSReferenciaPort` → `OSInexistente`; foto-tipo-inválido → `FotoTipoInvalido` 422; wiring fail-open de `esta_referenciado` no ColaboradorViewSet — débito **GATE-CT-COLABORADOR-REFERENCIADO**). Review (auditores roteados + verificação adversarial) consertou na causa-raiz: dedup foto `IntegrityError`→**409** (era 500; INV-CT-FOTO-DEDUP-001), consentimento `date`→datetime aware (sem naive), `mediafiles/` no `.gitignore` + `MEDIA_ROOT` tmp em test; **GATE-CT-HASH-ROTACAO-LOOKUP** documentado (Wave A key fixo). **Fatia 3b DONE** (T-CT-050/051 — consumer `colaborador.desligado` `@consumer_idempotente` → marca `CaixaTecnico.desligado_em` fail-closed (perfil do envelope, nunca corrente); 9 slugs `caixa_tecnico.*` canônicos; fan-out aditivo no `apps.py:ready` sem engolir agenda; `prestacao.fechada` no `BusOutbox`). **Fatia 3c DONE** (T-CT-055/056 — `pdf_prestacao.py` WeasyPrint + `montar_html_prestacao` testável + guard SSRF CVE-2025-68616; template `templates/caixa_tecnico/prestacao_pdf.html`; action GET `/prestacoes/{id}/pdf/` no `PrestacaoContasViewSet`, ownership técnico-próprio (hash colaborador↔caixa) OU financeiro/não-técnico → outro técnico 403, cross-tenant 404; GPS AUSENTE no PDF AC-CT-002-7; cache private 60s; `caixa_tecnico.ver` já seedado, sem migration nova; 8 testes). **Testes INV T-CT-057..062 DONE** (`tests/regressao/test_inv_ct_caixa_tecnico.py` — 6 casos rastreáveis por INV-ID: reapresentação não dispara trigger·foto cross-tenant coexiste+dedup 409·foto_hash pós-strip·batch parcial per-item·fechamento concorrente advisory lock·EXIF GPS não vaza). ruff/format/mypy limpos; fatia 2 sem regressão. **PRÓXIMO = P8 (matriz `matriz-reconciliacao.md` T-CT-070; GATE-CT-GPS-LGPD-OAB já em `gates-wave-a-consolidado.md`) + P9 (mutirão auditores roteados T-CT-071) p/ FECHAR o módulo.** Destrava app-tecnico/despesas/custeio-real.
2. **`chamados`** (N5) — entrada de demanda → vira OS. Dep: clientes(✓)+os(✓).
3. **`contas-pagar`** (N5) — par do CR; destrava despesas (precisa cadastro fornecedor mínimo).
4. **`estoque`** (N3, atrasado) — pré-req de app-tecnico/custeio-real. Dep: pps(✓)+os(✓)+equipamentos(✓).
5. **`frota`** (N4) · **`treinamentos`** (N3) · **`seguranca-trabalho`** (N3) — suporte; dep colaboradores/equipamentos (✓).
6. **N6:** `comissoes` (gatilha por recebimento ✓) → `despesas` → `app-tecnico` → `contabilidade-export`.
7. **N7+:** `fornecedores` → `crm` → `contratos` → `qualidade` → `custeio-real` (fecha stub precificacao) → níveis 8–10.

**DIFERIDOS (bloqueio externo — só quando Roldão liberar credencial/serviço):** `certificados-digitais` (Lacuna Web PKI/A3),
`comunicacao-omnichannel` (SMS/WhatsApp/e-mail real), `billing-saas` (gateway+fiscal reais), `integracoes-externas` (OAuth).

- **Para o Roldão (quando ativar e-mail real do CR):** criar `.env` com `EMAIL_HOST`/`EMAIL_HOST_USER`/
  `EMAIL_HOST_PASSWORD`/`DEFAULT_FROM_EMAIL` (SMTP). Hoje modo teste (não envia). Disparo a PF real só após GATE-LGPD-RAT.

## Última frente FECHADA — `agenda` MÓDULO 100% Wave A (2026-06-17)

- Fatias 1a..3d + P8 (matriz) + P9 (lgpd PASS + 6 MÉDIO consertados na causa-raiz; 2ª passada 6 PASS, sem novo MÉDIO+).
  **179 testes** (era 173). Sem ADR nova (D-AGE-15 já em P3). Detalhe + GATEs: `docs/faseamento/agenda/matriz-reconciliacao.md` §5/§8.
- **GATE-AGE-RT-WIRING + GATE-AGE-OS-WIRING FECHADOS** (Roldão 2026-06-17 — wirados): `criar_evento` passo 4.5 dispara 412 `SemRTNoSlot` perfil A det. (B/C aviso; D off; grandeza vazia fail-open);
  passo 5.5 chama `atribuir_tecnico` (tipo=os → OS PENDENTE→AGENDADA; ACL traduz erro da OS→ConflitoAgenda). **184 testes.** +GATEs abertos: NO-SHOW-AGENDA, RTSUBSTITUICAO-FORMAL, COLABORADOR-REFERENCIADO.
- **`contas-receber`** fechou antes (2026-06-16, ADR-0084; bus FAN-OUT [[fan-out-bus-consumers-os-concluida]]). [[estado-do-projeto-wave-a-em-curso]].

## Pendência de produto aberta

Terminologia B/C/D do M6 — veto item-a-item do Roldão pendente (cl. 8.1.3 "capacidade interna declarada").

## Ponteiros

- Contagens: `docs/governanca/STATUS-GERADO.md` · ADRs: `docs/adr/INDICE.md` · matriz: `docs/faseamento/orcamentos/matriz-reconciliacao.md`
- Proibido commit isolado de CURRENT.md — handoff entra no commit da fatia (R16).
