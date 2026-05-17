---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo SLA Contratual

> Personas específicas. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Gerente Comercial / Contas

**Identidade:** profissional comercial sênior, 30–50 anos, responsável por carteira de clientes recorrentes; negocia perfis de SLA e renovações.

**Goals deste módulo:**
- Cadastrar perfis de SLA reutilizáveis (Ouro/Prata/Bronze).
- Vincular perfil ao contrato sem retrabalho.
- Gerar relatório SLA para enviar ao cliente.
- Acompanhar % de cumprimento por cliente para defender renovação ou aumento.

**Frustrations específicas:**
- Cliente questiona SLA sem evidência objetiva.
- Penalidade aplicada errada gera reclamação e desgaste.
- Reabrir negociação por SLA mal calibrado.

**Jornada típica:**
1. Cria perfil "Ouro 24/7".
2. Vincula em contratos do segmento.
3. Mensalmente exporta relatório SLA e envia ao cliente.
4. Em reunião de QBR mostra dashboard de cumprimento.

**Devices:** web desktop.
**Frequência:** semanal (cadastro/ajuste) + mensal (relatório).

---

## Persona 2: Atendente / Despachante

**Identidade:** profissional operacional 20–40 anos, recebe chamados/OS e despacha técnico; primeiro a ver o cronômetro de SLA.

**Goals deste módulo:**
- Ver cronômetro de SLA em tempo real no chamado/OS.
- Priorizar chamados com SLA em risco.
- Pausar SLA quando depende do cliente, com justificativa.
- Escalar internamente antes do estouro.

**Frustrations específicas:**
- Estourar SLA por falta de visibilidade.
- Despausar manualmente e esquecer.
- Justificativas recusadas por não estarem em lista controlada.

**Jornada típica:**
1. Recebe chamado novo, vê cronômetro vermelho começando.
2. Despacha técnico mais próximo.
3. Cliente não atende → pausa SLA com motivo.
4. Cliente retorna → despausa e continua.

**Devices:** web desktop (call center).
**Frequência:** diário.

---

## Persona 3: Gerente de Operações

**Identidade:** responsável por SLA agregado de uma área/equipe; recebe alertas preventivos e escalonamentos nível 2.

**Goals deste módulo:**
- Receber alerta quando SLA atinge 80%.
- Realocar recursos antes do estouro.
- Acompanhar dashboard de cumprimento por equipe.

**Frustrations específicas:**
- Saber do estouro só quando cliente reclama.
- Não ter dado para decidir contratação/escala.

**Jornada típica:**
1. Recebe push: "SLA do chamado #1234 em 80%".
2. Verifica se técnico está em campo, redireciona se necessário.
3. Se não age em X min, escala para diretoria automaticamente.

**Devices:** web desktop + mobile.
**Frequência:** diário.

---

## Persona 4: Financeiro

**Identidade:** analista/coordenador financeiro; aplica penalidade/bonificação na fatura.

**Goals deste módulo:**
- Receber evento de penalidade/bonificação calculado.
- Aplicar valor na próxima fatura/nota.
- Auditar cálculo se cliente questiona.

**Frustrations específicas:**
- Cálculo manual sujeito a erro.
- Falta de evidência quando cliente contesta.

**Jornada típica:**
1. No fechamento, consulta eventos `SLA.PenalidadeCalculada` e `SLA.BonificacaoCalculada` do período.
2. Aplica na fatura do cliente.
3. Anexa relatório SLA como justificativa do ajuste.

**Devices:** web desktop.
**Frequência:** mensal (ciclo de faturamento).

---

## Convenções

- Persona específica = papel com responsabilidade única neste módulo.
- Persona "Cliente final" (que recebe o relatório) é transversal — fica em `docs/comum/personas.md`.
- Hook valida não-duplicação entre níveis.
