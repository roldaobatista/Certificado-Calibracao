---
template: MAINTAINERS.template.md
destino: MAINTAINERS.md
owner: <owner-do-projeto>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
proposito: lista de mantenedores ativos, criterios de entrada/saida, governanca e succession
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C0
limite-linhas: 250
---

# MAINTAINERS — Aferê Prumo

> **Mantenedor** = pessoa com permissao de merge, deploy, ou decisao sobre rumo do projeto. Esta lista e fonte de verdade — quem nao esta aqui nao tem essas permissoes.

## 1. Mantenedores ativos

| Nome | GitHub | Area principal | Contato | Ativo desde | MFA confirmado |
|---|---|---|---|---|---|
| <Nome 1> | @<handle> | <ex: backend, infra, frontend, seguranca, owner-geral> | <email/canal> | 2026-05-28 | <sim/nao> |
| <Nome 2> | @<handle> | <area> | <email/canal> | 2026-05-28 | <sim/nao> |
| <Nome 3> | @<handle> | <area> | <email/canal> | 2026-05-28 | <sim/nao> |

> Mantenedor sem MFA confirmado tem permissoes **suspensas** ate regularizar (ver `SECURITY.md` §MFA).

## 2. Owner do projeto

| Papel | Nome | Contato | Responsabilidade |
|---|---|---|---|
| Owner | <Nome> | <contato> | decisao final em impasse, succession, mudanca de licenca |

Owner pode tambem ser mantenedor; se for, aparece tambem na secao 1.

## 3. Criterios de promocao a mantenedor

Candidato vira mantenedor quando atinge **todos** os criterios:

| Criterio | Limite minimo |
|---|---|
| Tempo de contribuicao | >= 3 meses ativos |
| PRs aprovados como autor | >= <N, ex: 10> de qualidade consistente |
| Issues triadas/resolvidas | >= <M, ex: 15> |
| Reviews uteis em PRs alheios | >= <K, ex: 20> |
| Recomendacao | de >= 2 mantenedores existentes |
| Aceitacao do owner | sim |
| MFA ativo nas contas de codigo e cofre | sim |
| Aceite do CODE_OF_CONDUCT e CONTRIBUTING | sim |

Periodo de prova: **30 dias** com permissoes completas, observacao pelos mantenedores. Reversivel se houver problema.

Anuncio publico em release notes / canal oficial.

## 4. Criterios de hand-off / saida

Mantenedor sai (ou e movido para "emeritus") em qualquer destes:

| Situacao | Acao | Prazo |
|---|---|---|
| Inatividade > 6 meses | mover para "emeritus", remover permissoes ativas | imediato apos confirmacao |
| Pedido proprio | hand-off ordenado de areas + revogacao | <= 30 dias |
| Mudanca de empresa/projeto sem interesse em continuar | mover para "emeritus" | imediato |
| Quebra grave de CODE_OF_CONDUCT | suspensao imediata + processo de conflict resolution (§8) | imediato |
| Comprometimento de credencial | revogacao imediata + rotacao | imediato |

**Hand-off** inclui: lista de areas que cobria, PRs em aberto, ADRs em discussao, contatos externos, segredos a rotacionar.

### 4.1 Maintainers emeritus

Lista de quem ja foi mantenedor e nao tem mais permissoes operacionais, mas pode ser consultado:

| Nome | GitHub | Periodo | Motivo da saida |
|---|---|---|---|
| <Nome> | @<handle> | 2026-05-28 → 2026-05-28 | <motivo> |

## 5. SLA de resposta

Por severidade da demanda recebida (issue, PR, mensagem direta):

| Severidade | Tipo tipico | Tempo de **primeira resposta** | Tempo de **resolucao** |
|---|---|---|---|
| CRITICO | vulnerabilidade ativa, producao caida, regressao bloqueante | 24 horas | conforme `SECURITY.md` |
| ALTO | bug que afeta muitos usuarios, PR de fix de seguranca | 72 horas | 7 dias corridos |
| NORMAL | feature nova, bug em caso menor, duvida tecnica | 7 dias corridos | conforme prioridade |
| BAIXO | docs, refactor cosmetico, opiniao | 14 dias corridos | sem SLA |

SLA aplica **horario util** do mantenedor responsavel. CRITICO pode escalar fora do horario via canal de emergencia (`<canal>`).

## 6. Processo de release

| Etapa | Quem faz | Como verifica |
|---|---|---|
| Cut da release branch / tag candidata | <mantenedor-release> | CI verde, CHANGELOG atualizado |
| Teste em ambiente de staging | <mantenedor-qa ou owner da area> | suite de smoke + manual checklist |
| Aprovacao final | owner OU 2 mantenedores | assinatura/aprovacao no PR de release |
| Assinatura do artefato | <mantenedor-com-chave> | release assinada com chave conforme `SECURITY.md` |
| Publicacao | <mantenedor-release> | release publicada, anuncio enviado |
| Pos-release: monitorar 24h | <mantenedor-ops> | metricas, telemetria, canais de suporte |

Nenhuma release sai com **apenas uma pessoa** envolvida (regra de 2 olhos minimo).

## 7. Governanca de decisoes

### 7.1 Consenso (padrao)

A maioria das decisoes vem por **consenso lazy**: proposta circula, sem objecao fundamentada em <prazo, ex: 5 dias uteis>, aprovada.

### 7.2 Decisoes que exigem ADR

Toda decisao tecnica que afeta arquitetura ou contrato publico vira ADR em `docs/decisoes/`. ADR e revisada por >= 2 mantenedores antes de merge.

### 7.3 Fallback a votacao

Quando consenso falha, **votacao por maioria simples** entre mantenedores ativos:

- Quorum minimo: 50% + 1 dos mantenedores ativos.
- Voto do owner desempata.
- Resultado registrado em ADR ou no thread da decisao.
- Voto e publico entre mantenedores; pode ser anonimo a comunidade quando topico for sensivel.

### 7.4 Decisoes exclusivas do owner

- Mudanca de licenca.
- Mudanca de owner.
- Transferencia/arquivamento do repositorio.
- Aceitacao de patrocinio formal.
- Remocao de mantenedor por quebra grave (com input de outros mantenedores).

## 8. Conflict resolution

| Nivel | Escalacao | Quem decide |
|---|---|---|
| 1 — Conversa direta | entre as partes envolvidas | as partes |
| 2 — Mediacao interna | mantenedor neutro convidado | mediador + partes |
| 3 — Comite de mantenedores | >= 3 mantenedores nao envolvidos | maioria |
| 4 — Owner | owner ouve todos, decide | owner |

Decisao do owner e final dentro do projeto. CODE_OF_CONDUCT segue processo proprio (geralmente nivel 3 ou 4 direto).

## 9. Succession plan

O que acontece se mantenedor principal / owner sair sem hand-off ordenado:

1. **Detector**: mantenedor que perceba inatividade > 30 dias sem aviso aciona o grupo.
2. **Tentativa de contato**: ate 14 dias por canais conhecidos (email, mensagem, contato pessoal se houver).
3. **Sem retorno apos 60 dias**: assumir que houve saida silenciosa.
4. **Eleicao de owner interino**: maioria simples entre mantenedores ativos restantes.
5. **Acesso a recursos criticos**: chaves de assinatura, cofre, dominio, conta de organizacao — procedimento de recuperacao documentado em `docs/operacao/runbooks/succession.md` (acesso "break the glass" controlado, registro em audit).
6. **Comunicacao publica**: anuncio claro a comunidade dentro de 14 dias da eleicao.
7. **Periodo interino**: 90 dias. Apos, eleicao formal de owner permanente entre mantenedores ativos.

**Bus factor**: sempre **>= 2** pessoas com acesso a cada recurso critico (chave de assinatura, dominio, conta de cloud, cofre). Auditado anualmente.

## 10. Revisao desta lista

- Conferencia trimestral pela comunidade de mantenedores: quem esta ativo, MFA, areas cobertas.
- Revisao anual completa pelo owner, incluindo succession plan.
- Toda alteracao via PR aprovado por owner + 1 mantenedor.

## 11. Vinculacao com

- `CONTRIBUTING.md` — como virar contribuidor (passo anterior a mantenedor).
- `CODE_OF_CONDUCT.md` — regras de conduta cuja quebra gera processo de §8.
- `SECURITY.md` — MFA, rotacao de credenciais, canal de divulgacao.
- `governanca-comunidade.md` (a ser criado) — papel de contribuidores nao-mantenedores, conselhos consultivos.
- `docs/operacao/runbooks/succession.md` — procedimento operacional de break-the-glass.
- ADRs em `docs/decisoes/` — historico de decisoes que esta lista influenciou.
