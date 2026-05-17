---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Marketplace

> Personas específicas. Personas transversais ficam em `../../personas.md` (domínio) e `docs/comum/personas.md` (produto).

---

## P-MKT-01: Visitante anônimo

**Fonte canônica:** `docs/comum/personas.md` P-MKT-01 (promovida em 2026-05-17 — aparece em marketplace + portal-cliente landing). Aqui apenas referência. Atualizações de identidade/goals devem ir pra fonte canônica.

**Específico deste módulo:** entra pela vitrine pública → carrinho → solicitação. Depois de virar lead migra pra P-MKT-02 (cadastrado).

---

## P-MKT-02: Cliente cadastrado autoatendimento (entrada pelo marketplace)

> **Fronteira:** esta persona representa o **cliente cadastrado quando opera DENTRO do marketplace** (recompra rápida, assinatura recorrente, conferir status do que pediu por aqui). Para o mesmo cliente quando opera no relacionamento 360° (OS, faturas, certificados, mensagens, aprovação de orçamento), a fonte canônica é **P-COM-03 "Cliente cadastrado no Portal"** em `../portal-cliente/personas.md` — mesmo indivíduo, papéis e UIs distintas. O login é único (gerido pelo `portal-cliente`); a persona muda conforme a área onde o cliente está navegando.

**Identidade:** cliente que já fechou pelo menos 1 OS com o tenant e tem login no Portal do Cliente. Geralmente comprador técnico (engenheiro, gerente de manutenção) que recebe a senha após primeiro fechamento.

**Goals específicos deste módulo (marketplace):**
- Pedir novo serviço sem repetir cadastro (recompra a partir da vitrine).
- Assinar/cancelar serviços recorrentes pela vitrine.
- Conferir status processual das **solicitações originadas no marketplace** (US-MKT-003 com escopo restrito).
- Aproveitar tabela de preço privada atribuída.

**Goals que NÃO são deste módulo (vão pro Portal do Cliente):**
- Acompanhar OS em andamento → `portal-cliente` (US-POR-003/US-POR-007).
- Aprovar/rejeitar orçamento → `portal-cliente` (US-POR-005).
- Baixar certificados, faturas, contratos → `portal-cliente` (US-POR-006/US-POR-008).
- Trocar mensagem com a empresa → `portal-cliente` (US-POR-009).
- Editar dado cadastral → `portal-cliente` (US-POR-011).

**Frustrations específicas (no escopo deste módulo):**
- Não saber se a solicitação que mandou pela vitrine já virou orçamento ou caiu no esquecimento.
- Ter que refazer carrinho a cada renovação de serviço recorrente.

**Jornada típica:**
1. Login (autenticação única do `portal-cliente`) → redireciona para área restrita; volta ao marketplace só para recompra/assinatura.
2. Adiciona item recorrente no carrinho e assina contrato → `Marketplace.AssinouRecorrente`.
3. Para conferir status da OS gerada, **clica "Ver área do cliente completa"** → vai pro `portal-cliente`.

**Devices:** desktop (escritório) + mobile (consulta rápida).
**Frequência:** mensal/eventual (recompra/renovação).

---

## P-MKT-03: Gestor de catálogo do tenant

**Identidade:** funcionário comercial/marketing do tenant que decide o que aparece na vitrine, qual é destaque, qual tabela de preço é pública, qual é privada. Geralmente o próprio dono em empresa pequena; gerente comercial em empresa média.

**Goals deste módulo:**
- Curar vitrine (destaques, ordenação, ocultar itens).
- Definir tabela pública × tabela por cliente.
- Acompanhar funil de conversão (visita → solicitação → fechamento).
- Ajustar imagens, descrições, FAQs por item.

**Frustrations específicas:**
- Ter que editar HTML para mudar destaque.
- Não ver quantas pessoas viram o item antes de pedir.
- Site que mostra item esgotado/descontinuado.

**Jornada típica:**
1. Abre dashboard de funil — vê que serviço X tem 200 visualizações e 0 carrinhos.
2. Investiga: descrição confusa.
3. Edita descrição + adiciona foto melhor.
4. Marca como destaque por 7 dias.

**Devices:** desktop.
**Frequência:** semanal.

---

## Convenções

- Persona específica = papel com responsabilidade ÚNICA neste módulo.
- Se persona aparece em ≥2 módulos com mesma responsabilidade, promover para `../../personas.md`.
- Se aparece em ≥2 domínios, promover para `docs/comum/personas.md`.
