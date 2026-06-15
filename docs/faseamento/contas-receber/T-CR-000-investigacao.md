---
owner: agente-ia
revisado-em: 2026-06-15
proximo-review: 2026-09-15
status: stable
diataxis: reference
frente: contas-receber
tipo: investigacao-regra-0
relacionados:
  - docs/dominios/financeiro/modulos/contas-receber/prd.md
  - docs/dominios/comercial/modulos/orcamentos/prd.md
  - docs/adr/0043-calibracao-faturamento-bloqueio-inadimplencia.md
  - docs/adr/0050-gateway-pagamento-pix-recorrente.md
---

# T-CR-000 — Investigação regra #0 da frente `financeiro/contas-receber`

> Feita ANTES de escrever spec (regra #0 — investigar/rastrear o fluxo antes de
> mexer). Conclusão muda a ORDEM de dependência: contas-receber está a jusante da
> precificação, que ainda não existe. Detalhe abaixo.

## 1. Estado do código

**Greenfield total.** Não existe `src/{domain,application,infrastructure}/financeiro/contas_receber/`
nem qualquer modelo `Titulo`/`Fatura`/`Pagamento`. O único módulo financeiro com código
é `fiscal` (NFS-e), que serve de molde (porta + mock + domínio + use cases + REST +
WORM/RLS + perfil server-side + hooks).

## 2. Estado da especificação

**Alta.** PRD `docs/dominios/financeiro/modulos/contas-receber/prd.md` está **stable**
(US-CR-001..010 + AC binários GIVEN-WHEN-THEN + matriz perfil-aware). Modelo de domínio,
contratos (api/ui/exports), glossário, personas, métricas existem. ADRs 0043/0050/0052/
0033/0067/0015 aceitas. INV-FIN-* declaradas em REGRAS.

## 3. Rastreamento do fluxo — onde nasce o que CR consome (regra #0)

CR cria título a partir de 3 gatilhos primários (PRD §4 / US-CR-001):
`OS.Concluida` · `Certificado.Emitido` (ADR-0043) · contrato recorrente. Os AC exigem
payload com **`cliente_id` + `valor_centavos`**.

| Gatilho esperado (PRD) | Existe hoje? | Carrega `cliente_id`? | Carrega `valor_centavos`? |
|------------------------|--------------|----------------------|---------------------------|
| `OS.Concluida` | parcial — `os.concluida` é **evento interno** da cadeia WORM da OS (`EventoDeOS.tipo`, `src/infrastructure/ordens_servico/models.py:665`), consumido só pela saga de anonimização; **não** é evento de outbox cross-módulo modelado p/ CR | — | **NÃO** — OS não tem preço |
| `Certificado.Emitido` | **NÃO EXISTE** — M8 publica só `Certificados.CertificadoReconciliado` (`acoes_canonicas.py:298`); não há `Certificado.Emitido` | — | **NÃO** — calibração não tem preço |
| `fiscal.nfse_emitida` (secundário, "anexa à fatura" — Wave B) | SIM (frente fiscal recém-fechada, no outbox) | **NÃO** — guarda só `cliente_referencia_hash` pseudônimo (INV-FIS-009; `fiscal/models.py:83`) | tem `valor_centavos`, mas vínculo cliente é hash, não id |

### Achado central
**Nenhum módulo a montante publica hoje um evento de outbox com `cliente_id` + `valor_centavos`.**
O **preço/valor não existe em lugar nenhum do sistema** — ele nasce em `orcamentos`
(módulo `comercial/orcamentos`, PRD **stable**, **greenfield de código**). A própria
frente fiscal já registrou isto: `amount` = input do chamador ("orçamentos diferido —
seam pronto"). OS e calibração/certificado são operação/metrologia, sem preço.

Logo: o **coração** do contas-receber (faturar AUTOMÁTICO a partir de OS/Certificado —
o "por que existe": *"sem este módulo o cert vira trabalho de graça"*) está **bloqueado
na precificação**. Sem `orcamentos`, CR só faz cobrança MANUAL (financeiro digita o valor).

## 4. Consequência para a ordem de dependência (anti-retrabalho)

`orcamentos` é a **peça compartilhada a montante**: produz preço/itens que alimentam
título (CR), `amount` da NFS-e (fiscal — hoje stub), e base de comissão. Construído 1x,
destrava 3+ consumidores. Pela regra permanente "seguir a ordem por dependência +
diferir o que depende de inexistente", a precificação deveria preceder o consumidor.

## 5. Recorte possível de CR SEM orçamentos (se construído antes)

- **Construível:** domínio `Titulo`/`Fatura`/`Pagamento`/`Parcela` + máquina de estados +
  juros/multa-na-leitura (INV-026) + categoria_receita perfil-aware (INV-FIN-PERFIL-001) +
  WORM/RLS + **cobrança MANUAL** (financeiro digita valor) + porta `PaymentGatewayProvider`
  com **Mock** (boleto/PIX/webhook fake, molde fiscal) + job inadimplência dura perfil-aware
  (ADR-0043 grace 45/20/30/7) + override A3 + consumer desbloqueio (`ContasReceber.Pago` →
  `Cliente.Desbloqueado`, GATE-CLI-6).
- **Inerte até orçamentos:** consumers `criar_titulo_a_partir_de_os/certificado` (sem valor
  de origem) — wiráveis "seam pronto / fail-open lazy", mas sem valor real.
- **GATE pré-produção (molde fiscal):** adapter Asaas real + webhook HMAC real + B2.

## 6. Fork de sequenciamento (decisão de produto — Roldão)

1. **`orcamentos` primeiro** (recomendado) — destrava preço p/ CR + fiscal(`amount`) +
   comissões; depois CR fatura ponta-a-ponta de verdade. Dependency-first puro.
2. **CR núcleo agora** (manual + mock gateway + inadimplência) — entrega container de
   cobrança/dogfooding já, com auto-faturamento inerte até orçamentos (padrão fiscal).
3. **Outra frente** (app-técnico / operacional ADR-0051 / etc.).

Investigação por workflow de 1 leitor "very thorough" + rastreio direto do código
(acoes_canonicas, ordens_servico, fiscal/models). Sem alteração de código nesta etapa.

---

## 7. ATUALIZAÇÃO 2026-06-15 — re-rastreamento pós-`orcamentos` (regra #0, antes do P1)

> `orcamentos` FECHOU 100% Wave A em 2026-06-15 (commits b002dae/cf12bc8/24404ca/4f8b326).
> A §6 desta investigação dava 3 forks de sequenciamento; o fork #1 ("orçamentos primeiro")
> foi o adotado e está cumprido. Antes de escrever a spec, re-rastreei o CÓDIGO REAL de hoje
> (não as docs) para ver se o bloqueio de §3 mudou. Mudou **em parte** — abaixo.

### O que mudou desde 2026-06-09

| Gatilho | É outbox cross-módulo? | `cliente_id`? | `valor`? | Fonte (arquivo:linha) |
|---|---|---|---|---|
| `os.concluida` | **SIM** (bus via INT-01) | **NÃO** (payload = `os_id`, `tipo_predominante`, `nao_conformidade_global`) | **NÃO no evento** (mas `OSSnapshot.valor_total` AGORA existe no banco — vindo do orçamento, ADR-0082) | `value_objects.py:143`; `concluir_atividade.py:219-225`; `repositories.py:660-666`/`85-86` |
| `Certificados.CertificadoReconciliado` | **NÃO** (`outbox=False` — só cadeia hash interna) | **NÃO** | **NÃO** (certificado não tem preço) | `acoes_canonicas.py:296-300`; `certificados/views.py:161-166` |
| `fiscal.nfse_emitida` | **SIM** | **NÃO** — só `cliente_referencia_hash` (pseudônimo INV-FIS-009) | **SIM** — `valor_centavos` (int) | `fiscal/views.py:268-281`; `acoes_canonicas.py:321-326` |
| `orcamento.aprovado` (**NOVO** — não existia em jun/09) | **SIM** | **SIM** — `cliente_id` (pode ser `None` se anonimizado) | **SIM** — `valor_total` (string decimal `"1234.56"`, não centavos) | `transicoes.py:293-318`; `acoes_canonicas.py:426-437` |

### Achado central (atualizado)

1. **`Certificado.Emitido` continua INEXISTENTE.** O PRD (US-CR-001 AC-2) e a ADR-0043 / INV-CAL-FIN-001
   mandam CR reagir a `Certificado.Emitido` com `Certificado.valor_servico_snapshot`. No código: (a) o evento
   não existe (certificados publica só `CertificadoReconciliado`, `outbox=False`, reservando `CertificadoEmitido`
   para a assinatura A3 — Wave A futura); (b) o certificado **não tem campo de valor**; (c) não tem cliente.
   → **Conflito de fonte de verdade ADR-0043 × código.** Resolver no P2 (tech-lead) + ADR de reconciliação no P8
   (molde ADR-0083 de orçamentos). Faturar certificado E a OS que o gerou = **dupla cobrança** — a evitar.

2. **A OS é o único gatilho que JÁ tem cliente + valor carimbados** (`OSSnapshot.cliente_id` + `valor_total`
   via ADR-0082; por atividade: `AtividadeSnapshot.valor_unitario_snapshot`). **Mas não os publica** — o payload
   de `os.concluida` é minimalista e o sanitizador `sanitizar_payload_evento_os` proíbe `cliente_id` raw
   (`event_helpers.py:44-46`). Enriquecer o evento da OS (seguindo o padrão do orçamento, que já publica
   `cliente_id`+`cliente_referencia_hash`+`cliente_key_id`) é o caminho mais alinhado a "fatura pelo valor JÁ
   carimbado" + INV-026. **Toca módulo fechado (OS)** — decidir no P2.

3. **`fiscal.nfse_emitida` tem o valor mas não o `cliente_id`** (só hash). INV-FIS-CR-001 espera esse gatilho
   (`Fiscal.NFSeEmitida → ContasReceber.TituloEmitido ≤5s`). Viável se CR resolver `cliente_referencia_hash→id`
   internamente, OU se a NF-e carregar a referência PII anonimizável completa (hash+key_id+id) como o orçamento.

4. **Núcleo SEM auto-faturamento continua 100% construível agora** (T-CR-000 §5): domínio
   `Fatura`/`Titulo`/`Parcela`/`Pagamento` + máquina de estados + juros/multa-na-leitura + categoria perfil-aware
   + WORM/RLS + cobrança MANUAL + porta `PaymentGatewayProvider` com **Mock** (molde fiscal) + webhook baixa
   (HMAC+idempotência) + job inadimplência dura perfil-aware (grace 45/20/30/7) + override A3 + consumer
   desbloqueio (`ContasReceber.Pago → Cliente.Desbloqueado`, GATE-CLI-6).

### Decisão de gatilho LEVADA AO P2 (não decidida aqui)

A spec v1 propõe: **gatilho canônico de auto-faturamento = `os.concluida` enriquecido** (cliente+valor que a OS
já tem), porque (a) evita dupla cobrança certificado×OS, (b) respeita "fatura pelo valor carimbado"+INV-026,
(c) a calibração já nasce dentro de uma OS. `fiscal.nfse_emitida` vira gatilho secundário (anexa NF à fatura,
INV-FIS-CR-001). `Certificado.Emitido` é **reconciliado** (ADR no P8) — certificado não é unidade de cobrança
independente. Validação final = `tech-lead-saas-regulado` no P2.
