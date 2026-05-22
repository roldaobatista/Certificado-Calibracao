---
owner: claude-code
revisado-em: 2026-05-23
status: stable
escopo: módulo equipamentos — texto canônico do template de notificação de sucatamento + texto do modal de confirmação dupla (US-EQP-005 AC-EQP-005-2 + 4 / P-EQP-A5 / P-EQP-S9 / P-EQP-R8)
relacionados:
  - docs/faseamento/M2-equipamentos/spec.md (US-EQP-005)
  - docs/faseamento/M2-equipamentos/plan.md (P-EQP-A5 + P-EQP-R8 + P-EQP-S9)
  - REGRAS-INEGOCIAVEIS.md (INV-INT-002)
versao_canonica: v1.0-2026-05-23
fundamento_legal: ISO/IEC 17025 §7.1.1 + LGPD art. 5º IX (boa-fé) + CDC art. 6º III (informação adequada) + RBC NIT-DICLA-021
---

# Template de notificação de sucatamento + modal de confirmação dupla v1.0

> **Pra quê:** quando o laboratório sucata um equipamento que tinha
> certificado vigente, é decisão **operacional/comercial** — não
> regulatória. O certificado emitido **permanece tecnicamente válido**
> (ISO/IEC 17025 §7.1.1 — o certificado atesta o estado metrológico
> no momento da calibração, não a propriedade física do equipamento).
> Cliente precisa saber disso de forma clara, sem manipulação comercial
> (LGPD art. 5º IX — boa-fé + CDC art. 6º III — informação adequada).
>
> Este documento define DOIS textos canônicos imutáveis:
> 1. **Modal de confirmação dupla** (exibido na UI antes do sucatamento
>    com cert vigente — P-EQP-R8 / AC-EQP-005-5).
> 2. **Template de notificação ao cliente** (e-mail/portal — depende
>    do `comunicacao-omnichannel` Wave A; em Marco 2 fica como
>    `NotificacaoClienteService` stub).
>
> Mudar texto exige PR + bump `versao_canonica` no frontmatter +
> revisão `advogado-saas-regulado` + auditor RBC.

---

## 1) Modal de confirmação dupla (P-EQP-S9 — exibido ANTES de sucatear com cert vigente)

```
Você está prestes a marcar este equipamento como SUCATA, mas existe
certificado de calibração vigente associado a ele.

IMPORTANTE — antes de confirmar, leia:

1. O certificado emitido permanece TECNICAMENTE VÁLIDO conforme
   ISO/IEC 17025 §7.1.1. O certificado atesta o estado metrológico do
   equipamento no momento da calibração — NÃO atesta a propriedade
   física, posse ou continuidade de uso do equipamento.

2. Sucatamento é uma decisão OPERACIONAL/COMERCIAL do laboratório ou
   do cliente — separada e independente da emissão do certificado.

3. O cliente proprietário será notificado deste sucatamento via canal
   oficial. A notificação NÃO contém oferta comercial (recompra,
   desconto em recalibração ou outro CTA) — LGPD art. 5º IX (boa-fé)
   + CDC art. 6º III (informação adequada e clara) vedam manipulação
   emocional do titular.

4. Sucatamento é um estado TERMINAL. Após confirmar, o equipamento
   só poderá transitar para "extraviado" caso seja reportado como
   sumido fisicamente. Não há volta para "ativo" sem registro de
   nova rastreabilidade (NIT-DICLA-021).

[ ] Tenho ciência de que o certificado emitido permanece
    tecnicamente válido (ISO/IEC 17025 §7.1.1).

[ ] Confirmo o sucatamento sob minha responsabilidade técnica.

Para prosseguir, marque AMBAS as caixas acima e clique em "Confirmar
sucatamento".
```

**Constantes referenciadas no código:** `TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA`,
`TEXTO_MODAL_SUCATAMENTO_CERT_VIGENTE` em `equipamentos/validators.py`.

---

## 2) Template de notificação ao cliente proprietário (AC-EQP-005-4 — após sucatamento)

> **Marco 2 status:** stub — `NotificacaoClienteService` apenas
> registra o disparo no `bus_outbox`. Consumer real depende de
> `comunicacao-omnichannel` Wave A.

```
Assunto: Sucatamento registrado — equipamento {tag} (TAG opaca, sem
PII)

Prezado(a) cliente,

Comunicamos que o equipamento identificado pela TAG operacional
"{tag}" foi marcado como SUCATA em nosso sistema, na data
{sucateado_em} ({fuso}).

Sobre o certificado de calibração:

Caso houvesse certificado de calibração vigente associado a este
equipamento no momento do sucatamento, o referido certificado
PERMANECE TECNICAMENTE VÁLIDO conforme ISO/IEC 17025 §7.1.1. O
certificado atesta o estado metrológico do equipamento no momento
da calibração — não atesta a propriedade física, posse ou
continuidade de uso.

O sucatamento foi uma decisão OPERACIONAL do laboratório ou do
próprio cliente, e é INDEPENDENTE da validade técnica do
certificado. O documento original do certificado continua válido
para fins de auditoria, rastreabilidade metrológica e
comprovação histórica até a data de vencimento original.

Esta notificação tem caráter exclusivamente INFORMATIVO. Não
contém oferta comercial (recompra, desconto em recalibração,
contratação de novo serviço ou qualquer outro CTA), em
observância à LGPD art. 5º IX (princípio da boa-fé) e ao CDC
art. 6º III (direito à informação adequada e clara).

Em caso de dúvida sobre validade técnica do certificado,
procedimentos de descarte ambientalmente adequado ou outros
aspectos regulatórios, entre em contato com o Encarregado de
Dados (DPO) ou com o Responsável Técnico do laboratório pelos
canais oficiais.

Atenciosamente,
{laboratorio_nome_fantasia}
```

**Constantes referenciadas no código:** `TEMPLATE_NOTIFICACAO_SUCATAMENTO_VERSAO_CANONICA`,
`TEMPLATE_NOTIFICACAO_SUCATAMENTO` em `equipamentos/validators.py` (Wave A — Marco 2
expõe apenas a constante de versão).

---

## 3) Allowlist semântica anti-CTA (AC-EQP-005-4)

O template **NÃO PODE** conter, em qualquer variação ou contexto:

- "Recompra", "compra", "aquisição", "venda" do equipamento.
- "Desconto", "promoção", "oferta", "condição especial" em
  recalibração ou qualquer serviço.
- "Contrate", "adquira", "garanta", "aproveite", "não perca".
- Sugestão de equipamento substituto, marca ou modelo concorrente.
- Mensagem de urgência ou escassez ("últimas vagas", "tempo limitado").
- Link para checkout, cotação ou venda direta de qualquer produto.

Fundamentos: LGPD art. 5º IX (boa-fé) — manipulação emocional do
titular vedada; CDC art. 6º III — informação clara e adequada não
pode estar contaminada por interesse comercial conflituoso.

---

## 4) Versionamento

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| v1.0-2026-05-23 | 2026-05-23 | advogado-saas-regulado | Criação inicial. Modal + template + allowlist anti-CTA. |

Bump exige PR + revisão `advogado-saas-regulado` + alteração da
constante `TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA` em
`validators.py` (anti-drift via teste `tests/test_equipamentos_sucatar_*.py`).
