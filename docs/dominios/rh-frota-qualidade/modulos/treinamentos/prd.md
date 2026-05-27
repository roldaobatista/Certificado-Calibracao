---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
diataxis: explanation
audiencia: agente
modulo: treinamentos
dominio: rh-frota-qualidade
historico:
  - 2026-05-27 — Onda PRE-A.3 saneamento pré-Wave A (BATCH B3): frontmatter canônico
    (hífens); perfil ADR-0067 declarado em §4 + matriz feature×perfil; AC binário
    GIVEN-WHEN-THEN com ID; AC-TRE-007 reescrito por ADR-0069 (4 condições objetivas
    + cota mensal por perfil + lock pós-aceite + notificação CGCRE bypass perfil A
    > 2 meses); nova US-TRE-011 (matriz competência cl. 6.2.5 pessoa × atividade ×
    supervisor exigido); nova US-TRE-012 (plano anual auditoria interna 8.8 +
    análise crítica direção 8.9 — L3#A14 adiantado para Wave A); persona "operador
    metrologista júnior" (L3#A16) inline; non-objetivos expandidos; métricas
    inline; glossário §11.
  - 2026-05-17 — versão inicial.
relacionados:
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/prd.md
  - docs/dominios/rh-frota-qualidade/modulos/seguranca-trabalho/prd.md
  - docs/dominios/rh-frota-qualidade/modulos/qualidade/prd.md
  - docs/dominios/operacao/modulos/ordens-de-servico/prd.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0068-sucessao-substituicao-rt.md
  - docs/adr/0069-bypass-competencia-cl-6-2-objetivo.md
  - docs/conformidade/comum/lgpd-rat.md#RAT-14
  - docs/conformidade/comum/dpia-modulos-novos.md#DPIA-03
  - docs/conformidade/comum/retencao-matriz.md
  - docs/conformidade/comum/matriz-feature-perfil.md
---

# PRD — Módulo Treinamentos e Certificações Internas

> Origem: `docs/novas funcionalidades.txt` linhas 1413-1432 (Adicional 12 — Treinamentos e Certificações Internas).
>
> **v2 stable (2026-05-27):** saneamento pré-Wave A. AC-TRE-007 (bypass competência) reescrito pela ADR-0069 com 4 condições objetivas + cota perfil + lock; matriz competência cl. 6.2.5 adicionada (US-TRE-011); plano anual auditoria interna 8.8 + análise crítica direção 8.9 adiantados para Wave A (US-TRE-012 — L3#A14).

---

## 1. O que este módulo é

Módulo que gerencia capacitação técnica e de segurança da equipe: catálogo de treinamentos, eventos (turma / facilitador / data / presença), provas / avaliações, emissão de certificados com validade, trilha de capacitação por função / cargo / equipamento / norma, **matriz de competência cl. 6.2.5** (pessoa × atividade × supervisor presencial exigido sim/não), e **bypass de competência objetivo ADR-0069** (4 condições + cota perfil + lock). Atua como **trava operacional**: bloqueia execução de OS / calibração se o técnico não estiver habilitado para o equipamento/norma exigida, exceto via bypass objetivo.

Cobre também **plano anual de auditoria interna ISO 17025 cl. 8.8** e **ata de análise crítica pela direção cl. 8.9** (US-TRE-012 — L3#A14 adiantado de MVP-2 para Wave A).

## 2. Por que este módulo existe (problema a resolver)

**ISO/IEC 17025 cláusula 6.2 (Pessoal)** exige que o laboratório demonstre **competência** documentada de cada signatário e técnico em cada atividade que executa. Cl. 8.8 e 8.9 exigem auditoria interna anual + análise crítica pela direção. Sem matriz de competência viva e auditável, o tenant não passa em supervisão CGCRE (perfil A) nem em auditoria de qualidade ISO 9001 (perfis B/C).

Hoje, na operação do Roldão (Balanças Solution), capacitação fica em pastas físicas e ninguém sabe quem está habilitado para o quê — risco direto de emitir certificado com técnico não-competente (não-conformidade técnica). Pior: o AC-TRE-007-3 original permitia bypass arbitrário com "justificativa + aprovação do gerente Qualidade" — CGCRE não aceita esse texto livre (achado CRÍTICO L1#5 da auditoria 10 lentes 2026-05-27, resolvido pela ADR-0069).

## 3. Personas

- **P-RH-01 — Gerente RH/Qualidade** (principal): cadastra catálogo, programa eventos, gera certificados.
- **P-OP-04 — Gestor de qualidade do tenant** (perfil A obrigatório — ADR-0067): aprova trilha + assina A3 em bypass (ADR-0069 condição 4).
- **P-OP-03 — RT do tenant** (ADR-0022 v2 + ADR-0068): supervisor presencial em bypass (ADR-0069 condição 1).
- **P-OP-02-JR — Operador metrologista júnior** (nova — L3#A16): tem trilha incompleta + atua sob supervisão presencial cl. 6.2.5; consome bypass legítimo enquanto completa trilha.
- **P-COM-02 — Auditor CGCRE / consultor RBC** (perfil A): consulta matriz competência + bypass histórico.

Ver `personas.md` deste módulo + transversais em `../../personas.md`.

## 4. Perfil regulatório (ADR-0067)

| Perfil | Status do módulo | Cota bypass mensal (ADR-0069) | Predicate |
|---|---|---|---|
| **A — Acreditado RBC** | ✅ OBRIGATÓRIO_FULL (trilha + matriz cl. 6.2.5 + auditoria 8.8/8.9) | **5%/mês** rolling 30d | `tenant_perfil_e(["A"])` em US-TRE-007 + 011 + 012 |
| **B — Rastreável** | ✅ OBRIGATÓRIO (trilha; auditoria 8.8/8.9 recomendada) | **10%/mês** rolling 30d | `tenant_perfil_e(["A", "B"])` |
| **C — Em preparação D→A** | ✅ OBRIGATÓRIO_PARCIAL (trilha; auditoria 8.8 obrigatória; 8.9 recomendada) | **5%/mês** (mesma rigor de A para preparar promoção) | `tenant_perfil_e(["A", "B", "C"])` |
| **D — Comercial puro** | 🟢 OPCIONAL_RECOMENDADO (sem trilha obrigatória ISO; só SST que vem de `seguranca-trabalho`) | **20%/mês** (sem ISO 17025 envolvido) | sem bloqueio ISO; só NR vem de `seguranca-trabalho` |

Linha "Bypass competência cl. 6.2" da matriz `docs/conformidade/comum/matriz-feature-perfil.md` é fonte da verdade. ADR-0069 §2.4 detalha matriz × perfil.

## 5. Escopo (o que ESTÁ neste módulo)

- Catálogo de treinamentos (internos + externos), por categoria (segurança, técnico, normativo, comportamental).
- Eventos de treinamento: turma, facilitador, data, local, carga horária, lista de presença, material anexo.
- Provas / avaliações (questionário simples com nota mínima de aprovação).
- Certificado de conclusão com validade configurável (1 / 2 / 5 anos ou indeterminado).
- Trilha de capacitação por função / cargo / equipamento / norma.
- **Matriz de competência cl. 6.2.5** — `(pessoa × atividade × supervisor_presencial_exigido)` (US-TRE-011 nova).
- Matriz consolidada (linhas = colaboradores, colunas = habilidades; célula = válido / vencido / a vencer / inexistente).
- Bloqueio de execução de OS / emissão de certificado se técnico não habilitado (ISO 17025 cl. 6.2).
- **Bypass de competência objetivo ADR-0069** — 4 condições + cota perfil + lock pós-aceite + notificação CGCRE bypass perfil A > 2 meses.
- Histórico de capacitação por colaborador (linha do tempo).
- Notificação de vencimento (30/60/90 dias).
- Reciclagem programada (renovação obrigatória).
- Integração com módulo `seguranca-trabalho` (NR-10/NR-12/NR-35 são treinamentos com efeito SST — vide cross-link AC-TRE-001-2).
- **Plano anual auditoria interna cl. 8.8 + ata análise crítica direção cl. 8.9** (US-TRE-012 nova — L3#A14 adiantado).

## 6. Não-objetivos (o que NÃO está neste módulo)

> LLM não infere por omissão.

- **Plataforma LMS (vídeos, aulas online, fórum)** — Wave B. Wave A é gestão de registros, não EAD.
- **Pagamento de treinamento externo** — vive em `financeiro/` (não existe Wave A).
- **Avaliação de desempenho do colaborador** — Wave B; aqui é capacitação técnica.
- **Recrutamento / contratação baseada em competência** — Wave B.
- **Plano de carreira / sucessão** — Wave B.
- **Onboarding workflow** (checklist de admissão) — Wave B.
- **Reconhecimento facial / biometria de presença em treinamento** — Wave B.
- **Pesquisa de satisfação pós-treinamento** — Wave B.
- **eSocial S-2230 (treinamentos)** — Wave B.
- **Bypass por delegação cross-tenant (RT vendor)** — Wave B (ADR-0069 §6 non-goal).

## 7. User Stories

### US-TRE-001: Cadastrar treinamento no catálogo

**Como** gerente RH/Qualidade, **quero** cadastrar treinamento no catálogo (nome, categoria, carga horária, validade do certificado), **para** padronizar oferta.

**Critérios de aceite:**
- **AC-TRE-001-1**: GIVEN gerente RH autenticado, WHEN preenche nome + categoria + carga horária + validade do certificado, THEN treinamento ativo no catálogo.
- **AC-TRE-001-2**: GIVEN categoria="segurança" + sub-categoria `NR-*`, WHEN salvo, THEN publica evento `treinamento.cadastrado_sst` consumido por módulo `seguranca-trabalho`.

**Invariantes:** `INV-001`, `INV-TENANT-001`.

---

### US-TRE-002: Programar evento (turma)

**Como** gerente RH, **quero** programar evento (turma) de um treinamento do catálogo com data, local, facilitador e participantes, **para** organizar a execução.

**Critérios de aceite:**
- **AC-TRE-002-1**: GIVEN treinamento ativo no catálogo, WHEN gerente cadastra evento, THEN lista de participantes é vinculada a colaboradores ativos (FK validada).
- **AC-TRE-002-2**: GIVEN evento em criação, WHEN facilitador interno selecionado, THEN sistema valida que é colaborador ativo; WHEN facilitador externo, THEN aceita nome + CPF/CNPJ opcional.

**Invariantes:** `INV-001`.

---

### US-TRE-003: Registrar presença e nota

**Como** facilitador / gerente RH, **quero** registrar presença e nota (se houve prova) por participante, **para** gerar certificado válido.

**Critérios de aceite:**
- **AC-TRE-003-1**: GIVEN evento concluído + participante com presença ≥75% (configurável) + nota ≥ mínima do catálogo, WHEN gerente confirma, THEN certificado pode ser emitido (AC-TRE-004).
- **AC-TRE-003-2**: GIVEN presença <75% OU nota < mínima, WHEN tenta emitir certificado, THEN bloqueio com mensagem citando regra do catálogo.

---

### US-TRE-004: Emitir certificado de conclusão

**Como** gerente RH, **quero** emitir certificado de conclusão com validade configurável, **para** documentar competência.

**Critérios de aceite:**
- **AC-TRE-004-1**: GIVEN US-TRE-003 satisfeita, WHEN emite, THEN PDF gerado com identificação tenant + colaborador + treinamento + facilitador + carga horária + data + validade + hash SHA-256.
- **AC-TRE-004-2**: GIVEN certificado emitido, WHEN persistido, THEN imutável após emissão (`INV-001` + WORM).
- **AC-TRE-004-3**: GIVEN tenant `perfil_regulatorio ∈ {A, B, C}` + treinamento categoria=`técnico` ou `normativo`, WHEN emite, THEN exige assinatura A3 ICP-Brasil do gestor de qualidade (`INV-017`).
- **AC-TRE-004-4 (LGPD)**: Tratamento atende base **Execução de contrato (art. 7º V) + Obrigação regulatória (art. 7º II)** ISO 17025 cl. 6.2 (RAT-02 + RAT-14 quando treinamento de segurança). Para ASO vinculado a treinamento (NR-7/NR-35): base art. 11 II "a" — obrigação legal (DPIA-03).
- **AC-TRE-004-5 (Retenção)**: Certificado de conclusão conforme `retencao-matriz.md` linha "Cadastro de pessoa física" (vigência + 5 anos); para treinamentos NR-* com vínculo ASO: 20 anos pós-vínculo (NR-7); após prazo: anonimização (CPF → hash, nome preservado para histórico técnico).

---

### US-TRE-005: Definir trilha de capacitação por função / equipamento / norma

**Como** gerente Qualidade, **quero** definir trilha obrigatória de treinamentos por função (técnico calibrador), equipamento (balança comercial / paquímetro) e norma (NIT-DICLA-030 / ISO 17025), **para** que sistema saiba o que cada colaborador precisa.

**Critérios de aceite:**
- **AC-TRE-005-1**: GIVEN gerente qualidade autenticado, WHEN cadastra trilha por função, THEN sistema persiste lista de N treinamentos obrigatórios + N opcionais.
- **AC-TRE-005-2**: GIVEN trilha por equipamento, WHEN cadastrada, THEN vincula a `Equipamento.modelo` e propaga para todos os equipamentos daquele modelo.
- **AC-TRE-005-3**: GIVEN trilha por norma, WHEN cadastrada, THEN vincula a `NormaTecnica.codigo` (ex: ISO 17025 — interpretação cl. 6.2 e 6.5).
- **AC-TRE-005-4**: GIVEN mudança na trilha (adição/remoção), WHEN salva, THEN sistema versiona (`Trilha.versao` incrementa) + colaboradores existentes ficam na versão antiga até renovação (AC-TRE-010).

---

### US-TRE-006: Visualizar matriz de competência

**Como** gerente Qualidade / dono, **quero** matriz consolidada (linhas = colaboradores, colunas = habilidades), **para** ver lacunas e planejar capacitação.

**Critérios de aceite:**
- **AC-TRE-006-1**: GIVEN tela aberta, WHEN sistema renderiza, THEN cada célula colorida por status (válido verde / a vencer amarelo / vencido vermelho / inexistente cinza).
- **AC-TRE-006-2**: GIVEN filtro selecionado, WHEN aplicado, THEN matriz filtra por função, departamento, equipamento ou norma.
- **AC-TRE-006-3**: GIVEN matriz renderizada, WHEN gerente clica em exportar, THEN PDF + XLSX gerados.

---

### US-TRE-007: Bloquear execução de OS / calibração se técnico não habilitado (bypass ADR-0069)

**Como** sistema, **quero** bloquear alocação de técnico em OS / emissão de certificado de calibração se trilha de capacitação do equipamento / norma não está completa e válida, **para** atender ISO 17025 cl. 6.2. **Exceções via bypass ADR-0069 (4 condições objetivas + cota perfil + lock).**

**Critérios de aceite:**
- **AC-TRE-007-1**: GIVEN OS de calibração de balança 500kg + técnico sem trilha "calibração balanças >300kg" + sem bypass, WHEN tenta alocar, THEN bloqueio com motivo claro citando trilha ausente.
- **AC-TRE-007-2**: GIVEN signatário sem trilha "ISO 17025 — signatário" + sem bypass, WHEN tenta assinar certificado, THEN bloqueio (`INV-003` espírito).
- **AC-TRE-007-3 (reescrito por ADR-0069)**: GIVEN tenta bypass de competência, WHEN sistema valida, THEN exige TODAS as 4 condições simultâneas (para tenants `perfil_regulatorio ∈ {A, B, C}`):
  1. **Supervisão presencial documentada**: outro técnico do mesmo tenant com `RTCompetencia.{grandeza, metodo}` vigente (ADR-0022 v2) registrado em `Atividade.supervisor_presencial_id` + foto da bancada com 2 pessoas (timestamp ≤15min do início).
  2. **Treinamento expirado há ≤ 90 dias**: se vencido há mais de 90 dias, sistema retorna 422 `TreinamentoVencimentoExcedido` — exige renovação primeiro.
  3. **Justificativa categorizada em enum** (não texto livre): `EMERGENCIA_OPERACIONAL_CLIENTE` / `TREINAMENTO_AGENDADO_ATE_DATA` / `SUBSTITUICAO_TEMPORARIA_RT_ATIVO`.
  4. **A3 do gestor de qualidade** registrando bypass (não basta clique). Gestor responde solidariamente (ADR-0069 §2.1).
  Para `perfil_regulatorio = D`: condições 3 e 4 obrigatórias; condições 1 e 2 OPCIONAIS (sem ISO 17025 envolvido).
- **AC-TRE-007-4 (cota perfil — ADR-0069 §2.2)**: GIVEN bypass aprovado, WHEN sistema valida cota mensal rolling 30d, THEN cota máxima por perfil: **A 5% / B 10% / C 5% / D 20%** das atividades calibração+OS do mês. Atingiu cota → bloqueio duro até próximo mês (mesmo se condições 1-4 OK).
- **AC-TRE-007-5 (lock pós-aceite — ADR-0069 §2.3)**: GIVEN atividade com `competencia_bypass=TRUE`, WHEN `Atividade.aceita_pelo_cliente_em` preenchido, THEN registro IMUTÁVEL (trigger PG bloqueia UPDATE/DELETE em `competencia_bypass_*`).
- **AC-TRE-007-6 (notificação CGCRE — ADR-0069 §2.4 + INV-COMP-BYPASS-004)**: GIVEN `tenant_perfil_e(["A"])` + bypass com cota cheia em 2 meses consecutivos, WHEN job mensal roda, THEN dispara consumer `Tenant.BypassRecorrente → NotificacaoCGCRE` (síncrona) + flag em painel-do-dono.

**Invariantes:** `INV-001`, `INV-003` (escopo de signatário), `INV-002` (cadeia rastreabilidade), `INV-COMP-BYPASS-001..004` (ADR-0069), `INV-017`, `INV-PERFIL-001` (ADR-0067).

**Norma:** **ISO/IEC 17025 cláusula 6.2** (competência de pessoal).

---

### US-TRE-008: Alertar treinamento vencendo

**Como** gerente RH, **quero** painel + notificação de treinamentos a vencer em 30/60/90 dias, **para** programar reciclagem antes do vencimento.

**Critérios de aceite:**
- **AC-TRE-008-1**: GIVEN job diário em execução, WHEN detecta certificados vencidos OU a vencer em ≤30 / ≤60 / ≤90 dias, THEN cria notificação P2.
- **AC-TRE-008-2**: GIVEN notificação criada, WHEN entregue, THEN gerente RH + colaborador recebem (email + painel-do-dono).

---

### US-TRE-009: Histórico de capacitação do colaborador

**Como** gerente / colaborador, **quero** linha do tempo de todos os treinamentos do colaborador, **para** ter visão consolidada.

**Critérios de aceite:**
- **AC-TRE-009-1**: GIVEN colaborador selecionado, WHEN abre histórico, THEN cronologia renderizada + filtro por status (válido / vencido).
- **AC-TRE-009-2**: GIVEN histórico aberto, WHEN clica export, THEN PDF gerado (currículo interno).

---

### US-TRE-010: Reciclagem programada

**Como** gerente Qualidade, **quero** marcar treinamentos para reciclagem antes do vencimento, **para** evitar lapsos de habilitação.

**Critérios de aceite:**
- **AC-TRE-010-1**: GIVEN reciclagem programada com `dias_antes_vencimento`, WHEN job diário roda, THEN cria evento de reciclagem automaticamente N dias antes do vencimento.
- **AC-TRE-010-2**: GIVEN evento de reciclagem criado, WHEN gerente abre, THEN participantes da turma anterior aparecem pré-selecionados (convocação por padrão).

---

### US-TRE-011: Matriz competência cl. 6.2.5 — pessoa × atividade × supervisor exigido (NOVA)

**Como** RT do tenant, **quero** matriz formal `(pessoa × atividade × supervisor_presencial_exigido)` conforme ISO 17025 cl. 6.2.5, **para** atender requisito específico ausente na matriz consolidada de US-TRE-006.

**Critérios de aceite:**
- **AC-TRE-011-1**: GIVEN RT autenticado, WHEN abre tela "Matriz cl. 6.2.5", THEN sistema renderiza tabela 3D: linhas = pessoas, colunas = atividades, célula com 3 estados (`AUTONOMO` / `SUPERVISIONADO` / `INAPTO`) + flag `supervisor_presencial_exigido` (boolean).
- **AC-TRE-011-2**: GIVEN `tenant_perfil_e(["A", "B", "C"])` retorna TRUE + pessoa marcada `SUPERVISIONADO` numa atividade, WHEN alocada em OS sem supervisor presencial, THEN bloqueio (mesma trava AC-TRE-007 mas via campo declarativo, não inferência).
- **AC-TRE-011-3**: GIVEN matriz aprovada por RT, WHEN persistida, THEN evento `matriz_competencia_aprovada` em hash-chain HMAC ADR-0064 + status pessoa imutável até nova aprovação por RT.
- **AC-TRE-011-4**: GIVEN export pra dossiê CGCRE (perfil A), WHEN gerado, THEN matriz cl. 6.2.5 aparece em formato exigido pela NIT-DICLA.

**Invariantes:** `INV-MATRIZ-COMP-001` (nova — matriz exigida em perfil A/B/C), `INV-017`, `INV-HMAC-001..005`.

---

### US-TRE-012: Plano anual auditoria interna 8.8 + ata análise crítica direção 8.9 (NOVA — L3#A14 adiantado)

**Como** gestor de qualidade do tenant em perfil A/B/C, **quero** gerenciar plano anual de auditoria interna ISO 17025 cl. 8.8 + ata de análise crítica pela direção cl. 8.9, **para** atender supervisão CGCRE desde a 1ª visita (L3#A14 — originalmente MVP-2, adiantado para Wave A).

**Critérios de aceite:**
- **AC-TRE-012-1**: GIVEN `tenant_perfil_e(["A", "B", "C"])` + gestor qualidade autenticado, WHEN cria plano anual com itens (escopo + auditor interno + data prevista + checklist), THEN persiste com status `RASCUNHO`.
- **AC-TRE-012-2**: GIVEN plano em RASCUNHO, WHEN RT aprova com A3, THEN status `APROVADO` + job dispara alertas 30/15/7 dias antes de cada item.
- **AC-TRE-012-3**: GIVEN auditoria interna executada, WHEN gestor registra relatório (constatações + NCs detectadas + ação corretiva), THEN evento `auditoria_interna_concluida` em hash-chain HMAC; vincula a `NaoConformidade` existentes (cross-link com módulo `qualidade`).
- **AC-TRE-012-4**: GIVEN reunião de análise crítica pela direção realizada, WHEN gestor registra ata (presentes + pauta cl. 8.9.2 + decisões + ações), THEN persistida imutável após aprovação A3 do RT + diretor; export PDF disponível.
- **AC-TRE-012-5**: GIVEN `tenant_perfil_e(["A"])` + ano sem ata de análise crítica registrada, WHEN job anual roda em 31/12, THEN dispara alerta P1 ao RT + flag "NC ALTO — cl. 8.9 não atendida".

**Invariantes:** `INV-AUD-INT-001..003` (novas — plano anual + relatório + ata), `INV-017`, `INV-HMAC-001..005`, `INV-PERFIL-001`.

---

## 8. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Taxa de colaboradores 100% aderentes à trilha = 100%.
- Tempo médio entre vencimento e reciclagem ≤30 dias.
- **Zero emissões de certificado de calibração com técnico não-habilitado (exceto bypass ADR-0069 válido).**
- **% bypass mensal por perfil dentro da cota** (A ≤5%, B ≤10%, C ≤5%, D ≤20%): 100%.
- **Zero meses com plano de auditoria interna 8.8 atrasado em perfil A**.
- **% atas análise crítica direção 8.9 anuais em perfil A** = 100%.

## 9. NFR

- **Performance:** matriz de competência carrega em ≤3s para tenant com 100 colaboradores × 50 habilidades; matriz cl. 6.2.5 em ≤2s.
- **Disponibilidade:** SLO 99.9% — bloqueio de execução é caminho crítico de calibração.
- **Segurança:** SEC-* aplicáveis; certificado de conclusão pode ter dado pessoal (CPF do colaborador); RLS via `tenant_id` (ADR-0002); evento bypass em hash-chain HMAC ADR-0064.
- **Acessibilidade:** WCAG 2.1 AA (`INV-016` + ADR-0057).
- **Conformidade:** **ISO/IEC 17025 cláusulas 6.2, 6.2.5, 8.8, 8.9** + ISO 9001 (cap. 7.2 competência).

## 10. ADRs e INVs aplicáveis

- **ADRs:** 0007 (codegen), 0022 v2 (RT competência por método), 0026 (2ª conferência — modelo análogo), 0057 (a11y), 0064 (HMAC 25a), 0067 (perfil regulatório), 0068 (sucessão RT), 0069 (bypass competência objetivo).
- **INVs:** INV-001..003, INV-017, INV-MATRIZ-COMP-001, INV-COMP-BYPASS-001..004, INV-AUD-INT-001..003, INV-PERFIL-001, INV-HMAC-001..005, INV-TENANT-001, INV-016.

## 11. Glossário e referências

- **Competência (ISO 17025 cl. 6.2)** — capacidade demonstrada de aplicar conhecimento e habilidades. Evidência: educação + treinamento + experiência + capacidades demonstradas.
- **Trilha de capacitação** — conjunto de treinamentos obrigatórios por função/equipamento/norma.
- **Matriz cl. 6.2.5** — tabela formal `(pessoa × atividade × supervisor presencial exigido)` — autorização de signatário/operador documentada.
- **Bypass de competência** — operação fora da trilha autorizada, regulamentada pela ADR-0069 com 4 condições + cota perfil + lock pós-aceite + notificação CGCRE.
- **Supervisor presencial** (ADR-0069 condição 1) — outro técnico do mesmo tenant com `RTCompetencia.{grandeza, metodo}` vigente acompanhando presencialmente.
- **Cota bypass mensal** — % máximo do mês em bypass por perfil (A=5%, B=10%, C=5%, D=20%) — rolling 30d.
- **Auditoria interna cl. 8.8** — auditoria conduzida pelo próprio tenant em ciclos anuais.
- **Análise crítica direção cl. 8.9** — reunião anual obrigatória com pauta canônica cl. 8.9.2.
- Ver `glossario.md` deste módulo.

## 12. Como este PRD evolui

- US nova → próximo ID `US-TRE-NNN`.
- Mudança em AC implementado → ADR + novo teste de regressão.
- Mudança em cota bypass → ADR-0069 amendment.
