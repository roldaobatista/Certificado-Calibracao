---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/adr/0006-feature-flags.md
---

# Contratos Export — Módulo Release Management

---

## Exports

### Export 1: Release Notes (Markdown)

**Propósito:** Documento publicável em portal / blog / e-mail.
**Formato:** Markdown CommonMark.
**Regulado?:** não.
**Estrutura:**
```markdown
# Release vMAJOR.MINOR.PATCH — DD/MM/AAAA

## Adicionado
- [modulo] descricao curta — US-MOD-NNN

## Modificado
...

## Corrigido
...

## Removido
...

## Breaking Changes
- Descrição completa + link guia migração
```
**Geração:** automática a partir das notas estruturadas.

---

### Export 2: CHANGELOG.md (técnico)

**Propósito:** Versão acumulada para devs/integradores no padrão Keep a Changelog.
**Formato:** Markdown seguindo https://keepachangelog.com.
**Regulado?:** não, mas padrão de mercado.

---

### Export 3: Catálogo de Feature Flags (CSV/JSON)

**Propósito:** Auditoria de débito técnico — quais flags estão vivas, há quanto tempo, sem uso.
**Formato:** CSV ou JSON.
**Campos:** `chave`, `descricao`, `tipo`, `status`, `criada_em`, `data_revisao_obrigatoria`, `dias_desde_criacao`, `proprietario_modulo`, `qtd_regras_ativas`, `ultima_avaliacao` (timestamp da última vez que foi consultada — se possível).
**Regulado?:** não. Uso interno + relatórios ADR-0006.

---

### Export 4: Calendário de Breaking Changes (iCal/JSON)

**Propósito:** Integradores assinam calendário pra não perder data efetiva.
**Formato:** iCalendar (.ics) + JSON.
**Conteúdo:** evento por breaking change com `anunciado_em` (início) e `efetivo_em` (lembrete).
**Endpoint feed:** `GET /v1/public/breaking-changes/calendario.ics`.

---

### Export 5: Histórico de Migrações (CSV)

**Propósito:** Auditoria de SRE — todas as migrações executadas.
**Formato:** CSV.
**Campos:** `migracao_id`, `release_versao`, `nome`, `tipo`, `aprovadores`, `iniciada_em`, `concluida_em`, `status_final`, `checkpoints_count`, `revertida` (bool).
**Imutabilidade:** snapshot do registro auditado (`INV-001`).
**Retenção:** 7 anos (compliance).

---

### Export 6: Relatório de Adoção de Features (XLSX)

**Propósito:** PM avalia adoção de features liberadas.
**Formato:** XLSX.
**Abas:** "Por feature flag", "Por release", "Por plano".
**Campos por feature:** chave, tenants com flag ativa, % adoção, uso (eventos), churn de uso.

---

### Export 7: Snapshot de Configuração de Flags (JSON)

**Propósito:** Backup pré-mudança crítica ou auditoria forense.
**Formato:** JSON.
**Conteúdo:** todas as flags + todas as regras + timestamp.
**Uso:** rollback de configuração em caso de mudança errada.

---

### Export 8: Página Pública de Status de Versão (HTML)

**Propósito:** Rota pública mostrando versão atual + última release.
**Formato:** HTML simples (acessível sem JavaScript pesado).
**Endpoint:** `GET /public/versao` → renderiza versão atual em prod + link release notes.

---

## Exports inter-módulos

- Release notes → `suporte-saas` (banner in-app + base conhecimento atualizada).
- Breaking changes → notificação via `suporte-saas` aos integradores.
- Bugs corrigidos → atualização automática dos tickets em `suporte-saas` ("corrigido em vX.Y.Z").
- Comunicado de manutenção → cria `ComunicadoManutencao` em `suporte-saas` (US-REL-011).

## Versionamento

JSON do catálogo de flags versionado por `Accept: application/vnd.afere.flags+json;v=1`.
ICS do calendário versionado por path: `/v1/public/breaking-changes/calendario.ics`.

## Como evolui

Export novo → adicionar. Mudança em estrutura de release notes → ADR + bump CHANGELOG. Descontinuação → `@deprecated`.
