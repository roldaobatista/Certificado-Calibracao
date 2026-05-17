# Limites de autonomia dos agentes

> **Os 5 casos-limite em que o agente PARA e te avisa.** Em todo o resto, agente opera autônomo.
>
> Também define **limites de gasto / dados / SLA** (Auditor 2 v2 alertou que faltava).

---

## Os 5 casos-limite (escalation obrigatória pra humano)

### Caso 1 — Decisão irreversível em dados de produção
- Apagar dados de cliente (real ou de teste)
- `DROP TABLE`, `TRUNCATE`, migration destrutiva
- `git push --force` ou `git reset --hard` em qualquer branch
- Remover arquivos não-versionados do working tree
- Cancelar nota fiscal já emitida que ultrapassou janela de 24h

### Caso 2 — Mudança em 1 dos 10 paths CODEOWNERS
Lista: `.claude/hooks/`, `.claude/settings.json`, `.specify/memory/constitution.md`, `REGRAS-INEGOCIAVEIS.md`, `docs/conformidade/`, `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/`.

Mecânica: GitHub bloqueia merge sem aprovação do `@roldao`. Aviso aparece no `painel-do-dono.md` em PT-BR explicando o que está sendo afrouxado.

### Caso 3 — Gasto com terceiro (API paga, SaaS contratado, infra)
- Antes de assinar plano pago de SaaS (Pluggy, Belvo, Focus NFe, etc.)
- Antes de comprar volume novo de tokens, hospedagem, domínio
- Antes de contratar serviço de pesquisa, anotação, etc.
- **Threshold:** qualquer gasto > R$ 50/mês recorrente OU > R$ 200 único.

### Caso 4 — Decisão de produto estratégica
- Adicionar módulo novo fora dos N descobertos (entra em `faseamento-modulos.md`)
- Mudar pricing ou modelo de negócio
- Descontinuar feature em uso
- Acceitar ou rejeitar entrada de novo cliente piloto
- Mudar posicionamento do produto

### Caso 5 — Bloqueio técnico real
- Agente tentou 3 abordagens diferentes e nenhuma resolveu
- Auditor de Qualidade rejeitou 5 vezes seguidas a mesma feature
- Há contradição não-resolvida entre 2 specs ou 2 ADRs
- Stack escolhida está se mostrando inviável (recomendar pivot)

---

## Limites de gasto / dados / SLA

### Gasto autônomo permitido (sem aprovação)
- Tokens de IA: até R$ 50/dia em uso normal de desenvolvimento. Acima disso, alerta no `painel-do-dono.md`.
- Compute (Hostinger VPS já contratada): livre dentro do plano atual.
- Backups (B2 já contratado): livre dentro do plano atual.
- **Acima dos limites acima:** Caso 3 (escalation).

### Dados que agente pode manipular sozinho
- ✅ **Dados de teste / fake / fixture** — livre.
- ✅ **Dados da SUA empresa (Roldão é primeiro tenant)** — livre, com trilha em `trilha-auditoria-agentes.md`.
- ⚠️ **Dados de outros tenants (futuro)** — só leitura pra fins de debug, NUNCA mutação sem aprovação. INV-TENANT-001 + SEC-TENANT-001 protegem.
- ❌ **Dados de cliente em produção (mutação destrutiva)** — proibido sem Caso 1 (escalation).
- ❌ **Dados regulados (certificados emitidos, NF-e emitida)** — imutáveis. Cláusula 8.4 ISO 17025. Tentativa de mutação dispara alerta.

### SLA que agente pode prometer ao cliente
- Pré-MVP: sem SLA público. Comunicar "beta — sem garantia".
- Pós-MVP: SLA por módulo (Auditor 4 v2 alertou — SLO único é inadequado):
  - Calibração emissão: 99.9% (regulado)
  - Financeiro: 99.95% (NF-e SEFAZ tem janela)
  - CRM, Orçamentos, Chamados: 99.5%
- **Agente NÃO pode prometer SLA acima do publicado sem escalation.**

---

## Quando agente FICA EM DÚVIDA se é caso-limite

Default seguro: **escalation**. Melhor pausar 5 minutos esperando aprovação do Roldão do que destruir trabalho de meses.

---

## Como o agente escala

1. Atualiza `painel-do-dono.md` com a pergunta clara em PT-BR.
2. Atualiza `.agent/CURRENT.md` com status `BLOQUEADO: aguardando decisão`.
3. Se urgente: envia notificação (WhatsApp/SMS quando watchdog estiver pronto — `acionamento-agente.md`).
4. Não toma ação até receber resposta.

---

## Quem é o humano de escalation

**Roldão.** Único humano no projeto.

**Exceções (a definir):**
- Decisão jurídica complexa (LGPD, RBC) — Roldão pode delegar pra advogado/consultor especializado.
- Decisão metrológica de signatário técnico — exige profissional habilitado (RBC NIT-DICLA-021).

---

## Manutenção

Mudança nesta lista exige ADR + aprovação via CODEOWNERS (este arquivo está sob `docs/conformidade/`? Não. Sob `docs/governanca/`. Mas mudança em limites de autonomia deveria exigir CODEOWNERS — **ADR a considerar**: adicionar `docs/governanca/limites-autonomia.md` aos paths protegidos do `.github/CODEOWNERS`).
