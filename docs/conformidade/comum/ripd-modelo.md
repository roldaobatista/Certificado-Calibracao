---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# RIPD / DPIA — modelo de Relatório de Impacto à Proteção de Dados

> **Pra quê:** LGPD art. 38 + ANPD orientam que tratamento de alto risco exija RIPD documentado **antes** do release. Este é o template.

---

## Quando é obrigatório

- Tratamento de dados sensíveis (saúde, biometria, religião, opinião política) — não-aplicável MVP-1
- Geolocalização contínua de pessoas (RAT-07: GPS técnico de campo)
- Tratamento em larga escala
- Decisão automatizada que afete pessoas (e.g., classificação automatizada de risco creditício — não-aplicável)
- Vigilância sistemática
- Novas tecnologias (LLM autônomo decidindo sobre dados pessoais — V2)

---

## Template (copiar pra `RIPD-<ID>-<resumo>.md`)

```markdown
---
ripd_id: RIPD-NN
operacao: <ID do RAT>
data_avaliacao: YYYY-MM-DD
revisor: <DPO ou Roldão se DPO ainda não designado>
status: draft|aprovado|implementado|revisar
---

# RIPD-NN — <título>

## 1. Operação avaliada
- Operação: [referência ao `lgpd-rat.md` RAT-XX]
- Descrição em PT-BR claro: [...]
- Categoria de dado: [identificação | sensível | comportamento | ...]
- Quantidade de titulares afetados (estimativa): [N]
- Frequência: [única | recorrente | contínua]

## 2. Necessidade e proporcionalidade
- Por que coletar esse dado? [...]
- Quais alternativas foram consideradas e por que rejeitadas? [...]
- Minimização: estamos coletando o mínimo? Sim/não — justificar.

## 3. Bases legais (LGPD art. 7 ou 11)
- Base primária: [V (execução contrato) | II (obrigação legal) | IX (legítimo interesse) | I (consentimento) | ...]
- Justificativa: [...]
- Se legítimo interesse: balanceamento de teste em §6

## 4. Riscos identificados
| ID | Risco | Probabilidade (1-5) | Impacto (1-5) | Score |
|----|-------|---------------------|----------------|-------|
| R1 | [descrição] | N | N | N |
...

## 5. Medidas de mitigação
| Risco | Medida | Resíduo |
|-------|--------|---------|
| R1 | [...] | [aceitável | inaceitável] |
...

## 6. Balanceamento de legítimo interesse (se aplicável)
- Finalidade legítima: [...]
- Necessidade: [...]
- Equilíbrio: [...] (impacto positivo vs negativo)

## 7. Direitos do titular
- Como exerce: [referência a `lgpd-rat.md` §4]
- Canais disponíveis: [...]

## 8. Transferência internacional?
- Sim/não: [...]
- País destino: [...]
- Base legal da transferência: [decisão de adequação | cláusulas-padrão | ...]

## 9. Decisão
- ✅ Aprovado pra implementar
- ⚠️ Aprovado com restrições: [...]
- ❌ Rejeitado: [razão]

## 10. Revisão
- Próxima revisão: [data, geralmente anual]
- Gatilhos pra revisão antecipada: [mudança de norma, incidente, mudança de operação]

## 11. Histórico
| Data | Mudança | Quem |
|------|---------|------|
| ... | ... | ... |
```

---

## RIPDs obrigatórios no Aferê

| ID | Operação | Status |
|----|----------|--------|
| RIPD-01 | RAT-07 geolocalização técnico de campo | ⏳ a fazer antes do release mobile |
| RIPD-02 | RAT-09 telemetria + analytics | ⏳ a fazer antes de ligar |
| RIPD-03 | LLM chatbot CS (V2) | ⏳ a fazer antes do release V2 |
| RIPD-04 | A3 + chain of trust (gestão de certificados ICP-Brasil) | ⏳ avaliação de necessidade |

---

## Pendências

- [ ] DPO formal designado pra aprovar RIPDs (diferido V2)
- [ ] Pasta `conformidade/comum/ripd/` com RIPDs individuais (criar quando primeiro existir)

---

## Referências

- LGPD art. 38 + 50
- ANPD Resolução 2/2022 (orientações sobre RIPD)
- `lgpd-rat.md`
- `seguranca-dados.md`
