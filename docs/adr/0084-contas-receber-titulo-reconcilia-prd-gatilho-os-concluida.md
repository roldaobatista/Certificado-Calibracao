---
owner: agente-ia
revisado-em: 2026-06-16
status: aceito
adr: 0084
relacionados: [0043, 0023, 0040, 0070, 0082, 0083, 0033]
---

# ADR-0084 — `Titulo` de contas-receber reconcilia o "ContasReceber" do PRD; gatilho de faturamento = `os.concluida` (emenda ADR-0043 §1)

**Status:** aceito (2026-06-16 — P8 da frente `contas-receber`; decisões cravadas como D-CR-2 e D-CR-12 na investigação T-CR-000 e implementadas nas Fatias 1a..3d. Esta ADR formaliza a reconciliação e emenda o PRD/ADR-0043.)

## Contexto

O PRD do módulo financeiro declara um agregado **"ContasReceber"** como a obrigação a
receber do tenant, e a ADR-0043 (`calibracao-faturamento-bloqueio-inadimplencia`, §1)
cravou que o **consumer financeiro reage a `Certificado.Emitido`** (status → ASSINADO),
com `vencimento = Certificado.emitido_em + prazo`.

Quando a frente `contas-receber` fechou (Fatias 1a..3d, 2026-06-15/16), duas reconciliações
ficaram pendentes de formalização:

1. **Nome do agregado.** A investigação T-CR-000 (§D-CR-2) construiu o agregado raiz como
   `Titulo` (+ `Parcela` sub + `Pagamento` evento imutável), com **1 fato gerador → 1
   título**. O `Fatura` agrupador (N títulos / consolidação) foi **diferido para Wave B**.
   Há, portanto, dois nomes para o mesmo conceito ("ContasReceber" do PRD × `Titulo` do
   código) que precisam de destino canônico explícito.

2. **Gatilho de faturamento.** A D-CR-12 **inverteu** o gatilho da ADR-0043: o faturamento
   passa a disparar em **`os.concluida` enriquecido** (serviço entregue, valor carimbado em
   `OSSnapshot.valor_total`), **não** em `Certificado.Emitido`. A ADR-0043 §1 e a D-CR-12
   ficam em **conflito literal** enquanto não houver emenda formal.

O parecer metrológico consultivo (`consultor-rbc-iso17025`, 2026-06-16, ratificando RBC-CR-05)
confirmou a base normativa dos dois pontos e identificou uma ressalva acionável (abaixo).

## Decisão

1. **O agregado raiz é `Titulo`, que É o "ContasReceber" do PRD.** O VO/entidade
   "ContasReceber" proposto no PRD **não é criado** — fica reconciliado por esta ADR.
   `Titulo` (`@dataclass(frozen=True, slots=True)` em `src/domain/contas_receber/entities.py`)
   + `Parcela` (sub-obrigação) + `Pagamento` (evento INSERT-only) cobrem o conceito com
   **1 fato gerador → 1 título ativo** (`UNIQUE(tenant_id, os_id_origem) WHERE estado !=
   cancelado` — INV-CR-OS-TITULO-UNICO). O agregador **`Fatura`** (consolidação de N títulos,
   anexo de NF, régua rica) permanece **diferido para Wave B** (GATE-CR-FATURA).

2. **O gatilho canônico ÚNICO de auto-faturamento é `os.concluida` enriquecido no outbox**
   (D-CR-12), consumido por `handle_os_concluida`
   (`src/infrastructure/contas_receber/consumers/os_eventos.py`). Razão metrológica
   (parecer RBC P2, CONFIRMA): "serviço entregue" do ponto de vista do laboratório é a
   **conclusão da atividade técnica** (ISO/IEC 17025 cl. 7.1), não a emissão do documento;
   cobrar antes quebraria o modelo B2B (ADR-0043 já rejeitou pré-pago). Ancorar o
   faturamento em `os.concluida` (e não em `Certificado.Emitido`) é **também** o que permite
   que o bloqueio por inadimplência **não alcance a emissão de certificado de OS já em
   andamento** (D-CR-21 / RBC-CR-06) — reter certificado de serviço já contratado seria
   **NC ISO/IEC 17025 cl. 7.8** (e CDC art. 39 V).

3. **Esta ADR EMENDA a ADR-0043 §1:** o gatilho `Certificado.Emitido` é **substituído por
   `os.concluida`**. Os §2 (bloqueio por inadimplência perfil-aware, grace 45/20/30/7) e §3
   (override A3 até D+90, limite 5%/mês) da ADR-0043 **permanecem vigentes**. `Certificado.Emitido`
   como gatilho fica **reconciliado/não-construído** (GATE-CR-CERT-RECONCILIA fechado por aqui).

4. **Todo certificado de calibração faturável nasce de uma OS de cliente; padrão interno é
   não-faturável** (parecer RBC P1, CONFIRMA; base: ISO/IEC 17025 cl. 6.4/6.5/7.7/8.4):
   - O certificado nasce de `AtividadeDaOS.tipo=calibracao` (ADR-0023, ADR-0082), cujo valor
     é carimbado em `OSSnapshot.valor_total`. O certificado **NÃO é unidade de cobrança
     independente** — faturá-lo além da OS configuraria **dupla cobrança** do mesmo serviço.
   - Certificado/registro de **padrão metrológico interno** (recal externo de padrão,
     verificação intermediária, carta de Shewhart — ADR-0040, ADR-0070) é **não-faturável por
     construção**: o padrão pertence ao tenant (sem `cliente_id`), e o registro é evidência de
     garantia da validade de resultados (cl. 6.5, 7.7, 8.4), não prestação de serviço a terceiro.
     A criação de `Titulo` exige cliente (D-CR-16), então a hipótese é fail-closed na modelagem.

5. **OS reaberta por reprovação na 2ª conferência (cl. 6.2.5) cancela o título** (ressalva RBC
   P2): o consumer `handle_os_reaberta` (Fatia 3a) **já cancela** o título da OS reaberta se
   **sem pagamento**; **mantém** se houver pagamento parcial/total (AC-CR-006-2). Isso cobre o
   furo "cobrar serviço metrologicamente reprovado" para o caso comum (sem pagamento). Ficam
   como **débito rastreado** (não bloqueiam o fechamento, núcleo coberto):
   - **GATE-CR-REPROVA-PAGA:** OS faturada + paga parcial → reaberta por reprovação → hoje
     mantém + loga; falta sinalização de revisão gerencial (Wave B).
   - **GATE-CR-OBS-OS-SEM-CERT:** título de OS sem certificado emitido após N dias → alerta de
     visibilidade ao financeiro do tenant (observabilidade; não bloqueia o título; Wave B).

## Reconciliação campo-a-campo (PRD "ContasReceber" → código)

| Conceito do PRD | Destino canônico |
|---|---|
| `ContasReceber` (agregado) | `Titulo` (raiz) + `Parcela` (sub) + `Pagamento` (evento INSERT-only) |
| agrupamento de N obrigações / "fatura" | `Fatura` **Wave B** (GATE-CR-FATURA) — não criado |
| gatilho de geração | evento `os.concluida` enriquecido (D-CR-12) — não `Certificado.Emitido` |
| valor da obrigação | `OSSnapshot.valor_total_atualizado` (centavos, INV-OS-FAT-001) — carimbado, não reconsultado (INV-026) |
| cliente da obrigação | `cliente_referencia` (`ReferenciaPIIAnonimizavel`, ADR-0032 / D-CR-16) |
| classificação fiscal | `categoria_receita` perfil-aware (RBC só perfil A — INV-FIN-PERFIL-001) |

## Consequências

- **Positivas:** um único conceito (`Titulo`) e um único gatilho (`os.concluida`) — sem
  tradução lossy nem dois pontos a sincronizar sob INV-026; o conflito ADR-0043 §1 × D-CR-12
  é fechado; a separação "cobrar (OS) × emitir documento (certificado)" protege contra NC
  cl. 7.8; a base normativa metrológica fica citável para a supervisão CGCRE.
- **Negativas / custo:** `Fatura` agrupadora e a régua rica ficam para Wave B; a assimetria
  temporal "OS concluída × certificado emitido depois" exige os dois GATEs de visibilidade
  acima antes do 1º perfil A externo em produção.
- **Pré-produção (humano):** o parecer RBC é consultivo de subagente IA — o dossiê cl. 7.11 e a
  defesa de rastreabilidade financeira-metrológica exigem **revisão de consultor RBC humano
  credenciado** antes da 1ª supervisão CGCRE (custo pontual estimado R$ 5–15k; base ~80% pronta).

## Non-goals

Não cria: `Fatura` agrupadora, gatilho `Certificado.Emitido`, faturamento parcial por
`AtividadeDaOS` (ADR-0051), régua de cobrança Wave B, sinalização gerencial de reprovação-com-pagamento,
observabilidade de OS-sem-certificado (os dois últimos = GATE acima). Não reabre a decisão de
gatilho sem nova ADR.
