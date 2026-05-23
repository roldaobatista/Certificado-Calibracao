---
owner: roldao
revisado-em: 2026-05-22
proximo-review: 2026-08-22
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/faseamento/F-A/tasks-saneamento.md
  - docs/conformidade/comum/isolamento-multi-tenant.md
  - docs/adr/0001-stack.md
  - REGRAS-INEGOCIAVEIS.md
---

# Carimbo do tempo a partir de fonte NTP confiável

> **Para o dono (resumo em 5 linhas):**
> - O servidor que registra "quando aconteceu" cada coisa precisa estar com o relógio certo, vindo de uma fonte oficial pela Internet — não do clock do próprio computador.
> - Se o relógio do servidor estiver atrasado/adiantado, a trilha de auditoria fica com horários errados e auditor LGPD/ISO 17025 desqualifica a prova.
> - Solução: todo `agora()` no audit passa por um wrapper que pergunta a um servidor NTP oficial antes de devolver o horário.
> - Se o NTP cair, o wrapper devolve o horário local **e grava um alerta** — assim sabemos que aquele bloco de auditoria foi feito com clock "menos confiável".
> - É gate `GATE-3` (vem antes do 1º cliente externo pago).

---

## 1. Problema

ISO 17025 cl. 7.4 e LGPD art. 37 exigem que a trilha de auditoria tenha carimbo de tempo confiável. "Confiável" significa:

1. **Não vem do clock local** (que pode ser arrastado por NTP mal configurado ou ataque).
2. **Tem fonte externa autoritativa** (servidor NTP público + carimbo do tempo ITI quando o documento é fiscal/regulatório).
3. **Deriva ≤ 250ms** vs fonte autoritativa — senão o evento é "inelegível como prova".

Hoje (F-A) o audit usa `datetime.now(UTC)` direto. Funciona em desenvolvimento, mas falha em auditoria séria (ANPD em incidente + CGCRE em supervisão laboratório).

---

## 2. Decisão

Toda chamada de `datetime.now(UTC)` em **escrita** de audit trail (cadeia + outbox + AcessoDadosCliente + AuthorizationDecision) passa por wrapper `agora_ntp_confiavel()` (módulo a criar em `src/infrastructure/seguranca/clock_ntp.py`).

### 2.1 Comportamento do wrapper

```python
def agora_ntp_confiavel() -> datetime:
    """Retorna datetime UTC-aware vindo de fonte NTP autoritativa.

    Fallback: clock local + alerta P2 em audit_trail.eventos.
    """
```

Passos:

1. Consulta servidor NTP **primário** (`pool.ntp.org` — região SA).
2. Se primário falha em ≤500ms → tenta **secundário** (`a.ntp.br`, NIC.br).
3. Se secundário também falha em ≤500ms → retorna `datetime.now(UTC)` local **e** publica evento `clock.fallback_local` em `audit_trail.eventos` (action canônica a registrar) com severidade `P2`.
4. Diferença NTP - local > 250ms → log estruturado em `axiom` com severidade `WARN` (mas devolve o NTP).

### 2.2 Não aplica em

- Logs de aplicação genéricos (Axiom retém precisão de ~1s; não é prova).
- Telemetria + métricas Grafana.
- Testes (fixture `frozen_clock` continua valendo).

### 2.3 Carimbo do tempo ITI (separado do NTP)

NTP **não substitui** carimbo do tempo ITI (MP 2.200-2/2001 art. 10) exigido em certificados de calibração assinados ICP-Brasil. NTP entra no audit trail; ITI entra no PDF do certificado. Os dois caminhos são independentes.

---

## 3. Hook + invariante

- Adicionar `INV-CLOCK-001` em `REGRAS-INEGOCIAVEIS.md`: "Toda escrita em `audit_trail.*` usa `agora_ntp_confiavel()`; uso direto de `datetime.now()` em escrita de audit é violação."
- Hook `clock-ntp-check.sh` (a criar Wave A) bloqueia commit que adicione `datetime.now()` em arquivo dentro de `src/infrastructure/audit/` ou `src/infrastructure/multitenant/`. Allowlist: `src/infrastructure/seguranca/clock_ntp.py` (única exceção).

---

## 4. Testes

Obrigatórios (Wave A):

1. **Happy path:** NTP retorna timestamp; wrapper devolve esse timestamp.
2. **Unhappy primário:** primário timeout; secundário responde; wrapper devolve secundário.
3. **Unhappy total:** ambos falham; wrapper devolve `datetime.now(UTC)` + verifica que evento `clock.fallback_local` foi publicado.
4. **Deriva:** simular deriva 500ms entre local e NTP; wrapper devolve NTP + log WARN.

---

## 5. Non-goals

- **Não vamos** rodar servidor NTP próprio em MVP-1 (custo operacional).
- **Não vamos** integrar com PTP / `chronyd` no nível de sistema (depende da Hostinger — fora de escopo de aplicação).
- **Não vamos** rejeitar requisição quando NTP cai — degrada graciosamente com alerta.

---

## 6. Cronograma

- **Onda 2 (2026-05-22):** este PRD criado.
- **Wave A (próxima):** implementar wrapper + teste + hook + invariante + retrofit em `src/infrastructure/audit/services.py`.
- **GATE-3 fechado:** quando wrapper estiver em produção + 1ª evidência de execução real (log de uma requisição mostrando NTP timestamp aplicado).

---

## 7. Referências

- ISO 17025 cl. 7.4 — controle de itens de calibração (carimbo do tempo)
- LGPD art. 37 — registro das operações
- MP 2.200-2/2001 art. 10 — ICP-Brasil / ITI
- ABNT NBR ISO/IEC 27037 — preservação de evidência digital
- `docs/faseamento/F-A/tasks-saneamento.md` — T-FA-S-02
