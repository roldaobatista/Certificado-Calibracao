---
owner: agente-ia
revisado-em: 2026-06-09
proximo-review: 2026-09-09
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
