---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Template — Postmortem de incidente

> **Pra quê:** estrutura padrão pra escrever postmortem após qualquer SEV-0 ou SEV-1. Sem template antes do 1º incidente, postmortem vira "achei que era da rede" e perde aprendizado.

---

## Como usar este template

1. Copie pra `docs/operacao/postmortems/YYYY-MM-DD-<resumo-em-kebab>.md`
2. Preencha em até 30 dias após o incidente
3. Apresente ao Roldão; revisar com subagent `auditor-seguranca` se incidente foi de segurança
4. Atualizar `REGRAS-INEGOCIAVEIS.md` se uma regra nova nasceu deste postmortem
5. Versionar (não deletar postmortem antigo)

**Princípio blameless:** foco em sistema, não em pessoa. Pergunte "por que o sistema permitiu isso?", não "por que fulano fez isso?".

---

## Template — copiar a partir daqui

```markdown
---
owner: <responsável pela investigação>
revisado-em: <YYYY-MM-DD>
status: draft|stable
severidade: SEV-0|SEV-1|SEV-2|SEV-3
incidente_id: INC-<YYYY-MM-DD>-<resumo>
---

# Postmortem — <título curto do incidente>

## Resumo executivo (1 parágrafo)
<O que aconteceu, qual o impacto pro usuário/tenant, em quanto tempo foi resolvido. Linguagem clara — Roldão vai ler.>

## Linha do tempo

| T | Ação |
|---|------|
| T+0 | <detecção: como soubemos?> |
| T+? | <primeira ação> |
| T+? | <ação seguinte> |
| ... | ... |
| T+resolução | <quando voltou ao normal> |

## Impacto

- **Tenants afetados:** <lista ou "todos" ou "N tenants do perfil X">
- **Funcionalidade afetada:** <quais módulos>
- **Duração:** <minutos / horas>
- **Dados perdidos?** sim/não — <quantidade/tipo>
- **Dados expostos cross-tenant?** sim/não — <gatilho ANPD 72h se sim>
- **Receita perdida estimada:** R$ <valor>
- **Comunicação externa feita?** <ANPD, tenants, status page>

## Causa raiz (5 porquês)

1. <fato observável>
2. <por quê 1>
3. <por quê 2>
4. <por quê 3>
5. <causa raiz no sistema, não em pessoa>

## O que funcionou
- <ferramentas/processos que ajudaram>
- <decisões boas tomadas no momento>

## O que NÃO funcionou
- <onde demoramos mais que deveríamos>
- <ferramentas que faltaram ou falharam>
- <suposições erradas>

## Ações de remediação

| # | Ação | Tipo | Responsável | Prazo | Status |
|---|------|------|--------------|-------|--------|
| 1 | <ação concreta> | preventiva/detectiva/corretiva | <subagente ou Roldão> | <data> | aberto |
| 2 | ... | ... | ... | ... | ... |

> **Cada ação tem prazo e dono.** Sem isso, ação morre.

## Regras novas que nasceram deste incidente

- <ID novo em REGRAS-INEGOCIAVEIS.md, se aplicável>
- <Hook novo, se aplicável>
- <Subagente / prompt novo, se aplicável>

## Custo do incidente

- **Tokens LLM gastos em diagnóstico:** ~<estimativa>
- **Tempo Roldão:** <horas>
- **Custo Aferê (refund, brindes, perda de cliente):** R$ <valor>

## Lições aplicáveis a outros módulos

<O que aprendemos aqui que vale pra outras áreas do produto>

## Anexos
- Log relevante: <link ou copy>
- Trace OpenTelemetry: <link>
- Screenshot do alerta: <link>
- Mensagem ANPD enviada: <link, se aplicável>
- Comunicado a tenants: <link, se aplicável>
```

---

## Exemplos de incidente que dispara postmortem obrigatório

- Vazamento cross-tenant detectado
- Certificado de calibração emitido com erro de cadeia
- NF-e/NFS-e emitida em valor errado
- Sistema fora do ar > 30 min
- Backup falhou e não foi possível restaurar
- KMS chave perdida ou inacessível > 1h
- Comunicação a ANPD enviada
- Cliente cancelou por causa de incidente

---

## Calendário de revisão

- **Mensal:** Roldão revisa postmortems abertos + status das ações
- **Trimestral:** Auditor de Segurança roda metricas de tendência (mesmos tipos de incidente repetem?)
- **Anual:** revisão geral — quais ações nunca foram fechadas? por quê?

---

## Pre-MVP-1 (estado atual)

- ✅ Template (este doc)
- ⏳ Pasta `docs/operacao/postmortems/` não criada ainda (criar no 1º incidente real)
- ⏳ Nenhum incidente real ocorrido — não há postmortem ainda

---

## Referências

- [acionamento-agente.md](acionamento-agente.md) — quando incidente vira postmortem obrigatório
- `docs/governanca/RACI-incidente-ai.md` — quem responde
- `docs/governanca/trilha-auditoria-agentes.md` — registro append-only
- `REGRAS-INEGOCIAVEIS.md` — regras novas que saem de postmortem
