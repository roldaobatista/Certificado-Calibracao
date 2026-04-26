---
id: R6
version: 1
status: active
owner: lgpd-security
rto: 4h
rpo: "depende do último backup"
dispatcher: lgpd-security + product-governance
executor: lgpd-security
---

# R6 — Incidente de segurança

## Trigger

Executar quando houver suspeita ou confirmação de comprometimento da confidencialidade, integridade ou disponibilidade do sistema:

- acesso não autorizado detectado em logs (SIEM, CloudTrail, audit log);
- exfiltração ou vazamento de dados pessoais (clientes, certificados, trilhas de audit);
- comprometimento de credencial privilegiada (KMS, database, admin);
- malware ou ransomware em ambiente de produção;
- insider threat com acesso a dados regulatórios;
- alerta de vulnerabilidade crítica (CVSS >= 9.0) com exploit público confirmado.

## Impacto

Dados pessoais podem estar expostos, acionando obrigações LGPD (notificação à ANPD e titulares). A integridade de certificados emitidos e da trilha de audit pode estar sob suspeita. Emissão regulada deve congelar até contenção e triagem inicial. Reputação e acreditação podem ser afetadas se o incidente for comunicado ao Inmetro/Cgcre.

## Papéis

- Dispatcher: `lgpd-security` e `product-governance`.
- Executor: `lgpd-security`.
- Apoio: `backend-api` para freeze de emissão e análise técnica; `db-schema` para preservação de logs; `legal-counsel` para notificações regulatórias; `senior-reviewer` para análise de código afetado.
- Comunicação externa: `legal-counsel` coordena notificação à ANPD, titulares e órgãos reguladores quando aplicável.

## Passos

1. Ativar contenção imediata: freeze de emissão, revogação de sessões ativas, rotação de credenciais suspeitas.
2. Abrir incidente formal em `compliance/incidents/<YYYY-MM-DD>-security-incident-<slug>.md`.
3. Preservar evidências: snapshot de logs, capturas de tela, hashes de artefatos afetados. Não apagar logs.
4. Isolar sistemas comprometidos: desabilitar conta/API key suspeita, restringir acesso de rede se necessário.
5. Avaliar escopo: quais dados foram acessados, quantos titulares afetados, quais certificados ou trilhas estão sob suspeita.
6. Se dados pessoais foram expostos, iniciar processo de notificação LGPD em até 72h da descoberta (contato com `legal-counsel`).
7. Corrigir a causa raiz: patch, reconfiguração, remoção de acesso indevido, atualização de dependência.
8. Reconstruir ambiente se necessário a partir de backup íntegro (acionar `R7 — Backup Restore` se aplicável).
9. Revalidar integridade da hash-chain de audit após contenção.
10. Emitir novo checkpoint assinado do audit log.
11. Remover freeze de emissão apenas após validação completa e aprovação do dispatcher.
12. Realizar post-mortem em até 5 dias úteis e arquivar em `compliance/incidents/`.

## Validação

1. Confirmar que credenciais rotacionadas não mais funcionam.
2. Rodar `pnpm check:all`.
3. Rodar `pnpm test:tenancy` e `pnpm test:security`.
4. Verificar que `pnpm audit-chain:verify` aceita a cadeia após o incidente.
5. Confirmar que `pnpm worm-check` passa (nenhum artefato regulatório alterado indevidamente).
6. Emitir certificado dogfood em staging e verificar QR.

## Evidência

Arquivar em `compliance/runbooks/executions/<YYYY-MM-DD>-r6-security-incident-<slug>/`:

- `summary.md` com timeline, IOCs, escopo, decisões e resultados;
- logs preservados (hashes, não conteúdo sensível);
- evidência de contenção (screenshots, configurações alteradas);
- notificações LGPD e regulatórias emitidas;
- post-mortem;
- PRs de correção;
- parecer de `legal-counsel` quando aplicável.

## Drill

- Frequência: semestral.
- Ambiente: staging.
- Cenário: simular exfiltração de dados de cliente a partir de credencial vazada, executar contenção, notificação fictícia (sem envio real) e recuperação.
- Critério de sucesso: contenção em menos de 30 minutos, triagem em menos de 2h, RTO de 4h respeitado.

## Revisão

Revisar após incidente real, alteração na arquitetura de segurança, troca de provider cloud, mudança na legislação LGPD ou após drill. Mudança substantiva exige ADR.
