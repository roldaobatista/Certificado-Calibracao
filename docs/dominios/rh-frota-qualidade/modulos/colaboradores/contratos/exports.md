---
owner: Roldão
revisado-em: 2026-06-13
status: draft
modulo: colaboradores
dominio: rh-frota-qualidade
---

# Contrato Exports — Colaboradores

## Exports MVP-1

### E-COL-01 — Lista de colaboradores (Excel/CSV)
- **Quem dispara:** Dono / Gerente / Qualidade.
- **Colunas:** ID, Nome, CPF (mascarado p/ não-dono — LGPD), E-mail, Telefone, Vínculo, Papéis (concat), Habilidades (concat), Comissão %, Status, Data admissão, Data desligamento.
- **Filtros aplicados:** Mesmos da tela.
- **Formato:** XLSX padrão + CSV UTF-8 BOM.
- **Tenant:** Filtrado por `tenant_id` (INV-TENANT-001).

### E-COL-02 — Matriz de habilidades
- **Formato:** Excel pivotado — linhas = colaboradores, colunas = habilidades, células = nível (vazio se não tem).
- **Uso:** Auditoria interna ISO 17025 cl. 6.2 + planejamento de capacitação.

### E-COL-03 — Relatório de comissão (input pra Financeiro)
- **Quem dispara:** Financeiro / Dono.
- **Colunas:** Colaborador, OS#, Cliente, Valor OS, % comissão vigente, Comissão calculada R$.
- **Período:** Mês corrente ou range.
- **Origem dos dados:** JOIN com módulo Operação (OS) — implementação cross-domínio.
- **Não é folha de pagamento.** Marca explícito: "Este relatório é base de cálculo. A folha de pagamento não está incluída no MVP-1 do Aferê."

### E-COL-04 — Documentos do colaborador (ZIP)
- **Quem dispara:** Dono (próprio colaborador também via self-service).
- **Conteúdo:** PDF + ZIP de CTPS, CNH, certificados de curso. **ASO não está incluso** (R-COL-2 — dado de saúde art. 11; dono é módulo `seguranca-trabalho`).
- **Uso:** Auditoria fiscal ou solicitação do colaborador (LGPD art. 18 — direito de acesso).

## Mascaramento LGPD

- CPF: visível só pra Dono. Demais perfis veem `***.***.***-NN` (**últimos 2 dígitos** — TL-COL-05 / D-COL-7).
- E-mail e telefone: visíveis pra Dono / Gerente / próprio colaborador.
- Documentos pessoais (CTPS, CNH): só Dono + próprio colaborador.

## Auditoria

Todo export grava: usuário, timestamp, escopo, filtros aplicados, contagem de linhas (INV-001 + cl. 7.11 ISO 17025).

## Formatos suportados

- XLSX (default)
- CSV UTF-8 BOM
- PDF (apenas E-COL-02 matriz pra impressão)
- ZIP (apenas E-COL-04)

## Não-existem MVP-1

- Holerite PDF — V2
- DIRF / RAIS / eSocial XML — V2
- Folha resumo — V2

## Acessibilidade

PDFs gerados conformam PDF/UA (INV-016).
