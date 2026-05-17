---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: clientes
dominio: comercial
diataxis: reference
---

# Personas — Módulo Clientes

> Personas **específicas** deste módulo. Transversais comerciais em `../../personas.md`. Transversais do produto em `docs/comum/personas.md`.

## P-CLI-01 — Atendente (persona principal)

Referência: P-COM-01 (do domínio). No módulo Clientes é **a persona dominante** — usa cadastro + busca + visão 360° dezenas de vezes ao dia.

**Goals específicos:**
- Cadastrar PF em < 1 minuto sem digitar nada duplicado.
- Encontrar cliente por nome/CPF/CNPJ/telefone em < 3s (busca fuzzy).
- Ver na primeira tela: inadimplente? bloqueado? última OS?

**Frustrations:**
- Sistemas com 18 campos obrigatórios no cadastro inicial (foco MVP é mínimo).
- Não saber se cliente já existe → cria duplicado → financeiro reclama dias depois.

**Jornada típica:**
1. Telefone toca → "Sou o Carlos, queria orçamento"
2. Atendente abre `/clientes/buscar?q=carlos` → 4 resultados
3. Pergunta CPF/telefone pra desambiguar
4. Se não acha → `/clientes/novo` (form curto)
5. Já dentro do cliente → cria orçamento (módulo orçamentos) ou OS

**Devices:** web desktop (95%); mobile só consulta.
**Frequência:** dezenas de vezes/dia.

---

## P-CLI-02 — Vendedor (consulta)

Referência: P-COM-02. No módulo Clientes consulta para preparar contato — não cria muito.

**Goals:**
- Filtrar `/clientes` por segmento + última compra + rating pra priorizar ligações (JTBD-083).
- Ver visão 360° antes de ligar pra não perguntar coisa óbvia.

**Frustrations:**
- "Cadê os clientes que não compram há 90 dias?" — lista difícil de montar.

**Devices:** desktop + mobile (consulta em campo).

---

## P-CLI-03 — Dono (configuração + auditoria)

Referência: P-COM-05.

**Goals específicos:**
- Configurar tags de segmentação + regras de rating.
- Definir limite de crédito padrão por segmento.
- Auditar dedup (quem mesclou o quê).

**Frequência:** baixa (configuração inicial + revisões mensais).

---

## P-CLI-04 — Financeiro (read-only + bloqueio)

Referência transversal: Cláudia (financeiro) — ver `docs/discovery/personas-detalhadas.md` Persona 4.

**Goals no módulo Clientes:**
- Marcar bloqueio comercial quando inadimplência passa de X dias.
- Ver limite de crédito e uso atual sem precisar abrir financeiro.

**Permissões:** read na maior parte; write APENAS no campo "bloqueio comercial" e "limite de crédito".

---

## Anti-personas

- **Cliente final do tenant:** não cadastra nem edita aqui — vai pelo Portal (módulo separado).
- **Marketing externo:** não usa este módulo (e-mail marketing fora de escopo).

## Convenções

Persona que aparece em ≥2 módulos sobe pra `../../personas.md` (domínio). P-CLI-04 (Financeiro) é candidata a promover se reaparecer no módulo Contratos.
