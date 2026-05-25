# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS FECHADAS. **M4 calibracao P2 ENTREGUE (2026-05-25).**
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-25)

- pytest geral: **905/0/0** em 26min (último run 2026-05-24).
- Hooks `_test-runner.sh`: **312/312** verdes / **42 hooks ativos**.
- ruff/mypy: limpos nos paths novos.

## M4 calibracao — P2 entregue (4 reviews paralelos)

4 subagentes humano-substitutos revisaram spec.md em paralelo + plan.md consolida ata P2:
- `reviews/tech-lead.md` — 4 BLOQUEANTE + 5 MÉDIO + 2 ALTO Wave A (concorrência, motor de cálculo VAPOR, hash-chain garfo, ADR-0063 fail-open eterno).
- `reviews/advogado.md` — 0 BLOQUEANTE + 6 MÉDIO + 2 GATE Wave A (subcontratação DPA cl. 4.7, override de regra, anti-PII saúde, reclamação CDC art. 26, foto base legal, consentimento contato PF).
- `reviews/corretora.md` — 0 BLOQUEANTE + 4 MÉDIO + 5 ALTO + 1 ACEITE (8 cláusulas SUSEP novas + Modalidade 8 NOVA Property padrão próprio).
- `reviews/rbc.md` — 6 BLOQUEANTE + 3 MÉDIO + 5 ALTO Wave A + 2 ACEITE (6 zonas ILAC G8, componentes mínimos NIT-DICLA-030, acordo cliente cl. 7.1.3, recepção avulsa, política subcontratado cl. 6.6.2, decisão parar/continuar NC).
- **Total 45 achados** (vs 27 do M3 OS — +67%, coerente com densidade técnica M4).

`plan.md` consolida 10 BLOQUEANTE + 23 MÉDIO + 14 ALTO Wave A + 3 ACEITE + 32 GATEs Wave A novos + tabela ACTION_IDEMPOTENT 18 endpoints + drill `validar_m4_calibracao` 25 checagens + performance budgets p95.

## 5 decisões do Roldão (P2 → P3)

- **D-M4-1:** Motor 2º caminho = **GUM clássico Python (Decimal) + Monte Carlo NumPy (JCGM 101, seed em Calibracao.id)**. ✓
- **D-M4-2:** ADR-0063 ativação = **Lazy em configurar_calibracao + 3 use cases pós** (configurar_calibracao + aprovar_revisao + aprovar_2a_conferencia). `iniciar_atividade` fail-open documentado proposital. ✓
- **D-M4-3:** Corretora SUSEP humana = **sem previsão** → 9 GATE-SEG-* M4 rastreados pré-1º tenant externo; M4 dogfooding NÃO bloqueado.
- **D-M4-4:** Consultor CGCRE humano = **sem previsão** → agente redige 2 matrizes preliminares (componentes-obrigatorios + formula-calculo por grandeza) baseadas em NIT-DICLA-030 + ILAC G8 + GUM JCGM 100, selo `REQUER VALIDAÇÃO CGCRE HUMANO`. **GATE-CAL-MATRIZES-CGCRE** rastreado.
- **D-M4-5:** OAB humana = **sem previsão** → agente redige 6 minutas preliminares (DPA subcontratado + aceite subcontratação + cláusula override + aviso foto + consentimento contato PF + DPIA), selo `REQUER VALIDAÇÃO OAB HUMANA`. 8 GATE-CAL-*-OAB rastreados.

## Próxima fatia

**P3 (matriz reconciliação + retrofit spec + ADRs novas/retrofitadas + minutas preliminares):** decisões cravadas; agente parte para:
1. Atualizar spec.md absorvendo 10 BLOQUEANTE + 23 MÉDIO.
2. Criar ADR-0065 "Concorrência em calibração metrológica".
3. Retrofit ADR-0024 (6 zonas ILAC G8 + PFA + acordo cliente), ADR-0028 rev 3 (8 cláusulas + Modalidade 8 NOVA), ADR-0063 (Opção A lazy).
4. 8 entidades novas em spec §3.2.
5. US-CAL-018 nova (reclamação CDC art. 26).
6. 24 INVs novos em REGRAS-INEGOCIAVEIS.
7. 5 minutas canônicas preliminares (OAB-pendente) + 2 matrizes técnicas preliminares (CGCRE-pendente).
8. `matriz-reconciliacao.md` PRD ↔ spec ↔ plan zero conflito.
9. `tasks.md` ~150 T-CAL-NNN granulares em 10 fases.

## Pendências Wave A rastreadas (herdadas + 32 novas M4)

GATE-OS-* (~20) + GATE-CAL-* (~32 novos) + GATE-SEG-* (9 novos) + GATE-CAL-METODO-VAL + GATE-CAL-EP-TEND + GATE-CAL-VI-POL + GATE-CAL-MIG-CLASSIF + GATE-CAL-MANUAL-QUAL + GATE-CAL-LEITURA-CORR-TAXA + GATE-CAL-DPIA-OAB + GATE-HMAC-RETROFIT-MARCO-2-3 + GATE-KMS-IAM-LOCK + GATE-HMAC-DRILL + GATE-OS-GRANDEZA-EM-ATIVIDADE (M4 P3 ativa) + GATE-SEG-BPT-1 (emergencial corretora SUSEP humana).
