---
owner: roldao
revisado-em: 2026-05-23
status: stable
diataxis: explanation
audiencia: agente
relacionados:
  - REGRAS-INEGOCIAVEIS.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - .claude/hooks/arquivo-tamanho-aviso.sh
---

# God-modules — deferral formal para pós-Marco 3 Fase 5

> **Onda 2 plano-v2 (2026-05-23):** auditor QUAL apontou ⛔ ALTO god-modules em `src/infrastructure/equipamentos/models.py` (1831 linhas) e `src/infrastructure/ordens_servico/models.py` (1055 linhas), violando itens 234/237/238 da checklist de problemas IA.
>
> **Esta nota** registra que a correção fica **DEFERIDA** para depois do Marco 3 Fase 5 fechar. Sem deferral formal isso vira drift.

---

## Por que NÃO quebrar agora

A auditoria de plano-v2 (auditor QUAL) deu o sinal mais claro:

> "Onda 2 paralela ao Marco 3 OS = retrabalho garantido + merge hell. Inverter ordem: saneamento OS antes do spec FORWARD M3, OU congelar OS até Marco 3 fechar P4. Nunca paralelo."

Estado real verificado em 2026-05-23:

- Spec FORWARD do Marco 3 (P1) já fechou stable.
- P2 (reviews), P3 (retrofit), P4 Fases 1-4 (Schema + Domain + Predicates + Consumers/Sagas) também fecharam.
- **Próxima fase: P4 Fase 5 (Services + use cases — 15 US, ~45 tarefas)** — vai mexer pesadamente em `ordens_servico/models.py`.

Se eu quebrar `ordens_servico/models.py` agora em sub-arquivos por agregado:

1. Os ~45 commits da Fase 5 vão ter conflito a cada touch nos models (renomeações, novos campos, novos índices).
2. O CODEOWNERS protege `migrations/` — cada conflito vira escalation pra Roldão.
3. Risco real: regressão em INV crítico (cliente_canonico_imutavel, EXCLUDE GIST do RT, vigência) por erro de merge.

**Decisão:** quebrar god-modules **DEPOIS** que Marco 3 Fase 5 fechar, num PR dedicado. Sem paralelismo com fase de implementação.

## Por que NÃO quebrar por LINHA (auditor QUAL apontou)

Auditor QUAL alertou que quebrar pelo número de linhas é **sintoma**, não causa:

> "`equipamentos/models.py` tem N agregados misturados (Equipamento + RT + Vigência + Competência). Causa-raiz = ausência de bounded context interno. Cortar por linha gera arquivos coesos só por acaso."

**Decisão complementar:** antes de quebrar, mapear os agregados (bounded contexts internos) numa ADR curta. Cortar **POR AGREGADO**, não por tamanho.

## GATE-QUAL-GOD-MODULES-POS-M3F5

Quando Marco 3 Fase 5 fechar com 10 auditores PASS ZERO C/A/M, abrir esta ondinha:

1. **Mapeamento DDD curto** (ADR a numerar — ~ADR-0064+): listar agregados em `equipamentos/models.py` e `ordens_servico/models.py`. Critério: agregado = root entity + value objects + entities filhas que compartilham invariante de unicidade transacional.
2. **Plano de quebra por agregado**: nova estrutura `models/<agregado>.py` + `__init__.py` re-exportando classes pra preservar imports externos.
3. **Migration zero**: o Python imports re-exportam tudo — não há migration de banco.
4. **PR único por módulo** (`equipamentos` num PR, `ordens_servico` em outro) com checklist:
   - Suite 621+ verde antes e depois.
   - Hooks 234+ verde antes e depois.
   - Nenhum import externo precisa mudar.
5. **Hook `arquivo-tamanho-aviso.sh`** (criado nesta Onda 2 como rede de segurança) avisa em 600 linhas, bloqueia em 1500.

## Rede de segurança ATIVA hoje (hook arquivo-tamanho-aviso)

Pra evitar que NOVOS módulos repitam o erro, esta Onda cria hook `arquivo-tamanho-aviso.sh` que:

- Aplica a `src/infrastructure/**/models.py` e `src/infrastructure/**/views.py`.
- **Avisa** (exit 0 + mensagem em stderr) quando arquivo passa de 600 linhas.
- **Bloqueia** (exit 2) quando arquivo passa de 1500 linhas.
- Allowlist com motivo: `# arquivo-tamanho: skip -- <razão ≥10 chars>` (ex: `equipamentos/models.py` já tem skip por estar em deferral).

Arquivos atuais que excedem:
- `src/infrastructure/equipamentos/models.py` (1831 linhas) — DEFERIDO via skip inline a adicionar
- `src/infrastructure/ordens_servico/models.py` (1055 linhas) — abaixo do bloqueio (1500), só aviso

## Quando reabrir esta nota

- Marco 3 Fase 5 fechar com 10 auditores PASS → criar ADR de quebra DDD + executar GATE-QUAL-GOD-MODULES-POS-M3F5.
- Surgir 3º módulo passando de 1500 linhas → revisar limite do hook.

## Histórico

- 2026-05-23: deferral formal registrado. Hook `arquivo-tamanho-aviso.sh` criado como rede de segurança.
