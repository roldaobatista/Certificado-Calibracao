---
owner: roldao
revisado-em: 2026-05-28
idioma: pt-BR
status: draft
limite-linhas: 200
proposito: registrar camadas/templates que o projeto decidiu não aplicar e por quê, com gatilho de reavaliação
---

<!--
template: docs/nao-aplica.md
uso: copiar para docs/ na raiz.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C0
proposito: registrar camadas/artefatos da estrutura canônica que este projeto NÃO usa, com justificativa,
            evidência concreta, responsável pela revalidação e gatilho de reavaliação.
            Evita ser cobrado por auditor-meta sem ter contexto.
-->

# Não aplica — Aferê Prumo

> O que este projeto deliberadamente NÃO faz da estrutura canônica, e quando reavaliar.

## Regras de uso

- **Toda entrada exige evidência concreta.** Justificativa textual sozinha não basta — precisa link para schema, ADR, screenshot, configuração, ou outro artefato que prove a ausência.
- **Toda entrada exige `revalidacao-em` (data concreta).** Nenhuma exceção fica "pra sempre".
- **Toda entrada exige `responsavel-revalidacao`** (pode ser diferente do `owner` do doc — é quem vai conferir na data).
- Gatilho de reavaliação deve ser **evento observável**, não "talvez no futuro".
- Auditor-meta lê este arquivo: o que está aqui não gera finding; o que está faltando gera.
- Quando o gatilho disparar OU `revalidacao-em` vencer, mover a linha pra histórico abaixo e implementar a camada (ou justificar nova entrada com novo prazo).

### Exemplo do nível de prova exigido

- **NÃO ACEITAR:** "Projeto não trata dado pessoal."
- **ACEITAR:** "Projeto não trata dado pessoal — schema confirma só campos técnicos (link: `docs/dados/schema.md`), ADR-0003 documenta decisão, revalidar em 6 meses."

## Tabela de exceções

| Camada / Artefato | Não aplica porque | Evidência | Responsável revalidação | Revalidação em | Reavaliar quando |
|---|---|---|---|---|---|
| C12 / `docs/comunidade/` (OSS) | Produto comercial fechado (SaaS por assinatura); não é open-source. | Sem licença pública aberta; sem repositório público. | Roldão | 2026-11-28 | Abrir o código ou criar comunidade externa. |
| Internacionalização (i18n) | Operação só no Brasil, em pt-BR. | `restricoes.md` §4 (idioma pt-BR, mercado Brasil). | Roldão | 2026-11-28 | Atender cliente fora do Brasil. |

> **NÃO entram aqui (porque APLICAM a este projeto):**
> - **Multi-empresa / `INV-TENANT-*`**: a IA se conecta no **Aferê**, que é multi-tenant + RLS,
>   e o plano do dono já prevê `tenant_id`/`company_id`. Mesmo com a Balanças Solution sendo o
>   primeiro usuário (dogfooding), a infra **nasce multi-empresa** → isolamento de dados aplica.
> - **C6 LGPD + segurança**: trata dado pessoal de cliente (nome, telefone, CNPJ, histórico) via
>   WhatsApp e LLM → LGPD aplica. Plano já prevê pseudonimização pré-LLM, auditoria WORM e DPIA/RoPA.
>   Materializado na **fase-2** quando a `sintese-final.md` virar `stable`.
> - **ADR-0000 (uso de IA)**: usa LLM em produção (Claude) → obrigatório.
> - **C8 operação**: aplica quando entrar em produção (kill-switch de custo, observabilidade já no plano).

<!-- Adicionar uma linha por camada/artefato pulado. NUNCA pular sem registrar aqui —
     se não está nesta tabela, é porque o projeto deveria ter o artefato. -->

## Histórico (camadas reativadas)

<!-- Quando uma camada antes "não aplica" passa a aplicar, registrar aqui em vez de apagar. -->

| Camada | Data reativação | Motivo (gatilho que disparou) |
|---|---|---|
| <vazio> | | |

---

> **Link bidirecional:** revisar este NÃO-APLICA em `<revalidacao-em>` — se o gatilho mudou ou a evidência envelheceu, reabrir o doc original (LGPD, i18n, etc.) e mover a linha para o histórico acima.
