---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Personas transversais

> **Pra quê:** personas que aparecem em mais de 1 módulo. Personas específicas (técnico de campo, signatário, metrologista) ficam no `personas.md` do módulo.
>
> **Fonte rica:** `docs/discovery/personas-detalhadas.md` (16 personas). Este doc consolida só as transversais.

---

## P1 — Dono / sócio do lab ou assistência técnica

**Perfil:** 35-55 anos, técnico/engenheiro que abriu empresa. Decisor de compra de software. Stress alto com inadimplência, regulação, falta de pessoal.

**Goals no Aferê:**
- Reduzir 3+ sistemas paralelos (Bling + planilha + WhatsApp)
- Visibilidade financeira em tempo real
- Compliance regulatória (NFS-e, ISO 17025) sem ansiedade
- Reduzir esquecimento de recalibração (perde 30-50% das renovações)

**Frustrations:**
- "Pago por sistema que não entrega"
- Atendimento ruim de fornecedor
- Falta de transparência em pricing
- Customização promessa-só

**Permissões no Aferê:** Dono do tenant (papel máximo dentro do tenant).

**Quem é no MVP-1:** Roldão (Balanças Solution).

---

## P2 — Gerente operacional

**Perfil:** 30-45 anos, braço-direito do dono. Conhece processo na ponta + acompanha equipe.

**Goals:**
- Distribuir OS sem brigar com técnicos
- Acompanhar pipeline financeiro (recebimentos, inadimplência)
- Resolver "cliente liga querendo status da OS"

**Frustrations:**
- "Ferramenta nova exige mais trabalho que ajuda"
- Treinamento equipe

**Permissões:** Gerente — tudo exceto financeiro sensível + admin RBAC.

---

## P3 — Atendente / recepcionista

**Perfil:** 20-35 anos. Primeira porta. Cadastra cliente, agenda, abre OS, responde telefone/WhatsApp.

**Goals:**
- Cadastrar cliente em < 1 min
- Abrir OS sem mil cliques
- Encontrar histórico do cliente rápido
- Não perder mensagem WhatsApp

**Frustrations:**
- Cadastro duplicado entre sistemas (Dor #01)
- "Cadê a OS do Sr. Silva?"

**Permissões:** Atendente — CRM + criar OS + ver cliente + ver agenda.

---

## P4 — Financeiro

**Perfil:** 25-50 anos. Emite nota, controla cobrança, conferência.

**Goals:**
- Emitir NFS-e sem ansiedade (Dor #10)
- Conciliar pagamento ao OFX/extrato
- Cobrar inadimplente sem ofender bom pagador

**Frustrations:**
- NFS-e municipal de Vitória vs Curitiba vs SP — cada um diferente
- "Banco mudou layout do OFX outra vez"

**Permissões:** Financeiro — NFS-e + cobrança + comissões + relatórios financeiros.

---

## P5 — Auditor externo (regulador)

**Perfil:** Auditor CGCRE, fiscal estadual, ANPD (V2).

**Goals (no Aferê pelo tenant):**
- Conferir audit trail
- Verificar dossiê de validação software (ISO 17025 7.11)
- Conferir conformidade com normas

**Permissões:** Auditor read-only — acesso temporário concedido pelo Dono do tenant; auditoria reforçada.

**Quem é no MVP-1:** ninguém ainda (V2 quando 1º tenant RBC acreditado).

---

## Personas específicas (vão pro módulo)

| Persona | Módulo |
|---------|--------|
| Técnico de campo | `os/`, `mobile/` |
| Signatário técnico | `calibracao/` |
| Metrologista de bancada | `calibracao/` |
| Vendedor com comissão | `crm/`, `financeiro/` |
| Cliente final do tenant | `cliente/` |
| Suporte Aferê | `support/` |

---

## Referências

- `docs/discovery/personas-detalhadas.md` (16 personas completas com goals/frustrations)
- `docs/discovery/jobs-to-be-done.md` (BIG-01..BIG-12)
- `docs/dominios/<dominio>/personas.md` (personas por domínio)
