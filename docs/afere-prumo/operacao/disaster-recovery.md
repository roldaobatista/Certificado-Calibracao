---
owner: <responsavel-DR>
ultima-conferencia: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 150
proposito: plano de recuperacao de desastre com RTO, RPO e passo-a-passo de retorno
---

<!-- proposito: plano de recuperacao de desastre (o que fazer quando o servico cai feio: perda de servidor, regiao, ransomware) | renomear-para: docs/operacao/disaster-recovery.md -->

# Plano de Disaster Recovery — <nome-do-projeto>

> **Disaster Recovery (DR)** = "recuperação de desastre". Plano para reerguer o serviço quando algo grande quebra: servidor inteiro caiu, região da nuvem ficou offline, ataque de ransomware criptografou os dados, alguém apagou tabela em produção por engano.
>
> Este plano define **quanto tempo aceitamos ficar fora** (RTO), **quanto dado aceitamos perder** (RPO), e o **passo-a-passo** para voltar.

## 1. Cenários cobertos

| ID | Cenário | Probabilidade | Impacto |
|---|---|---|---|
| DR-1 | Perda do servidor principal (instância caiu, disco corrompeu) | média | alto |
| DR-2 | Perda da região inteira do provedor de nuvem | baixa | crítico |
| DR-3 | Ransomware (dados criptografados por atacante) | baixa | crítico |
| DR-4 | Erro humano (DROP TABLE acidental, deploy errado em prod) | média | alto |
| DR-5 | Vazamento de dados / acesso indevido confirmado | baixa | crítico |

<!-- exemplo ilustrativo, substituir antes de usar -->
Exemplo: DR-1 cobre falha do banco primário `<nome-da-instancia>` na região `<regiao-do-provedor>`.

## 2. RTO — Recovery Time Objective

> **RTO** = "objetivo de tempo de recuperação". Tempo MÁXIMO aceitável entre o desastre e o serviço voltar a funcionar.

| Cenário | RTO definido | Justificativa |
|---|---|---|
| DR-1 (perda de servidor) | 1 hora | failover automático para réplica |
| DR-2 (perda de região) | 4 horas | promover réplica cross-region |
| DR-3 (ransomware) | 8 horas | restaurar de backup limpo offsite |
| DR-4 (erro humano) | 2 horas | point-in-time-recovery do banco |
| DR-5 (vazamento) | imediato (isolar) + 24h (análise) | conter primeiro, depois apurar |

## 3. RPO — Recovery Point Objective

> **RPO** = "objetivo de ponto de recuperação". Quantidade MÁXIMA de dados que aceitamos perder, medida em tempo (ex: "no máximo 15 min de transações").

| Cenário | RPO definido | Como atingimos |
|---|---|---|
| DR-1 | 5 minutos | replicação síncrona da réplica local |
| DR-2 | 15 minutos | replicação assíncrona cross-region |
| DR-3 | 24 horas | último backup diário offsite limpo |
| DR-4 | 5 minutos | WAL contínuo permite PITR (point-in-time-recovery) |

## 4. Procedimento de ativação

1. **Quem decide acionar DR:** tech lead OU plantonista de sobreaviso se não alcançar tech lead em 10min.
2. **Como aciona:** mensagem em `#war-room` com tag `@dr-team` + paging dos contatos da §8 do `on-call.md`.
3. **Confirmação:** abrir incidente em `<sistema-de-incidentes>` com severidade SEV1.
4. **Comunicação interna:** atualização a cada 30min em `#war-room` até resolução.
5. **Comunicação externa:** ver §6.

## 5. Passos por cenário

### DR-1 — Perda do servidor principal
1. Confirmar que o servidor primário não responde (3 tentativas, intervalos de 30s).
2. Promover réplica para primário: runbook `docs/operacao/runbooks/failover-banco.md` (instanciar via `runbook.template.md`).
3. Atualizar DNS / connection string da aplicação.
4. Validar com queries de sanidade (ver runbook).

### DR-2 — Perda de região
1. Promover réplica cross-region em `<regiao-secundaria>`.
2. Trocar entrada DNS principal para apontar para a região secundária.
3. Avisar cliente sobre latência maior (região mais distante).
4. Runbook: `docs/operacao/runbooks/failover-regiao.md` (instanciar via `runbook.template.md`).

### DR-3 — Ransomware
1. Isolar imediatamente: cortar acesso de rede do ambiente comprometido.
2. NÃO pagar resgate (política da empresa).
3. Restaurar a partir do backup offsite mais recente conhecidamente limpo.
4. Acionar resposta a incidente: `docs/seguranca/resposta-incidente.md`.
5. Comunicar ANPD se houver dado pessoal afetado (prazo: 72 horas, LGPD Art. 48).

### DR-4 — Erro humano
1. Pausar deploys imediatamente.
2. Identificar timestamp exato do erro (logs, audit trail).
3. Point-in-time-recovery para timestamp imediatamente anterior.
4. Runbook: `docs/operacao/runbooks/pitr-banco.md` (instanciar via `runbook.template.md`).

### DR-5 — Vazamento confirmado
1. Conter (rotacionar credenciais expostas, revogar tokens).
2. Preservar evidências (snapshot de logs).
3. Acionar DPO e jurídico.
4. Comunicar ANPD + titulares afetados (prazo: 72 horas, LGPD Art. 48).

## 6. Comunicação ao cliente

- **Canal:** status page pública em `<status.exemplo.com>` + e-mail para contatos cadastrados.
- **Antecedência:** primeira atualização em até 30min após confirmação do incidente.
- **Mensagem padrão inicial:**
  > "Estamos investigando uma indisponibilidade em <serviço>. Equipe acionada. Próxima atualização em 30 minutos."
- **Mensagem padrão de resolução:**
  > "Serviço restabelecido às <HH:MM>. Causa: <resumo de 1 linha>. Post-mortem completo em até 5 dias úteis."

## 7. Teste de DR

> Plano de DR que nunca foi testado não é plano, é ficção.

- **Frequência mínima:** trimestral.
- **Tipos:**
  - **Tabletop** (mesa-redonda, sem mexer no sistema): trimestral. Equipe discute cenário hipotético e revisa o plano.
  - **Simulado** (executa em ambiente de staging): semestral.
  - **Real** (em produção, com janela agendada): anual.
- **Aceite:** RTO e RPO observados <= RTO e RPO definidos.
- **Registro:** post-mortem do teste em `docs/operacao/testes-dr/2026-05-28.md`.

## 8. Pós-DR — post-mortem obrigatório

Após qualquer ativação real OU teste:
1. Post-mortem em até 5 dias úteis (template `templates/post-mortem.template.md`).
2. Revisão deste plano (precisa ajustar RTO/RPO? cenário novo descoberto?).
3. Ações de melhoria com owner e prazo.
4. Compartilhamento interno do aprendizado.

## 9. Histórico de revisões

| Data | Revisor | Mudança |
|---|---|---|
| 2026-05-28 | <nome> | criação inicial |
