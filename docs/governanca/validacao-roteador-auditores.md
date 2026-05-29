---
owner: roldao
revisado_em: 2026-05-29
proximo_review: 2026-08-29
status: stable
diataxis: explanation
audiencia: agente
relacionados:
  - docs/governanca/ritual-orquestrador.md
  - REGRAS-INEGOCIAVEIS.md
  - docs/faseamento/M3-os/auditoria-familia5.md
  - docs/faseamento/M4-calibracao/auditoria-familia5.md
  - docs/faseamento/auditorias/AUDITORIA-MAQUINA-DEV-rodada-1.md
---

# Validação do roteador de auditores (pré-condição INV-RITUAL-003)

> **Pra quê:** INV-RITUAL-003 (roteamento de auditores Família 5 por tipo de mudança) só pode ser ATIVADO depois de provar, contra módulos reais, que o roteador teria chamado **todos os auditores que acharam problema real**. Esta é a evidência. Sem ela, roda-se os 10 sempre.
>
> **Resultado: ✅ VALIDADO — roteador SEGURO para ativação (com a trava falha-aberto como rede).**

---

## Regra sob teste (INV-RITUAL-003)

- **6 ESSENCIAIS rodam SEMPRE** em qualquer mudança de código: Segurança, Qualidade, Produto, LLM-correctness, Idempotência, Conformidade-LGPD.
- **4 ROTEADOS rodam só se o diff toca a área deles** (na dúvida, RODA — falha-aberto):
  - Performance → `views.py`/`services.py`/`use_cases.py`/`domain`
  - Supply-chain → `pyproject.toml`/`poetry.lock`/`Dockerfile`/`.github/workflows`
  - Observabilidade → `financeiro`/`auth`/`authz`/`tenant`/`kms`/`audit`(trilha WORM)/`views.py`
  - Drift-docs → docs de status/contagem

**Pergunta de validação:** algum dos 4 ROTEADOS achou problema real (CRÍTICO/ALTO/MÉDIO) em M3 ou M4 num diff que o roteador NÃO teria disparado? Se sim → roteador inseguro.

---

## Evidência — M3 `ordens_servico` (fonte: M3-os/auditoria-familia5.md L37-46)

| Auditor | Tipo | Veredito 1ª passada | C/A/M | Roteador dispararia? | Seguro? |
|---|---|---|---|---|---|
| Segurança | essencial | FAIL | 0/2/4 | sempre | ✅ |
| Qualidade | essencial | FAIL | 4/3/3 | sempre | ✅ |
| Produto | essencial | FAIL | 0/1/3 | sempre | ✅ |
| LLM-correctness | essencial | PASS | 0/0/0 | sempre | ✅ |
| Idempotência | essencial | FAIL | 0/0/7 | sempre | ✅ |
| LGPD | essencial | PASS | 0/0/0 | sempre | ✅ |
| **Drift-docs** | **roteado** | **FAIL** | **0/8/5** | **SIM** — fechamento M3 tocou AGENTS/tasks/CURRENT (docs de status) | ✅ |
| Performance | roteado | PASS | 0/0/0 | (tocou views, mas nada real) | ✅ economia segura |
| Observabilidade | roteado | PASS | 0/0/0 | — | ✅ economia segura |
| Supply-chain | roteado | PASS | 0/0/0 | — | ✅ economia segura |

**M3: o único roteado com achado real (Drift-docs) seria disparado.** Performance/Observabilidade/Supply-chain não acharam nada real — exatamente onde o roteamento economiza.

---

## Evidência — M4 `metrologia/calibracao` (fonte: M4-calibracao/auditoria-familia5.md L41-50)

| Auditor | Tipo | Veredito 1ª passada | C/A/M | Roteador dispararia? | Seguro? |
|---|---|---|---|---|---|
| Segurança | essencial | FAIL | 1/3/4 | sempre | ✅ |
| Qualidade | essencial | FAIL | 0/1/4 | sempre | ✅ |
| Produto | essencial | FAIL | 0/3/3 | sempre | ✅ |
| LLM-correctness | essencial | CONCERNS | 0/0/0 | sempre | ✅ |
| Idempotência | essencial | FAIL | 1/2/2 | sempre | ✅ |
| LGPD | essencial | FAIL | 0/0/1 | sempre | ✅ |
| **Drift-docs** | **roteado** | **FAIL** | **0/4/9** | **SIM** — fechamento M4 tocou AGENTS/CLAUDE/tasks/CURRENT | ✅ |
| **Observabilidade** | **roteado** | **FAIL** | **0/0/3** | **SIM** — M4 toca `views.py` + emite trilha WORM `EventoDeCalibracao` (área `audit`) | ✅ |
| Performance | roteado | PASS | 0/0/0 | (tocou views, nada real) | ✅ economia segura |
| Supply-chain | roteado | PASS | 0/0/0 | — | ✅ economia segura |

**M4: os dois roteados com achado real (Drift-docs e Observabilidade) seriam disparados.** O achado de Observabilidade (OBS-CAL-01/02/03 — emitir `EventoDeCalibracao` na trilha WORM) cai diretamente no gatilho `audit`/`views.py`.

---

## Veredito

✅ **Roteador SEGURO para ativação.** Em M3 e M4 (os dois únicos módulos completos pré-Wave-A), **100% dos auditores roteados que acharam problema real teriam sido disparados** pelo gatilho de área. Os roteados que não acharam nada real (Performance nos dois; Observabilidade no M3; Supply-chain nos dois) são exatamente as economias seguras. Os 6 essenciais capturaram **100% dos CRÍTICOs** dos dois módulos.

**Travas que ficam ativas (rede mesmo após validação):**
1. **Falha-aberto** — dúvida sobre área = RODA o auditor.
2. **Nunca pular por código** — só por extensão inerte (`.md`, template de tela).
3. **Gatilho de Observabilidade inclui emissão de trilha WORM** (área `audit`) — não só `views.py`.
4. **Re-validar quando surgir um tipo de módulo de forma diferente** (ex: módulo puro de integração/fila). Esta validação cobre módulos com domínio + REST + WORM; um módulo só-infra pode ter perfil de risco diferente.

**Decisão:** INV-RITUAL-003 passa de "documentado" para **ATIVO** a partir de 2026-05-29.
