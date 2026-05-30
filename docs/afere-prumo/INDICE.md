---
owner: <responsavel>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 160
proposito: sitemap navegável da documentação do projeto, com links para todas as seções
---

<!--
template: INDICE.md
destino: docs/INDICE.md
uso: sitemap navegável da documentação do projeto.
validado-por: auditor-doc-quality (regra: links e existência de arquivos).
-->

# Índice da Documentação — Aferê Prumo

Mapa navegável de toda a documentação do projeto. Atualizar sempre que uma pasta ou documento contratual for adicionado/removido.

> Este índice é validado por `auditor-doc-quality` (regra: links e existência de arquivos). Qualquer entrada quebrada bloqueia marco.

## 1. Como navegar
- Documentos contratuais ficam na **raiz** do repositório (`AGENTS.md`, `REGRAS-INEGOCIAVEIS.md`, `README.md`, `MAINTAINERS.md`, `GLOSSARIO-ROLDAO.md`).
- Documentação de produto, processo e operação fica sob `docs/`.
- Estado vivo de execução fica sob `.agent/`.
- **Raiz tem precedência sobre `docs/`** em qualquer conflito de definição.
- **Dois glossários, escopos distintos:** `GLOSSARIO-ROLDAO.md` (raiz) é jargão técnico → dono não-técnico; `docs/glossario.md` é termo do domínio do produto. Não duplicar entradas entre eles.

## 2. Árvore de pastas

```
docs/
  adr/                       Decisões arquiteturais (ADR-NNNN-<slug>.md).
  conformidade/              LGPD, contratos, requisitos regulatórios.
    lgpd/                    ROPA, DPIA, política de retenção.
  dados/                     Modelo de dados, migrations, dicionário.
  descoberta/                Pesquisa, entrevistas (EE), personas.
    entrevistas/             Transcrições e snapshots de EE-NNN.
  dominios/                  Domínios de negócio.
    <dominio>/
      modulos/
        <modulo>/
          stories/           US-<ESC>-NNN e seus AC.
          tarefas/           T-<ESC>-NNN (ficam aqui, NÃO em docs/tarefas/ global).
          revisoes/          Revisões de subagentes por US.
  faseamento/                Fases do roteiro (kickoff, gates).
    <fase>/
  governanca/                Catálogo de auditores, riscos, invariantes-agente.
    catalogo-auditores.md    Lista canônica de auditores ativos.
    registro-de-riscos.md    Riscos mapeados (R-NNN).
    invariantes-agente.md    Invariantes observadas por subagentes (INV-AGENT-NNN).
    auditoria-saida.md       Resumo dos achados por marco.
  operacao/                  Runbooks, incidentes, SLO/SLI, observabilidade.
    runbooks/                Procedimentos operacionais executáveis.
    incidentes/              Post-mortems (YYYY-MM-DD-slug).
    slo-sli.md               Metas de nível de serviço.
    on-call.md               Plantão e escalonamento.
    backup.md                Política de backup.
    disaster-recovery.md     Plano de DR (RTO/RPO).
    change-management.md     Controle de mudança em produção.
    observabilidade.md       Métricas, logs, traces (OBS-NNN).
  qualidade/                 Casos de teste, estratégia de testes.
    casos-de-teste/          TST-NNN rastreáveis a ACs.
    estrategia.md            Estratégia de testes (pirâmide, gates).
  seguranca/                 Requisitos SEC, invariantes-tenant, modelo de ameaças.
    invariantes-tenant.md    INV-TENANT-NNN (isolamento multi-tenant).
    modelo-ameacas.md        STRIDE / DREAD / PASTA aplicado ao sistema.
    requisitos-sec.md        SEC-NNN.
  dados/                     Modelo de dados, migrations, dicionário.
    dicionario.md            Dicionário de campos / DAT-NNN.
    modelo.md                Modelo lógico/físico.
  glossario.md               Glossário de termos do PRODUTO/NEGÓCIO deste projeto.
.agent/
  CURRENT.md                 Foco atual e próximo passo. Único arquivo de estado vivo (cross-harness).
.claude/
  agents/                    Subagentes (orquestrador + auditores).
    maestro.md               Orquestrador-mestre do ciclo problema→spec→plan→tasks→marco.
    auditor-<dominio>.md     Auditores especializados (ver catálogo de auditores).
  memory/                    Memória canônica do Claude Code.
    constitution.md          Princípios fundadores. Único arquivo aqui.
```

> Nota: `CONVENCOES-DOC.md` §10 mantém a separação — `constitution.md` em `.claude/memory/`, `CURRENT.md` em `.agent/`. Sem cópia em duas pastas.

## 3. Entradas principais

| Caminho | Descrição |
|---|---|
| `AGENTS.md` | Contrato do projeto: identidade, stack, princípios, comandos. |
| `REGRAS-INEGOCIAVEIS.md` | Regras não-negociáveis (segurança, qualidade, processo). |
| `SECURITY.md` | Política de segurança e canal de divulgação responsável. |
| `MAINTAINERS.md` | Mantenedores ativos, processo de release, sucessão. |
| `CONTRIBUTING.md` | Fluxo de contribuição (humanos e agentes). |
| `docs/CONVENCOES-DOC.md` | Nomenclatura, IDs, links, TODO/FIXME. |
| `docs/documentos-do-projeto.md` | Status de cada documento contratual. |
| `GLOSSARIO-ROLDAO.md` (raiz) | Tradução do jargão técnico (PR, commit, lint, deploy...) para linguagem de dono não-técnico. **Canônico para o método.** |
| `docs/glossario.md` | Glossário dos termos do **domínio do produto** (entidades, papéis, estados de máquina). **Canônico para o domínio.** |
| `docs/nao-aplica.md` | Camadas/contratos que não se aplicam a este projeto (com justificativa). |
| `docs/adr/` | ADRs aceitas, propostas e rejeitadas. |
| `docs/faseamento/<fase>/kickoff.md` | Kickoff de cada fase. |
| `docs/governanca/catalogo-auditores.md` | Lista canônica de auditores ativos. |
| `.claude/agents/maestro.md` | Orquestrador-mestre do ciclo problema→spec→plan→tasks→marco. |
| `docs/seguranca/invariantes-tenant.md` | INV-TENANT-NNN. |
| `docs/qualidade/casos-de-teste/` | TST-NNN rastreáveis a ACs. |
| `docs/dados/dicionario.md` | Dicionário de dados / DAT-NNN. |
| `docs/operacao/runbooks/` | Procedimentos operacionais executáveis. |
| `docs/operacao/on-call.md` | Plantão e escalonamento. |
| `docs/operacao/backup.md` | Política de backup. |
| `docs/operacao/disaster-recovery.md` | Plano de DR (RTO/RPO). |
| `docs/operacao/change-management.md` | Controle de mudança em produção. |
| `docs/operacao/observabilidade.md` | Logs, métricas, traces, dashboards, alerting. |
| `docs/operacao/release-process.md` | Versionamento, changelog, tag, rollout, rollback. |
| `docs/operacao/deployment-strategy.md` | Rolling, blue-green, canary, feature flags. |
| `docs/operacao/capacity-planning.md` | Forecast, dimensionamento, auto-scaling. |
| `docs/operacao/performance-testing.md` | Load, stress, soak, spike. |
| `docs/seguranca/threat-model.md` | STRIDE por componente, atacantes, trust boundaries. |
| `docs/seguranca/dependency-policy.md` | Critérios de pacote, max-age, SBOM, scanning. |
| `docs/conformidade/lgpd/ropa.md` | Registro de Operações de Tratamento. |
| `docs/conformidade/lgpd/retencao-dados.md` | Política de retenção. |
| `.claude/memory/constitution.md` | Princípios fundadores (canônica). |
| `.agent/CURRENT.md` | Foco atual da sessão (canônica, cross-harness). |

## 4. Como adicionar uma nova entrada
1. Criar o documento seguindo `docs/CONVENCOES-DOC.md`.
2. Registrá-lo em `docs/documentos-do-projeto.md` com status, owner e data.
3. Adicionar linha neste índice apontando para o caminho relativo.
4. Se for documento contratual, atualizar também `AGENTS.md` quando aplicável.

## 5. Como manter este índice em dia

Manutenção é manual (não há geração automática). O maestro deve atualizar este arquivo no MESMO turno em que cria/move/remove documento em `docs/`. Para detectar drift, rode periodicamente o snippet abaixo no git-bash a partir da raiz do projeto e cruze com o conteúdo de §3:

```bash
# Lista todos os .md em docs/ + raiz que deveriam estar listados aqui
find docs -type f -name "*.md" 2>/dev/null | sort
find . -maxdepth 1 -type f -name "*.md" 2>/dev/null | sort

# Diff dos paths citados neste índice vs paths reais (manual; serve como olhômetro)
grep -oE '`docs/[^`]+\.md`|`\.[a-z./-]+\.md`' INDICE.md | sort -u
```

O `auditor-doc-quality` é o gate formal: ele falha se algum link em §3 apontar para arquivo inexistente, e isso bloqueia fechamento de marco. Use o snippet acima para evitar surpresa do auditor.
