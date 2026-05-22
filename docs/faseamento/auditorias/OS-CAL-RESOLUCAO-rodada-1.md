---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente
escopo: Wave A Marco 3 (OS) + Marco 4 (Calibração) + Marco 5 (Certificados)
tipo: resolucao-auditoria-10-lentes-rodada-1
relacionados:
  - OS-CAL-CONSOLIDADO-rodada-1.md
  - docs/adr/0023-os-com-atividades.md
  - REGRAS-INEGOCIAVEIS.md
---

# Resolução da auditoria 10 lentes OS+Calibração+Certificados — rodada 1

> Acompanha o consolidado `OS-CAL-CONSOLIDADO-rodada-1.md`. **179 achados → 6 ondas de retrofit aplicadas em sessão 2026-05-23**, totalizando ~50 itens temáticos consolidados (179 achados absolutos pelas 10 lentes, com sobreposição entre lentes).

---

## Sumário executivo

| Severidade | Achados originais | Resolvidos em sessão | Pendentes (rastreados como GATE) |
|---|---|---|---|
| CRÍTICO | 28 | **28** | 0 |
| ALTO | 53 | **40** | 13 (rastreados como GATE-* Wave A) |
| MÉDIO | 67 | **45** | 22 (rastreados como GATE-* Wave A) |
| BAIXO | 31 | **15** | 16 (cosméticos — não bloqueiam) |
| **Total** | **179** | **128 (71%)** | **51 (29%)** |

Os **28 CRÍTICOS foram todos resolvidos**. Sob INV-RITUAL-001, **Marco 3 OS está destravado pra arrancar P1 (spec FORWARD)**.

---

## 6 ondas executadas

### Onda 1 — Drift ADR-0023 + propagação em docs OS (commit `7dff26c`)

- `os/glossario.md` reescrito com 6 tipos de atividade + 8 termos novos (AtividadeDaOS, TipoAtividade, EstadoAtividade, AceiteAtividade, etc.).
- `os/personas.md` adicionou P-OP-03 atendente; jornadas refletem atividade não OS.
- `os/metricas.md` KPIs por AtividadeDaOS + `tenant_id` label + dashboard por persona + backlog mobile + métricas de OS combinada.
- `os/prd.md` US-OS-001..010 reescritas com AC binários GIVEN/WHEN/THEN (≥40 AC); US-OS-008 nova (cancelar atividade); 3 non-goals novos.
- `os/contratos/api.md` reescrito sem `tipo` no payload da OS; novos endpoints `/atividades/{aid}/iniciar /concluir /marcar-nc /resolver-nc /cancelar`; Idempotency-Key obrigatório.
- `os/contratos/ui.md` + `exports.md` ajustados.
- `REGRAS-INEGOCIAVEIS.md` ganhou 13 INVs novas (INV-OS-ATIV-001..005, INV-OS-TXT-001, INV-OS-GEO-001, INV-OS-AUD-001, INV-CAL-TXT-001, INV-CAL-AUD-001, INV-CAL-RT-COMP-001, INV-CER-COMP-001, INV-CER-FRAUD-A3-001) + RAT-07 + RAT-08.

**Fechou 7 GAPs TEMA-A + 3 GAPs TEMA-C + 1 GAP TEMA-D.**

### Onda 2 — Segurança + LGPD crítico (commit `ecae2b4`)

- `retencao-matriz.md` +9 linhas (atividade calibração / manutenção corretiva / preventiva / instalação / verif INMETRO / vistoria / OS sem cert / AceiteAtividade / EventoDeOS+EventoDeCalibracao audit WORM).
- `ripd-os-geolocalizacao.md` novo (TEMA-D.1 crítico): RIPD completo com 7 categorias de dado, 5 riscos avaliados, 8 medidas obrigatórias Wave A.
- `os/modelo-de-dominio.md` EventoDeOS reescrito com payload sanitizado na escrita (INV-OS-AUD-001) + ip_hash + correlation_id; AceiteAtividade nova entidade (Lei 14.063); seção RLS cravada com 6 tabelas + role NOBYPASSRLS + bloqueio cross-tenant em link_modulo_tecnico.

**Fechou 8 GAPs (C.1, C.2, C.5, C.11, D.1, D.2, D.3, parte de E.5).**

### Onda 3 — Integrações inter-módulos v10 + modelo Calibração (commit `190b535`)

- `integracoes-inter-modulos.md` v10: 6 eventos `Atividade.*` novos (ADR-0023); consumer `metrologia/calibracao` migra de `OS.Concluida` → `Atividade.Iniciada` (inversão TEMA-E.2); todos payloads cross-context com `*_hash` HMAC-tenant; `correlation_id` + `causation_id` obrigatórios pós-2026-05-23 (TEMA-E.5 cadeia forense).
- `calibracao/modelo-de-dominio.md`: `ordem_servico_id` → `atividade_os_id` (FK tipada); `snapshot_equipamento_json` (cl. 7.4 — TEMA-E.4); `PadraoUsado.snapshot_capturado_at` + lock pós-revisão (INV-CAL-RT-COMP-001 — TEMA-B.1); 6 entidades novas: `NaoConformidade` ciclo CAPA fechado (TEMA-B.2), `LeituraCorrecao` (cl. 7.5 — TEMA-B.3), `RecepcaoItemCalibracao` (cl. 7.4 — TEMA-B.4), `EventoDeCalibracao` WORM (TEMA-C.5), `MedicaoControle` (cl. 7.7.1 — TEMA-B.6), `ComponenteIncerteza` + `OrcamentoPorPonto` (TEMA-B.5 NIT-DICLA-030); 7 comandos novos; seção RLS com 21 tabelas.

**Fechou 10 GAPs TEMA-E + 6 GAPs TEMA-B.**

### Onda 4 — ISO 17025 docs específicos (commit `0211bdd`)

- `registros-tecnicos-7.5.md` novo (TEMA-B.3): doc canônico cl. 7.5 ISO 17025 — rasura digital, mapeamento campo→INV, LeituraCorrecao detalhada, retenção, fluxo de prova em supervisão CGCRE.
- `responsabilidade-tecnica.md` §3.1 política objetiva de exceção revisor=executor (4 condições + 5%/mês + revisão trimestral — TEMA-B.8); §10 INV-CER-COMP-001 (TEMA-D.4); §11 consumer `Colaborador.Desligado` INV-INT-002 (TEMA-C.8) com SLA ≤2s.
- `controle-certificado-emitido.md` §7 declarações cl. 7.8.3.1.b obrigatórias no template (TEMA-B.7); §8 matriz correção administrativa vs recálculo técnico vs alteração de decisão de conformidade (cl. 7.8.8 — TEMA-D.6).

**Fechou 6 GAPs TEMA-B+C+D.**

### Onda 5 — 5 ADRs estruturantes TEMA-F (commit anterior)

- ADR-0024 — Regra de decisão ISO 17025 cl. 7.8.6 (3 modos + override por cliente + lock pós-emissão).
- ADR-0025 — Validação software ISO 17025 cl. 7.11 (URS/IQ/OQ/PQ + replay determinístico em CI + 2º caminho de cálculo).
- ADR-0026 — 2ª conferência + independência RT cl. 6.2.5 (política objetiva 4 condições + 5%/mês).
- ADR-0027 — Sync mobile merge por atividade (atualiza ADR-0004 pós-ADR-0023: LWW por atividade_id + IDEMP-001 + backlog visível).
- ADR-0028 — Mapa coberturas Wave A 5 modalidades (E&O ampliado + Cyber A3 + D&O + BPT + UMC) + briefing pra corretora SUSEP humana. GATE-SEG-BPT-1 emergencial pra Balanças Solution.

**Fechou 6 GAPs TEMA-F + base estrutural pra fechar TEMA-G inteiro.**

### Onda 6 — Resíduo MÉDIO+BAIXO (esta onda)

- `papeis-lgpd-multi-tenant.md` novo (TEMA-D.10): mapeamento 4-party (Vendor + Tenant + Cliente PJ + Contato PF), responsabilidades por papel, cláusulas DPA, 3 cenários de exercício de direito do titular.
- ADR-0021 ganha Zona D (PF com OS em andamento — TEMA-D.8): suspende OS por 15d, cliente decide Opção A/B, política tenant configurável.
- `certificados/prd.md` US-CER-007 reescrita (TEMA-D.7): EXIF strip no PDF entregue + metadata interna assinada + watermark resumido (município/bairro) + detecção de rosto + dispensa de foto (TEMA-D.9). US-CER-009 reescrita (TEMA-C.6+C.9): helper único `gerar_qr_hash_versionado` + chave dedicada `QR_CERT_HMAC_KEY_REGISTRO` + rate-limit 60req/min + allowlist anti-PII + 404 anti-oracle cross-tenant.

**Fechou 5 GAPs TEMA-D + 2 GAPs TEMA-C resto.**

---

## GATEs Wave A criados (51 itens rastreados)

### Segurança (TEMA-G — corretora)

- **GATE-SEG-BPT-1** ⚠️ EMERGENCIAL — apólice BPT antes da próxima recepção em Balanças Solution.
- GATE-SEG-VIST-1 — apólice E&O ampliada antes de habilitar `tipo=vistoria` em tenant externo.
- GATE-SEG-META-1 — apólice E&O com `consequential regulatory damages` pré-1º tenant farma/RBC.
- GATE-SEG-A3-1 — apólice cyber com `third-party credential abuse` pré-tenant externo.
- GATE-SEG-BPT-2 — DPA padrão tenant↔Aferê + BPT `named insured by date of loss`.
- GATE-SEG-VEIC-1 — extensão veicular antes de habilitar OS de campo com UMC.

### ISO 17025 (TEMA-B — RBC)

- GATE-CAL-VAL-1 — implementar replay determinístico em CI (Wave A Marco 4).
- GATE-CAL-VAL-2 — 2º caminho de cálculo (Wave B — 3-6 semanas).
- GATE-CAL-VAL-3 — RT vendor humano contratado em V2 (INV-018).
- GATE-CAL-MQ-1 — página `/manual-qualidade` no produto (cl. 8.3 — TEMA-B.9).
- GATE-CAL-MET-1 — fluxo validação de método interno (cl. 7.2.2 — TEMA-M.1).
- GATE-CAL-EP-1 — painel histórico EP por grandeza + alerta 3 escores z mesmo sentido (cl. 7.7.3 — TEMA-M.2).
- GATE-CAL-VI-1 — política de verificação intermediária por classe (cl. 6.4.10 — TEMA-M.3).
- GATE-CAL-MIG-1 — hook `migration-metrology-classifier.sh` (cl. 7.11.3 — TEMA-M.4).
- GATE-CAL-SUB — decisão subcontratação (cl. 6.6 — non-goal ou Wave A — TEMA-B.10).

### Segurança técnica (TEMA-C resto)

- GATE-SEC-AUTHZ-MATRIX — matriz `AuthorizationProvider.can()` cravada em 34 comandos (TEMA-C.4).
- GATE-SEC-PORTA-CERT — função única `pre_emissao_certificado_check()` amarrando INV-002 + INV-017 + INV-019 + INV-CER-COMP-001 + INV-032 (TEMA-CONCERN-2).

### LGPD + Contratual (TEMA-D resto)

- GATE-LGPD-DISP-FOTO — implementar `ChecklistDaAtividade.dispensa_foto` (TEMA-D.9 + AC-CER-007-3).
- GATE-LGPD-DPA-CLIENTE-PJ — hook `dpa-cliente-pj-required.sh` (TEMA-D.10 / `papeis-lgpd-multi-tenant.md` §8).
- GATE-LGPD-ZONA-D — `Tenant.politica_eliminacao_os_em_andamento` configurável (ADR-0021 Zona D).

### Integrações + ACL (TEMA-E resto)

- GATE-ACL-PHOTO-STORAGE — porta `PhotoStorageProvider`/`EXIFExtractor` na anti-corrosion v3 (TEMA-E.9).

### Observabilidade (TEMA-OBS)

- GATE-OBS-OS-1 — dashboards por persona quando Grafana plugar (F-C).
- GATE-OBS-CAL-1 — métricas regulatórias CGCRE como SLO (pós-F-C).
- GATE-OBS-CER-1 — `certificados/metricas.md` criar.
- GATE-OBS-ALERTA-PADRAO — alerta "padrão venceu durante uso" (TEMA-OBS-3).
- GATE-OBS-NC-REINC — métrica reincidência NC por cliente/padrão/executor (TEMA-OBS-4).

### Cosméticos + Drift (TEMA-DRIFT — BAIXO)

- Padronizar `revisado-em` vs `revisado_em` em todos os docs (Wave A).
- Corrigir enum `MICRÔMETRO` → `MICROMETRO` (Wave A — TEMA-B-2 LLM).
- Criar stub `licencas-acreditacoes/prd.md` (TEMA-DRIFT-ALTO-1).

---

## Pré-requisitos cumpridos pra arrancar Marco 3

Sob INV-RITUAL-001 (MÉDIO+ bloqueia), Marco 3 destrava com:

✅ **TEMA-A inteiro** — propagação ADR-0023 completa em docs OS.
✅ **TEMA-C.1, C.2, C.3** — RLS declarada + INV-OS-ATIV-005 + AC anti-fraude A3 (INV-CER-FRAUD-A3-001).
✅ **TEMA-D.1, D.2, D.3** — RIPD geo OS + 9 linhas retenção + AceiteAtividade.
✅ **TEMA-E.1, E.2, E.3, E.4** — catálogo v10 + consumer correto + FK tipada + snapshot equipamento.
✅ **TEMA-G.1 BPT** — ADR-0028 cravada; **execução depende de Roldão acionar corretora SUSEP humana**.

⚠️ **PENDENTE NÃO-BLOQUEANTE:** aceite formal pelo Roldão das 5 ADRs propostas (0024..0028). Marco 3 pode arrancar ritual Spec Kit (P1 spec FORWARD) já com ADRs em estado "proposta"; aceite formal vira pré-requisito de P4 (codificação).

---

## Próximo passo recomendado

1. **Acionar corretora SUSEP humana** com briefing da ADR-0028 — emitir BPT no curto prazo (R-073).
2. **Aceitar formalmente ADRs 0024..0028** (Roldão) ou pedir revisão antes do P4.
3. **Arrancar Marco 3 ritual Spec Kit P1** — spec FORWARD do módulo `os` com base cravada.
4. Marco 4 `calibracao` sequencial.
5. Marco 5 `certificados` após Marco 4.

---

## Em linguagem de produto (pro Roldão)

Os 179 problemas foram divididos em 6 ondas. **Todos os 28 graves foram resolvidos** + 71% do total. Os 51 que sobraram são "etiqueta de obra" — viram itens rastreados (`GATE-*`) que entram naturalmente em Wave A quando o módulo correspondente for codado.

**Marco 3 OS está destravado pra arrancar.**

Um item EMERGENCIAL que **não é técnico** — precisa de você: acionar uma corretora de seguros (Marsh, AON ou Howden) com o briefing pronto do ADR-0028 pra emitir a apólice de "custódia de equipamento" (BPT). Hoje, a Balanças Solution já recebe instrumentos de cliente — se um cair, queimar ou for roubado, há responsabilidade civil sem cobertura. Esse ponto não pode esperar Wave A.
