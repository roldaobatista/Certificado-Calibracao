---
owner: Roldão
revisado-em: 2026-05-23
status: stable
modulo: equipamentos
dominio: suporte-plataforma
versao: 1
---

# Débitos técnicos — Módulo Equipamentos

> Criado na **Onda 5 saneamento (2026-05-23)** — pós-auditoria
> projeto-inteiro 10 lentes. Concentra dívidas conhecidas do módulo
> sem fazer change agora pra não quebrar referências cross-onda.
> Cada débito tem dono, motivo, momento de pagar e critério de
> mortalidade.

---

## D-EQP-001 — Mover módulo de `suporte-plataforma` para `metrologia`

**Achado:** G1 ALTO (auditoria projeto-inteiro 10 lentes).

**Drift:** o módulo `equipamentos` modela equipamentos físicos
calibrados (balanças, termômetros, paquímetros do cliente). Está em
`docs/dominios/suporte-plataforma/modulos/equipamentos/` mas a
classificação semântica correta é **metrologia** — equipamento do
cliente é sujeito da calibração.

**Decisão:** mover `docs/dominios/suporte-plataforma/modulos/equipamentos/`
→ `docs/dominios/metrologia/modulos/equipamentos/` na Wave A
(antes de Marco 4 entrar em codificação).

**Não fazer agora:** a Onda 5 pré-Marco 3 envolve várias ondas
paralelas tocando referências cross-módulo. Mover diretório
quebraria `docs/INDICE.md`, `AGENTS.md §8`, frontmatter de
`prd.md`/`modelo-de-dominio.md` e ~20 referências em ADRs / docs de
conformidade. **Outra Onda final consolidará** após todas as 10
ondas terminarem.

**Quando pagar:** Wave A — primeira sprint, antes de Marco 4 codar.

**Quem paga:** agente Onda final consolidadora (não esta Onda 5).

---

## D-EQP-002 — Tipagem `Equipamento.faixa: str` → `FaixaMedicao[]`

**Achado:** G3 CRÍTICO (auditoria 10 lentes).

**Drift atual:** `EquipamentoVersao.snapshot_atributos_versionaveis`
guarda `faixa_medicao: str` solto (texto livre tipo
"0 a 200 kg"). Já existem VOs metrológicos tipados
(`src/domain/metrologia/value_objects.py` — `FaixaMedicao`).

**Decisão:** Wave A migra `Equipamento` para usar
`faixas_medicao: list[FaixaMedicao]` (1 equipamento N grandezas;
cada grandeza M faixas). Snapshot da versão guarda JSONB
deserializável no VO.

**Cross-módulo:** `Calibracao.atividade` referencia
`cmc_aplicavel_id: FK opcional` — CMC (Capability of Measurement,
art. ILAC P14) vive em `padroes` ou em `calibracao` (decidir em
PRD Marco 4).

**AC novo a inserir em PRD US-EQP-002:** "1 equipamento N grandezas;
cada grandeza M faixas; cada faixa carrega VO tipado".

**Quando pagar:** Wave A Marco 4 (`calibracao` exige tipagem
metrológica forte; pre-emissão usa `FaixaMedicao` para checar
cobertura do padrão).

**Quem paga:** Marco 4 (`calibracao`) com colaboração de
`equipamentos` para migrar schema sem drift.

---

## D-EQP-003 — Cenário OS combinada (manutenção + calibração) na atividade

**Achado:** G5 CRÍTICO (auditoria 10 lentes).

**Cenário:** OS recebe equipamento que precisa de manutenção
**E** calibração na mesma visita (ADR-0023 — OS contém N
AtividadeDaOS de tipos diferentes). Equipamento fica em fluxo
sobreposto.

**Decisão (a cravar em Onda 6):**

- `AtividadeDaOS` ganha FK lógica `equipamento_id` (já cravada em
  INV-OS-ATIV-002 — herdada da OS pai).
- Predicate "equipamento bloqueado por atividade em curso" valida
  antes de aceitar nova atividade simultânea.
- **AC novo (a inserir em PRD `os` Marco 3):** "atividades
  EM_EXECUCAO simultâneas no mesmo equipamento exigem
  compatibilidade — INV-OS-CONC-001 vai cravar matriz".
- Matriz de compatibilidade (esboço):
  - `manutencao_corretiva` ↔ `calibracao` no mesmo equipamento =
    SERIAL (manutenção primeiro, calibração depois).
  - `verificacao_inmetro` ↔ qualquer = SERIAL.
  - `vistoria` ↔ `instalacao` = PARALELA permitida.

**Quando pagar:** Onda 6 cria `INV-OS-CONC-001`. Esta Onda 5
**apenas referencia** o INV futuro.

**Quem paga:** Onda 6 (Marco 3 OS).

---

## D-EQP-004 — Materialização `HistoricoCertificadoEquipamento`

**Achado:** G6 ALTO (auditoria 10 lentes).

**Estado atual:** ficha 360° agrega últimos 10 certs via JOIN ao
módulo `certificados` (porta `CertificadoQueryService` ainda
stub). Quando módulo entrar em volume, p95 estoura.

**Decisão:** Wave A materializa
`HistoricoCertificadoEquipamento(equipamento_id, ultimos_10_certs: JSONB,
atualizado_em)` via consumer do evento `certificado.emitido`.
Mantém p95 < 1.5s mesmo com 1000+ certs no histórico.

**AC novo (a inserir em PRD US-EQP-003):** "Ficha 360° agrega
últimos 10 certs (via materialização `HistoricoCertificadoEquipamento`)
+ p95<1.5s".

**Quando pagar:** Wave A — quando módulo `certificados` cravar +
primeiro tenant com volume.

**Quem paga:** Marco `certificados` Wave A (consumer +
materialização).

---

## D-EQP-005 — Multi-estado de manutenção em paralelo

**Achado:** G7 ALTO (auditoria 10 lentes).

**Drift atual:** `Equipamento.status` é enum single-value. Marco 2
não previu cenários como "equipamento em manutenção corretiva E
verificação INMETRO em paralelo" (atividades simultâneas — D-EQP-003).

**Decisão:** Wave A adiciona campos de status segmentados:
- `EM_MANUTENCAO_CORRETIVA`
- `EM_MANUTENCAO_PREVENTIVA`
- `EM_CALIBRACAO_LAB`
- `EM_VERIFICACAO`

Para atividades paralelas, expor `estados_concorrentes: set` em vez
de single enum. Gate: `INV-OS-CONC-001` (Onda 6) define quais
combinações são permitidas.

**Quando pagar:** Wave A Marco 3 — junto com OS multi-atividade.

**Quem paga:** Marco 3 (`os`) + retrofit em `equipamentos`.

---

## D-EQP-006 — Entidade `Movimentacao` (rastreio físico)

**Achado:** G4 ALTO (auditoria 10 lentes).

**Cenário:** equipamento muda de localização sem ser
recebimento/devolução: emprestado a outro tenant (cliente leva pra
filial), troca de componente (módulo trocado por outro do mesmo
fabricante), reaparecimento após `EXTRAVIADO`. Não há entidade
canônica.

**Decisão:** Wave A cria `Movimentacao`:

```
Movimentacao(
  equipamento_id: FK,
  tipo: enum {recebimento_lab, recebimento_campo, saida_para_uso,
              devolucao, emprestimo, troca_componente,
              sucateamento, reaparecimento},
  data: timestamp,
  responsavel_id: usuario_id,
  justificativa: text (≥30 chars, anti-PII INV-EQP-LOC-001),
  audit_event_id: FK,
  local_recebimento: enum {lab, domicilio_cliente, em_evento} NULL,
  -- D-EQP-008 ADR-0028 BPT recebimento em campo
)
```

**Regras:**
- `EXTRAVIADO → ATIVO` exige `tipo=reaparecimento` + justificativa.
- WORM (padrão B — ADR-0031).
- Toda mudança em `Equipamento.status` precisa Movimentacao na
  mesma transação.

**Quando pagar:** Wave A — antes do 1º tenant que opera com
UMC/empréstimo.

**Quem paga:** Marco 3 (`os`) ou retrofit em `equipamentos`.

---

## D-EQP-007 — Carta de competência RT + GATE-EQP-RT-NOTIF

**Achado:** G8 ALTO (auditoria 10 lentes).

**Gap atual:** ADR-0022 entrega modelo de RT + competência por
grandeza, mas falta:
- Job diário `expirar_rt_competencia_vigente_ate`.
- Job notificação `notificar_rt_competencia_vencendo_30d_15d_7d_1d`.
- Anexo PDF da carta de competência (assinado A3 PJ + retenção
  25a).
- Consumer `notificar_anpd_cgcre_rt_trocado` (cl. 5.6.1
  NIT-DICLA-021 — laboratório informa CGCRE em 30d).

**Decisão (US-EQP-RT-008 a inserir em PRD):**

```
US-EQP-RT-008 — RT competência vencendo / expirada
- AC1: job diário 02:00 BRT expira RTCompetencia onde
  vigente_ate < now() → evento padrao.competencia_expirada
- AC2: job 09:00 BRT notifica gestor de qualidade do tenant para
  competências vencendo em 30/15/7/1 dia
- AC3: cadastro de RTCompetencia exige anexo PDF da carta de
  competência (assinada A3 PJ) — retenção 25a
- AC4: troca de RT dispara consumer stub
  notificar_anpd_cgcre_rt_trocado (Wave A entrega payload
  estruturado; integração real em GATE-EQP-RT-NOTIF)
```

**GATE-EQP-RT-NOTIF — Wave A:** criar consumer stub
`notificar_anpd_cgcre_rt_trocado` em
`src/infrastructure/equipamentos/consumers/`. Stub loga payload +
publica `padrao.rt_trocado_notificacao_pendente` em audit. Wave A+
pluga integração real (e-mail/API CGCRE).

**Quando pagar:** Wave A (gestor de qualidade do tenant não pode
operar sem alertas de expiração).

**Quem paga:** retrofit em `equipamentos` US-EQP-007 +
`comunicacao-omnichannel` (job notificação).

---

## D-EQP-008 — `local_recebimento` em `Recebimento`/`Movimentacao`

**Achado:** G12 MÉDIO (auditoria 10 lentes — TEMA-G ADR-0028 BPT).

**Cenário:** ADR-0028 (mapa de coberturas seguro Wave A) cita BPT
(Balança Portátil de Transporte) — equipamento pode ser recebido
em domicílio do cliente ou em evento (feira/treinamento). Cobertura
de seguro muda por local.

**Decisão:** adicionar campo
`local_recebimento: enum {lab, domicilio_cliente, em_evento}` em:
- `EquipamentoRecebimento` (já existe — adicionar campo)
- `RecebimentoProvisorio` (já existe — adicionar campo)
- `Movimentacao` (D-EQP-006 — incluir desde o nascimento)

Quando `local_recebimento != lab`, dispara consumer cobertura BPT
(ADR-0028 GATE-SEG-BPT-1).

**Quando pagar:** Wave A — antes do 1º tenant BPT (Balanças
Solution dogfooding usa UMC).

**Quem paga:** retrofit em `equipamentos` + `comunicacao-omnichannel`.

---

## D-EQP-009 — Cascade anonimização cliente → equipamento

**Achado:** G10 ALTO (auditoria 10 lentes).

**Drift atual:** `Equipamento.cliente_atual_id` é FK NULL com
`ON DELETE SET NULL`. Quando cliente é anonimizado (LGPD art. 18
VI — Zona A do ADR-0021), evento `Cliente.Anonimizado` deve
propagar para equipamento sem quebrar rastreabilidade de cert
emitido.

**Decisão:** Wave A cria consumer
`equipamentos.consumir_cliente_anonimizado`:

```
def consumir_cliente_anonimizado(evento):
    # 1. Localizar todos Equipamento com cliente_atual_id = evento.cliente_id
    # 2. Atualizar Equipamento.cliente_atual_id → NULL
    # 3. Preservar Equipamento.cliente_id_original_hash (já imutável — INV-025)
    # 4. Idem para RecebimentoProvisorio.cliente_id_provisorio
    # 5. Registrar audit AcessoDadosCliente motivo=anonimizacao_propagada
    #    (INV-ANON-004)
    # 6. Publicar evento equipamento.cliente_anonimizado_propagado
```

**Esta Onda 5 apenas declara o consumer.** Onda 1 (drift + evento
canônico `Cliente.Anonimizado` v11) cria o evento; aqui só
referenciamos.

**Cross-módulo:** ADR-0032 governa o padrão geral; consumers em
`equipamentos`, `os`, `certificados` seguem mesmo molde.

**Quando pagar:** Wave A — antes do 1º exercício direito ao
esquecimento por cliente final.

**Quem paga:** retrofit em `equipamentos` (consumer) + Onda 1
(evento canônico).

---

## D-EQP-010 — Flutter PWA: contrato `verificar_qr_hash` cobre ambos

**Achado:** G9 MÉDIO (auditoria 10 lentes — ADR-0018).

**Estado atual:** US-EQP-003 entrega scanner QR em PWA com
`BarcodeDetector` (Marco 2). Flutter chega em Wave B.

**Decisão:** endpoint server-side
`POST /v1/qr/verificar` (já existe — INV-051) **já cobre ambos**.
Contrato:

```
request: { hash: str, contexto_cliente: enum {pwa, flutter} }
response: { equipamento: EquipamentoSummary | EquipamentoSummaryMinimo,
            escopo: enum {A, B, C} }
```

Flutter Wave B chama o mesmo endpoint passando
`contexto_cliente=flutter` para analytics. Não há fork de contrato.

**Quando pagar:** declarado já. Flutter Wave B só consome.

---

## D-EQP-011 — Porta-stub `metrologia/procedimentos`

**Achado:** G11 MÉDIO (auditoria 10 lentes).

**Cenário:** `Equipamento.procedimento_calibracao_aplicavel: FK
opcional` aponta para `ProcedimentoCalibracao` que ainda não
existe.

**Decisão:** Onda 7 cuida do módulo `metrologia/procedimentos`
(criação do PRD + entidades + porta exposta). Esta Onda 5 apenas
referencia o débito.

**Quem paga:** Onda 7.

---

## Rastreio cross-onda

| Débito | Onda que cria | Onda que paga | Bloqueia |
|---|---|---|---|
| D-EQP-001 | Onda 5 | Onda final consolidadora | Wave A começo |
| D-EQP-002 | Onda 5 | Marco 4 | Marco 4 |
| D-EQP-003 | Onda 5 | Onda 6 | Marco 3 OS |
| D-EQP-004 | Onda 5 | `certificados` Wave A | 1º tenant volume |
| D-EQP-005 | Onda 5 | Marco 3 + retrofit | Marco 3 OS multi-ativ. |
| D-EQP-006 | Onda 5 | Marco 3 ou retrofit | 1º tenant UMC/BPT |
| D-EQP-007 | Onda 5 | Wave A retrofit | 1º tenant em A |
| D-EQP-008 | Onda 5 | Wave A retrofit | 1º tenant BPT |
| D-EQP-009 | Onda 5 | Onda 1 + retrofit | 1º exercício LGPD art. 18 VI |
| D-EQP-010 | Onda 5 | declarado | Wave B Flutter |
| D-EQP-011 | Onda 5 | Onda 7 | Marco 4 detalha |
