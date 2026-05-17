---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: qualidade
dominio: rh-frota-qualidade
---

# Modelo de domínio — Qualidade

## Agregados

### NC / NaoConformidade (agregado raiz — coração INV-012)
- `id`, `tenant_id` (INV-TENANT-002), `numero` (sequencial por tenant: NC-2026-0001), `data_abertura`, `descricao`, `origem` (enum: AUDITORIA_INTERNA, RECLAMACAO, PT_PROFICIENCY, VERIFICACAO_INTERMEDIARIA, AUTOAVALIACAO, INSPECAO_PADRAO, OUTRA), `severidade` (enum: CRITICA, MAIOR, MENOR), `status` (enum: TRIAGEM, ABERTA, EM_ACAO, AGUARDANDO_EFICACIA, FECHADA, ABERTA_COM_PENDENCIA), `responsavel_id`, `instrumento_id?` (FK Metrologia), `os_id?` (FK Operação), `certificado_id?` (FK Metrologia), `padrao_id?` (FK Metrologia), `evidencias` (anexos).
- **INV-012 — invariante ativa:** NC com `severidade=CRITICA` + `status IN (ABERTA, EM_ACAO, AGUARDANDO_EFICACIA, ABERTA_COM_PENDENCIA)` + `instrumento_id|padrao_id IS NOT NULL` → bloqueia emissão de certificado que use esse instrumento/padrão.

### Workflow de NC (máquina de estados — cl. 7.10)

```
TRIAGEM
  ↓ (responsável avalia + classifica severidade)
ABERTA
  ↓ (5 Porquês preenchido — obrigatório em CRITICA + MAIOR)
EM_ACAO (plano de ação criado + tarefas atribuídas)
  ↓ (todas tarefas do plano concluídas com evidência)
AGUARDANDO_EFICACIA
  ↓ (revisão de eficácia agendada — obrigatório)
   ├─ eficácia confirmada → FECHADA
   └─ revisão vencida sem realizar → ABERTA_COM_PENDENCIA
ABERTA_COM_PENDENCIA
  ↓ (eficácia revista)
FECHADA
```

- Invariantes da máquina:
  - Transição `ABERTA → EM_ACAO` exige 5 Porquês completo em CRITICA e MAIOR.
  - Transição `EM_ACAO → AGUARDANDO_EFICACIA` exige todas tarefas do plano com `status=CONCLUIDA` + evidência anexa.
  - Transição `AGUARDANDO_EFICACIA → FECHADA` exige `data_revisao_eficacia IS NOT NULL` + `eficacia_confirmada=true`.
  - Sem transição direta para FECHADA.

### CincoPorques (entidade filha de NC)
- `id`, `nc_id`, `pergunta_1..5`, `resposta_1..5`, `causa_raiz_final`, `preenchido_em`, `preenchido_por`.

### PlanoAcao (entidade filha de NC)
- `id`, `nc_id`, `objetivo`, `tarefas` (lista `{descricao, responsavel_id, prazo, status, evidencia_url, concluido_em}`).

### RevisaoEficacia (entidade filha de NC)
- `id`, `nc_id`, `data_agendada`, `data_realizada?`, `eficacia_confirmada?` (bool), `observacao`, `realizado_por_id?`.
- Invariante: Se `data_agendada < hoje` e `data_realizada IS NULL` → NC volta a `ABERTA_COM_PENDENCIA` automaticamente (job diário).

### Reclamacao (entidade — cl. 7.9)
- `id`, `tenant_id`, `data`, `cliente_id?`, `os_id?`, `descricao`, `canal` (WHATSAPP, EMAIL, TELEFONE, PORTAL, NPS), `recebido_por_id`, `status` (TRIAGEM, VIROU_NC, IMPROCEDENTE, RESOLVIDA_SEM_NC), `nc_id?` (se virou NC).

### NPS (entidade)
- `id`, `tenant_id`, `os_id`, `cliente_id`, `enviado_em`, `respondido_em?`, `score?` (0-10), `classificacao` (DETRATOR 0-6 / NEUTRO 7-8 / PROMOTOR 9-10), `comentario?`, `virou_reclamacao_id?`.
- Regra: score 0-6 com comentário → cria Reclamacao automática + sugere "abrir NC?".

### RiscoOportunidade (entidade — cl. 8.5)
- `id`, `tenant_id`, `tipo` (RISCO, OPORTUNIDADE), `descricao`, `probabilidade?` (1-5, soft MVP-1), `impacto?` (1-5, soft), `tratamento` (texto livre), `responsavel_id`, `nc_id?` (se já materializado).

### DocumentoQualidade (entidade — cl. 8.3 controle de documentos)
- `id`, `tenant_id`, `tipo` (MANUAL, POP, INSTRUCAO, REGISTRO), `titulo`, `versao`, `data_efetivacao`, `arquivo_url`, `aprovado_por_id`, `superseded_by_id?`.

## Hook INV-012

`check_inv012_on_emit(certificado_id) → {pode_emitir: bool, ncs_bloqueantes: [...]}`.
Disparado em: pre-emissão de certificado, geração de PDF, change de padrão usado.

## Hook INV-022 (cross-domínio)

Verificação intermediária de padrão fora da tolerância → cria NC CRITICA automática com `origem=VERIFICACAO_INTERMEDIARIA` + `padrao_id=X`. Sem intervenção humana — o hook abre.

## Eventos

`NcAberta`, `NcBloqueouEmissao` (P0 — notifica responsável + dono), `NcFechada`, `NcReabertaPorPendencia`, `EficaciaVencida`, `NpsRespondido`, `ReclamacaoRegistrada`, `RiscoIdentificado`.

## Não-modelado MVP-1

Cartas de controle, Cpk/Cp, gestão de riscos quantitativa, auditoria interna estruturada, análise crítica pela direção. → MVP-2 / V2.

## Dúvidas em aberto

- [INFERÊNCIA] Severidade MENOR também bloqueia emissão? Default MVP-1: **não** (só CRITICA bloqueia). MAIOR e MENOR alertam mas não bloqueiam. Confirmar com responsável-pela-qualidade auditor.
- [INFERÊNCIA] NC pode ter múltiplos instrumentos? Default MVP-1: sim, lista de FKs.
