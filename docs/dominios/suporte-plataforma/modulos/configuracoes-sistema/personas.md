---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Configurações do Sistema

---

## Persona 1: Administrador do tenant

**Identidade:** sócio, gerente operacional ou TI interno da empresa-cliente. Detém o papel "Admin" no tenant.

**Goals deste módulo:**
- Manter dados cadastrais corretos.
- Definir como sua empresa quer trabalhar (workflows, status, campos).
- Liberar/restringir acesso da equipe (RBAC).
- Conectar integrações (banco, NF, WhatsApp).
- Garantir conformidade (backup, retenção).

**Frustrations específicas:**
- Sistema engessado que obriga seguir fluxo "padrão" do fornecedor.
- Ter que abrir chamado pra mudar uma alíquota.
- Não saber quem mudou o quê (sem auditoria).

**Jornada típica:**
1. Recebe acesso admin após onboarding.
2. Ajusta dados da empresa, filiais, séries.
3. Cria papéis e atribui equipe.
4. Configura workflows e SLAs.
5. Liga integrações.
6. Eventualmente volta pra ajustar (mensal/trimestral).

**Devices:** web desktop.
**Frequência:** intenso na implantação, depois esporádico (semanal a mensal).

---

## Persona 2: Contador / responsável fiscal

**Identidade:** profissional contábil interno ou terceirizado, acessa o sistema com papel restrito a configurações fiscais e relatórios.

**Goals deste módulo:**
- Manter regime tributário, alíquotas, CFOP, NCM padrão atualizados.
- Garantir numeração e séries de documentos fiscais corretas.
- Validar antes de emissão em massa.

**Frustrations específicas:**
- Alíquota mudada sem aviso.
- Numeração com gaps (problema na auditoria fiscal).
- Configuração fiscal espalhada em vários menus.

**Devices:** web desktop.
**Frequência:** mensal (fechamento) + sob demanda quando muda legislação.

---

## Persona 3: Gestor operacional

**Identidade:** gerente de operações que define processos internos (workflows, status, SLAs, regras comerciais).

**Goals deste módulo:**
- Modelar processo real da empresa em workflows do sistema.
- Definir alçadas de aprovação.
- Configurar SLAs por tipo de cliente/contrato.

**Frustrations específicas:**
- Workflow rígido que não reflete o real.
- Não conseguir ter status personalizados.

**Devices:** web desktop.
**Frequência:** trimestral (revisão de processos).

---

## Persona 4: Auditor interno / DPO

**Identidade:** responsável por LGPD, conformidade, auditoria interna.

**Goals deste módulo:**
- Verificar configuração de retenção alinhada à matriz legal.
- Auditar mudanças (quem mudou o quê, quando).
- Garantir backup configurado conforme política.

**Frustrations específicas:**
- Sem histórico de mudança em config crítica.
- Retenção configurável abaixo do mínimo legal.

**Devices:** web desktop.
**Frequência:** trimestral + ad-hoc.

---

## Convenções

- "Administrador do tenant" e "Auditor interno / DPO" são candidatos a promoção pra `../../personas.md` se aparecerem em outros módulos.
