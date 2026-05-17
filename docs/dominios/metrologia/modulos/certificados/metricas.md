---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Certificados

> Como saber se este módulo está entregando valor.

> **Convenção canônica de cobertura/completude** (ver `docs/comum/glossario-roldao.md`):
> - **Qualidade de dados inicial** = onboarding (dimensão: dados)
> - **Cobertura documental por equipamento** = base-conhecimento (dimensão: conhecimento)
> - **Conformidade de formato PDF/A** = certificados (dimensão: formato)
>
> Neste módulo usamos `conformidade_formato_pdfa` (% certificados emitidos em PDF/A-1).

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Gaps de numeração | Quantidade de números pulados na sequência por tenant/tipo/ano | 0 | Job diário verifica continuidade | diária |
| Tempo médio emissão→assinatura | Minutos entre criar certificado e ser assinado pelo RT | ≤ 5 min mediana | Diff timestamps | semanal |
| Taxa de entrega e-mail cliente | E-mails entregues (não bounce) ÷ enviados | ≥ 98% | Webhook do provedor SMTP | semanal |
| Taxa de reemissões | % certificados reemitidos no primeiro mês | ≤ 2% | Reemissões ÷ emissões | mensal |
| Adoção do portal pelo cliente | % clientes que baixaram pelo portal nos últimos 90 dias | ≥ 60% | Eventos `Certificados.Baixado` | mensal |
| Verificações via QR Code | Quantidade de acessos à página pública verificadora | crescente | Eventos `Certificados.VerificacaoPublica` | mensal |
| Conformidade de formato PDF/A — canônico, dimensão: formato (antes "Cobertura PDF/A-1") | % certificados emitidos em PDF/A-1 | 100% | Validação no pipeline emissão | semanal |
| Error rate pré-emissão (qualidade) | % certificados que falharam validação automática (gaps de dados, incerteza inconsistente, escopo, padrão vencido) antes da emissão. **Fórmula:** `count(`Certificado.PreEmissao.Bloqueada`) ÷ count(tentativas de emissão)`. | ≤ 5% (5% indica problemas a montante em calibração; >10% = revisar UX do metrologista) | Eventos `Certificado.PreEmissao.Validada` + `.Bloqueada` agrupados por motivo | semanal |
| Reemissão — RCA categorizada (qualidade) | Distribuição das reemissões por categoria-raiz: `[dado-cliente-errado, erro-metrologico, erro-administrativo, recalculo-incerteza, falha-sistema, outro]`. Toda reemissão exige preenchimento obrigatório de `motivo_categoria`. | nenhuma categoria > 40% (sinal de defeito sistêmico); `falha-sistema` ≤ 5% | Tabela `Certificado.Reemissao.motivo_categoria` agregada mensal | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade | 99.9% | 43min |
| Latência geração PDF p95 | < 3s | — |
| Latência assinatura A3 (round-trip) p95 | < 10s | — |
| Latência página pública verificadora p95 | < 500ms | — |
| Taxa de erro emissão | < 0.1% | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001.
- **Axiom (logs):** a definir.

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Gap detectado na sequência | Job diário acha número pulado | RT + admin tenant + watchdog | P0 |
| Falha repetida na assinatura A3 | ≥3 tentativas falhas em 5min | RT + watchdog | P1 |
| Bounce e-mail cliente | E-mail não entregue após 3 tentativas | RT | P2 |
| Latência geração PDF > 10s | p95 acima de threshold | Watchdog | P1 |
| Tentativa de edição em cert emitido | Bloqueado pelo INV-014 | Watchdog (suspeita) | P0 |

---

## Métricas de saúde dos AGENTES

- Tokens por feature deste módulo.
- Taxa de retrabalho em US-CER-NNN.

---

## Como esta lista evolui

- Métrica nova → adicionar + coleta + CHANGELOG.
- Obsoleta → `@deprecated`.
- Mudança de target → ADR.
