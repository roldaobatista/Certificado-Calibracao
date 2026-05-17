# Domínio: [NOME] (TEMPLATE)

> **Como usar este template:**
> 1. Copie a pasta `_TEMPLATE-dominio/` pra `<nome-do-dominio>/` (ex: `comercial/`, `financeiro/`, `metrologia/`).
> 2. Substitua `[NOME]`, `[descrição]`, etc.
> 3. Liste módulos que pertencem ao domínio.
> 4. Adicione entrada no `docs/INDEX.yaml`.

---

## O que é este domínio

[Descrição em 1–2 frases do que o domínio agrupa. Exemplo: "Domínio Comercial agrupa tudo o que tange à relação pré-venda com cliente: captura, prospecção, funil, orçamento e contrato."]

## Por que este domínio existe (limite com outros)

[Explicar fronteiras. O que ENTRA neste domínio? O que NÃO entra (e por quê)? Exemplo: "Comercial cuida até o momento do pedido fechado; execução do pedido (criar OS, agendar técnico) é do domínio Operação."]

## Módulos deste domínio

| Módulo | Status | Pasta |
|---|---|---|
| [Módulo A] | ⏳ a descobrir | `modulos/[modulo-a]/` |
| [Módulo B] | ⏳ a descobrir | `modulos/[modulo-b]/` |

## Personas que tocam este domínio

Ver `personas.md` deste domínio. Personas específicas de cada módulo ficam em `modulos/<modulo>/personas.md`.

## Compliance específico

- LGPD: ver `../../conformidade/comum/lgpd-rat.md`
- Fiscal: ver `../../conformidade/comum/fiscal.md` (se domínio = Financeiro)
- ISO 17025: ver `modulos/calibracao/conformidade-iso-17025.md` (se domínio = Metrologia)
- Conformidade específica do domínio (se houver): listar aqui

## Integrações com outros domínios

Ver `../../comum/integracoes-inter-modulos.md` pra contratos detalhados. Exemplos típicos:
- Comercial → Operação: orçamento aprovado vira OS
- Operação → Financeiro: OS concluída vira faturamento
- Metrologia → Operação: certificado emitido é evidência de OS de calibração

## ADRs específicos do domínio

Listados em `modulos/<modulo>/adr/` quando aplicável.
