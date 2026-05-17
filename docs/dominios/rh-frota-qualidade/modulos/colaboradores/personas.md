---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: colaboradores
dominio: rh-frota-qualidade
---

# Personas — Colaboradores

## Primárias

### Dono / sócio (cadastra novo colaborador)
- **Goal:** Adicionar técnico/atendente/signatário em < 3 min com papéis e habilidades.
- **Frustração hoje:** Planilha duplicada; esquece de cadastrar habilidade; comissão calculada errada no fim do mês.
- **Cenário típico:** Contratou técnico de campo. Cadastra: nome, CPF, papel "técnico", habilidades "balança até 50kg + paquímetro", comissão 5%.

### Gerente (atribui habilidade + comissão)
- **Goal:** Ajustar matriz de habilidades quando técnico faz curso novo; alterar % comissão.
- **Frustração hoje:** Quando técnico vira mestre, ninguém atualiza; agenda continua alocando aprendiz.

### Financeiro (consulta comissão)
- **Goal:** Listar OS faturadas no mês × técnico × % comissão → relatório de comissão a pagar.
- **Frustração hoje:** Soma manual no Excel com erro recorrente.
- **Integração:** módulo Financeiro lê comissão daqui (read-only).

## Secundárias

### Técnico / signatário (consulta os próprios dados)
- **Goal:** Ver minha % de comissão e meu escopo de assinatura.
- **Permissão:** Read-only do próprio perfil; sem acesso a colaborador alheio.

### Responsável pela qualidade (P-RFQ-02)
- **Goal:** Garantir que matriz de habilidades reflete capacitações registradas (auditoria interna ISO cl. 6.2).
- **Cenário:** Audita "quem assina o quê" antes de auditoria CGCRE.

### Motorista UMC (P-RFQ-01)
- **Toque aqui:** Apenas cadastro básico + papel "motorista". Compliance Lei 13.103 fica no módulo `frota` (INV-020). Aqui só vincula CNH (anexo PDF) e categoria.

## Anti-personas

- **Tenant que cadastra colaborador "fantasma"** pra inflar comissão → audit trail INV-001 + suspeita de fraude vira NC interna.
- **Tenant que não cadastra colaborador e bota tudo no nome do dono** → bloqueio na emissão de certificado se signatário não tem escopo (INV-003).

## Referências

- `docs/dominios/rh-frota-qualidade/personas.md` (P-RFQ-01..06)
- `docs/discovery/personas-detalhadas.md` Persona 9, Persona 16
