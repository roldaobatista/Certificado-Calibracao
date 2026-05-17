---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: orcamentos
dominio: comercial
diataxis: explanation
---

# PRD — Módulo Orçamentos

## 1. O que este módulo é

Criação, versionamento, envio digital, aprovação e conversão de **orçamentos comerciais em OS**. Estilo "carrinho" com itens do catálogo, cálculo automático de impostos/comissão e envio via link WhatsApp/e-mail com tracking de leitura.

## 2. Por que existe

JTBD-041 (mandar proposta profissional em < 5 min) + JTBD-020 (não copiar info 3x: chamado → orçamento → OS) + JTBD-075 (vendedor ver impacto do desconto na própria comissão antes de fechar). Custo do status quo: Word + e-mail + impressão + caneta → 30-60 min/orçamento + perda de versão + zero tracking. Gap defensável #8 (CRM + calibração integrados).

## 3. Personas

Ver `../../personas.md` (P-COM-02 Vendedor é a dominante) + P-COM-03 Cliente final (aprova) + P-COM-05 Dono (configura templates + aprovação interna).

## 4. Escopo MVP-1

**Wave A (semanas 1-13):**
- Criação de orçamento (header + itens + descontos + impostos + condições)
- Templates pré-configurados pelo tenant
- Conversão em OS rascunho ao aprovar (OP15.4)
- PDF exportável + link público com aprovação 1-clique

**Wave B (semanas 14-22):**
- Versionamento + comparação V1/V2/V3
- Tracking de leitura (cliente abriu o link)
- Assinatura eletrônica simples (não-ICP — V2 considera ICP-Br)
- Aprovação interna escalada (se desconto > X%, pede aprovação dono)

## 5. Non-goals

- **Assinatura digital ICP-Brasil** (V2)
- **Negociação multi-rodada com tracking de chat** (V2 — só comentário simples no MVP-1)
- **Orçamento sem cliente cadastrado** — cliente deve existir (US-CLI-001 é pré-requisito)
- **Catálogo de serviços/produtos** — pertence ao módulo `suporte-plataforma/catalogo` (este módulo só consome)
- **Pricing dinâmico por margem** — V2
- **Orçamento internacional/multi-moeda** — fora do MVP
- **Geração de NFS-e** — pertence a `financeiro` (após OS concluída)
- **Re-precificação retroativa após aprovação** — INV-026 proíbe

## 6. User Stories

### US-ORC-001: Criar orçamento em < 5 min (JTBD-041)
**Como** vendedor, **quero** abrir tela tipo carrinho, escolher cliente, adicionar serviços do catálogo, **para** mandar proposta antes do cliente esquecer.
- AC-1: GIVEN cliente selecionado WHEN adiciono item do catálogo THEN sistema preenche preço atual + alíquota fiscal + comissão prevista.
- AC-2: GIVEN orçamento pronto WHEN clico "enviar" THEN gera PDF + link público + envia por WhatsApp/e-mail conforme canal preferido do cliente.
- **INV:** INV-026 (preço da emissão é snapshot — não retroage), INV-TENANT-001.

### US-ORC-002: Cliente aprova orçamento em 1 clique (OP15.3)
**Como** cliente final, **quero** abrir link, ver PDF/visualização web, clicar "Aprovar", **para** não ter que imprimir/assinar.
- AC-1: Link público com token expirável (validade do orçamento).
- AC-2: Aprovação registra IP + user-agent + carimbo de tempo + LGPD aceite (RAT-06).
- AC-3: Aprovação dispara evento `Orcamento.Aprovado` → módulo OS cria rascunho.

### US-ORC-003: Versionar e comparar (Wave B)
**Como** vendedor, **quero** revisar orçamento (V2) sem perder V1, **para** mostrar ao cliente o que mudou.
- AC-1: Cada edição após primeiro envio cria nova versão.
- AC-2: Tela de comparação V1 × V2 lado a lado (itens adicionados/removidos/alterados).
- AC-3: Apenas a versão "ativa" pode ser aprovada; demais são histórico.

### US-ORC-004: Ver impacto de desconto na comissão (JTBD-075)
**Como** vendedor, **quero** que ao digitar desconto X% apareça quanto perco de comissão, **para** decidir conscientemente.
- AC-1: Preview em tempo real ao alterar campo desconto.
- AC-2: Bloqueio configurável se desconto > limite definido pelo dono.

### US-ORC-005: Templates por tipo de serviço
**Como** dono, **quero** configurar templates (calibração padrão, manutenção, instalação), **para** vendedor não recriar tudo toda vez.

### US-ORC-006: Tracking de leitura (Wave B)
**Como** vendedor, **quero** ver "cliente abriu o link há 2h, não respondeu", **para** fazer follow-up no momento certo.

## 7. Métricas

Ver `metricas.md`. Resumo: tempo médio criação < 5 min, taxa conversão orçamento → OS > 40%, taxa expirado sem resposta < 20%.

## 8. NFR

- Performance: criação salva p95 < 1s; geração PDF < 3s.
- Disponibilidade: 99.5%.
- LGPD: aprovação digital registra consentimento (RAT-06 WhatsApp).
- Imutabilidade: versão aprovada é snapshot (INV-026).

## 9. Glossário

Ver `glossario.md`.
