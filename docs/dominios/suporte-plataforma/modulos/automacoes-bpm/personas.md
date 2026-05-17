---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Automações & BPM

> Personas específicas deste módulo. Transversais ficam em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Configurador de Fluxos (BPM Designer)

**Identidade:** gestor de área (comercial, financeiro, técnico) ou TI interno do tenant; entende regra de negócio mas não programa; 30-55 anos.

**Goals deste módulo:**
- Desenhar fluxo de aprovação sem depender de desenvolvedor.
- Publicar/versionar regra sem derrubar o ERP.
- Testar regra em modo sandbox antes de publicar.

**Frustrations:**
- Regra fixa no código que não cabe na realidade da empresa.
- Não saber qual evento existe pra encaixar na condição.
- Mudar alçada e quebrar fluxo em produção.

**Jornada típica:**
1. Identifica gargalo (ex: "todo orçamento com desconto > 20% trava na minha mesa").
2. Abre editor visual, escolhe evento de origem (`Orcamentos.Submetido`).
3. Define condição (`desconto > 20%`), ação (`criar pendencia para grupo Gerentes`) e SLA (`24h`).
4. Publica em modo "shadow" (executa mas não bloqueia) por 1 semana.
5. Analisa logs e promove a "ativo".

**Devices:** web desktop primariamente.
**Frequência:** semanal-mensal (configura) + diário (consulta logs).

---

## Persona 2: Aprovador

**Identidade:** qualquer pessoa com alçada (gerente, diretor, técnico responsável, financeiro); recebe pendência e decide.

**Goals deste módulo:**
- Ver minhas pendências em um lugar só, com SLA visível.
- Aprovar/rejeitar com 1 clique + comentário curto.
- Delegar período de ausência sem expor senha.

**Frustrations:**
- Pendência espalhada por 5 telas diferentes.
- SLA estoura sem aviso.
- Não saber qual era a condição que disparou a pendência.

**Jornada típica:**
1. Recebe notificação (e-mail/WhatsApp/in-app) de nova pendência.
2. Abre painel "Minhas Aprovações" pelo link.
3. Lê contexto (qual orçamento, qual cliente, qual condição disparou, qual SLA).
4. Aprova/rejeita com comentário.
5. Evento publicado, fluxo prossegue.

**Devices:** mobile (notificação) + web (decisão).
**Frequência:** diário.

---

## Persona 3: Operador de Suporte (reprocessamento)

**Identidade:** equipe interna do tenant que monitora execuções e reprocessa falhas; pode ser TI ou suporte de produto.

**Goals:**
- Ver execuções falhadas em painel central.
- Reprocessar com 1 clique preservando payload original.
- Investigar causa raiz (gateway fora, payload malformado, regra com bug).

**Jornada típica:**
1. Recebe alerta de spike de falhas.
2. Filtra "Execuções > status FALHA > últimas 24h".
3. Identifica padrão (ex: "todas falharam no gateway WhatsApp").
4. Reprocessa em lote depois que gateway voltou.

**Devices:** web desktop.
**Frequência:** diário (rotina de monitoração).

---

## Convenções

- Persona específica = papel com responsabilidade ÚNICA neste módulo.
- "Aprovador" pode aparecer em outros módulos, mas aqui é a persona-chave operacional do BPM — manter aqui salvo se virar transversal a ≥2 módulos com mesma responsabilidade.
