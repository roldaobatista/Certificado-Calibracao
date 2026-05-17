---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# SEFAZ / Municípios — NFS-e (via BaaS fiscal)

## Resumo

| Item | Detalhe |
|------|---------|
| Função | Emissão de notas fiscais municipal NFS-e (e eventualmente NFe estadual) |
| Status | ⏳ Wave A — via PlugNotas/Focus, não direto |
| Forma de acesso | Indireto via BaaS (`plugnotas.md`, `focus-nfe.md`) |

---

## Por que indireto

Cada município brasileiro tem padrão próprio de NFS-e:
- ABRASF (padrão nacional, ~70% dos municípios)
- Padrões proprietários: SP, Rio de Janeiro, Belo Horizonte, Curitiba, Salvador, Manaus, Vitória, etc.
- Mudanças de schema sem aviso prévio
- Suspensões temporárias por manutenção
- Padrões "nacional" novo cutover 09/2026 (Dor #10)

Manter integração direta pra todos = ~50-100 implementações específicas + manutenção contínua. Inviável pra Aferê solo + agentes.

**Decisão:** delegar pra BaaS (PlugNotas + Focus como fallback). Aferê foca em valor de produto.

---

## SEFAZ (estadual — NFe)

NFe estadual fora do MVP-1 (calibração tipicamente emite NFS-e municipal, não NFe). Quando entrar (V2):
- Mesmo modelo: via PlugNotas/Focus
- Padrão único nacional (mais simples que NFS-e)

---

## Padrão nacional NFS-e 09/2026 (Dor #10)

Cutover obrigatório:
- Receita Federal liderando padronização (Convênio CONFAZ 95/22)
- Modelo único pra ~5500 municípios brasileiros
- Janela competitiva pra Aferê — muitos players atuais não se atualizam a tempo

PlugNotas + Focus prometem cobertura — Aferê monitora SLA de ambos durante transição.

---

## Contingência fiscal

Quando SEFAZ/município cai:
- Modo contingência ABRASF (SVC-AN, SVC-RS)
- EPEC (Evento Prévio Emissão em Contingência)
- CC-e (Carta de Correção eletrônica)
- Cancelamento < 24h
- Inutilização de numeração

Detalhes em `docs/conformidade/comum/fiscal-contingencia.md` (a criar quando Wave A começar — citado em v6 mas pendente).

---

## Custo total

Tenant paga BaaS direto (não via Aferê). Aferê só gerencia onboarding + interface.

---

## Pendências

- [ ] Criar `fiscal-contingencia.md` (Wave A)
- [ ] Smoke test trimestral incluindo cenário cutover NFS-e
- [ ] Monitorar regulamentação Receita Federal sobre cutover 09/2026

---

## Referências

- `plugnotas.md`
- `focus-nfe.md`
- ADR-0008 (fiscal pluggable)
- `discovery/normas-e-regulacao.md`
- `discovery/sintese-final.md` §1 (Dor #10)
