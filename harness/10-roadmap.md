# 10 — Roadmap por fatias verticais auditáveis

> **P1-4**: substitui o roadmap original de 4 semanas (otimista) por sequência de fatias verticais com gate regulatório de saída.

## Princípio

Cada fatia é **emitível ponta a ponta** (dentro do seu escopo limitado) e tem dossiê de validação fechado **antes** de a próxima iniciar. Não há "fatia parcial" — ou a fatia sai com gate verde, ou não sai.

## Fatias

### V1 — Emissão Tipo B ou C em ambiente controlado
**Escopo**
- Organização Tipo B (laboratório não acreditado) **ou** Tipo C (prestadora simples).
- Sem sync offline (tudo online).
- Sem Tipo A (acreditado).
- Wizard de emissão completo com bloqueios §9 ativos.
- Backend `apps/api` com auth, RBAC básico, emissão, assinatura, QR.
- Audit log com hash-chain + WORM.

**Gate de saída**
- 100% dos AC §13 do escopo Tipo B/C verdes.
- Dossiê V1 fechado em `compliance/validation-dossier/releases/v1.md`.
- Release-norm V1 aprovado por `product-governance`.
- Pacote normativo v1.0.0 assinado e em uso.

**Prazo realista estimado:** 6–8 semanas.

---

### V2 — Sync offline-first robusto
**Escopo**
- Android em campo, 100% offline.
- Simulador determinístico (ver `08-sync-simulator.md`) com todos os cenários C1–C8 verdes.
- Reconciliação server-side com fila de revisão humana.
- SQLCipher + chave derivada por device.

**Gate de saída**
- Matriz de conflitos 100% coberta com seeds canônicos.
- 1 seed weekly rodou sem falha.
- Dossiê V2 inclui trace de cada cenário.

**Prazo realista:** +4–6 semanas.

---

### V3 — Tipo A (acreditado) com escopo/CMC e símbolo Cgcre/RBC
**Escopo**
- Perfil A habilitado.
- Cadastro formal de escopo acreditado + CMC.
- Template A com selo Cgcre/RBC aplicado por regra de arquitetura.
- Bloqueio absoluto: Tipo B/C não conseguem emitir com selo (campo nem existe na UI e validação server-side).

**Gate de saída**
- Testes anti-deriva: tentativa semântica de Tipo B inserir selo = rejeição.
- `regulator` aprova escopo/CMC implementados.
- `product-governance` libera release V3.
- Parecer jurídico datado em `compliance/legal-opinions/`.

**Prazo realista:** +6–8 semanas.

---

### V4 — Reemissão controlada (ISO 17025 §7.8.8)
**Escopo**
- Fluxo completo de reemissão com justificativa.
- Hash-chain preservada: certificado original continua acessível e verificável.
- Novo certificado referencia o anterior.
- Trilha imutável de quem pediu, quem revisou, quem aprovou.

**Gate de saída**
- Teste de imutabilidade: certificado original não sofre alteração após reemissão.
- Verificação por QR continua funcional para certificado antigo.
- Fuzz cross-tenant verde.

**Prazo realista:** +4 semanas.

---

### V5 — Módulo Qualidade completo
**Escopo**
- Gestão de não-conformidades.
- Controle de competências.
- Auditorias internas.
- Indicadores e análise crítica.

**Gate de saída**
- Auditoria interna dry-run executada com auditor convidado.
- Relatório em `compliance/release-norm/v5-dry-run.md`.
- Módulo Qualidade passa em auditoria simulada ISO 17025.

**Prazo realista:** +6–8 semanas.

---

## Total realista

**V1 → V5: ~26–34 semanas** (≈ 6–8 meses).

Compara com o roadmap original de 4 semanas do `HARNESS_DESIGN.md` — que era, reconhecidamente, otimista para o escopo do PRD.

## Regras de gate

1. Nenhuma fatia inicia sem gate da anterior fechado em `compliance/release-norm/`.
2. Gate de saída inclui: dossiê de validação, pacote normativo vigente, guardrails verdes, aprovação `product-governance`.
3. Regressão em fatia anterior (teste que era verde fica vermelho) = release da nova fatia bloqueado.
4. Fatia pode ser **dividida** se escopo crescer, mas nunca **mesclada** (cada uma mantém gate próprio).

## Gate executável

`pnpm roadmap-check` valida `compliance/roadmap/v1-v5.yaml` como fonte canônica operacional:

- ordem estrita V1 → V5;
- dependência sequencial entre fatias;
- exigência de gate anterior antes da próxima fatia;
- `epic_id` e `linked_requirements` por fatia para agregação L0 na cascata;
- integridade de `linked_requirements` contra `requirements.yaml`, sem REQ inexistente ou duplicado entre fatias;
- bloco `coverage` explicitando quais `REQ-PRD-*` o roadmap cobre e quais ficam excluídos por serem gates transversais;
- `compliance/roadmap/transversal-tracks.yaml` mapeando cada exclusão para uma trilha transversal com owner, referência de harness e comandos de gate canônicos;
- release-norm, dossiê e pacote normativo por fatia;
- escopo, agentes primários e gates de saída por fatia.

O gate entra em `pnpm check:all` e no pre-commit quando arquivos P1-4 mudam.

## Paralelização possível

Dentro de uma fatia, agentes podem trabalhar em paralelo (Tier 2) em áreas não conflitantes:
- V1: `backend-api` + `web-ui` + `db-schema` em paralelo após specs aprovadas.
- V2: `android` foca; `backend-api` suporta.
- V3: `regulator` + `backend-api` + `web-ui` em sequência curta.
