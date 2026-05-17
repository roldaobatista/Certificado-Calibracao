---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Onboarding

---

## Persona 1: Responsável interno pela implantação (Aferê)

**Identidade:** colaborador interno do Aferê (PM ou consultor de implantação), responsável por conduzir o tenant cliente desde o cadastro até o go-live.

**Goals deste módulo:**
- Concluir implantação dentro do prazo combinado.
- Garantir que nenhuma etapa crítica seja pulada.
- Manter o cliente engajado durante o processo.
- Documentar tudo (treinamentos, inconsistências, decisões).

**Frustrations específicas:**
- Cliente demora a entregar dados pra importação.
- Inconsistências na migração descobertas só depois do go-live.
- Falta de visibilidade sobre o que falta.

**Jornada típica:**
1. Recebe novo tenant atribuído.
2. Abre wizard de cadastro com o cliente em call.
3. Solicita planilhas pra import.
4. Roda import no sandbox, trata inconsistências.
5. Agenda treinamentos, registra cada um.
6. Roda validação final do ambiente.
7. Gera termo de aceite, coleta assinatura, promove pra produção.

**Devices:** web desktop.
**Frequência:** diário durante implantações ativas.

---

## Persona 2: Administrador do tenant cliente

**Identidade:** usuário-chave da empresa-cliente (geralmente sócio, gerente operacional ou TI interno), recebe acesso administrador no novo tenant.

**Goals deste módulo:**
- Entender o que o sistema faz antes de pagar a mensalidade completa.
- Validar que os dados migrados estão corretos.
- Treinar a equipe.
- Assinar termo de aceite sem surpresa.

**Frustrations específicas:**
- Receber sistema "vazio" sem orientação.
- Não conseguir testar sem medo de quebrar produção.
- Treinamento incompleto.

**Jornada típica:**
1. Recebe convite de acesso ao sandbox.
2. Envia planilhas pra import.
3. Valida dados importados.
4. Participa de treinamentos.
5. Assina termo de aceite.
6. Entra em produção.

**Devices:** web desktop, eventualmente mobile.
**Frequência:** intenso durante implantação (~30 dias).

---

## Persona 3: Gestor do time de implantação (Aferê)

**Identidade:** liderança interna que acompanha múltiplas implantações em paralelo.

**Goals deste módulo:**
- Ver status agregado de todas as implantações.
- Identificar onde está parado e por quê.
- Atribuir/reatribuir responsáveis.

**Frustrations específicas:**
- Falta de visibilidade consolidada.
- Implantações que arrastam sem motivo claro.

**Devices:** web desktop.
**Frequência:** diário (dashboard de gestão).

---

## Convenções

- Persona específica = papel com responsabilidade ÚNICA neste módulo.
- "Responsável interno" e "Administrador do tenant" podem ser promovidas pra `../../personas.md` se aparecerem em ≥2 módulos do domínio.
