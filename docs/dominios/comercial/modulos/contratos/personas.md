---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contratos
dominio: comercial
diataxis: reference
---

# Personas — Módulo Contratos

## P-CTR-01 — Dono (configurador, persona dominante)

Referência: P-COM-05.

**Goals específicos:**
- Configurar templates de contrato (calibração padrão, manutenção trimestral, instalação anual).
- Definir política de reajuste (IGP-M, IPCA, % fixo) e configurar alertas (90/60/30 dias).
- Ver MAPA-DO-DONO com MRR atual + previsão + alertas de churn.
- Auditar contratos suspensos/encerrados (entender motivos).

**Frequência:** semanal/mensal.

---

## P-CTR-02 — Vendedor (negociador + renovador)

Referência: P-COM-02.

**Goals:**
- Negociar novo contrato (longo lifetime = comissão maior).
- Renovar contratos antes do fim (wizard em < 5 min).
- Acompanhar contratos "a vencer" da própria carteira (60-90 dias antes).
- Aditivar quando cliente expande escopo (mais equipamentos).

**Frustrations:**
- "Esqueci de renovar o contrato do João — ele saiu pro concorrente."
- "Cliente pediu pra mudar escopo, virou virou negociação inteira nova."

**Devices:** desktop principal.
**Frequência:** semanal.

---

## P-CTR-03 — Atendente (revisor de pré-OS)

Referência: P-COM-01.

**Goals:**
- Bandeja "pré-OS pendentes" diária — revisar e confirmar (US-CTR-002).
- Ajustar pré-OS se necessário (data, técnico) antes de virar OS formal.
- Receber alerta se contrato gerou pré-OS com cliente bloqueado.

**Frequência:** diária (bandeja matinal).

---

## P-CTR-04 — Cliente final (titular do contrato)

Referência: P-COM-03.

**Goals:**
- Visualizar contrato no portal (escopo + vigência + próximos atendimentos).
- Encerrar contrato facilmente (US-CTR-005 — anti-fidelidade) sem ouvir argumentos retenção.
- Aprovar aditivo/renovação digitalmente.
- Pedir suspensão temporária.

**Frustrations (do mundo atual):**
- "Tenho que ligar pra saber quando vai vencer."
- "Pra cancelar, me passam pra 4 pessoas em call de retenção."

**Devices:** mobile principal (consumo via portal/link).
**Frequência:** raro (pontos de inflexão: aprovar, renovar, encerrar).

---

## P-CTR-05 — Financeiro (consultor)

Referência transversal: Cláudia.

**Goals no módulo:**
- Ver lista de contratos x parcelas previstas vs realizadas (alimenta `financeiro`).
- Marcar cliente bloqueado para impedir geração de pré-OS.

**Permissões:** read em contratos; write na flag "bloqueio" (já no módulo Clientes — propaga aqui).

---

## Anti-personas

- **Vendedor agressivo que quer "amarrar" cliente com multa pesada:** módulo proíbe (princípio anti-fidelidade).
- **Sistema legado que quer auto-renovação silenciosa:** proibido — renovação sempre exige ação humana.

## Convenções

P-CTR-05 Financeiro reaparece como persona transversal — promover pra `../../personas.md` (já existe P-CLI-04 similar; consolidar).
