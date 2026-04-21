# Coverage Report

> Gerado por `pnpm validation-dossier:write`. Não editar manualmente.

## PRD §13

- Total de critérios: 22
- Critérios com requisito mapeado: 22
- Critérios validados por teste ativo: 13
- Critérios sem requisito mapeado: 0

## Validados

- §13.2: REQ-PRD-13-02-STANDARD-ELIGIBILITY-BLOCK — O sistema **bloqueia** uso de padrão vencido, sem certificado, fora de faixa.
- §13.3: REQ-PRD-13-03-CERTIFICATE-MEASUREMENT-DECLARATIONS — O certificado é emitido com **resultado, incerteza expandida e fator k declarado**.
- §13.4: REQ-PRD-13-04-TECHNICAL-REVIEW-SIGNATURE-AUDIT — A revisão técnica e a assinatura ficam **registradas com identidade, timestamp e dispositivo**.
- §13.6: REQ-PRD-13-06-CRITICAL-EVENT-AUDIT-TRAIL — Todo evento crítico aparece na **trilha de auditoria imutável**.
- §13.7: REQ-PRD-13-07-ANDROID-SYNC-IDEMPOTENCY — A sincronização Android → backend é **idempotente e resiliente** a perda de rede.
- §13.10: REQ-PRD-13-10-SCOPE-CMC-BLOCK — Certificado emitido por laboratório acreditado respeita **escopo e CMC**.
- §13.13: REQ-PRD-13-13-RLS-ISOLATION — **Multitenancy isolada por RLS** verificada por testes automatizados de cross-tenant leak (zero vazamentos).
- §13.15: REQ-PRD-13-15-REGULATORY-PROFILES-PDF — Sistema reconhece os **3 perfis regulatórios** (Tipo A/B/C) e seleciona automaticamente o template de PDF correspondente; tentativa de uso indevido de selo Cgcre/RBC é bloqueada.
- §13.18: REQ-PRD-13-18-VALIDATION-DOSSIER — **Plano de Validação do Software Aferê** aprovado e executado: protocolo formal, casos-teste normativos (incluindo ≥10 cenários-referência EURAMET cg-18 rodados em CI para a engine de incerteza — release bloqueado se qualquer divergir além de ε declarado), rastreabilidade requisito→teste, registro de evidências e procedimento de revalidação após mudança relevante (ISO/IEC 17025 §7.11).
- §13.19: REQ-PRD-13-19-AUDIT-HASH-CHAIN, REQ-PRD-13-19-TENANT-SQL-LINTER, REQ-PRD-13-19-WORM-STORAGE-CHECK — **Hardening de multitenancy e audit log**: pool de conexões fail-closed sem `tenant_id`; linter de PR rejeita SQL sem `organization_id`; fuzz cross-tenant semanal em CI; audit log em object storage WORM (object lock) com checkpoints assinados periodicamente.
- §13.20: REQ-PRD-13-20-OFFLINE-SYNC-CHAOS — **Modelo de sincronização offline documentado e testado**: event sourcing por OS, idempotência por `(device_id, client_event_id)`, optimistic locking por agregado, lock exclusivo por OS após início da assinatura, matriz de conflitos com política de merge/rejeição por tipo. Teste de caos: 1.000 OS geradas offline por ≥ 5 dispositivos com sync randomizado — zero perdas, zero duplicatas.
- §13.21: REQ-PRD-13-21-LEGAL-OPINION-DPA — **Parecer jurídico formal** sobre assinatura eletrônica auditável (MP 2.200-2 §10 II) anexado ao dossiê; minuta de DPA e matriz controlador/operador (§11.4) revisadas por advogado LGPD.
- §13.22: REQ-PRD-13-22-NORMATIVE-GOVERNANCE-OWNER — **Owner de governança normativa** nomeado com RACI e orçamento antes do go-live (§16.4).

## Mapeados sem validação ativa

- §13.1: REQ-PRD-13-01-MOBILE-OFFLINE-CALIBRATION — Uma calibração de balança IPNA pode ser executada do início ao certificado **exclusivamente pelo celular**, offline.
- §13.5: REQ-PRD-13-05-PUBLIC-QR-AUTHENTICITY — O QR code do certificado **valida autenticidade publicamente**.
- §13.8: REQ-PRD-13-08-EQUIPMENT-CUSTOMER-ADDRESS — O cadastro de equipamento exige obrigatoriamente vínculo com cliente e endereço.
- §13.9: REQ-PRD-13-09-SIGNATORY-COMPETENCE-BLOCK — Signatário sem competência para o tipo de instrumento **não consegue assinar**.
- §13.11: REQ-PRD-13-11-AUTH-SSO-MFA — Auto-cadastro funciona com e-mail/senha **e** SSO (Google/Microsoft/Apple); MFA obrigatório para signatários e admins.
- §13.12: REQ-PRD-13-12-ONBOARDING-WIZARD-BLOCKS — **Wizard de Onboarding (§7.14)** completável em ≤ 1 hora pelo Administrador inicial, com bloqueios duros para emitir o 1º certificado.
- §13.14: REQ-PRD-13-14-SEQUENTIAL-NUMBERING — Numeração sequencial por organização sem colisão entre tenants.
- §13.16: REQ-PRD-13-16-CONTROLLED-REISSUE — **Reemissão controlada (§17.8)** funciona com dupla aprovação, versionamento R1/R2, hash anterior preservado e notificação automática ao cliente.
- §13.17: REQ-PRD-13-17-PUBLIC-QR-MINIMAL-METADATA — Página pública de verificação por QR responde corretamente para certificado autêntico, reemitido e não localizado (§17.5.6) e **expõe apenas metadados mínimos** (sem dados de cliente final, sem PDF completo sem autenticação).

## Sem Requisito Mapeado

- Nenhum.
