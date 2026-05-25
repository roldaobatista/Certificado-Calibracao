# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS FECHADAS. **M4 calibracao P1 ENTREGUE (2026-05-25).**
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-25)

- pytest geral: **905/0/0** em 26min (último run 2026-05-24).
- Hooks `_test-runner.sh`: **312/312** verdes / **42 hooks ativos**.
- ruff/mypy: limpos nos paths novos.

## Saneamento pré-M4 concluído 2026-05-25 (commit `27f7699`)

- ADR-0040 aceita (padrão metrológico módulo separado).
- ADR-0064 criada e aceita (rotação HMAC + KMS Multi-Region 25a; INV-HMAC-001..005).
- US-CAL-017 adicionada ao PRD calibracao (subcontratação cl. 6.6, 6 AC, 4 INV-CAL-SUBC-*).
- Drift AGENTS §11 zerado (ADRs 0021/0024/0025/0026 status aceito).
- Dossiê `docs/faseamento/auditorias/PRE-M4-CALIBRACAO-saneamento.md` com 10 lições G1..G10 do M3 OS.

## M4 calibracao — P1 entregue (commit `08264cf`)

`docs/faseamento/M4-calibracao/spec.md` (676 linhas, 13 seções, similar a M3 649 linhas):
- 17 entidades + schema sketch (Calibracao, Leitura, LeituraCorrecao, OrcamentoIncerteza + ComponenteIncerteza + OrcamentoPorPonto, PadraoUsado, RecepcaoItemCalibracao, MedicaoControle, EventoDeCalibracao, NaoConformidade, AnaliseImpactoNCProficiência, LaboratorioSubcontratado, AceiteSubcontratacao, etc).
- 24 INV-CAL-* + 5 INV-HMAC-* + 6 INV-PAD-* + 4 INV-CAL-SUBC-* + 4 INV-CAL-FRAUDE-* a cravar em P3.
- Máquina estados Calibracao (10 estados) + ciclo CAPA NaoConformidade.
- 23 eventos publicados + 8 consumidos com envelope v10.
- 17 user stories (US-CAL-001..017) referenciadas no PRD.
- 17 riscos R-M4-01..17 mapeados; R-M4-11..17 cobrem G1..G10 das lições M3.

## Próxima fatia

**P2 (`/plan`):** gerar `plan.md` + submeter review aos 4 subagentes (tech-lead-saas-regulado, advogado-saas-regulado, corretora-seguros-saas, consultor-rbc-iso17025) em paralelo. Cada review vira `docs/faseamento/M4-calibracao/reviews/{subagente}.md`. Consolidar matriz de reconciliação.

## Pendências Wave A rastreadas (herdadas M3 OS + novas M4)

GATE-OS-* (~20) + GATE-CAL-METODO-VAL + GATE-CAL-EP-TEND + GATE-CAL-VI-POL + GATE-CAL-MIG-CLASSIF + GATE-CAL-MANUAL-QUAL + GATE-CAL-LEITURA-CORR-TAXA + GATE-CAL-DPIA-OAB + GATE-HMAC-RETROFIT-MARCO-2-3 + GATE-KMS-IAM-LOCK + GATE-HMAC-DRILL + GATE-OS-GRANDEZA-EM-ATIVIDADE (M4 P3 ativa) + GATE-SEG-BPT-1 (emergencial corretora SUSEP humana).
