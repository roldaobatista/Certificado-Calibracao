---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
modulo: treinamentos
dominio: rh-frota-qualidade
relacionados:
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/prd.md
  - docs/dominios/rh-frota-qualidade/modulos/seguranca-trabalho/prd.md
  - docs/dominios/rh-frota-qualidade/modulos/qualidade/prd.md
  - docs/dominios/operacao/modulos/ordens-de-servico/prd.md
---

# PRD — Módulo Treinamentos e Certificações Internas

> Origem: `docs/novas funcionalidades.txt` linhas 1413-1432 (Adicional 12 — Treinamentos e Certificações Internas).

---

## 1. O que este módulo é

Módulo que gerencia capacitação técnica e de segurança da equipe: catálogo de treinamentos, eventos (turma / facilitador / data / presença), provas / avaliações, emissão de certificados com validade, trilha de capacitação por função / cargo / equipamento / norma, e **matriz de competência** auditável. Atua como **trava operacional**: bloqueia execução de OS / calibração se o técnico não estiver habilitado para o equipamento ou norma exigida.

## 2. Por que este módulo existe (problema a resolver)

**ISO/IEC 17025 cláusula 6.2 (Pessoal)** exige que o laboratório demonstre **competência** documentada de cada signatário e técnico em cada atividade que executa. Sem matriz de competência viva e auditável, o tenant não passa em supervisão CGCRE (perfil A) nem em auditoria de qualidade ISO 9001 (perfis B/C). Hoje, na operação do Roldão (Balanças Solution), capacitação fica em pastas físicas e ninguém sabe quem está habilitado para o quê — risco direto de emitir certificado com técnico não-competente (não-conformidade técnica).

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Catálogo de treinamentos (internos + externos), por categoria (segurança, técnico, normativo, comportamental).
- Eventos de treinamento: turma, facilitador, data, local, carga horária, lista de presença, material anexo.
- Provas / avaliações (questionário simples com nota mínima de aprovação).
- Certificado de conclusão com validade configurável (1 / 2 / 5 anos ou indeterminado).
- Trilha de capacitação por função / cargo / equipamento / norma — define o que o colaborador PRECISA ter para exercer.
- Matriz de competência (visão consolidada: linhas = colaboradores, colunas = habilidades / normas / equipamentos; célula = válido / vencido / a vencer / inexistente).
- Bloqueio de execução de OS / emissão de certificado se técnico não está habilitado (ISO 17025 cl. 6.2).
- Histórico de capacitação por colaborador (linha do tempo).
- Notificação de vencimento (30/60/90 dias).
- Reciclagem programada (renovação obrigatória).
- Integração com módulo `seguranca-trabalho` (NR-10, NR-12, NR-35 são treinamentos com efeito SST).

## 5. Non-goals (o que NÃO está neste módulo)

> LLM não infere por omissão.

- **Plataforma LMS (vídeos, aulas online, fórum)** — V2. MVP é gestão de registros, não EAD.
- **Pagamento de treinamento externo** — vive em `financeiro/` (não existe MVP-1).
- **Avaliação de desempenho do colaborador** — V2; aqui é capacitação técnica.
- **Recrutamento / contratação baseada em competência** — V2.
- **Plano de carreira / sucessão** — V2.
- **Onboarding workflow** (checklist de admissão) — V2.
- **Reconhecimento facial / biometria de presença em treinamento** — V2.
- **Pesquisa de satisfação pós-treinamento** — V2.
- **eSocial S-2230 (treinamentos)** — V2.

## 6. User Stories

### US-TRE-001: Cadastrar treinamento no catálogo
**Como** gerente RH/Qualidade, **quero** cadastrar treinamento no catálogo (nome, categoria, carga horária, validade do certificado), **para** padronizar oferta.

**Critérios de aceite:**
- **AC-TRE-001-1**: GIVEN cadastro, WHEN nome + categoria + carga horária preenchidos, THEN treinamento ativo.
- **AC-TRE-001-2**: Categoria "segurança" + sub-categoria NR-* publica integração com módulo `seguranca-trabalho`.

**Invariantes:** `INV-001`, `INV-TENANT-001`.

---

### US-TRE-002: Programar evento (turma)
**Como** gerente RH, **quero** programar evento (turma) de um treinamento do catálogo com data, local, facilitador e participantes, **para** organizar a execução.

**Critérios de aceite:**
- **AC-TRE-002-1**: Lista de participantes vinculada a colaboradores ativos.
- **AC-TRE-002-2**: Facilitador pode ser interno (colaborador) ou externo (texto livre + CPF/CNPJ opcional).

**Invariantes:** `INV-001`.

---

### US-TRE-003: Registrar presença e nota
**Como** facilitador / gerente RH, **quero** registrar presença e nota (se houve prova) por participante, **para** gerar certificado válido.

**Critérios de aceite:**
- **AC-TRE-003-1**: GIVEN evento concluído, WHEN registra presença ≥75% (configurável) + nota ≥ mínima, THEN certificado pode ser emitido.
- **AC-TRE-003-2**: GIVEN presença <75% OU nota < mínima, THEN certificado bloqueado.

---

### US-TRE-004: Emitir certificado de conclusão
**Como** gerente RH, **quero** emitir certificado de conclusão com validade configurável, **para** documentar competência.

**Critérios de aceite:**
- **AC-TRE-004-1**: PDF gerado com identificação tenant + colaborador + treinamento + facilitador + carga horária + data + validade + hash.
- **AC-TRE-004-2**: Certificado imutável após emissão (`INV-001`).
- **AC-TRE-004-3**: Em V2, assinatura digital ICP-Brasil opcional (`INV-017` aplicado).

---

### US-TRE-005: Definir trilha de capacitação por função / equipamento / norma
**Como** gerente Qualidade, **quero** definir trilha obrigatória de treinamentos por função (técnico calibrador), equipamento (balança comercial / paquímetro) e norma (NIT-DICLA-030 / ISO 17025), **para** que sistema saiba o que cada colaborador precisa.

**Critérios de aceite:**
- **AC-TRE-005-1**: Trilha por função = N treinamentos obrigatórios + N opcionais.
- **AC-TRE-005-2**: Trilha por equipamento = treinamentos específicos do equipamento.
- **AC-TRE-005-3**: Trilha por norma = treinamentos da norma (ex: ISO 17025 — interpretação cl. 6.2 e 6.5).
- **AC-TRE-005-4**: Mudança na trilha gera versionamento; colaboradores existentes ficam na versão antiga até renovação.

---

### US-TRE-006: Visualizar matriz de competência
**Como** gerente Qualidade / dono, **quero** matriz consolidada (linhas = colaboradores, colunas = habilidades), **para** ver lacunas e planejar capacitação.

**Critérios de aceite:**
- **AC-TRE-006-1**: Célula colorida por status (válido verde / a vencer amarelo / vencido vermelho / inexistente cinza).
- **AC-TRE-006-2**: Filtros por função, departamento, equipamento, norma.
- **AC-TRE-006-3**: Export PDF + XLSX.

---

### US-TRE-007: Bloquear execução de OS / calibração se técnico não habilitado
**Como** sistema, **quero** bloquear alocação de técnico em OS / emissão de certificado de calibração se trilha de capacitação do equipamento / norma não está completa e válida, **para** atender ISO 17025 cl. 6.2.

**Critérios de aceite:**
- **AC-TRE-007-1**: GIVEN OS de calibração de balança 500kg, WHEN tenta alocar técnico sem trilha "calibração balanças >300kg", THEN bloqueio com motivo claro.
- **AC-TRE-007-2**: GIVEN signatário sem trilha "ISO 17025 — signatário", WHEN tenta assinar certificado, THEN bloqueio (`INV-003` espírito).
- **AC-TRE-007-3**: Bypass exige justificativa + aprovação do gerente Qualidade + registro em audit (`INV-001`).

**Invariantes:** `INV-001`, `INV-003` (escopo de signatário), `INV-002` (cadeia rastreabilidade).

**Norma:** **ISO/IEC 17025 cláusula 6.2** (competência de pessoal).

---

### US-TRE-008: Alertar treinamento vencendo
**Como** gerente RH, **quero** painel + notificação de treinamentos a vencer em 30/60/90 dias, **para** programar reciclagem antes do vencimento.

**Critérios de aceite:**
- **AC-TRE-008-1**: Job diário detecta vencimentos.
- **AC-TRE-008-2**: Notificação para gerente RH + colaborador.

---

### US-TRE-009: Histórico de capacitação do colaborador
**Como** gerente / colaborador, **quero** linha do tempo de todos os treinamentos do colaborador, **para** ter visão consolidada.

**Critérios de aceite:**
- **AC-TRE-009-1**: Cronologia + filtro por status (válido / vencido).
- **AC-TRE-009-2**: Export PDF (currículo interno).

---

### US-TRE-010: Reciclagem programada
**Como** gerente Qualidade, **quero** marcar treinamentos para reciclagem antes do vencimento, **para** evitar lapsos de habilitação.

**Critérios de aceite:**
- **AC-TRE-010-1**: Reciclagem programada gera evento automaticamente N dias antes do vencimento.
- **AC-TRE-010-2**: Convoca participantes da turma anterior por padrão.

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Taxa de colaboradores 100% aderentes à trilha = 100%.
- Tempo médio entre vencimento e reciclagem ≤30 dias.
- Zero emissões de certificado de calibração com técnico não-habilitado.

## 8. NFR

- **Performance:** matriz de competência carrega em ≤3s para tenant com 100 colaboradores × 50 habilidades.
- **Disponibilidade:** SLO 99.9% — bloqueio de execução é caminho crítico de calibração.
- **Segurança:** SEC-* aplicáveis; certificado de conclusão pode ter dado pessoal (CPF do colaborador).
- **Acessibilidade:** WCAG 2.1 AA (`INV-016`).
- **Conformidade:** **ISO/IEC 17025 cláusula 6.2** + ISO 9001 (cap. 7.2 competência).

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID `US-TRE-NNN`.
- Mudança em AC implementado → ADR + novo teste.
