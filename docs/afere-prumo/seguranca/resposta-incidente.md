---
owner: <SecurityOwner>
revisado-em: 2026-05-28
status: draft
idioma: pt-BR
limite-linhas: 180
proposito: plano de resposta a incidente de segurança — severidade, contenção, comunicação, evidência, pós-incidente e vínculo com LGPD
---

<!--
template: resposta-incidente.template.md
destino: docs/seguranca/resposta-incidente.md
uso: plano central para incidente de segurança. Runbooks específicos podem viver em docs/operacao/runbooks/.
referência: ESTRUTURA-PROJETO-NOVO-DO-ZERO.md §C6 + §C8
revisão obrigatória: 6 meses, após incidente MEDIO+ ou após mudança relevante em infraestrutura/auth/criptografia.
-->

# Plano de Resposta a Incidente — Aferê Prumo

> **Incidente de segurança** = evento que ameaça confidencialidade, integridade ou disponibilidade do sistema ou dos dados. Ex.: credencial vazada, acesso indevido, dado pessoal exposto, ransomware, invasão, alteração não autorizada, indisponibilidade causada por ataque.

## 1. Objetivo

Este plano define como o time identifica, classifica, contém, comunica e aprende com incidentes. Ele não substitui runbooks técnicos; ele coordena a resposta.

## 2. Papéis

| Papel | Responsável | Função |
|---|---|---|
| Incident commander | <nome/cargo> | Coordena resposta e decide prioridade operacional. |
| Security owner | <nome/cargo> | Conduz investigação técnica e contenção. |
| DPO / Encarregado | <nome/cargo> | Avalia dado pessoal, comunicação com titular e ANPD. |
| Comunicação | <nome/cargo> | Mensagens para clientes/parceiros. |
| Jurídico | <nome/cargo> | Avaliação legal e preservação de evidência. |

## 3. Severidade

| Severidade | Critério | SLA de triagem | Comunicação |
|---|---|---|---|
| CRITICO | Dado pessoal exposto, credencial mestra vazada, invasão ativa, perda de integridade, sistema indisponível para clientes críticos. | 15 min | DPO + direção imediatos; avaliar ANPD/titulares. |
| ALTO | Acesso indevido limitado, segredo de ambiente não-prod vazado, exploração provável sem confirmação de dado exposto. | 1h | Security owner + DPO se houver dado pessoal. |
| MEDIO | Vulnerabilidade explorável com mitigação disponível, tentativa de ataque bloqueada, falha de controle detectada. | 1 dia útil | Registrar e corrigir com plano datado. |
| BAIXO | Hardening, falso positivo, melhoria preventiva sem exploração conhecida. | 5 dias úteis | Backlog de segurança. |

## 4. Fluxo de resposta

### 4.1 Detectar

- Fonte: alerta, log, cliente, auditoria, bug report, fornecedor, pesquisador.
- Registrar horário UTC, fonte, resumo, sistemas afetados e evidência inicial.
- Abrir registro em `docs/operacao/incidentes/<YYYY-MM-DD-slug>.md` usando `post-mortem.template.md`.

### 4.2 Conter

Escolher a contenção menos destrutiva que interrompa o risco:

- Rotacionar segredo comprometido.
- Revogar sessão/token.
- Bloquear rota, IP, tenant ou integração.
- Desativar feature flag.
- Isolar serviço/worker.
- Congelar deploy se o incidente estiver ativo.

Toda contenção precisa ter dono, horário e efeito esperado.

### 4.3 Preservar evidência

- Copiar logs relevantes para local imutável ou com controle de alteração.
- Não apagar recurso comprometido antes de coletar evidência mínima.
- Registrar comandos executados durante contenção.
- Mascare PII em relatórios operacionais; evidência bruta fica restrita.

### 4.4 Erradicar

- Corrigir causa raiz.
- Remover backdoor, segredo, pacote ou configuração vulnerável.
- Atualizar dependência comprometida.
- Adicionar teste/hook/auditor que impediria recorrência.

### 4.5 Recuperar

- Restaurar serviço de forma controlada.
- Validar integridade de dados.
- Rodar smoke test e checagem de segurança relevante.
- Monitorar por pelo menos <janela> após recuperação.

## 5. Incidente com dado pessoal

Se houver indício de dado pessoal exposto, alterado, perdido ou acessado indevidamente:

- Acionar DPO imediatamente.
- Identificar titulares, categorias de dado, volume, origem, período e consequência provável.
- Avaliar comunicação à ANPD e aos titulares conforme LGPD Art. 48.
- Registrar base da decisão, mesmo quando decidir não comunicar.

## 6. Comunicação

| Público | Quando comunicar | Dono | Canal |
|---|---|---|---|
| Direção | CRITICO/ALTO imediato | Incident commander | <canal> |
| DPO | Qualquer suspeita de dado pessoal | Security owner | <canal> |
| Clientes afetados | Quando houver impacto confirmado ou obrigação legal | Comunicação + DPO | <canal> |
| ANPD | Quando incidente puder acarretar risco ou dano relevante aos titulares | DPO + Jurídico | Canal oficial |
| Pesquisador externo | Se veio por disclosure responsável | Security owner | SECURITY.md |

## 7. Pós-incidente

Em até 5 dias úteis após estabilizar:

- Preencher post-mortem.
- Listar causa raiz, causa contribuinte e controles ausentes.
- Criar tasks corretivas com dono e prazo.
- Atualizar `threat-model.md`, `dependency-policy.md`, `criptografia-policy.md` ou `key-management-policy.md` se necessário.
- Revisar se `SECURITY.md` e canais de reporte funcionaram.

## 8. Checklist de promoção draft → stable

- [ ] Papéis nomeados.
- [ ] Severidades e SLAs aprovados.
- [ ] Canal de acionamento testado.
- [ ] Fluxo com dado pessoal validado pelo DPO.
- [ ] Modelo de post-mortem referenciado.
- [ ] Primeiro tabletop exercise executado e registrado.
- [ ] `revisado-em` atualizado; `status: stable`.
