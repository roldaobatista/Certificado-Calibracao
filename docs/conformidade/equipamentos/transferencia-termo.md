---
owner: claude-code
revisado-em: 2026-05-22
status: stable
escopo: módulo equipamentos — texto canônico do termo de transferência (US-EQP-004 AC-EQP-004-5 / P-EQP-A1)
relacionados:
  - REGRAS-INEGOCIAVEIS.md (INV-050)
  - docs/faseamento/M2-equipamentos/spec.md (US-EQP-004)
  - docs/faseamento/M2-equipamentos/plan.md (P-EQP-A1)
versao_canonica: v1.1-2026-05-22
fundamento_legal: LGPD art. 18 + Lei 14.063/2020 art. 4º + LGPD art. 5º VI/VII + CC art. 421
---

# Termo de transferência de equipamento — texto canônico v1.1

> **Pra quê:** quando o cessionário aceita receber o equipamento, o
> termo exibido (UI ou PDF) é **igual sempre** — não é gerado por LLM,
> não tem variação por tenant. Isso permite que advogado-saas-regulado
> credite o texto + auditor RBC valide a cláusula de confidencialidade
> + cessionário tenha rastreabilidade da versão que aceitou.
>
> **Origem:** parecer `advogado-saas-regulado` (P-EQP-A1) + revisão
> auditoria PRD `equipamentos` Wave A Marco 2 (2026-05-21).
> **v1.1 vs v1.0:** v1.1 acrescenta cláusula 4 (titularidade do dado
> pessoal do cedente NÃO é cedida ao cessionário — LGPD art. 5º VI/VII).
>
> **Atualização desta lista:** mudança de texto exige PR revisado pelo
> `advogado-saas-regulado` + bump de `versao_canonica` no frontmatter
> + bump da constante Python `TEXTO_TERMO_TRANSFERENCIA_VERSAO_CANONICA`.

---

## Por que texto canônico (não geração livre)

LGPD art. 18 exige que o titular saiba **quem** trata dados pessoais
seus. Quando um equipamento muda de cliente cedente para cliente
cessionário, dois titulares de dados estão envolvidos (cedente +
cessionário) — o termo precisa explicitar direitos de cada um e o que
NÃO é transferido.

ISO/IEC 17025 cl. 4.2 (confidencialidade) reforça que histórico
metrológico não migra automaticamente — exige consentimento expresso
do cedente. Variação de texto entre tenants quebra a rastreabilidade
documental.

Cravado em [AC-EQP-004-5](../../faseamento/M2-equipamentos/spec.md) e
expandido em [P-EQP-A1](../../faseamento/M2-equipamentos/plan.md).

---

## Cláusula 1 — Direitos LGPD do cedente (LGPD art. 18)

```
O cedente preserva todos os direitos previstos no art. 18 da LGPD
sobre seus dados pessoais já tratados pelo laboratório responsável,
inclusive: confirmação de tratamento, acesso, correção, anonimização,
eliminação, portabilidade e informação sobre uso compartilhado. A
transferência deste equipamento não revoga, suspende nem limita tais
direitos. Contato do Encarregado de Dados (DPO) consta no Portal LGPD
do laboratório.
```

## Cláusula 2 — Natureza da assinatura (Lei 14.063/2020 art. 4º)

```
A assinatura registrada neste termo enquadra-se em uma das modalidades
da Lei 14.063/2020 (art. 4º). Quando o aceite é coletado
presencialmente pelo atendente do laboratório (modalidade fraca), o
atendente declara expressamente, sob as cominações dos arts. 299
(falsidade ideológica) e 171 (estelionato) do Código Penal e do art.
482 alínea "a" da CLT (justa causa por ato de improbidade), que
apresentou este termo ao titular e obteve seu consentimento verbal
informado, registrando hora, local e identificação do interlocutor.
```

## Cláusula 3 — Não-cessão de garantia ou contrato de serviço

```
A transferência altera EXCLUSIVAMENTE a titularidade cadastral do
equipamento para fins de identificação do cliente atual. Não transfere
ao cessionário: (a) garantias do fabricante; (b) contratos de prestação
de serviço entre o cedente e o laboratório (calibração, manutenção,
inspeção); (c) certificados emitidos sob titularidade do cedente, que
permanecem associados à versão histórica do equipamento conforme ISO/IEC
17025 cl. 8.4. O cessionário deve celebrar novo contrato de serviço com
o laboratório, se assim desejar, antes da próxima calibração.
```

## Cláusula 4 — Titularidade do dado pessoal NÃO é cedida (LGPD art. 5º VI/VII)

```
O cedente NÃO transfere ao cessionário, neste ato, a titularidade dos
dados pessoais coletados pelo laboratório durante o relacionamento
anterior. Dados sensíveis (LGPD art. 5º II), de identificação (art. 5º
VI) e cadastrais (art. 5º VII) do cedente permanecem sob sua
titularidade — o cessionário NÃO ganha direitos sobre tais dados pelo
simples fato de receber o equipamento. O acesso a histórico
metrológico (certificados anteriores, OS, eventos) do cedente pelo
cessionário depende de CONSENTIMENTO EXPRESSO do cedente registrado
neste mesmo termo (campo `consentimento_historico_expresso`). Na
ausência de consentimento, o cessionário verá APENAS os dados gerados
a partir da efetivação desta transferência.
```

---

## Como o sistema usa este texto

O helper Python
`src/infrastructure/equipamentos/validators.texto_termo_transferencia(versao)`
retorna o texto completo (4 cláusulas concatenadas) para a versão
canônica solicitada. O modelo `TransferenciaEquipamentoAceite` grava
`texto_termo_versao_id` apontando para a versão exibida ao
cessionário no momento do aceite — esse ID é evidência de rastreabilidade
em auditoria CGCRE.

UI (Wave A) renderiza as 4 cláusulas em sequência + campo de aceite +
checkbox `consentimento_historico_expresso`. Termo PDF gerado no fim
da transferência (Wave A) inclui as cláusulas + hash SHA-256 do texto
+ hora UTC + IP_hash de origem do aceite.

---

## Versão atual

`v1.1-2026-05-22` — diff vs v1.0:
- ➕ Cláusula 4 (titularidade do dado pessoal NÃO é cedida).
- Texto v1.0 mantido em histórico para transferências antigas
  (efetivadas antes de 2026-05-22) que continuam apontando para
  `v1.0-2026-05-22` no campo `texto_termo_versao_id`.
