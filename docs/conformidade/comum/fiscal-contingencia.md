---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Contingência fiscal — quando SEFAZ/município cai

> **Pra quê:** SEFAZ/município indisponível = NF-e não emite = tenant trava. Sem playbook, Roldão "descobre na hora" que precisa fazer algo. Documentado em separado do `fiscal.md` (Auditor 4+5 da 2ª auditoria).

---

## 1. Cenários

| Cenário | Frequência | Duração típica |
|---------|-----------|------------------|
| SEFAZ estadual fora (NF-e) | mensal | 1-4h |
| Município fora (NFS-e) | semanal pra alguns | minutos a horas |
| Cutover de padrão (NFS-e 09/2026) | uma vez | 1-3 dias instabilidade |
| Sistema do BaaS (PlugNotas/Focus) fora | raro | minutos a 1h |
| Conexão Aferê → BaaS fora | raro | minutos |

---

## 2. Modos de contingência

### NFe estadual
- **SVC-AN** (Sefaz Virtual de Contingência — Ambiente Nacional)
- **SVC-RS** (Sefaz Virtual de Contingência — Rio Grande do Sul, backup do nacional)
- **EPEC** (Evento Prévio de Emissão em Contingência) — válido por 168h, regulariza depois

Aferê delega pra BaaS:
- PlugNotas/Focus detectam SEFAZ down + ativam SVC automaticamente
- Aferê expõe estado "operando em contingência" na UI
- Tenant continua emitindo; XML regulariza quando SEFAZ volta

### NFS-e municipal
- Municípios têm contingência própria (varia)
- Alguns mantêm fila offline
- Outros não — emissão bloqueada até voltar

Aferê delega; expõe estado.

### Cutover NFS-e nacional 09/2026
Plano especial — 1-3 dias instabilidade esperada:
- Smoke test em sandbox 30 dias antes
- Comunicado a tenants 15 dias antes
- Modo "draft postergado" — Aferê aceita rascunho, emite quando estável
- Suporte estendido durante semana de cutover
- Postmortem completo após estabilizar

---

## 3. CC-e (Carta de Correção eletrônica)

Quando NFS-e emitida tem erro **corrigível** (não muda valor, não muda CPF/CNPJ):
- Tenant emite CC-e via Aferê
- Aferê passa pro BaaS
- Mantém histórico (NFS-e original + CC-e em WORM)

Limite: alguns municípios restringem o que CC-e corrige (variações em formato, descrição).

---

## 4. Cancelamento

| Cenário | Permitido |
|---------|-----------|
| < 24h após emissão | Sim — cancelamento padrão |
| > 24h e < N dias (variável por município) | Cancelamento extemporâneo (sujeito a multa do município) |
| > N dias | Só via processo administrativo manual |

Aferê implementa cancelamento padrão. Casos extremos: comunicar tenant + sugerir suporte do município.

---

## 5. Inutilização de numeração

Quando tenant pula numeração (e.g., NF-e 100 emitida, 101 falhou, 102 emitida — 101 fica "buraco"):
- Inutilização de 101 em até 30 dias do mês seguinte
- Aferê expõe na UI "numeração X-Y pendente de inutilização"
- Auditor de Segurança alerta se passa do prazo

---

## 6. Auditoria de contingência

Auditor de Segurança em pre-commit verifica:
- Diff que adiciona emissão sem fallback de contingência → CONCERN
- Diff que remove modo contingência → FAIL

Drill anual (V2): simular SEFAZ fora; verificar que tenant continua emitindo via SVC.

---

## 7. Pendências

- [ ] Implementar UI de estado "contingência ativa" (Wave A)
- [ ] Painel pra tenant ver NF-e em SVC + regularização pendente
- [ ] Smoke test cutover NFS-e 09/2026 (30 dias antes)
- [ ] Calendário de inutilização automática
- [ ] Drill anual (V2)

---

## 8. Referências

- `fiscal.md`
- ADR-0008 (fiscal pluggable)
- `comum/integracoes-externas/plugnotas.md`
- `comum/integracoes-externas/focus-nfe.md`
- `operacao/acionamento-agente.md` (alerta quando SEFAZ caiu)
