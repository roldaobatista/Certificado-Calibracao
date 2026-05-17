---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Auditoria Externa

> Personas **específicas** deste módulo. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Responsável da Qualidade (RQ)

**Identidade:** Profissional sênior (30-55 anos) com formação técnica + cursos de norma (ISO 17025/9001), em geral o RT (Responsável Técnico) da empresa ou o gestor de qualidade. Pessoa de confiança do dono, responde diretamente à diretoria. Tem ansiedade de auditoria — perde sono na véspera. Conhece a norma de cor mas odeia papelada.

**Goals deste módulo:**
- Saber a qualquer momento "estamos prontos para auditoria?".
- Não correr na véspera atrás de evidência.
- Reduzir não-conformidades a zero ou só menores.
- Ter histórico organizado pra mostrar evolução ao auditor.
- Delegar evidência sem perder controle.

**Frustrations específicas:**
- Evidência espalhada em emails, pastas Drive e gavetas físicas.
- Responsável da evidência "esquecer" e descobrir 2 dias antes.
- Documento controlado vencido sem aviso.
- Auditor pedir registro de 3 anos atrás e ninguém achar.

**Jornada típica:**
1. Mês 0: cadastra auditoria programada (ano+1).
2. Mês -6: gera checklist, atribui evidências, define prazos.
3. Mês -3: roda drill interno.
4. Mês -1: painel de prontidão fica verde; resolve top-3 lacunas residuais.
5. Dia D: registra apontamentos em tempo real.
6. Pós-auditoria: lidera planos de ação até fechamento.

**Devices:** web desktop (principal), mobile (registro de apontamento em tempo real).
**Frequência:** diário (em proximidade de auditoria), semanal (rotina).

---

## Persona 2: Responsável da Evidência (RE)

**Identidade:** Pessoa de qualquer área (laboratório, comercial, financeiro, RH) que tem que produzir/manter uma evidência específica. Não é especialista em norma — só executa quando avisado.

**Goals deste módulo:**
- Receber tarefa clara: "preciso de X até dia Y".
- Anexar evidência em 2 cliques.
- Não receber 10 emails de cobrança.

**Frustrations específicas:**
- Tarefa vaga ("manda evidência da cláusula 7.5.3").
- Não saber qual versão do documento é a vigente.
- Receber cobrança depois do prazo sem aviso prévio.

**Jornada típica:**
1. Recebe notificação: tarefa Y, prazo Z.
2. Abre tela, anexa arquivo.
3. Recebe confirmação. Acabou pra ele.

**Devices:** web + mobile (notificação push).
**Frequência:** mensal/trimestral.

---

## Persona 3: Auditor Interno / Agente Família 5 Qualidade

**Identidade:** Pessoa ou agente que simula auditor externo no drill. Conhece norma; aplica checklist sem viés.

**Goals deste módulo:**
- Aplicar checklist no drill com rigor de auditor externo.
- Registrar gaps com clareza.

**Frustrations específicas:**
- Receber pressão pra "passar a mão" — viola integridade do drill.

**Jornada típica:**
1. Recebe drill atribuído.
2. Acessa evidências, marca conformidade item a item.
3. Registra gaps.
4. Entrega "gap report" ao RQ.

**Devices:** web.
**Frequência:** mensal-trimestral por norma.

---

## Persona 4: Diretor / Dono (Roldão no piloto)

**Identidade:** Decisor de negócio. Não acompanha detalhe — só olha painel de prontidão.

**Goals deste módulo:**
- Olhada de 30s no painel → saber se posso aceitar auditoria-surpresa de cliente.
- Decidir investimento em ação corretiva.

**Frustrations específicas:**
- Painel cheio de jargão técnico.
- Não conseguir entender semáforo sem ligar pro RQ.

**Devices:** mobile (preferência) + web.
**Frequência:** semanal/mensal.

---

## Convenções

- Persona específica = papel ÚNICO neste módulo.
- Diretor aparece em outros módulos (Financeiro, BI) — promover pra `docs/comum/personas.md`.
- RE pode aparecer em outros módulos de qualidade — promover pra `../../personas.md` (domínio) se ≥2 módulos.
- Hook valida não-duplicação.
