---
template: release-process.template.md
destino: docs/operacao/release-process.md
owner: <lider-tecnico>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
proposito: definir como uma versao nova vai do codigo congelado ate o cliente, com rollback automatico e comunicacao de breaking changes
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C8
limite-linhas: 200
---

<!--
Agente IA: preencha placeholders entre <...> e tabelas exemplo conforme realidade do projeto.
Mantenha tom direto, sem emoji. Cada coluna "owner" deve apontar para pessoa real, nao papel generico.
Se o projeto nao tem canary/progressive ainda, mantenha as secoes mas marque "ainda nao implementado — alvo: <data>".
-->

# Processo de Release — <nome-do-projeto>

## 1. Versionamento

> Escolha **uma** convencao e justifique. Mudar depois exige ADR.

| Convencao | Quando usar | Formato |
|---|---|---|
| **SemVer** (`MAJOR.MINOR.PATCH`) | biblioteca, API publica, SDK consumido por terceiros que dependem de contrato estavel | `1.4.2` |
| **CalVer** (`YYYY.MM.PATCH`) | aplicacao SaaS interna, produto end-user, cadencia previsivel de release | `2026.05.3` |

Convencao escolhida: **<SemVer|CalVer>**.
Justificativa: <ex: produto SaaS sem API publica, cadencia mensal previsivel — CalVer evita debate de "isso e MINOR ou MAJOR?">.

### 1.1 Regras de incremento (SemVer)
- **MAJOR**: quebra contrato com cliente (remocao de endpoint, mudanca de schema de saida, mudanca de comportamento padrao).
- **MINOR**: feature nova retrocompativel.
- **PATCH**: bugfix retrocompativel, sem mudanca de comportamento intencional.

## 2. Changelog (obrigatorio)

Toda release tem entrada em `CHANGELOG.md` antes da tag ser criada. Formato [Keep a Changelog](https://keepachangelog.com/pt-BR/):

```
## [<versao>] - 2026-05-28
### Adicionado
- <item visivel ao cliente>
### Alterado
- <item>
### Corrigido
- <item>
### Removido / Breaking
- <item — vincular ADR se aplicavel>
### Seguranca
- <item — vincular ao auditor de seguranca>
```

> Sem entrada no changelog = release nao sai. Validado por gate em §6.

## 3. Tagging git

- Tag anotada (`git tag -a v<versao> -m "<resumo>"`), nunca tag leve.
- Tag aponta para commit que ja passou em todos gates de §6.
- Push da tag sempre apos confirmacao de smoke test verde em staging.

## 4. Processo de cut (passo a passo)

| Etapa | Acao | Duracao alvo | Responsavel |
|---|---|---|---|
| **1. Freeze** | bloqueio de merge na branch de release; so bugfix entra | 24h | <lider-tecnico> |
| **2. Release candidate (RC)** | build assinado, publicado em ambiente de staging com dados realistas | 1-3 dias | <eng-release> |
| **3. Smoke test** | suite minima automatica + checklist manual em `docs/operacao/smoke-test.md` | < 30min | <qa-ops> |
| **4. Aprovacao** | aprovador de §7 confirma em `#change-approvals` | < 4h | <aprovador> |
| **5. Tag e publish** | tag git, build de producao, publish no registry/store | < 1h | <eng-release> |
| **6. Rollout** | estrategia §5 (canary -> progressive) | 1-7 dias | <eng-release> + <on-call> |
| **7. Verificacao pos-release** | §8 | 24h apos 100% | <on-call> |

## 5. Rollout estagiado (staged rollout)

> Nunca subir 100% de uma vez em release com mudanca de comportamento.

| Fase | % de trafego/clientes | Janela minima | Sinal verde para avancar |
|---|---|---|---|
| **Canary** | <1-5>% (clientes internos + voluntarios) | <2-24h> | error rate canary <= baseline + 10%, p95 <= baseline + 15% |
| **Progressive 25%** | 25% | <12-24h> | metricas estaveis, zero alerta novo |
| **Progressive 50%** | 50% | <12-24h> | idem |
| **Full** | 100% | — | idem por 24h apos 100% |

Avancar so quando todos os sinais verdes estiverem confirmados na janela. Em duvida, pausar — pausa nao precisa de aprovacao, retomada precisa.

## 6. Rollback automatico por metricas

Gatilho automatico de rollback (executado pelo orquestrador sem intervencao humana):

| Metrica | Janela | Limite que dispara rollback |
|---|---|---|
| error rate (5xx + erros de aplicacao) | 5 min rolantes | > <2x baseline> OU > <1%> absoluto |
| latencia p95 | 5 min rolantes | > <baseline + 50%> |
| taxa de crash do cliente (desktop/mobile) | 10 min rolantes | > <0,5%> |
| saturacao de recurso critico (CPU/RAM/DB conn) | 5 min rolantes | > <85%> |

Rollback automatico executa: reverter trafego para versao N-1, manter logs/metricas para post-mortem, abrir incidente SEV2 minimo, notificar `#war-room`.

> Rollback manual sempre permitido. Operador de plantao nao precisa de aprovacao para reverter.

## 7. Responsabilidades

| Papel | Quem | Faz |
|---|---|---|
| Release manager | <nome> | coordena cut, comunica, garante gates |
| Aprovador | <nome / lider-tecnico> | da go/no-go formal em §4.4 |
| Plantao pos-release | <nome / escala on-call> | acompanha §8 nas 24h apos full |
| Comunicacao cliente | <nome / produto> | aviso prévio em §9 |

## 8. Verificacao pos-release (24h)

- [ ] SLOs em `docs/operacao/slo-sli.md` dentro do alvo nas ultimas 24h.
- [ ] Zero alerta SEV1/SEV2 atribuido a esta release.
- [ ] Logs sem novo padrao de erro recorrente (> 10 ocorrencias).
- [ ] Feedback do canal de suporte sem aumento significativo de chamados.
- [ ] Changelog publico publicado.
- [ ] Tag git acessivel publicamente (se aplicavel).

Se algum item falhar -> abrir investigacao e considerar rollback parcial.

## 9. Breaking changes e deprecacao

Mudanca breaking (remove campo, muda contrato, muda comportamento padrao) exige:

1. **Anuncio previo** em release de pelo menos **N=2** versoes MINOR antes da remocao (ou 90 dias, o que for maior).
2. **Deprecacao** ativa: campo/endpoint continua funcionando mas emite warning (log, header `Deprecation`, banner no UI).
3. **Documentacao de migracao** em `docs/operacao/breaking-changes.md` antes da release que introduz a deprecacao.
4. **Comunicacao direta** com clientes integradores: e-mail + entrada em release notes + status page se afetar API publica.
5. **Remocao efetiva** so em release MAJOR (SemVer) ou release marcada como breaking em CHANGELOG (CalVer).

> Quebrar contrato sem deprecacao previa exige ADR + aprovacao de lider-tecnico + comercial.

## 10. Vinculacao com

- `docs/operacao/change-management.md` — janelas de mudanca e freeze que regem **quando** uma release pode sair.
- `docs/operacao/deployment-strategy.md` — detalhe tecnico de como o rollout e executado.
- `docs/operacao/slo-sli.md` — baseline de metricas usado nos gatilhos de rollback automatico.
- `docs/operacao/runbooks/rollback-release.md` (instanciar via `runbook.template.md`) — passo a passo executavel de rollback manual.
- `docs/decisoes/ADR-XXXX-versionamento.md` — escolha entre SemVer e CalVer.
- `INV-AGENT-XXX` — invariantes de seguranca aplicaveis a artefatos de release (assinatura, integridade).
- `auditores/release-auditor.md` — checagem automatica de presenca de changelog, tag anotada, RC verde.
