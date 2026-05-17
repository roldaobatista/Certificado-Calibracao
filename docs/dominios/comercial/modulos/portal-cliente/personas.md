---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/comum/personas.md
---

# Personas do módulo Portal do Cliente

> Personas **específicas** do portal externo. Transversais (atendente do tenant) em `docs/comum/personas.md`.

---

## Persona 1: Cliente PF (pessoa física)

**Identidade:** consumidor final (ex: dono de balança de açougue, cliente que mandou consertar equipamento pessoal). 25-60 anos, tech-fluência baixa-média, predominantemente mobile.

**Goals deste módulo:**
- Ver status do que mandou consertar / calibrar sem ligar.
- Aprovar orçamento por celular.
- Baixar 2ª via de boleto/Pix.

**Frustrations específicas:**
- Sistema "de empresa" complicado.
- Login chato — esquece senha.
- Mensagens técnicas que não entende.

**Jornada típica:**
1. Recebe link no WhatsApp com botão "ver orçamento".
2. Clica → abre direto no orçamento (sem login, com link mágico OU login simples por CPF).
3. Aprova/rejeita.
4. Acompanha status pela notificação WhatsApp.

**Devices:** mobile (95%).
**Frequência:** ocasional (1x por serviço contratado).

**Permissões:** ver apenas o próprio CPF/relacionamento. RBAC `cliente_portal`.

---

## Persona 2: Cliente PJ — contato comercial / administrativo

**Identidade:** Comprador, financeiro ou administrativo de PJ cliente do tenant. 25-50 anos, familiaridade média com sistemas, web desktop predominante.

**Goals:**
- Aprovar orçamento com rastreabilidade (precisa do "comprovante" de quem aprovou).
- Baixar 2ª via de fatura + nota fiscal.
- Ver pendências financeiras consolidadas.

**Frustrations:**
- Falta de prova de aprovação (e-mail/WhatsApp se perdem).
- Não conseguir baixar XML da NF-e.
- Demora pra emitir 2ª via.

**Jornada típica:**
1. Recebe notificação por e-mail de orçamento.
2. Loga no portal (web desktop).
3. Vê orçamento + condições.
4. Aprova / pede revisão.
5. Recebe NF + acessa portal pra baixar XML+PDF.

**Devices:** web desktop (80%) + mobile (20%).
**Frequência:** semanal.

**Permissões:** RBAC `cliente_portal_admin` por CNPJ — vê orçamentos, faturas, OS administrativas; sem dado técnico de outros contatos do mesmo CNPJ.

---

## Persona 3: Cliente PJ — contato técnico

**Identidade:** responsável técnico do cliente PJ (ex: engenheiro da qualidade, técnico de manutenção). 25-55 anos, técnico-fluente, web desktop + tablet.

**Goals:**
- Ver OS técnicas em andamento (status, técnico responsável).
- Baixar certificados de calibração (precisa para auditoria ISO do próprio cliente).
- Acompanhar prazo de recalibração de equipamentos.
- Trocar mensagem técnica com técnico do tenant (anexar foto, esquema).

**Frustrations:**
- Demora pra receber certificado por e-mail.
- Não saber se equipamento está no laboratório do tenant ou foi devolvido.
- Anexo só por WhatsApp pessoal do técnico.

**Jornada típica:**
1. Loga → "Meus Equipamentos" / "Minhas OS".
2. Vê status + checklist público + anexos liberados.
3. Baixa certificado de calibração.
4. Abre mensagem técnica com anexo na thread da OS.

**Devices:** web desktop (60%) + tablet (30%) + mobile (10%).
**Frequência:** semanal-mensal.

**Permissões:** RBAC `cliente_portal_tecnico` — vê OS, equipamentos, certificados; sem fatura nem orçamento (a menos que mesmo papel admin).

---

## Persona 4: Atendente do tenant (reutilizada de `docs/comum/personas.md`, comportamento específico)

Persona transversal P3 (atendente/recepcionista). No portal, ela aparece **do outro lado** das mensagens:
- Vê thread de mensagens do cliente.
- Aprova solicitação de mudança de CNPJ/IE.
- Vê tentativas de login bloqueadas.

Permissões internas (não-cliente): RBAC `atendente`.

---

## Convenções

- Persona específica = papel com responsabilidade ÚNICA neste módulo.
- Se persona aparece em ≥2 módulos com mesma responsabilidade → promover pra `../../personas.md` (domínio).
- Se aparece em ≥2 domínios → promover pra `docs/comum/personas.md`.
