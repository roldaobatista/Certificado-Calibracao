---
template: deployment-strategy.template.md
destino: docs/operacao/deployment-strategy.md
owner: <lider-tecnico>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
proposito: definir COMO uma versao nova entra em producao tecnicamente (estrategia, feature flag, migracao de banco, rollback)
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C8
limite-linhas: 200
---

<!--
Agente IA: este e o complemento tecnico de release-process.md. release-process define QUANDO/QUEM. este define COMO tecnicamente.
Mantenha tom direto. Adapte ferramentas reais. Se o projeto e monolito sem orquestrador, marque secao como "n/a — alvo: <data>" em vez de fingir que tem.
-->

# Estrategia de Deployment — <nome-do-projeto>

## 1. Estrategias suportadas

| Estrategia | O que e | Quando usar |
|---|---|---|
| **Rolling** | substitui instancias N por N+1 gradualmente, sem ambiente paralelo | mudanca sem breaking change, sem mudanca de schema |
| **Blue-Green** | dois ambientes completos (blue ativo, green novo); switch atomico de trafego | release com mudanca grande mas reversivel rapidamente |
| **Canary** | nova versao recebe % pequeno de trafego real antes do full | release com risco moderado, validacao com trafego real |
| **Dark launch** | codigo novo deployado mas inativo (gated por feature flag desligada) | preparar release grande em pedacos, desacoplar deploy de release |
| **Shadow traffic** | requisicoes reais sao replicadas para a versao nova sem afetar resposta ao cliente | validar carga, compatibilidade, performance sem risco |

## 2. Criterio de escolha

| Tipo de mudanca | Estrategia recomendada | Por que |
|---|---|---|
| Bugfix simples, sem mudanca de comportamento | Rolling | mais barato, baixo risco |
| Feature nova retrocompativel | Canary 5% -> 25% -> 50% -> 100% | valida em trafego real com baixo blast radius |
| Refator de logica critica (ex: motor de cobranca) | Shadow traffic + Canary | confirma equivalencia funcional antes de servir cliente |
| Mudanca de schema de banco | Expand -> Migrate -> Contract (§4) com Rolling | zero-downtime |
| Mudanca grande com janela curta de rollback | Blue-Green | switch instantaneo back |
| Feature em desenvolvimento ainda nao pronta | Dark launch (flag off) | desacopla merge de release |

Decisao de estrategia consta no PR/issue da mudanca. Auditor checa.

## 3. Feature flags

### 3.1 Tipos

| Tipo | Quando usar | Tempo de vida esperado |
|---|---|---|
| **Boolean** (on/off global) | kill switch de feature nova | curto: < 30 dias apos GA |
| **Percentage** (rollout %) | canary progressivo, A/B | curto: < 30 dias apos 100% |
| **Audience** (segmento de usuario/tenant) | beta privado, cliente piloto, regiao | medio: ate fim do piloto |
| **Permission** (entitlement por plano) | gating comercial permanente | longo: vive enquanto o plano existir |

Flags de **kill switch** de seguranca (desligar feature em incidente) tem tempo de vida indefinido — sao infraestrutura, nao debito.

### 3.2 Audit log

Toda mudanca de flag em ambiente produtivo gera evento:
- `timestamp`, `flag_name`, `valor_anterior`, `valor_novo`, `quem_mudou`, `motivo`, `ticket`.
- Logs com retencao minima de 1 ano.
- Mudanca de flag e operacao de mudanca — segue `change-management.md` §1 (janela).

### 3.3 Cadencia de limpeza (dead-code cleanup)

> Flag temporaria que vira permanente vira debito tecnico. Limpar agressivamente.

- Revisao **mensal** das flags com idade > 30 dias por <owner-flags>.
- Cada flag tem `created_at`, `owner`, `removal_target_date` cadastrados no momento da criacao.
- Flag boolean a 100% por 14 dias consecutivos -> abrir tarefa de remocao (PR que apaga a flag e mantem so o ramo ativado).
- Auditor `auditores/feature-flag-auditor.md` falha o build se flag estiver > 90 dias sem `removal_target_date`.

## 4. Migracoes de banco zero-downtime

Padrao **Expand -> Migrate -> Contract** (3 releases):

| Fase | Codigo | Schema | Garantia |
|---|---|---|---|
| **Expand** | le formato antigo, escreve em ambos | adiciona coluna/tabela nova, mantem antiga | versao antiga continua funcionando |
| **Migrate** | le e escreve no formato novo | backfill assincrono dos dados antigos | nenhuma escrita no formato antigo |
| **Contract** | le e escreve so no formato novo | dropa coluna/tabela antiga | sem rollback para versao Expand |

Regras:
- **Nunca** rodar migration destrutiva (`DROP`, `RENAME` sem alias, `ALTER COLUMN` que muda tipo incompativel) em uma unica release.
- Backfill em batch com idempotencia e checkpoint (retomavel).
- Migration que demora > <5min> em producao -> rodar fora do deploy via job dedicado.
- Migration sempre tem script de rollback testado em staging.

## 5. Janela de compatibilidade (backward compatibility)

- API publica: **N-1** versoes MAJOR retrocompativeis (ver `release-process.md` §9).
- Schema de banco: **N-2** versoes da aplicacao conseguem rodar contra o schema atual (cobertura do periodo de rollout + rollback).
- Eventos em fila: produtor e consumidor evoluem em pacotes separados — consumidor sempre aceita schema antigo + novo durante a transicao.

## 6. Playbook de rollback

Por estrategia, o rollback e diferente:

| Estrategia | Como reverter | Tempo alvo |
|---|---|---|
| Rolling | re-deploy da versao N-1 | < 10min |
| Blue-Green | switch de trafego de volta para blue | < 1min |
| Canary | dropar % para 0 | < 1min |
| Dark launch | flag para off | < 30s |
| Shadow | desabilitar replicacao | < 30s |
| Migration Expand | re-deploy app N-1 (schema continua compativel) | < 10min |
| Migration Migrate | re-deploy app + restaurar de backup se backfill corrompeu dados | < 1h |
| Migration Contract | **sem rollback simples** — requer restore de backup | horas |

Detalhe operacional em `docs/operacao/runbooks/rollback-deploy.md` (instanciar via `runbook.template.md`).

## 7. Ambientes

| Ambiente | Proposito | Dados | Acesso |
|---|---|---|---|
| **dev** | desenvolvimento local + branch preview | sintetico | dev |
| **staging** | espelho de producao para validacao final, smoke test, RC | anonimizado de prod (sem PII bruta) | dev + qa |
| **prod** | clientes reais | reais | restrito, audit log |

Regras:
- Dev nao usa dados de producao com PII.
- Staging refresh de schema semanal a partir de snapshot anonimizado de prod.
- Mudanca so chega em prod depois de >= 24h em staging sem alerta.

## 8. Promotion gates (porteiros entre ambientes)

| Gate | Entre | Criterio |
|---|---|---|
| dev -> staging | PR merged | testes unit + integration verdes, lint, type-check, build, auditores |
| staging -> prod (RC) | RC publicado | smoke test (`docs/operacao/smoke-test.md`) verde + 24h sem alerta SEV3+ |
| prod canary -> prod full | rollout progressivo | metricas §5 de `release-process.md` dentro do limite |

Gate falhado -> bloqueia automaticamente. Bypass manual exige ADR + aprovacao de §2.4 de `release-process.md`.

## 9. Vinculacao com

- `docs/operacao/release-process.md` — fluxo de release usa estas estrategias.
- `docs/operacao/change-management.md` — janela em que o deploy pode ocorrer.
- `docs/operacao/observabilidade.md` — metricas que disparam rollback automatico.
- `docs/operacao/runbooks/rollback-deploy.md` (instanciar via `runbook.template.md`) — execucao manual de rollback.
- `docs/decisoes/ADR-XXXX-estrategia-deploy.md` — escolha de orquestrador e estrategia padrao.
- `auditores/feature-flag-auditor.md` — valida ciclo de vida das flags.
- `auditores/migration-auditor.md` — valida que migrations seguem expand/migrate/contract.
- `INV-AGENT-XXX` — invariantes de retrocompatibilidade de contrato.
