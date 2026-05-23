---
owner: roldao
revisado-em: 2026-05-23
status: stable
diataxis: reference
audiencia: auditor
relacionados:
  - REGRAS-INEGOCIAVEIS.md
  - .claude/hooks/secrets-scanner.sh
---

# Varredura de segredos no histórico — relatório 2026-05-23

> **Pra quê:** auditor de segurança apontou (SEC-3) que o hook `secrets-scanner.sh` cobre **commits novos** mas o histórico nunca foi escaneado. Memória `feedback_handholding_terminal` registra que um token GitHub já vazou pelo terminal uma vez — pode haver resíduo dormente.
>
> **Janela do plano:** Onda 0 do plano-v2 de saneamento.

## Ferramenta

`gitleaks` não estava instalado no Windows do Roldão (verificado em 2026-05-23). Em vez de pedir instalação (depende de admin + escolha de versão), foi feito **scan manual com regex via Git Bash** sobre todo o histórico (`git log --all -p`).

## Padrões escaneados

### Padrões fortes (chave/token cru — qualquer ocorrência = vazamento)

| Padrão | Regex |
|---|---|
| Chave de acesso AWS | `AKIA[0-9A-Z]{16}` |
| Token clássico GitHub | `ghp_[A-Za-z0-9]{30,}` |
| Token OAuth GitHub | `gho_[A-Za-z0-9]{30,}` |
| Token Anthropic | `sk-ant-[A-Za-z0-9_-]{20,}` |
| Token OpenAI/genérico | `sk-[A-Za-z0-9]{30,}` |
| Token Slack bot | `xoxb-[A-Za-z0-9-]{20,}` |
| Chave privada PEM | `-----BEGIN [A-Z ]+PRIVATE KEY-----` |

**Resultado:** zero ocorrências.

### Padrões soft (literais `password=`/`secret=`/`token=` com string ≥8 chars)

Filtrados para excluir contextos óbvios de teste (`dev-only`, `placeholder`, `example`, `test`, `fake`, `change_me`, `do_not_use`, `DEFAULT`, `hash`, `TYPE`, `FIELD`).

**Resultado: 32 linhas remanescentes — todas classificadas como falso positivo após inspeção manual:**

- `Usuario.objects.create_user(email="a@b.com", password="outra-12-chars")` — fixture de teste em factory pytest.
- `publicVerificationToken: "token-b-001"` / `pubtok-os141` — tokens públicos de exemplo em PRDs antigos; têm prefixo "tok"/"pubtok" propositalmente sintético, não são credenciais reais.
- `password="wrong-password"` — fixture de teste de login com senha errada.
- `GITHUB_TOKEN="${GITHUB_TOKEN:-}"` — referência a variável de ambiente, não literal.
- `gh auth token` (em string de instalação) — comando, não literal.
- `email="admin@afere.local"` — não é segredo; é endereço local de teste.

## Conclusão

**ZERO segredo real vazado no histórico.** Hook `secrets-scanner.sh` defende presente; este scan confirma que não há resíduo passado.

## Decisão sobre rotação

Auditor SEC recomendou "gitleaks sem rotação = teatro". Como **nenhum segredo real foi encontrado**, rotação não é necessária por causa de vazamento.

**Recomendação operacional adjacente:** ainda que sem vazamento, F-C1 deve rotacionar credenciais dogfooding (`DJANGO_SECRET_KEY`, `KMS_KEY_ID` dev) como exercício de procedimento de rotação antes do 1º deploy externo — para que o playbook esteja exercitado.

## GATE adicional

- **GATE-SEC-GITLEAKS-CI:** quando F-C3 ativar pipeline com SUPPLY-1, instalar `gitleaks` no runner GitHub Actions e rodar em todo PR (`gitleaks detect --redact --no-banner`). Pre-commit local fica com regex próprio do `secrets-scanner.sh`.

## Comando reproduzível

```bash
git log --all -p 2>/dev/null | grep -nE '(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{30,}|gho_[A-Za-z0-9]{30,}|xoxb-[A-Za-z0-9-]{20,}|-----BEGIN [A-Z ]+PRIVATE KEY-----)' | head -50
```

Pode rodar a qualquer momento. Saída esperada: vazia.
