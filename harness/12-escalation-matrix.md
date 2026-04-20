# 12 — Matriz de escalonamento e rito de desempate

> **P0-8**: a autoridade de cada agente está clara em `03-agentes.md`, mas o **rito de desempate** quando dois ou mais agentes autoritativos divergem não estava explicitado. Sem isso, divergência trava merge sem resolução formal.

## 1. Tipos de divergência previstos

| # | Divergência | Exemplo concreto |
|---|-------------|------------------|
| D1 | `regulator` × `metrology-calc` | Como interpretar tolerância numérica entre ILAC G8 e EURAMET cg-18 |
| D2 | `regulator` × `backend-api` | Se é aceitável cachear decisão normativa por OS ou recalcular a cada emissão |
| D3 | `lgpd-security` × `product-governance` | Claim comercial que é legalmente defensável mas comercialmente arriscado |
| D4 | `db-schema` × `lgpd-security` | Política de retenção vs performance de audit log |
| D5 | `metrology-calc` × `qa-acceptance` | Tolerância numérica em assertion de teste |
| D6 | `regulator` × `regulator` (versão da norma) | Norma atualizada durante a task; qual versão vale |
| D7 | `product-governance` × qualquer técnico | Release gate bloqueado por risco regulatório contra recomendação técnica |
| D8 | `regulator` × `regulator` (dupla checagem) | Passagem A (spec apenas) e Passagem B (spec + pacote normativo anexado) deram resultados divergentes. Ver `15-redundancy-and-loops.md` §3 |
| D9 | Auditor externo × executor interno | `metrology-auditor` bloqueia mas `regulator` discorda; ou `legal-counsel` bloqueia mas `lgpd-security` discorda; ou `senior-reviewer` bloqueia mas dono do path discorda. Ver `16-agentes-auditores-externos.md`. **Precedência**: auditor prevalece em risco regulatório/jurídico/arquitetural; override exige ADR + aprovação do usuário ciente do risco |

## 2. Ordem de precedência por domínio

**Técnica-metrológica (cálculo, incerteza, método):**
`metrology-calc` propõe → `regulator` valida contra norma → `product-governance` aprova release.

**Normativa (interpretação de DOQ, NIT, Portaria, ILAC):**
`regulator` é a autoridade primária → `product-governance` não reverte interpretação normativa; apenas decide se **release** aceita o risco.

**Jurídica (LGPD, claim, assinatura, retenção):**
`lgpd-security` é a autoridade primária → exige parecer jurídico datado em `compliance/legal-opinions/` antes de qualquer override.

**Arquitetural (onde mora regra, como flui dado):**
`backend-api` propõe → `db-schema` valida persistência/tenant → `product-governance` aprova se impacta audit ou emissão.

**Release gate:**
`product-governance` tem **veto absoluto** na publicação. Não pode forçar código, mas pode bloquear release.

## 3. Rito de desempate (obrigatório)

### Passo 1 — Divergência detectada
Qualquer agente que identifique divergência com outro autoritativo abre entrada em `compliance/escalations/<YYYY-MM-DD>-<slug>.md` com template:

```markdown
# Escalation <slug>
- Data: <ISO-8601>
- Trigger: <PR / incidente / revisão>
- Agentes envolvidos: <lista>
- Divergência: <uma linha>

## Posições
### <agente A>
<argumento + referência normativa/técnica>

### <agente B>
<argumento + referência>

## Impacto se não resolvido
<bloqueio de release / risco regulatório / dívida técnica>
```

### Passo 2 — Tentativa de consenso assíncrona
- Prazo: **24h úteis**.
- Agentes se respondem em comentários no próprio arquivo.
- Se consenso, preenche seção `## Resolução` e fecha.

### Passo 3 — Quorum formal
- Se não houve consenso em 24h: **quorum mínimo de 2 humanos autoritativos** (owners declarados em `.claude/agents/` + CODEOWNERS).
- Decisão registrada na escalation com assinatura (nome + timestamp).

### Passo 4 — Tiebreaker humano
Se quorum também empatar:
- **Tiebreaker designado**: papel humano único — "Responsável Técnico do Produto" — documentado em `adr/0002-tiebreaker-designation.md`.
- Decisão do tiebreaker é final para aquela escalation.
- Prazo total (passos 1–4): **48h úteis**.

### Passo 5 — Aprendizado
Se a escalation revelou lacuna de política:
- Abrir PR em `compliance/` atualizando a regra.
- Criar/atualizar ADR correspondente.
- Notificar `product-governance` para adicionar à checklist de release seguinte.

## 4. Regras duras

- **Ninguém faz merge durante escalation aberta** em área afetada.
- **Tiebreaker não é flexível**: mesmo humano desempata até que sucessor seja designado por ADR.
- **Override de gate automático** (quando o sistema diz "não" e humano diz "sim") exige:
  - ADR dedicada explicando contexto único.
  - Aprovação de `product-governance` + tiebreaker.
  - Entrada em `compliance/overrides-log.md` com data de expiração.
  - Próxima release revisa o override.
- **Norma atualizada durante task (D6)**: congela a task, cria draft de `normative-package` (ver `04-compliance-pipeline.md`), task só retoma após pacote assinado.

## 5. SLAs

| Passo | SLA | Escalação automática |
|-------|-----|----------------------|
| Detecção → abertura de escalation | Imediato no PR | — |
| Consenso assíncrono | 24h úteis | Quorum formal |
| Quorum formal | 12h úteis adicionais | Tiebreaker |
| Tiebreaker | 12h úteis | Freeze de release até resolução |
| Total máximo | 48h úteis | — |

Em incidente de segurança/LGPD: SLAs reduzidos a **1h / 4h / 24h** respectivamente; `lgpd-security` tem prioridade automática.

## 6. Não-objetivos desta matriz

- Não cria hierarquia fixa de agentes (eles continuam com autoridade de domínio).
- Não substitui pareceres jurídicos — apenas formaliza como decidir quando o parecer não basta.
- Não bypassa CODEOWNERS — os dois mecanismos se somam.

## 7. Exemplo resolvido (caso de uso)

`regulator` diz que OS com padrão fora da faixa bloqueia emissão; `backend-api` propõe cache de 24h da decisão normativa para performance.
- D2 aberta.
- Precedência: regulatória prevalece; cache proibido se altera decisão de bloqueio.
- Resolução: cache permitido apenas para leitura de pacote normativo vigente; decisão de bloqueio é sempre recomputada por emissão.
- ADR gerada para formalizar a regra.
