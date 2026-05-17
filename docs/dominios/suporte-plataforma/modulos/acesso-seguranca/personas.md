---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/arquitetura/cross-cutting/auth-rbac.md
  - docs/conformidade/comum/lgpd-rat.md
---

# Personas — Módulo Acesso, Segurança e Controle de Usuários (ACS)

> Personas **específicas** deste módulo. Personas operacionais (atendente, técnico, metrologista, financeiro) ficam em `../../personas.md` (domínio) e `docs/comum/personas.md` (produto).

---

## Persona 1: Admin do Tenant

**Identidade:** dono/sócio/gerente administrativo da empresa cliente do Aferê. 30-60 anos. Conhece o negócio, não conhece TI a fundo. Quem o Roldão é hoje para a Balanças Solution.

**Goals deste módulo:**
- Cadastrar e desligar funcionários sem precisar pedir para ninguém.
- Atribuir perfil de acesso por função em 1 clique.
- Saber quem fez o quê quando algo dá errado.
- Atender pedido de cliente sobre dados LGPD em minutos, não dias.
- Restringir filial A de ver filial B sem entender "RLS" ou "tenant_id".

**Frustrations específicas:**
- Sistemas concorrentes obrigam ligar para o suporte só pra cadastrar funcionário.
- Matriz de permissão complicada que precisa de consultor pra configurar.
- "Auditoria" que só mostra log técnico ilegível.

**Jornada típica:**
1. Recebe pedido "preciso de acesso pro novo técnico" via WhatsApp.
2. Abre "Usuários", clica "Novo", preenche nome/email/CPF, escolhe perfil "Técnico Campo", marca filial "Matriz".
3. Sistema envia email de boas-vindas com link de definição de senha + setup MFA.
4. Mensalmente abre "Auditoria" pra revisar acessos suspeitos.

**Devices:** web desktop (principal), mobile (eventual).
**Frequência:** semanal (cadastros), mensal (auditoria), diário (durante onboarding de funcionário).

---

## Persona 2: Titular de Dados Pessoais (cliente final do tenant)

**Identidade:** pessoa física cujo CPF/telefone/email está cadastrado no Aferê de um tenant. NÃO é usuário do sistema no fluxo normal — só acessa via portal LGPD.

**Goals deste módulo:**
- Exportar tudo que o tenant tem sobre mim, em formato legível.
- Pedir anonimização sem precisar advogado.
- Pedir exclusão sabendo o prazo real (por causa de retenção fiscal/ISO).
- Revogar consentimento de marketing sem perder atendimento técnico.

**Frustrations específicas:**
- Empresas que respondem LGPD em PDF rasurado, semanas depois.
- Não entender por que dado não foi excluído (não sabe que NF tem retenção legal).

**Jornada típica:**
1. Recebe link "Portal LGPD" do tenant ou descobre via site.
2. Faz login com CPF + código enviado por email/SMS (autenticação leve, sem MFA).
3. Vê 3 botões: Exportar, Anonimizar, Excluir.
4. Recebe email de confirmação + prazo + comprovante PDF.

**Devices:** mobile (provável).
**Frequência:** 1-2 vezes na vida (eventos raros).

---

## Persona 3: Auditor RBC / Fiscal LGPD (externo)

**Identidade:** auditor CGCRE em visita de manutenção da acreditação ISO 17025, OU fiscal ANPD investigando incidente. Sessão temporária com perfil dedicado "Auditor Externo".

**Goals deste módulo:**
- Ler trilha de auditoria sem poder alterar nada.
- Exportar evidências assinadas digitalmente.
- Ver histórico de quem editou um certificado ou registro fiscal.
- Confirmar que o sistema atende cláusulas de rastreabilidade (ISO 17025 7.5, 8.4) e LGPD (Art. 37, 46).

**Frustrations específicas:**
- Sistema que mostra só log técnico cru.
- Exportação sem timestamp/assinatura (vira "papel").
- Acesso amplo demais (auditor não pode ver dado pessoal não-relacionado).

**Jornada típica:**
1. Admin do tenant cria sessão temporária com perfil "Auditor Externo" + escopo (período, módulos).
2. Auditor entra, navega trilha filtrada, exporta PDF assinado.
3. Sessão expira automaticamente ao fim do prazo configurado (default 8h).

**Devices:** web desktop.
**Frequência:** anual (RBC), eventual (ANPD).

---

## Persona 4: Admin Global do Aferê (operação interna)

**Identidade:** Roldão ou agente IA com permissão de operador do SaaS. Atua a nível plataforma, não cliente.

**Goals deste módulo:**
- Criar tenant novo (provisionar).
- Suspender tenant inadimplente.
- Investigar incidente entre tenants (sem violar isolamento — somente metadados).
- Operar rotação de chaves KMS.

**Frustrations específicas:**
- Risco enorme de errar e atravessar tenant (`INV-TENANT-004` impede até para esse perfil).
- Precisar de evidência clara em cada ação (audit trail dele mesmo).

**Jornada típica:**
1. Recebe alerta de incidente.
2. Entra com MFA + segunda revisão (4-eyes para ações destrutivas).
3. Toda ação fica em trilha separada (`acs.admin_global.acao`).

**Devices:** web desktop com sessão restrita por IP/VPN.
**Frequência:** diário (monitoramento), eventual (intervenção).

---

## Convenções

- Persona aparece em ≥2 módulos com mesma responsabilidade → promover pra `../../personas.md` (domínio) ou `docs/comum/personas.md` (produto).
- "Admin do Tenant" pode promover-se para `comum` quando outro módulo usar.
- Hook valida não-duplicação entre os 3 níveis.
