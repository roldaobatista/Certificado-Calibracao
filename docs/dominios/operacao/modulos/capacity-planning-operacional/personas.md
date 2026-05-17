---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: capacity-planning-operacional
dominio: operacao
---

# Personas — Capacity Planning Operacional

> Específicas. Transversais em `../personas.md` e `docs/comum/personas.md`.

---

## P-CPO-01 — Gerente de Operações

**Identidade:** responsável pela entrega; presta conta de prazo e produtividade; 35-55 anos; conhece todos os técnicos pelo nome.

**Goals:**
- Saber a capacidade real disponível por semana, equipe e laboratório
- Decidir contratação baseado em dado, não no "achismo"
- Detectar gargalo com 2-4 semanas de antecedência

**Frustrations:**
- Descobrir sobrecarga quando o cliente já está reclamando
- Agenda visual não mostra "quanto sobra"
- Cada técnico responde "tá tranquilo" e ninguém vê o todo

**Jornada típica:**
1. Abre painel consolidado pela manhã
2. Vê heatmap de ocupação por equipe nas próximas 8 semanas
3. Identifica gargalo (laboratório dimensional na semana 5)
4. Roda simulação "remanejar 3 OS pra técnico B"
5. Aplica distribuição sugerida

**Devices:** web desktop.
**Frequência:** diária.

---

## P-CPO-02 — Atendente / Comercial (consumidor)

**Identidade:** quem promete prazo ao cliente; primeira linha; 25-45 anos.

**Goals:**
- Prometer prazo realista, sem precisar ligar pro gerente
- Ver disponibilidade do tipo de serviço antes de confirmar

**Frustrations:**
- Prometer e descobrir depois que não cabe
- Ter que esperar gerente confirmar

**Jornada típica:**
1. Cliente pede calibração de balança até dia X
2. Atendente vê widget "capacidade até dia X" em verde/amarelo/vermelho
3. Confirma com tranquilidade ou negocia data alternativa sugerida

**Devices:** web desktop + tablet.
**Frequência:** várias vezes ao dia.

---

## P-CPO-03 — Coordenador de Laboratório

**Identidade:** responsável pelo laboratório de calibração; conhece bancadas, equipamentos-padrão, turnos.

**Goals:**
- Otimizar uso das bancadas e equipamentos-padrão
- Antecipar manutenção/calibração dos próprios padrões

**Frustrations:**
- Bancada parada por falta de planejamento
- Dois técnicos disputando mesmo equipamento-padrão

**Jornada típica:**
1. Atualiza disponibilidade do laboratório (manutenção, calibração interna)
2. Confere distribuição de carga por bancada
3. Reajusta quando equipamento-padrão sai pra calibração externa

**Devices:** web desktop.
**Frequência:** diária.

---

## Convenções

Se persona aparecer em ≥2 módulos com mesma responsabilidade, promover.
