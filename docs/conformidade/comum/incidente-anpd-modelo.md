---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Modelo de notificação ANPD — incidente de segurança

> **Pra quê:** Resolução ANPD 15/2024 exige comunicação de incidente em até 3 dias úteis. Sem template pronto, escrever sob pressão produz erro + atraso. Este é o template.

---

## Quando notificar ANPD

Incidente que afete dados pessoais com **risco ou dano relevante** aos titulares. Critérios (ANPD):
- Vazamento de dados sensíveis
- Vazamento de dados em larga escala
- Risco à integridade física, moral, financeira do titular
- Acesso não-autorizado por terceiros

**Em dúvida, notificar.** Subagent `advogado-saas-regulado` consulta + humano licenciado pode ser acionado pontual.

---

## Prazo

**Até 3 dias úteis** após Aferê tomar conhecimento (ANPD Resolução 15/2024 art. 5).

Fluxo:
- T+0: detecção
- T+24h: comunicar tenant(s) afetado(s) se confirmado
- T+72h: comunicar ANPD via formulário oficial

---

## Template (copiar pra `INC-<YYYY-MM-DD>-<resumo>/notificacao-anpd.md`)

```markdown
---
incidente_id: INC-YYYY-MM-DD-<resumo>
data_deteccao: YYYY-MM-DD HH:MM
data_comunicacao_anpd: YYYY-MM-DD
status: draft | enviado | resposta_recebida
---

# Notificação ANPD — Incidente <ID>

## 1. Identificação do controlador / operador
- **Controlador:** [tenant afetado — razão social + CNPJ + DPO]
- **Operador:** Aferê <razão social + CNPJ + DPO Aferê>
- **Encarregado de contato:** <nome + e-mail + telefone>

## 2. Natureza do incidente
- Tipo: [vazamento | acesso não-autorizado | alteração indevida | perda | indisponibilidade prolongada]
- Descrição em linguagem clara: [...]
- Quando ocorreu (T-0): [...]
- Quando foi descoberto: [...]
- Como foi descoberto: [...]

## 3. Dados pessoais afetados
- Categorias: [identificação | sensível | financeiro | localização | ...]
- Volume: [N titulares afetados — estimativa]
- Possibilidade de identificação?: sim/não/parcial

## 4. Titulares afetados
- Quantidade total: [N]
- Categoria: [clientes finais do tenant X | funcionários | ...]
- Características: [...]
- Foram comunicados? Sim/não — se sim, quando + como; se não, justificativa.

## 5. Consequências possíveis
- Risco identificado: [financeiro | reputacional | discriminação | fraude | ...]
- Possibilidade de reversão: sim/não — explicar
- Indicações de uso fraudulento detectado?: [...]

## 6. Medidas de segurança vigentes na ocasião
- [listar TODAS — multi-tenant RLS, criptografia em repouso, audit log, ...]

## 7. Medidas tomadas após incidente
- T+15min: [contenção inicial]
- T+1h: [...]
- T+24h: [...]
- T+72h: [enviar esta notificação]
- T+30d: [postmortem público]

## 8. Causa raiz (5 porquês)
- [se já conhecida; se não, "investigação em curso, atualização em até 30 dias"]

## 9. Plano de remediação
- [ ] Ação 1 — prazo X — responsável Y
- [ ] Ação 2 — ...
- [ ] Postmortem completo — T+30d

## 10. Comunicação aos titulares
- Como serão comunicados: [e-mail | banner no app | mídia | ...]
- Quando: [...]
- Linguagem: PT-BR claro sem jargão técnico

## 11. Aprovação e assinatura
- DPO Aferê: [nome + data]
- Roldão (representante legal Aferê): [nome + data]
- Assinatura digital ICP-Brasil A3: [hash do PDF]
```

---

## Anexos obrigatórios

1. **Linha do tempo** detalhada (T+0 até comunicação)
2. **Lista de tenants afetados** (sem PII no doc; referência por ID)
3. **Evidências técnicas** (logs anonimizados, hash de queries, screenshot de alerta)
4. **Comunicado aos titulares** (modelo do que foi enviado)
5. **Postmortem inicial** (mesmo que parcial)

---

## Onde envia

Formulário oficial ANPD: https://www.gov.br/anpd (verificar URL atual)

Backup: e-mail formal pro DPO da ANPD com PDF assinado A3.

---

## Acompanhamento

- ANPD pode pedir esclarecimento → SLA resposta: 5 dias úteis
- ANPD pode determinar publicidade do incidente
- ANPD pode aplicar sanção (advertência → multa de 2% do faturamento limitado a R$ 50M)

---

## Pendências

- [ ] DPO formal designado (V2)
- [ ] Conta no portal ANPD criada (V2)
- [ ] Drill anual: simular incidente; redigir notificação completa em < 72h; medir tempo
- [ ] Template digital (formulário pronto, não markdown) — V2

---

## Referências

- LGPD lei 13.709 art. 48
- ANPD Resolução 15/2024
- `lgpd-rat.md` §5
- `incidente-postmortem.md`
- `RACI-incidente-ai.md`
