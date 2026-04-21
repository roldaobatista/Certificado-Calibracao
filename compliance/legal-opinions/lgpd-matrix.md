---
id: LGPD-MATRIX-MVP
status: approved
owner: lgpd-security
reviewed_by_role: legal-counsel
date: 2026-04-21T05:32:00-04:00
---

# Matriz controlador/operador e suboperadores

## Matriz de tratamento

| Classe de dado | Papel Aferê | Base legal (LGPD) | Retenção |
|---|---|---|---|
| Usuários da plataforma (nome, e-mail, credenciais) | Controlador | Execução de contrato (art. 7 V) | Ativa + 5 anos pós-desligamento |
| Clientes finais do laboratório (cadastros, contatos) | Operador | Sob instrução do controlador (laboratório) | Conforme instrução do lab; mín. 5 anos para registros técnicos |
| Leituras, evidências, certificados | Operador | Obrigação legal do lab (art. 7 II) + Execução de contrato (art. 7 V) | Mín. 5 anos; configurável no plano (5/10 anos) |
| Audit logs (identidade do ator + ação) | Controlador | Legítimo interesse (art. 7 IX) + obrigação legal | Mín. 10 anos; PII pseudonimizável sem quebra de hash chain |
| Biometria Android (2º fator local) | Não coletada | — | Template permanece no dispositivo via Android Keystore; Aferê não recebe o template |

## Suboperadores revisados

| Suboperador | Papel | Escopo |
|---|---|---|
| Hostinger | Suboperador | Hospedagem principal do MVP |
| Backblaze B2 | Suboperador | Storage imutavel e retenção regulatória |
| AWS KMS `sa-east-1` | Suboperador | Assinatura, material criptográfico e chaves |
| Grafana Cloud | Suboperador | Observabilidade operacional |
| Axiom | Suboperador | Telemetria e analytics operacional |

## Observações

- A matriz serve como anexo de referência contratual do DPA.
- Revisão de suboperadores deve acompanhar qualquer mudança material de infraestrutura.
- Pedidos baseados no art. 18 da LGPD exigem distinção entre dados tratados como Controlador e dados tratados como Operador.
