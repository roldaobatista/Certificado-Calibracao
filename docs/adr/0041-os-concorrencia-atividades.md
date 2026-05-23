---
adr: 0041
titulo: Concorrência de atividades no mesmo equipamento — matriz tipo×tipo
status: proposta
data: 2026-05-23
proposto-por: agente (Onda 6 saneamento pré-Marco 3 — auditor 5)
revisado-por: tech-lead-saas-regulado (pendente)
bloqueia-fase: Wave A Marco 3 (`os`)
depende-de: ADR-0023 (OS com Atividades)
---

# ADR-0041 — Concorrência de atividades no mesmo equipamento

## Contexto

ADR-0023 cravou que 1 OS contém N AtividadeDaOS, cada uma com tipo
próprio. Não cravou regra de concorrência: o que acontece quando duas
atividades sobre o **mesmo equipamento físico** estão em
`EM_EXECUCAO` simultaneamente?

Operação real expõe incompatibilidades:

- Manutenção corretiva desmonta o instrumento (peças fora). Calibração
  no mesmo período produz medições inválidas — instrumento não está
  íntegro.
- Verificação INMETRO exige integridade do lacre. Calibração e
  verificação simultâneas corrompem o resultado regulatório.
- Treinamento (uso simulado) não impede outra atividade — o equipamento
  está disponível pra observação sem alteração metrológica.

Sem matriz, dois técnicos podem iniciar atividades incompatíveis no
mesmo equipamento — vira NC silenciosa CGCRE + retrabalho.

## Decisão

Matriz fixa `tipo × tipo` para o mesmo `equipamento_id` em estado
`EM_EXECUCAO`. Servidor valida em `iniciarAtividade` (US-OS-003).

| Tipo A → Tipo B (simultâneos) | Compatível? | Razão |
|---|---|---|
| manutencao_corretiva ↔ calibracao | INCOMPATÍVEL | peças desmontadas durante manutenção corretiva invalidam medição |
| manutencao_corretiva ↔ verificacao_inmetro | INCOMPATÍVEL | lacre INMETRO violado |
| manutencao_corretiva ↔ manutencao_preventiva | INCOMPATÍVEL | mesmo equipamento desmontado por 2 técnicos |
| manutencao_preventiva ↔ calibracao | OK SE cronograma | calibração de verificação após preventiva é fluxo normal — gate de sequência ADR-0023 trata |
| manutencao_preventiva ↔ verificacao_inmetro | INCOMPATÍVEL | preventiva pode mexer no lacre |
| calibracao ↔ verificacao_inmetro | INCOMPATÍVEL | dois procedimentos sobre o mesmo lacre |
| calibracao ↔ calibracao (mesma grandeza) | INCOMPATÍVEL | mesmo padrão sendo aplicado em paralelo |
| calibracao ↔ calibracao (grandezas distintas) | OK | grandezas independentes (massa × volume) |
| instalacao ↔ qualquer | INCOMPATÍVEL | equipamento ainda não está em local definitivo |
| vistoria ↔ qualquer não-vistoria | INCOMPATÍVEL | vistoria observacional pura, sem intervenção física, mas exige estado estável |
| treinamento ↔ qualquer | OK | treinamento não muda estado metrológico |

Aplicação: `iniciarAtividade(atividade_id)` consulta atividades EM_EXECUCAO
no mesmo `equipamento_id` → se par incompatível → 412
`ConcorrenciaAtividadesIncompativel: [tipo_em_curso, tipo_solicitado]`.

Hook futuro: `os-concorrencia-check.sh` (débito Wave A — anotado em
`docs/governanca/gates-wave-a-consolidado.md`).

## Invariante

`INV-OS-CONC-001` — "atividades EM_EXECUCAO simultâneas no mesmo
equipamento exigem compatibilidade da matriz tipo×tipo (tabela
canônica ADR-0041)".

## Consequências

- **Positivas:** zero NC CGCRE por intervenção concorrente; rastreabilidade
  ISO 17025 cl. 7.4 preservada; técnicos forçados a sequenciar trabalho.
- **Negativas:** atendente precisa entender a matriz ao planejar OS
  combinada — mitigação: PRD §6 US-OS-009 já cobre gate de sequência;
  alerta no app quando bloquear.
- **Débito:** hook `os-concorrencia-check.sh` codado em Marco 3 P4.

## Alternativas rejeitadas

- "Travamento total de equipamento por OS aberta" — bloqueia uso paralelo
  legítimo (treinamento + reuniao com cliente).
- "Sem trava, confiar no atendente" — viola REGRA-RESOLVER-NAO-DOCUMENTAR.

## Como evolui

Tipo novo de atividade (ADR-0023 INV-OS-ATIV-003) exige extensão desta
matriz no mesmo ADR (apêndice) + atualização de hook.
