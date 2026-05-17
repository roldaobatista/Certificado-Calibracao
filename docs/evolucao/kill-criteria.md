---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Kill criteria — quando descontinuar feature ou módulo

> **Pra quê:** zumbis (feature pronta mas ninguém usa) custam manutenção sem entregar valor. Sem critério explícito, time mantém zumbi pra "não desperdiçar o esforço".

---

## Princípio

**Custo de manter > valor entregue** → matar.

---

## Critérios por categoria

### Feature
- **0 uso em 90 dias** com base instalada > 3 tenants → marcar como candidata
- **< 5% dos tenants usam** após 6 meses de release → revisar UX, depois matar
- **Custo de manter** (bugs, suporte) > **valor** (tempo economizado, satisfação) → matar
- **Substituído por alternativa melhor** → matar feature antiga

### Módulo inteiro
- **Reach < esperado** (< 10% do que `roadmap` previu) → revisar
- **Custo regulatório novo** desproporcional → descontinuar
- **Dependência crítica fim-de-vida** (lib abandonada, parceiro descontinuou) → migrar ou matar

### Tenant
- **6 meses sem login** → contato proativo; se não retornar em 3 meses, suspender
- **3 meses inadimplente** → suspender (já documentado em fluxo financeiro)
- **Tenant solicita exclusão LGPD** → processo conforme `retencao-matriz.md`

---

## Processo de descontinuação

1. **Identificar candidato** via métricas (`metricas-sucesso.md`)
2. **Avaliar:** Roldão + auditor produto + signatário técnico (se módulo regulado)
3. **Comunicar tenants afetados** com 90 dias de antecedência
4. **Período de transição** — feature marcada "deprecated" na UI; alternativa sugerida
5. **Remover** — após 90 dias, retira código + migração de dados pendentes
6. **Audit log** — registrar decisão + razão em `auditoria-decisoes-autonomas.md`
7. **CHANGELOG** — registrar remoção como BREAKING ou DEPRECATED conforme caso

---

## Atenção em produto regulado

Feature ligada a obrigação ISO 17025 / fiscal **não pode ser matada unilateralmente** se houver tenant ativo usando. Migrar usuários primeiro, depois descontinuar.

Manter por 5 anos pós-descontinuação se houver dado retido (fiscal Receita).

---

## Exemplos hipotéticos (V2+)

- Bling import feature: se < 5% migrações em 12 meses → mata
- Conta Azul export: se nenhum tenant exportou em 6 meses → mata
- Calculadora ROI no site: se 0 conversões em 6 meses → mata

---

## Referências

- `metricas-sucesso.md`
- `roadmap.md`
- `auditoria-decisoes-autonomas.md`
- `CHANGELOG.md`
