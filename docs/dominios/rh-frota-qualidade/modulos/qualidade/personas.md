---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: qualidade
dominio: rh-frota-qualidade
---

# Personas — Qualidade

## Primárias

### P-QUA-01 — Responsável pela qualidade (= P-RFQ-02)
- **Quem é:** Em tenant grande, dedicado; em tenant pequeno, acumula com signatário.
- **Goal:** Registrar NC em < 2 min, acompanhar plano até fechamento, preparar dossiê CGCRE rápido.
- **Frustração hoje:** NC em Excel separado, sem correlação com OS/certificado; auditor pede evidência e não tem; "causa-raiz" registrada em uma frase e some.
- **Cenário típico:** Cliente reclamou que padrão veio com calibração vencida. Abre NC Crítica no instrumento. App bloqueia emissão automaticamente. 5 Porquês → causa: gerente não viu lembrete. Ação: ativar alerta 60/30 dias antes. Revisão eficácia em 90 dias.

### P-QUA-02 — Dono / Gerente (recebe alertas)
- **Goal:** Saber NC abertas que afetam emissão; ver tendência mensal.
- **Frustração hoje:** Dono assina certificado sem saber que instrumento tem NC.

### P-QUA-03 — Andréia CS L1 (Persona 16 + P-RFQ-04)
- **Quem é:** Suporte L1 do tenant que recebe reclamação do cliente final em primeira ligação.
- **Goal:** Registrar reclamação em < 1 min sem precisar entender se "vira NC ou não" (decisão da qualidade).
- **Cenário típico:** Cliente liga: "certificado veio com data errada". Andréia clica "Nova reclamação", anexa OS, classifica gravidade "Alta", botão "Enviar para Qualidade". P-QUA-01 vê na fila e decide.

## Secundárias

### P-QUA-04 — Auditor CGCRE (V2)
- **Goal:** Auditar evidências de NC + plano de ação + eficácia em cl. 7.10, 8.5, 8.6, 8.7.
- **Toque MVP-1:** Read-only completo no histórico.

### P-QUA-05 — Cliente final (NPS)
- **Goal:** Responder 1 pergunta em 10s no WhatsApp/e-mail.
- **Frustração:** Survey de 20 perguntas → ignora.

### P-QUA-06 — Técnico / Signatário
- **Goal:** Saber se instrumento que vai usar tem NC aberta ANTES de calibrar.
- **Cenário:** Vai gerar certificado → app mostra "Atenção: padrão X tem NC Crítica aberta. Bloqueio ativo. Veja NC#NNN".

## Anti-personas

- **Tenant que ignora NC** → INV-012 bloqueia emissão; tenant não tem como contornar a não ser fechando NC.
- **Tenant que fecha NC sem revisão de eficácia** → AC-QUA-03 bloqueia.
- **Tenant que registra "causa-raiz: erro humano"** sem 5 Porquês → AC-QUA-02 bloqueia campo livre vazio em Crítica/Maior.

## Referências

- P-RFQ-02 em `docs/dominios/rh-frota-qualidade/personas.md`
- Persona 16 Andréia CS L1 em `docs/discovery/personas-detalhadas.md`
- INV-012; cl. 7.10, 8.5, 8.7
