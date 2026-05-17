---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos UI — Módulo Release Management

---

## Telas

### Tela 1: Histórico de Releases

**Propósito:** Lista cronológica das releases publicadas.
**Persona principal:** PM + Tenant Admin.
**US:** `US-REL-001`, `US-REL-002`.
**Acessível por:** menu "Sobre o sistema" → "Versões".

**Elementos:**
- Lista cronológica reversa: versão, data, tipo (badge), resumo.
- Filtros: tipo (MAJOR/MINOR/PATCH/HOTFIX), módulo afetado, ano.
- Link pra notas completas + breaking changes.

**Estados:**
- Vazio: "Nenhuma release ainda."
- Carregando: skeleton.

**Mobile:** responsivo.
**Acessibilidade:** WCAG AA.

---

### Tela 2: Detalhe da Release (Notas)

**Propósito:** Notas completas da release.
**US:** `US-REL-002`, `US-REL-007`.

**Elementos:**
- Header: versão, data, tipo.
- Abas: Adicionado / Modificado / Corrigido / Removido / Breaking Changes.
- Cada item agrupado por módulo.
- Lista de bugs corrigidos com link pros tickets (se usuário foi reporter).

---

### Tela 3: Painel de Feature Flags (admin Aferê)

**Propósito:** PM gerencia flags.
**Persona:** PM.
**US:** `US-REL-003`.

**Elementos:**
- Lista de flags com: chave, descrição, tipo, valor default, dias até cleanup.
- Indicador visual de "flag morta" (sem uso > 60 dias).
- Ação: criar / editar regras / aposentar.
- Editor de regras: priorizar, escolher escopo (tenant/plano/segmento/beta), valor.
- Histórico de mudanças por flag.

**Estados:**
- Flag morta: badge vermelho "Cleanup pendente".

---

### Tela 4: Programa Beta (tenant admin)

**Propósito:** Tenant admin opta por entrar/sair.
**Persona:** Tenant Admin.
**US:** `US-REL-004`.

**Elementos:**
- Toggle "Participar do programa beta".
- Lista das features beta ativas.
- Aviso: "Recursos beta podem ter bugs. Reporte via suporte."

---

### Tela 5: Ambiente de Homologação (tenant Enterprise)

**Propósito:** Tenant Enterprise gerencia sandbox.
**US:** `US-REL-005`.

**Elementos:**
- Botão "Provisionar ambiente".
- Indicador de data do snapshot atual + botão "Atualizar snapshot".
- Link pro sandbox (subdomínio próprio).
- TTL e botão "Renovar".

---

### Tela 6: Painel de Migrações (SRE)

**Propósito:** SRE planeja e executa migrações.
**Persona:** SRE.
**US:** `US-REL-006`.

**Elementos:**
- Lista de migrações (planejada / aprovada / executando / concluída / revertida).
- Detalhe: tipo, plano de rollback, aprovadores, checkpoints.
- Botão "Aprovar" (exige 2 aprovadores diferentes pra destrutiva).
- Botão "Executar" (só quando aprovada).
- Botão "Reverter" (até último checkpoint reversível).

**Estados:**
- Falha: alerta vermelho + log do erro.

---

### Tela 7: Breaking Changes (público + integrador)

**Propósito:** Integradores consultam o que vai quebrar.
**US:** `US-REL-008`.

**Elementos:**
- Lista cronológica com: título, anunciado em, efetivo em (countdown), endpoints afetados, link guia migração.
- Filtro por endpoint / módulo / janela (próximos 90 dias).
- Indicador visual: verde (> 60d), amarelo (30-60d), vermelho (< 30d).

---

### Tela 8: Status do Sistema (público)

**Propósito:** Tenant vê versão atual + manutenções.

**Elementos:**
- Versão atual em produção (semver).
- Janelas de manutenção próximas.
- Link pra histórico de releases.

---

### Tela 9: Recursos por Plano (CTA upgrade)

**Propósito:** Quando tenant Free tenta feature Pro, vê CTA.
**US:** `US-REL-010`.

**Elementos:**
- Modal/banner: "Esse recurso está disponível no plano Pro. Veja vantagens."
- Botão "Fazer upgrade" → módulo `gestao-assinaturas-planos/`.

---

## Componentes reutilizáveis

Compartilhados em `../../../comum/contratos/ui.md`: badge de versão semver, indicador de countdown, painel de checkpoint.

## Como evolui

Tela nova → ligar US. Mudança UX → CHANGELOG.
