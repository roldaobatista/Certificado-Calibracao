---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Custeio Real

> Personas específicas deste módulo. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Dono / Sócio gestor

**Identidade:** dono da empresa de assistência técnica/calibração; quer entender rentabilidade real e tomar decisão de portfólio (manter/cortar cliente, ajustar preço, treinar técnico).

**Goals deste módulo:**
- Ver margem real consolidada do mês.
- Saber quais clientes são lucrativos e quais drenam.
- Saber quais técnicos têm muito retrabalho/garantia.
- Saber quais serviços têm margem baixa (candidatos a reprecificação).

**Frustrations específicas:**
- "Faturo bem mas o caixa não fecha — onde está vazando?"
- "Esse cliente sempre quer desconto — vale a pena mesmo?"
- "Esse técnico parece eficiente, mas custa muita garantia."

**Jornada típica:**
1. Abre dashboard "Margem por Cliente" do mês.
2. Identifica 3 clientes deficitários.
3. Vai pra detalhe → vê que 80% do prejuízo vem de retrabalho.
4. Decide renegociar preço com esses clientes.

**Devices:** web desktop.
**Frequência:** semanal/mensal.

---

## Persona 2: Gestor operacional / Coordenador técnico

**Identidade:** chefe técnico ou gerente operacional que acompanha execução das OSs e responde por margem operacional.

**Goals deste módulo:**
- Receber alertas de OS deficitária no mesmo dia do encerramento.
- Investigar causa raiz (estouro de horas, peça cara não orçada, deslocamento extra).
- Pedir nota de aditivo ao comercial quando OS estourou por mudança de escopo.

**Frustrations específicas:**
- "Só descubro que a OS deu prejuízo quando faço fechamento do mês."
- "Os técnicos não anotam tempo direito, fica difícil cobrar."

**Jornada típica:**
1. Recebe alerta "OS #1234 deficitária".
2. Abre comparação previsto × real → vê estouro de 12h em mão de obra.
3. Pede ao técnico explicação; ajusta orçamento próximo.

**Devices:** web desktop + mobile (notificação).
**Frequência:** diária.

---

## Persona 3: Sistema (job de apuração)

**Identidade:** worker procrastinate que consome eventos de OS encerrada, peça baixada, comissão calculada, etc., e consolida custo real.

**Goals deste módulo:**
- Apurar custo real assim que todos os insumos estão disponíveis.
- Reapurar se houver correção (idempotente).
- Disparar alerta se margem < threshold.

**Devices:** backend.
**Frequência:** contínua (event-driven).

---

## Convenções

- Dono / gestor — papéis transversais; aqui só recortes específicos de custeio.
- Sistema é incluído porque a apuração é assíncrona e crítica.
